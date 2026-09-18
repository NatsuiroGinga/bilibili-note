---
title: "2026-CALIBURN-Regime-Dependent-Conformal-Risk-Control-IDS"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-CALIBURN-Regime-Dependent-Conformal-Risk-Control-IDS.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# CALIBURN: Operationally Calibrated Streaming Intrusion Detection with Regime-Dependent Conformal Risk Control

Michel A. Youssef

Independent Researcher, Beirut, Lebanon

## Abstract

Streaming network intrusion detection systems must process flows continuously under bounded memory, yet most leave alerting-threshold selection as a post-hoc tuning problem that is incompatible with production deployment, where operators commit in advance to alert budgets, misclassification costs, and Service Level Objectives. We present CALIBURN, a streaming alerting pipeline that derives its decision threshold from these operational inputs rather than from a label-dependent validation search. CALIBURN composes, on a single streaming substrate, truncated Bayesian online change-point detection, isotonic calibration of the change-point posterior to an empirical conditional attack probability $\hat { P } ( y _ { t } \mid \textit { \textbf { \ i } } | \textit { \textbf { s } } _ { t } )$ , cost-sensitive thresholding from operator-specified costs, a Conformal Risk Control (CRC) wrapper that converts an alert budget α into a threshold with marginal false-positive validity under exchangeability, and multi-window burn-rate alerting adapted from Site Reliability Engineering practice. Each component is individually established; the contribution is their integration and a falsifiable empirical finding about that integration: the operational behaviour of calibration and conformal risk control is strongly regime-dependent across attack prevalence. Evaluating across three prevalence regimes — LITNET-2020 (5.2 percent), CICIDS2017 (22.06 percent), and UNSW-NB15 (64 percent) — we show that CALIBURN achieves AUC-PR 0.943 in the rare-attack regime it targets, outperforming the best streaming baseline by 2.21× and the best batch reference by 4.12×, with isotonic calibration reducing Brier score by 30 percent; that it remains the strongest streaming method at moderate prevalence while a batch density method overtakes it; and that all streaming methods, including CALIBURN, converge toward the prevalence floor under base-rate inversion. A TTL-feature ablation on UNSW-NB15 confirms this high-prevalence collapse is intrinsic to the streaming setting rather than a removable dataset artifact. We additionally characterise two distinct mechanisms — a theoretical CRC overshoot $2 B / ( n _ { 0 } + 1 )$ and an empirical-density degeneracy — by which conformal alerting collapses at very small α, and propose both as explicit predeployment checks. All code, configurations, and experimental artifacts are released under Apache 2.0 (Zenodo DOI 10.5281/zenodo.20074590) for full reproducibility.

Keywords: streaming anomaly detection, network intrusion detection, Bayesian online change-point detection, conformal risk control, calibration, cost-sensitive learning, service-level objective, alert fatigue, reproducibility

## 1. Introduction

Network intrusion detection systems in production deployments face a chronic gap between the statistical anomaly score produced by a detector and the operational alert that an analyst eventually sees. Most academic intrusion detection systems present a single threshold-tuned point on the precision-recall curve, leaving the practitioner to translate it into alerts compatible with finite analyst capacity, asymmetric incident costs, and Service Level Objectives. This is not a peripheral concern: a qualitative study of security operations centre analysts found that practitioners dismiss the overwhelming majority of generated alerts as false positives (Alahmadi et al., 2022), so the alert budget, not the raw anomaly score, is frequently the dominant operational constraint. Threshold-tuning on test labels compounds the problem with a methodological gap: the threshold cannot be specified before deployment because the labels are not yet available, and in real operations labels are scarce, delayed, or missing entirely. An operationally useful streaming detector must therefore derive its threshold from quantities the organisation already commits to in advance — false-negative cost, false-positive cost, and an alert budget — rather than from a label-dependent search that production cannot run.

This paper presents CALIBURN, a streaming alerting pipeline whose threshold is derived from operational commitments rather than post-hoc tuning. CALIBURN composes five layers. The first is a truncated Bayesian online change-point detector (Adams and MacKay, 2007; Knoblauch and Damoulas, 2018) that produces a per-flow run-length posterior $s _ { t } = P ( r _ { t } =$ $0 \ | \ x _ { 1 : t } )$ with bounded update cost. The second is an isotonic regression calibration map (Zadrozny and Elkan, 2002; Niculescu-Mizil and Caruana, 2005) fit on the validation split that produces the empirical conditional probability $\hat { p } _ { t } = \hat { P } ( y _ { t } = 1 \mid s _ { t } )$ The third is a cost-sensitive decision threshold $\tau ^ { * } = C _ { F P } / ( C _ { F P } + C _ { F N } )$ (Elkan, 2001) derived from operator-specified misclassification costs. The fourth is a Conformal Risk Control wrapper (Angelopoulos et al., 2024) that maps an operator-specified alert budget α to a threshold $\hat { \tau } _ { \alpha }$ with marginal validity guarantees under exchangeability. The fifth is a multi-window, multi-burn-rate alerting policy (Beyer et al., 2018) that converts threshold crossings into escalated alerts only when the alert budget is being consumed at unsustainable velocity. Each of these components is individually established in its own literature. Their integration on a single streaming substrate — and in particular the use of an alerting layer borrowed from Site Reliability Engineering rather than from the intrusiondetection literature — is the system contribution of this paper. Conformal and calibration-aware methods for intrusion detection are an actively developing area. Two concurrent 2026 eforts are closest to ours and clarify what CALIBURN does and does not do. Barrett et al. (2026) apply conformal evaluation to quantify predictive uncertainty and detect concept drift in supervised IDS classifiers, triggering retraining; Gurjar and Camp (2026) forecast whether the intensity of an existing alert stream will cross a high quantile in the near future. CALIBURN addresses a diferent question from either: it uses Conformal Risk Control to set a false-positive-bounded alerting threshold on an unsupervised streaming change-point score, rather than to quantify classifier uncertainty (as in FIRCE) or to forecast future alert intensity from alerts already raised (as in the tail-risk setting). Section 2 develops this positioning in detail.

A careful reading of each layer reveals a tension. Each individual component has well-understood guarantees in isolation. BOCPD is a calibrated posterior over run length under its generative model. Isotonic regression is the empirical Bayes monotone map between any score and the conditional probability of the label given that score. Conformal Risk Control provides a marginal expectation bound on a chosen loss under exchangeability of calibration and test samples. The cost-sensitive threshold is Bayes-optimal under a correctly specified probability. Burn-rate alerting controls long-run alert rates relative to a service-level commitment. Yet the composition of these layers in a streaming network setting raises substantive questions. Is $\hat { p } _ { t } = \hat { P } ( y _ { t } = 1 \mid s _ { t } )$ a useful probability of attack, given that $s _ { t }$ measures regime shift rather than attack identity? Does CRC’s exchangeability assumption survive in a streaming context with drift, evolving service mixes, and adversarial behaviour? In which attack-prevalence regimes do these components support each other rather than interfere? These are empirical questions, and the answer to the third — that the composition’s operational behaviour depends sharply on attack prevalence — is the central finding of this paper.

We answer these questions empirically rather than by asserting uniform superiority. We evaluate the pipeline across three publicly available NIDS datasets that span the realistic prevalence range encountered in production: LITNET-2020 (Damaševičius et al., 2020) at 5.2 percent attack prevalence; CICIDS2017 (Sharafaldin et al., 2018; Engelen et al., 2021; Liu et al., 2022) at 22.06 percent; and the testing partition of UNSW-NB15 (Moustafa and Slay, 2015) at approximately 64 percent attack prevalence. For each regime we report not just headline metrics but reliability diagrams, ablations across the four post-hoc layers, and an operational threshold map that practitioners can use to decide whether the pipeline is appropriate for their setting.

The contributions of this paper are as follows.

First, and most importantly, we establish empirically that the operational behaviour of calibrated, conformal-risk-controlled streaming alerting is strongly regime-dependent across attack prevalence — a dependence that, to our knowledge, has not previously been characterised for this class of pipeline. The four-variant ablation in Section 5.6 shows that the full pipeline dominates strawman variants in the rare-attack regime but degenerates in higher-prevalence regimes via a documented Conformal Risk Control mechanism rather than via algorithmic failure. This is a falsifiable finding with direct deployment consequences: it tells a practitioner, in advance, the prevalence range within which the pipeline can be trusted.

Second, we identify and quantify two distinct CRC-collapse mechanisms relevant to operator-supplied alert budgets. The first is the theoretical overshoot of the CRC procedure of Angelopoulos et al. (2024), which can overshoot the target α by up to $2 B / ( n _ { 0 } + 1 )$ , where B is the loss upper bound and $n _ { 0 }$ is the size of the validation negative set. The second is an empirical-density failure mode that arises when the calibrated-score distribution of validation negatives is heavily concentrated below the candidate CRC thresholds, leaving no $\tau \in [ 0 , 1 ]$ for which $\widehat { \mathrm { F P R } } ( \tau ) \leq \alpha - 1 / ( n _ { 0 } + 1 )$ except $\tau  1$ . The procedure then trivially satisfies the bound by producing zero alerts. Both mechanisms can drive $F _ { 1 }  0$ but operate via diferent routes: the first via the theoretical overshoot bound, the second via CDF-sparsity in the upper tail. We quantify both numerically for our three datasets and propose them as two explicit deployment checks before applying CRC at small $\alpha .$

Third, we contribute an explicit calibration analysis. Isotonic regression reduces Brier score by 30 percent on LITNET-2020, 32 percent on CI-CIDS2017, and 63 percent on UNSW-NB15 compared to the raw BOCPD posterior, with calibration error reductions of comparable magnitude. We discuss the epistemological status of the resulting $\hat { p } _ { t } = \hat { P } ( y _ { t } = 1 \mid s _ { t } )$ , which is an empirical conditional probability rather than an unconditional posterior of attack given the raw stream.

Fourth, we test an alternative explanation for the UNSW-NB15 collapse. Prior work documents that the UNSW-NB15 TTL features (sttl, dttl, ct\_state\_ttl) are correlated with class labels through the IXIA PerfectStorm testbed routing topology (Moustafa and Slay, 2015; Mohy-Eddine et al., 2023; Komisarek et al., 2021). We re-run the full pipeline with these features ablated and find that CALIBURN’s performance under base-rate inversion remains essentially unchanged: AUC-PR moves from 0.677 to 0.694 (calibrated, isotonic); AUC-ROC moves from 0.50 to 0.53. The collapse is intrinsic to streaming under high prevalence, not an artifact of removable feature leakage.

Fifth, we honestly delineate the operational scope of CALIBURN. The pipeline is best suited to deployments where (a) attack prevalence is below approximately 25 percent, (b) the operator-specified alert budget α is comfortably above $2 B / ( n _ { 0 } + 1 )$ for the chosen validation set size, and (c) the calibration distribution is approximately exchangeable with deployment. In settings that violate any of these conditions, the pipeline degrades in characterised ways that we document.

Scope and limitations.. CALIBURN is deliberately specialized, and we state its boundaries plainly rather than obscure them. It targets the rare-attack regime typical of production monitoring and is not intended to dominate at high attack prevalence, where batch density methods with full training access remain stronger; we demonstrate this boundary experimentally. The CRC validity guarantee is marginal and assumes approximate exchangeability between the calibration and deployment distributions, which holds only under bounded drift; we document where and how it fails. The cost-sensitive threshold requires the operator to supply a meaningful cost ratio, which not every organisation can estimate reliably. And the measured per-flow latency positions CALIBURN as a flow-level triage layer over aggregated telemetry rather than an in-line wire-speed packet inspector. We regard making these boundaries explicit, and quantifying the failure modes at each one, as part of the contribution rather than a caveat to it.

The remainder of the paper is organized as follows. Section 2 reviews related work in streaming anomaly detection, Bayesian online change-point detection, cost-sensitive learning, SLO-based alerting, conformal prediction, and NIDS dataset critique. Section 3 presents CALIBURN’s five-component design and the assumptions under which each component is valid. Section 4 describes the experimental setup including chronological splits, evaluation metrics, the TTL-ablation protocol on UNSW-NB15, and the reliability diagram methodology. Section 5 reports results across the three regimes. Section 6 discusses limitations, threats to validity, and the explicit operational scope under which CALIBURN is appropriate. Section 7 concludes.

## 2. Background and Related Work

This section positions CALIBURN across four research areas that usually remain separate: streaming anomaly detection, Bayesian online changepoint detection, cost-sensitive decision theory, and SLO-based alerting. The method proposed in this paper does not claim that any one of these components is new by itself. The contribution is the way they are combined into a streaming security detector whose threshold is derived from operational inputs rather than selected after the fact.

We first situate CALIBURN relative to the two concurrent 2026 eforts noted in the introduction, because both combine conformal ideas with intrusion detection and the distinctions are instructive. Barrett et al. (2026) introduce FIRCE, which augments a supervised IDS classifier with conformal evaluation: conformal prediction sets quantify the classifier’s predictive uncertainty, and shifts in that uncertainty signal concept drift and trigger model retraining. The conformal machinery there is a drift-detection and uncertainty-quantification instrument layered on a trained classifier. Gurjar and Camp (2026) take a forecasting view: they model the IDS alert stream as a time series and use gradient-boosted trees on intensity, volatility, and momentum features to predict whether alert intensity will exceed its 95th percentile within a short horizon, an early-warning signal for analyst-overload surges. CALIBURN shares the operational motivation of both — reducing the burden that uncalibrated alerting places on analysts — but occupies a distinct point in the design space. It is unsupervised (a streaming changepoint detector, not a trained classifier), it uses Conformal Risk Control rather than conformal prediction sets or conformal evaluation, and it applies that risk control to a single, specific operational quantity: the decision threshold that converts a calibrated streaming score into an alert under a false-positive budget. It does not forecast future alert intensity, and it does not quantify a supervised classifier’s uncertainty. The three lines of work are complementary: FIRCE decides when to retrain, the tail-risk forecaster decides when to expect a surge, and CALIBURN decides when a flow should raise an alert given an operator’s cost and budget commitments.

## 2.1. Streaming Anomaly Detection

Streaming anomaly detection has been studied through several families of methods. Tree-based methods are a major line of work. Half-Space Trees were introduced as a fast one-class anomaly detector for evolving data streams, with the goal of detecting anomalous points without repeatedly rebuilding a full batch model (Tan et al., 2011). Robust Random Cut Forest, introduced by Guha et al. (2016), takes a related stream-oriented approach, using random cut trees as a sketch of the input stream and updating that sketch dynamically.

Another line of work uses lightweight ensembles. LODA (Pevný, 2016) is based on the idea that an ensemble of weak random-projection detectors can produce a strong anomaly detector while remaining fast enough for online use. Pevný explicitly motivates LODA for settings with many samples, concept drift, and the need for online updates. Sliding-window adaptations of batch methods, such as iForest\_ASD, use a moving Isolation Forest over recent windows of the stream. Ding and Fei (2013) proposed this approach specifically to handle the infinite volume, fast arrival, and concept-drift properties of streaming data. Neural methods have also been adapted to online intrusion detection. Kitsune, and its core algorithm KitNET (Mirsky et al., 2018), use an ensemble of autoencoders to learn normal network behavior in an unsupervised and eficient online manner, with the specific goal of making NIDS practical on resource-constrained gateways. Cao et al. (2025) provide a recent benchmark of these and related streaming detectors.

These methods are valuable because they satisfy the basic streaming constraint: the detector can update incrementally as data arrives. However, they usually leave the alerting threshold as a separate tuning problem. In practice, thresholds are often chosen through validation search, percentile rules, or heuristic score cutofs. CALIBURN addresses a diferent part of the problem. It does not only ask how to score a flow online. It asks how that score should become an alert when the operator has a finite false-positive budget and a real cost for missing attacks.

## 2.2. Bayesian Online Change-Point Detection

Bayesian Online Change-Point Detection (BOCPD) was introduced by Adams and MacKay (2007) as an online method for detecting abrupt changes in the generative parameters of a data sequence. The key idea is to maintain a posterior distribution over the current run length, meaning the number of observations since the most recent change-point. As each new observation arrives, the posterior is updated using a message-passing recursion rather than waiting for the full sequence.

Classical sequential detection provides the broader statistical background for this work. Wald (1945)’s sequential probability ratio test established the basic logic of making decisions sequentially rather than after collecting a fixed sample, while Page (1954)’s CUSUM procedure introduced a practical cumulative inspection scheme for detecting distributional shifts. Lorden (1971) later formalized quickest detection as a problem of reacting to a change in distribution under delay and false-alarm constraints, and Shiryaev (1978) connected quickest detection to optimal stopping. CALIBURN follows this same sequential-detection tradition, but uses BOCPD because it gives an explicit run-length posterior that can be updated online and then connected to an operator-facing threshold.

This is closely related to other online change-point work. Fearnhead and Liu (2007) developed an online inference method for multiple change-point problems, using filtering and particle methods to represent the posterior over change-point structures. Their exact filtering algorithm has quadratic cost in the number of observations, which is important because it shows why direct online change-point inference can become expensive on long streams. Later variants extended the BOCPD idea to richer observation models, including Gaussian process change-point models (Saatçi et al., 2010), and to spatiotemporal settings.

The issue for security monitoring is that network streams can be long and continuous. A detector that grows in cost with the full history is not practical. Knoblauch and Damoulas (2018) extended BOCPD to online spatiotemporal change-point detection with model selection, and Knoblauch et al. (2018) reported linear time and constant space behavior under their scalable formulation. CALIBURN follows this practical direction by truncating the run-length posterior to a maximum length L. This keeps the update bounded and makes BOCPD usable as a streaming anomaly detector rather than only as an elegant Bayesian model.

## 2.3. Cost-Sensitive Learning and Operational Thresholds

Cost-sensitive learning provides the decision-theoretic basis for CALIBURN’s threshold. In normal binary classification, false positives and false negatives are often treated as equal. That assumption is usually wrong in security. A missed attack and a false alert do not have the same operational cost, and the correct decision rule should reflect that diference.

Elkan (2001) provides the most direct reference for this paper. The work revisits decision-making when misclassification errors carry diferent penalties and makes clear that the decision rule should be tied to the cost matrix. For a calibrated posterior probability $p ,$ , with false-positive cost $C _ { F P }$ and falsenegative cost $C _ { F N }$ , the cost-sensitive alert threshold is:

$$
\tau^ {*} = \frac {C _ {F P}}{C _ {F P} + C _ {F N}}.\tag{1}
$$

This means the threshold should come from the relative cost of the two mistakes, not from a blind search over the validation set. Related work such as MetaCost (Domingos, 1999) also tries to make classifiers cost-sensitive, but through a wrapper procedure around existing classifiers. The calibration of probability estimates remains important here. Niculescu-Mizil and Caruana (2005) showed that many classifiers can have strong discrimination while still producing distorted probability estimates, which is why calibrated posterior scores matter when the output is used for cost-sensitive decisions (Zadrozny and Elkan, 2002).

CALIBURN uses the decision-theoretic rule directly. The detector produces a posterior-like streaming score, the operator specifies the cost ratio, and the threshold follows from that cost ratio. The attack prior is not folded into the threshold again, because it already enters the streaming model through the BOCPD hazard parameter. This keeps the statistical prior and the operational cost model separate.

## 2.4. SLO-Based Alerting in Site Reliability Engineering

The alerting layer in CALIBURN comes from Site Reliability Engineering rather than from classical intrusion detection. Google’s SRE practice formalized the idea that reliability should be managed through service-level objectives and error budgets. The SRE book (Beyer et al., 2016) describes how Google uses these ideas to build and operate large production systems, and the SRE Workbook (Beyer et al., 2018) turns them into concrete operational practices.

The most relevant concept for this paper is multi-window, multi-burnrate alerting. The Site Reliability Workbook explains that alerting logic can use multiple burn rates and time windows, and can fire when the burn rate exceeds a specified threshold. This helps balance fast detection against alert noise. A short window catches sudden spikes, while a longer window confirms that the budget is being consumed at a sustained rate. This is useful because a single error should not always page an operator, but a sustained pattern of errors should not be ignored.

Industrial deployments confirm the pattern beyond the original SRE framing. Large-scale infrastructure teams have adopted burn-rate alerting in production monitoring because it gives operators a way to separate short-lived noise from sustained budget exhaustion. In SRE, the budget is usually an availability or error budget. In CALIBURN, the same idea is applied to security alerting. A suspicious flow that crosses the cost-sensitive threshold consumes alerting budget. The burn-rate layer then decides whether that consumption pattern should become a ticket, a slow page, or a fast page. This is a deliberate separation between scoring, thresholding, and alert escalation.

## 2.5. NIDS Dataset Critique Literature

Network intrusion detection datasets have been heavily criticized in recent years, and this matters for the design of the experiments. CICIDS2017 (Sharafaldin et al., 2018) is one of the most widely used intrusion detection benchmarks, but later work showed that the dataset has significant problems. Engelen et al. (2021) revisited CICIDS2017 and found issues in trafic generation, flow construction, feature extraction, and labeling, then proposed improved processing to correct many of them. Liu et al. (2022) further document errors in CIC-IDS-2017 and CIC-CSE-IDS-2018 across the dataset creation lifecycle, including attack orchestration, feature generation, documentation, and labeling, and release a refined version that this paper uses.

Lanvin et al. (2023) additionally identify packet misordering, duplicate flows, undocumented capture gaps, and labelling errors that materially change detection performance, and Catillo et al. (2023) go further to question whether public NIDS benchmarks have produced concrete advances at all when accuracy gains are dominated by dataset artefacts rather than methodological progress. We use the corrected versions of CICIDS2017 in this paper for these reasons.

UNSW-NB15 is also widely used. Moustafa and Slay (2015) introduced it as a comprehensive dataset for network intrusion detection systems, and the oficial UNSW project page provides the published training and testing partitions. We use that partition because it is common in the literature, but we do not treat it as the main operational benchmark. Its high attack prevalence makes it a useful stress case for understanding what happens when the stream is no longer mostly benign.

LITNET-2020 is a more recent dataset collected from a real-world academic network. Damaševičius et al. (2020) present it as an annotated network flow dataset with real examples of normal and under-attack trafic, including 85 network flow features and 12 attack types. Broader methodological work has also warned against common mistakes in machine learning for security, including invalid evaluation assumptions and weak experimental hygiene. The “dos and don’ts” paper of Arp et al. (2022) is especially relevant because it argues that security ML results must be interpreted with care rather than treated as generic benchmark wins.

Overall, the experimental design follows the dataset-critique literature by using corrected datasets where available, treating high-prevalence partitions carefully, and avoiding the assumption that all NIDS benchmarks measure the same operational problem.

## 2.6. Operational Motivation and Gap Statement

The practical motivation for this work is alert fatigue. Security teams do not only need high anomaly scores. They need alerting rules that can be defended operationally. Alahmadi et al. (2022) studied SOC analysts’ perspectives on security alarms and found that practitioners reported high false-positive rates requiring manual validation. This is exactly the setting where a detector that only optimizes a benchmark score is incomplete.

The related work shows that all the pieces exist, but they have not been connected in this way. Streaming anomaly detectors can process data online, but their thresholds are usually selected through validation tuning or heuristic score cutofs. BOCPD provides a principled way to model streaming changes, but by itself it does not define an operational alerting policy. Costsensitive learning gives a clean decision rule for calibrated probabilities, but it is usually discussed in classification settings rather than streaming security. SLO-based burn-rate alerting gives operators a mature alerting framework, but it has mostly remained in service reliability and infrastructure monitoring.

CALIBURN fills this gap by combining these ideas into one detector. It uses truncated BOCPD to produce a streaming posterior change-point score, derives the threshold from the operator’s cost ratio, and uses SLO burn-rate logic to decide when suspicious events should escalate. The architectural point is the separation between statistical scoring, operational decision, and alerting policy. That separation is what makes the detector explainable before deployment, instead of relying on a threshold selected after looking at the validation or test behavior.

## 3. Method

In this section, we describe CALIBURN, a streaming anomaly detector designed for security settings where attacks are rare, labels are delayed or unavailable, and operators cannot aford an alerting system that depends on arbitrary threshold tuning. The main idea is simple. Instead of treating anomaly detection as only a scoring problem, CALIBURN treats it as an operational decision problem. A detector should not only say that a flow looks unusual. It should also decide when the score is strong enough to consume alerting budget, analyst time, and possibly incident response efort.

CALIBURN has three parts. First, it uses a truncated Bayesian online change-point detector to process network flows sequentially and produce a probabilistic anomaly score. Second, it converts operational inputs, such as the relative cost of a missed attack and the cost of a false alert, into a posterior decision threshold. Third, it wraps the detector with multi-window burn-rate alerting so that the system behaves more like an operational security control and less like an ofline machine learning benchmark. Figure 1 shows how these components are organized into three responsibility layers: statistical scoring, operational decision, and alerting policy.

CALIBURN architecture  
![](images/229774be5f6c4f5f8a4e1d63037685a1ca92f540f19283ebb363ad0905dc43ca.jpg)  
Figure 1: CALIBURN architecture, organized into three responsibility layers. Streaming network flows enter the truncated Bayesian online change-point detector, which produces a probabilistic anomaly score $s _ { t } = P ( r _ { t } = 0 \mid x _ { 1 : t } )$ . The cost-sensitive threshold $\tau ^ { * } =$ ${ C _ { F P } } / ( { C _ { F P } } + { C _ { F N } } )$ is derived from operator-specified costs, not from a validation set. The SLO burn-rate alerting layer escalates the resulting events into ticket, slow page, or fast page actions using multi-window burn-rate logic. Each layer can be inspected and adjusted independently of the others.

## 3.1. Problem Formulation

Let a network trafic stream be represented as a sequence of feature vectors:

$$
x _ {1}, x _ {2}, \ldots , x _ {t}, \quad x _ {t} \in \mathbb {R} ^ {d},\tag{2}
$$

where each $x _ { t }$ is a flow observed at time t, and d is the number of extracted features. The detector sees each flow once, in chronological order. At every time step, it must update its internal state and output an anomaly score:

$$
s _ {t} = f (x _ {t}, x _ {1: t - 1}),\tag{3}
$$

where $s _ { t }$ represents how suspicious the current flow is given the history observed so far. The final alerting decision is binary:

$$
a _ {t} = \left\{ \begin{array}{l l} 1, & s _ {t} > \tau \\ 0, & s _ {t} \leq \tau , \end{array} \right.\tag{4}
$$

where $a _ { t } = 1$ means an alert is raised and $\tau$ is the decision threshold.

The usual way to choose τ is to tune it on validation data. We consider this a weak choice for operational security. It may maximize a benchmark metric, but it does not explain why a real operator should accept that threshold. In a live environment, the question is not only “which threshold gives the best F1 score?” The real question is: “how many false alerts can we aford, and how bad is it if we miss a real attack?”

This is especially important in rare-attack settings. In these settings, ROC-AUC can look good even when the detector is not useful operationally, because the number of benign flows is very large. For this reason, we treat AUC-PR as the main evaluation metric, since it focuses directly on precision and recall under class imbalance (Saito and Rehmsmeier, 2015). The streaming constraint is also important. The detector cannot retrain on the full dataset every time a new flow arrives. It must update incrementally and keep bounded memory.

The problem studied in this paper is therefore not just anomaly scoring. It is streaming, cost-aware, operationally calibrated alerting.

## 3.2. Truncated Bayesian Online Change-Point Detection

The core probabilistic model in CALIBURN is BOCPD (Adams and MacKay, 2007). BOCPD was introduced as an online method for estimating whether a data-generating process has changed, while maintaining a posterior distribution over the current run length. A run length is the number of observations since the most recent change-point. If the run length is large, the model believes the stream has been stable for a while. If the run length resets to zero, the model believes a new regime has started.

In network security, this is a natural fit. A sudden change in the statistical behavior of flows may indicate scanning, flooding, lateral movement, or another abnormal condition. CALIBURN does not assume that every change-point is malicious. Instead, it uses the posterior change-point probability as an anomaly score that can later be converted into an operational alert.

Let $r _ { t }$ denote the run length at time t. BOCPD maintains the posterior:

$$
P (r _ {t} \mid x _ {1: t}).\tag{5}
$$

At each step, the model updates this posterior by combining three pieces of information: the previous run-length distribution, the predictive likelihood of the new observation, and a hazard function that controls the prior probability of a change-point. Each step, probability mass either grows, meaning the current run continues, or resets to $r _ { t } = 0$ with rate H. Unlikely observations under the current run shift more mass toward the reset case, but the hazard term ensures that some baseline reset probability is always present.

The anomaly score used by CALIBURN is:

$$
s _ {t} = P (r _ {t} = 0 \mid x _ {1: t}).\tag{6}
$$

This score has a direct interpretation. It is the posterior probability that the current flow begins a new regime.

The original BOCPD formulation is elegant, but the exact algorithm becomes expensive as the stream grows, because the number of possible run lengths increases with time. For real streaming detection, this is not acceptable. CALIBURN therefore uses a truncated run-length approximation. Instead of keeping all possible run lengths from 0 to t, it keeps only the most recent L run lengths:

$$
r _ {t} \in \{0, 1, \dots , L \}.\tag{7}
$$

This makes the update cost bounded. Knoblauch et al. (2018) later developed robust streaming variants of BOCPD with linear-time updates and constantspace posterior representations. Their result confirms that bounded-truncation approaches like ours can run continuously without re-fitting the model.

Within each run, CALIBURN uses a Gaussian observation model. This means that the model assumes flows in the same run are generated from a distribution with stable mean and variance. The model updates the suficient statistics of this distribution online. To avoid numerical instability, a variance floor is used. A warm-up period is also used before alerts are emitted, so that the model does not page operators before it has seen enough normal context. The update can be summarized in Algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Truncated BOCPD update
Require: New flow $x_t$, previous run-length posterior $P(r_{t-1} \mid x_{1:t-1})$, maximum run length $L$, hazard rate $H$, sufficient statistics for each run length
1: for each retained run length $r$ do
2: Compute the predictive likelihood of $x_t$
3: end for
4: Compute growth probabilities for continuing the current run
5: Compute reset probability for $r_t = 0$ using hazard rate $H$
6: Normalize all probabilities so they sum to one
7: Truncate the posterior to run lengths 0 through $L$
8: Update sufficient statistics for each retained run length
9: return Anomaly score $s_t = P(r_t = 0 \mid x_{1:t})$
</div>

This gives CALIBURN a probabilistic streaming score without retraining a batch model. The detector only needs the current flow, the retained runlength posterior, and the suficient statistics for the retained runs. Figure 2 illustrates the posterior dynamics of the truncated BOCPD on a synthetic stream containing one injected change-point.

## 3.3. SLO-Aware Threshold Derivation

The main contribution of CALIBURN is not only that it uses BOCPD. BOCPD already exists. The contribution is that CALIBURN connects the probabilistic score to an operational decision rule.

Most anomaly detectors output a score and then choose a threshold using grid search. This is common in papers, but it is not how production security teams think. A SOC or infrastructure team does not start by asking which threshold maximizes a validation metric. It starts by asking how costly a missed incident is, how much alert fatigue the team can tolerate, and how quickly an alert should consume the available operational budget.

(a) Observation stream (Gaussian, mean shift at t=300)  
![](images/5f6d67620053432e71728765951119f944b4e4b38ba02504db2968dbf0e6ec3b.jpg)  
(b) Run-length posterior $P ( r _ { t } \mid x _ { 1 : t } )$

![](images/a301f82811c22c98076ebb196770bb4185509a014b750dc0044be24dece3d7d4.jpg)

![](images/42903c097e3118c8c810177e7ce9558c27a8c97ccf9ec3dd631896a44fb13c4c.jpg)  
Figure 2: Truncated BOCPD posterior dynamics on a synthetic stream with one changepoint at $t { = } 3 0 0$ . (a) Observation stream with mean shift. (b) Run-length posterior $P ( \boldsymbol { r } _ { t } |$ $x _ { 1 : t } )$ visualized as a heatmap; the bright diagonal ridge representing the dominant run length grows with time and resets at the change-point. (c) The anomaly mass concentrated at recent run lengths (here illustrated as $P ( r _ { t } \leq 5 \mid x _ { 1 : t } )$ to make the discrete pulse visible) spikes sharply at the true change-point and crosses the cost-derived threshold $\tau ^ { * } = 0 . 0 9 1$ corresponding to cost ratio $C { = } 1 0$

CALIBURN uses cost-sensitive decision theory to make this connection explicit. Let:

$$
p _ {t} = P (y _ {t} = 1 \mid x _ {1: t})\tag{8}
$$

denote an ideal calibrated posterior probability that the current flow belongs to an attack or abnormal regime. Let $C _ { F P }$ be the cost of a false positive and $C _ { F N }$ be the cost of a false negative. If the detector raises an alert, the expected false-positive cost is:

$$
C _ {F P} (1 - p _ {t}).\tag{9}
$$

If the detector does not raise an alert, the expected false-negative cost is:

$$
C _ {F N} p _ {t}.\tag{10}
$$

A cost-sensitive alert is justified when the expected cost of staying silent exceeds the expected cost of alerting:

$$
C _ {F N} p _ {t} > C _ {F P} (1 - p _ {t}).\tag{11}
$$

Solving this inequality gives the cost-sensitive threshold $p _ { t } > \tau ^ { * }$ , where:

$$
\tau^ {*} = \frac {C _ {F P}}{C _ {F P} + C _ {F N}}.\tag{12}
$$

Equivalently, if $C = C _ { F N } / C _ { F P }$ , then:

$$
\tau^ {*} = \frac {1}{1 + C}.\tag{13}
$$

In the unrealistic case where $s _ { t }$ from BOCPD already equalled $p _ { t }$ , applying the threshold $\tau ^ { * }$ to $s _ { t }$ would be cost-optimal. In practice, $s _ { t }$ is the posterior probability that the run length resets to zero, which need not equal the posterior probability that the current flow is an attack. We treat this gap as a first-class concern. Section 3.4 introduces an explicit post-hoc calibration step that maps $s _ { t }$ to a calibrated estimate $\hat { p } _ { t }$ using validation labels, and a Conformal Risk Control wrapper that converts an operator-supplied alert budget α into a marginally-valid threshold $\hat { \tau } _ { \alpha }$ under exchangeability of validation and test negatives. The cost-sensitive derivation in this section is therefore a design principle: it specifies what the threshold should mean when applied to a calibrated probability. The implementation applies it to $\hat { p } _ { t }$ , not to $s _ { t }$ directly.

This threshold is cost-sensitive, not empirically tuned. It follows the same logic as classical cost-sensitive learning: diferent mistakes should not be treated as equal when their operational consequences are diferent. Elkan (2001)’s cost-sensitive learning framework is especially relevant here because it argues that once reliable probability estimates are available, the correct decision should be made explicitly using the cost matrix rather than by changing the training distribution blindly. Recent work (Yang and Bi, 2024) has further refined this view, showing that calibration and cost-sensitive thresholding are not strictly independent post-processing steps: an isotonic calibrator fit under symmetric proper scoring rules may suboptimally bin probabilities near the asymmetric cost-derived decision boundary. The conformal risk-control layer described in Section 3.4 substantially mitigates this concern by separately bounding the realised false-positive rate; the residual question of whether a cost-aware calibration objective would improve operational performance is a direction for future work.

For example, suppose a missed attack is considered 10 times worse than a false alert. Then $C = 1 0$ , and the threshold becomes:

$$
\tau^ {*} = \frac {1}{1 1} = 0. 0 9 1.\tag{14}
$$

This means that if the detector assigns more than 0.091, about 9 percent, posterior probability to an attack or change-point condition, alerting is justified by the cost model. If the missed-attack cost is much higher, the threshold becomes lower. If false positives are more expensive, the threshold becomes higher. Table 1 shows several cost-ratio values and the resulting thresholds.

Table 1: Cost ratio $C = C _ { F N } / C _ { F P }$ and the resulting cost-sensitive posterior threshold $\tau ^ { * }$

<table><tr><td>Cost ratio C</td><td>Threshold τ*</td></tr><tr><td>1</td><td>0.500</td></tr><tr><td>5</td><td>0.167</td></tr><tr><td>10</td><td>0.091</td></tr><tr><td>25</td><td>0.038</td></tr><tr><td>50</td><td>0.020</td></tr></table>

This table is important because it shows the operational meaning of the threshold. The threshold is not chosen because it looks good on a test set.

It comes from an explicit judgment about the cost of missing an attack compared with the cost of raising a false alert.

CALIBURN deliberately keeps the threshold formula independent of the attack prior π. The prior enters CALIBURN through the BOCPD model itself: the hazard parameter H encodes the prior probability of a changepoint per flow. Folding the prior into the posterior threshold as well would double-count the same information. In other words, the model uses the prior to produce the posterior score, and the decision rule uses the cost ratio to decide whether that posterior probability is high enough to alert.

The SLO defines the alert budget. If the operator commits to a 99.9 percent SLO with respect to alerting, the system is allowed at most 0.1 percent of flows to consume budget. The cost ratio determines which flows become threshold-crossing events. The burn-rate layer in Section 3.5 then determines how aggressively that budget is being consumed. These three layers are intentionally separable: score, threshold, and alerting. An operator can adjust the cost ratio during a high-risk period without retraining the detector, and can adjust the SLO independently of either.

## 3.4. Calibration and Conformal Risk Control

Section 3.3 derived the cost-sensitive threshold $\tau ^ { * }$ under the assumption that the input score is a calibrated posterior $p _ { t } \ : = \ : P ( y _ { t } \ : = \ : 1 \mid x _ { 1 : t } )$ . The BOCPD output $s _ { t } = P ( r _ { t } = 0 ~ | ~ x _ { 1 : t } )$ is the posterior probability of a runlength reset, not of an attack. Treating $s _ { t }$ as if it equalled $p _ { t }$ would be a category error: a benign regime shift such as a scheduled backup window can drive $s _ { t }$ high without any attack being present. CALIBURN therefore inserts an explicit calibration layer between the BOCPD score and the costsensitive decision rule, and adds a distribution-free risk-control layer on top of the calibrated probability.

Calibration via isotonic regression.. We fit a monotone calibration map $g :$ $[ 0 , 1 ]  [ 0 , 1 ]$ on the validation split, using isotonic regression with the pooladjacent-violators algorithm (Zadrozny and Elkan, 2002; Niculescu-Mizil and Caruana, 2005). The map is fit to the pairs $\{ ( s _ { i } , y _ { i } ) \} _ { i \in \mathrm { v a l } }$ where $y _ { i }$ is the binary attack label. At test time, the BOCPD score is transformed into a calibrated probability:

$$
\hat {p} _ {t} = g (s _ {t}).\tag{15}
$$

We choose isotonic regression rather than Platt (sigmoid) scaling because the validation sets in our experiments are large (at least 38,650 samples), which removes isotonic’s small-sample weakness, and because the BOCPD posterior is unlikely to follow a clean sigmoid distortion. The fitted isotonic map is a step function that is stored as a sorted set of breakpoints and queried in $O ( \log K )$ time per flow, preserving the streaming character of CALIBURN. Both calibrators are reported in the empirical evaluation (Section 5.5).

What $\hat { p } _ { t }$ measures.. We emphasise that the isotonic map produces $\begin{array} { r l } { \hat { p } _ { t } } & { { } = } \end{array}$ ${ \hat { P } } ( y _ { t } \mid = { \hat { \textbf { l } } } \mid \ s _ { t } )$ , the empirical conditional probability of attack given the BOCPD score, rather than $P ( y _ { t } = 1 \mid x _ { 1 : t } )$ , the unconditional posterior given the raw stream. The two coincide only when $s _ { t }$ is a suficient statistic for $y _ { t }$ , which we do not assume and which is unlikely to hold under benign regime shifts. Treating $\hat { p } _ { t }$ as a useful operational ranking statistic with monotonic calibration to the label, rather than as a structural probability of attack, is the appropriate epistemological stance for the streaming changepoint setting (Bates et al., 2021). This distinction matters when interpreting the downstream cost-sensitive threshold $\tau ^ { * }$ and the CRC threshold $\hat { \tau } _ { \alpha } \colon$ both are validly applied to a calibrated conditional probability $\hat { P } ( y _ { t } \mid \textit { \textbf { \ i } } | \textit { \textbf { s } } _ { t } )$ but their operational interpretation is “alert when the empirical conditional attack probability given the change-point signal exceeds the threshold,” not “alert when the unconditional attack probability given the entire stream history exceeds the threshold.”

Conformal Risk Control for the alert budget.. Calibration narrows the empirical gap between $s _ { t }$ and $p _ { t }$ but does not by itself provide guarantees on the realised false-positive rate. Even a well-calibrated $\hat { p } _ { t }$ thresholded at the operator-derived $\tau ^ { * }$ may produce an FPR that diverges from the alert budget the operator actually specified. To close this gap, we apply Conformal Risk Control (CRC) (Angelopoulos et al., 2024), which extends conformal prediction to control the expected value of any monotone loss under exchangeability of calibration and test points.

For binary alerting under a false-positive budget $\alpha _ { \because }$ , define the indicator loss $L _ { i } ( \tau ) = \mathcal { H } [ \hat { p } _ { i } \geq \tau , y _ { i } = 0 ]$ and let $n _ { 0 }$ be the number of negatives in the validation set. CRC selects:

$$
\hat {\tau} _ {\alpha} = \inf \left\{\tau \in [ 0, 1 ]: \frac {n _ {0}}{n _ {0} + 1} \widehat {\mathrm{FPR}} (\tau) + \frac {1}{n _ {0} + 1} \leq \alpha \right\},\tag{16}
$$

where $\widehat { \mathrm { F P R } } ( \tau )$ is the empirical FPR of the calibrated scores on the validation negatives. Theorem 1 of Angelopoulos et al. (2024) guarantees:

$$
\mathbb {E} \big [ \mathrm{FPR} _ {\mathrm{test}} (\hat {\tau} _ {\alpha}) \big ] \leq \alpha ,\tag{17}
$$

under exchangeability of validation and test negatives. The slack term $1 / ( n _ { 0 } +$ 1) is below $1 0 ^ { - 5 }$ at all three of our datasets and contributes essentially nothing to the bound at the operator-relevant range $\alpha \in [ 1 0 ^ { - 3 } , 1 0 ^ { - 1 } ]$

Three layers, three operator inputs.. The complete decision pipeline is now:

1. BOCPD produces a streaming change-point posterior $s _ { t }$ (parameter: hazard H, encodes the prior rate of regime shifts).

2. Isotonic calibration produces $\hat { p } _ { t } = g ( s _ { t } )$ (fit once on the validation split; operator input: cost ratio $C = C _ { F N } / C _ { F P }$ , used by Equation 13).

3. Conformal Risk Control produces $\hat { \tau } _ { \alpha }$ (operator input: alert budget $\alpha ,$ e.g. derived from an SLO).

The operator can use either $\tau ^ { * }$ from the cost ratio or $\hat { \tau } _ { \alpha }$ from the alert budget, and reasonable practice is to use whichever is more conservative on a given deployment. In the empirical evaluation we report both. The CRC threshold satisfies the FPR bound under exchangeability of validation and test negatives; the cost-sensitive threshold reflects an explicit cost judgment but does not satisfy a marginal validity bound.

Limitations and the exchangeability question.. The CRC validity bound assumes exchangeability of the validation and test negatives. Under significant concept drift or non-stationarity between calibration and deployment, the empirical test FPR can exceed the nominal α. Barber et al. (2023) characterise this formally: the coverage gap is upper-bounded by the total-variation distance between the calibration and test distributions, which is additive in the recency-weighted divergence between observed and exchangeable streams. Tibshirani et al. (2019) earlier framed the closely related covariate-shift case via weighted conformal prediction. For the streaming setting specifically, Gibbs and Candès (2021) introduce Adaptive Conformal Inference (ACI), an online wrapper that re-estimates the efective $\alpha _ { t }$ in response to observed miscoverage and recovers the target frequency over long intervals irrespective of the data-generating process; Gibbs and Candès (2024) extend ACI to arbitrary distribution shifts. Farinhas et al. (2024) extend these ideas to non-exchangeable conformal risk control specifically, providing the theoretical roadmap for relaxing the exchangeability requirement of the framework used here. In our experiments the chronological $7 0 / 1 5 / 1 5$ split provides only an approximate exchangeability guarantee within each calibration window, and we report the empirical test FPR alongside the nominal α in Section 5.5 so that the reader can judge how tight the bound is in practice. Periodic recalibration is recommended for production deployments, and online conformal calibration via ACI or weighted non-exchangeable CRC is the natural next architectural step for non-stationary streams.

## 3.5. Multi-Window Burn-Rate Alerting

Even with a calibrated threshold, raw anomaly alerts can still be noisy. A single suspicious flow may not justify waking up an engineer. At the same time, a sustained stream of suspicious flows should escalate quickly. This is the same type of problem that Site Reliability Engineering teams face when alerting on service-level objectives. The SRE Workbook (Beyer et al., 2018) recommends burn-rate alerting and multi-window alerting to balance fast detection with lower false positives.

CALIBURN uses burn-rate logic as an alert-budget wrapper around the detector. First, each flow is scored by the streaming BOCPD model. Then the cost-sensitive threshold converts the score into a threshold-crossing event. Finally, the burn-rate layer decides whether the recent pattern of threshold crossings is serious enough to become a ticket or a page.

The budget used here is an alert budget, not a verified false-positive budget. At decision time, the system does not yet know whether a thresholdcrossing event is truly malicious or benign. It therefore meters threshold crossings as budget-consuming events. Verified false positives can later be used to adjust the cost ratio or the alert budget ofline, but they are not required for the online alerting rule.

Let B be the allowed number of threshold-crossing events over a target period. Let $e _ { w }$ be the number of threshold-crossing events observed inside window w. The burn rate is:

$$
b _ {w} = \frac {e _ {w} / | w |}{B / T},\tag{18}
$$

where |w| is the window length and T is the full SLO period. A burn rate greater than 1 means the system is consuming the budget faster than allowed. For example, with a 1-hour SLO budget of 1,000 events $( B = 1 0 0 0 , T = 6 0$ minutes), a 5-minute window observing 50 events has burn rate:

$$
b = \frac {5 0 / 5}{1 0 0 0 / 6 0} = 0. 6.\tag{19}
$$

This means the system is consuming budget at 60 percent of the allowed rate.

CALIBURN uses paired long and short windows. An alert fires only when both windows exceed their threshold. This reduces flapping. A short window catches sudden spikes, while a longer window confirms that the spike is not just a one-of anomaly. Table 2 shows the window pairs and burn-rate thresholds used in this paper.

Table 2: Multi-window burn-rate alerting configuration used in CALIBURN, following Beyer et al. (2018).

<table><tr><td>Alert level</td><td>Long window</td><td>Short window</td><td>Burn threshold β</td></tr><tr><td>page-fast</td><td>60 min</td><td>5 min</td><td>14.4</td></tr><tr><td>page-slow</td><td>360 min</td><td>30 min</td><td>6.0</td></tr><tr><td>ticket</td><td>4320 min</td><td>360 min</td><td>1.0</td></tr></table>

The logic is:

$$
\text { alert   if } b _ {\text { long }} > \beta \text { and } b _ {\text { short }} > \beta ,\tag{20}
$$

where $\beta$ is the burn-rate threshold for that alert level.

This gives the system three operational behaviors. A severe attack-like burst can trigger a fast page. A slower but still dangerous pattern can trigger a delayed page. A persistent low-level issue can create a ticket without immediately waking someone up. This is what makes CALIBURN diferent from a normal anomaly detector. It does not only produce scores. It produces alerts in a way that maps to how real teams operate. Figure 3 illustrates the dual-window protection mechanism on a synthetic stream containing a transient burst and a sustained attack.

## 3.6. Pseudocode and Complexity

The full CALIBURN update combines the streaming BOCPD score, the cost-sensitive posterior threshold, and the burn-rate alerting layer. The update is performed once per flow and does not require re-fitting on the full history. The complete per-flow update is shown in Algorithm 2.

The per-flow update cost is bounded by the truncation length L. For each new flow, CALIBURN updates at most $L$ retained run-length hypotheses. If the feature dimension is $d ,$ the memory cost is $O ( L d )$ and the per-flow update cost is $O ( L d )$

![](images/8fea3378bc532d687ce3fd0c1a4b4984b834e4d0d829a5a26b2284893c5601a5.jpg)  
Figure 3: Multi-window burn-rate alerting on a synthetic event stream. (a) shows a transient noise burst at t=120 minutes and a sustained attack starting at t=300. (b) shows that the short-window burn rates spike with the noise burst, but the long windows do not cross threshold simultaneously, so no alert fires. The sustained attack drives both short and long windows above their thresholds. (c) shows the resulting alerts: the page-fast and page-slow levels both fire only during the sustained attack, demonstrating dual-window protection from transient noise.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 CALIBURN per-flow update
Require: Flow $x_t$, BOCPD state $S_{t-1}$, max run length $L$, hazard rate $H$, cost ratio $C = C_{FN}/C_{FP}$, burn-rate windows $W$, warm-up period $W_0$
1: Update truncated BOCPD posterior using $x_t$
2: Compute anomaly score $s_t = P(r_t = 0 \mid x_{1:t})$
3: if $t &lt; W_0$ then
4: update model state only
5: return no alert
6: end if
7: Compute cost-sensitive threshold $\tau = 1/(1 + C)$
8: Convert score to budget event: $z_t = 1$ if $s_t &gt; \tau$ else $z_t = 0$
9: Update burn-rate windows using $z_t$
10: if both long and short windows exceed page-fast threshold then
11: return page-fast
12: else if both long and short windows exceed page-slow threshold then
13: return page-slow
14: else if both long and short windows exceed ticket threshold then
15: return ticket
16: else
17: return no alert
18: end if
</div>

This is the main reason for using the truncated BOCPD formulation. The detector can run continuously without retraining over the full history. Batch methods may still perform well on some datasets, but they do not satisfy the same operational constraint. CALIBURN is designed for the setting where the stream keeps moving, the base rate of attack is low, and the operator needs an alerting rule that is explainable before the test labels are known.

## 4. Experimental Setup

This section describes the datasets, baselines, and evaluation protocol used to test CALIBURN. The goal of the experiments is not only to compare anomaly detection scores, but to evaluate whether a streaming detector remains useful across diferent attack-prevalence regimes. For this reason, we use three network intrusion datasets with very diferent attack rates: LITNET-2020 at 5.2 percent, CICIDS2017 at 22.06 percent, and UNSW-NB15 at 64 percent. This allows the evaluation to test the main claim of the paper: CALIBURN is most useful in the rare-attack regime where streaming detection and operationally calibrated alerting matter most.

## 4.1. Datasets

We evaluate CALIBURN on three widely used network intrusion detection datasets.

The first dataset is LITNET-2020 (Damaševičius et al., 2020), a realworld NetFlow dataset collected from an academic network. The original dataset contains 85 NetFlow features and 12 attack types, and was released specifically for network intrusion detection research. We use LITNET-2020 as the main rare-attack benchmark because it is closest to the operational setting targeted by this paper. From the original files, we extracted 1.5 million flows from three attack types: BLASTER\_WORM, UDP\_FLOOD, and SPAM. Their individual attack rates were 0.78 percent, 14.94 percent, and 0.06 percent, respectively. We matched ATTACKERS\_ONLY signatures against the FLOWS files using hash-based row matching, then round-robin interleaved the selected attack windows to form a single stream. This interleaving step was necessary because the individual attack types occur in diferent time windows. The final LITNET stream has an overall attack rate of 5.2 percent.

The second dataset is CICIDS2017 (Sharafaldin et al., 2018), using the corrected version published by Engelen et al. (2021) and refined by Liu et al.

(2022). CICIDS2017 is one of the most widely used intrusion detection datasets, but the original release has documented issues in attack orchestration, feature generation, documentation, and labeling. Because of these known problems, we use the corrected version rather than the original 2017 labels. The dataset contains multiple weekdays of captured trafic and includes attacks such as DDoS, brute force, web attacks, and infiltration. We used 1.6 million flows with proportional per-day subsampling so that each day kept its natural attack rate. We dropped high-cardinality identifier columns such as IP addresses and ports, and removed rows marked as “Attempted.” We then performed day-by-day round-robin interleaving to keep the train, validation, and test splits balanced. The final attack rate is 22.06 percent.

The third dataset is UNSW-NB15, using the published files from Moustafa and Slay (2015). UNSW-NB15 is a benchmark dataset built from a mixture of modern normal trafic and synthetic attack activity, and the oficial project page provides predefined training and testing files of 175,341 and 82,332 records respectively. Because our evaluation uses a chronological 70/15/15 split for consistency across all three datasets (Section 4.3), we combine the published files into a single 257,673-record corpus and apply the same split, which yields a test set of 38,652 records. We use UNSW-NB15 in this form because it is widely used in the literature and gives a useful stress test for the regime-sensitivity argument. However, this corpus has a high attack prevalence of approximately 64 percent, which is very diferent from the rare-attack setting that motivates CALIBURN. We therefore treat UNSW-NB15 not as the main operational benchmark, but as a stress case showing what happens when the attack base rate is inverted relative to typical streaming security operations.

This range is important because the paper’s central empirical question is precisely whether CALIBURN’s advantage holds across attack-prevalence regimes, and if not, where it fails. The three datasets bracket the regime space from rare to moderate to high prevalence, so the regime-sensitivity hypothesis can be evaluated rather than asserted.

## 4.2. Baselines

We compare CALIBURN against five streaming anomaly detection baselines and three batch reference baselines.

The streaming baselines are Half-Space Trees (Tan et al., 2011), KitNET (Mirsky et al., 2018), LODA (Pevný, 2016), Robust Random Cut Forest (Guha et al., 2016), and iForest\_ASD (Ding and Fei, 2013). These methods cover the main families of streaming anomaly detection used in current practice and literature: tree-based streaming detection, autoencoder-based online detection, projection-based lightweight detection, and streaming isolationbased detection. They are direct competitors because they process the stream incrementally and do not assume access to the full future test distribution.

The batch reference baselines are Local Outlier Factor (Breunig et al., 2000), ECOD (Li et al., 2022), and COPOD (Li et al., 2020). LOF is a classical density-based outlier detection method. ECOD is an empirical cumulative distribution based detector, and COPOD is a copula-based outlier detector. These methods are not direct streaming competitors, because they do not satisfy the same online constraint. We include them as reference points because they show what can be achieved when a detector has access to full training data or can operate in a more traditional ofline setting.

We exclude xStream (Manzoor et al., 2018) from the LITNET-2020 and CICIDS2017 experimental sets because preliminary trials showed prohibitive compute cost at those dataset scales, approximately three hours per million rows on the c7i.2xlarge machine used for this study. xStream did complete on the smaller UNSW-NB15 partition, where the test set is 38,652 rows, and we report its result in Section 5.3 for completeness. We note that Cao et al. (2025) provides a recent comprehensive xStream evaluation at scale, which complements the partial inclusion in this study.

## 4.3. Evaluation Protocol

All datasets are evaluated using chronological splits. After preprocessing and interleaving where needed, each stream is sorted by timestamp and split into 70 percent training, 15 percent validation, and 15 percent test. LITNET-2020 and CICIDS2017 required round-robin interleaving before splitting because their raw attack windows are not naturally balanced across time. Without this step, the validation and test partitions would have substantially diferent attack rates, which would make threshold and calibration analysis unstable.

Table 3 summarizes the main experimental configuration used for CAL-IBURN and the baselines.

For CALIBURN, the run-length truncation L, hazard rate H, warm-up period $W _ { 0 } ,$ cost ratio, and burn-rate windows are fixed before evaluation and are not tuned on the test labels. All streaming baselines are run with library default hyperparameters under fixed seeds where stochasticity exists;

Table 3: Main experimental configuration used for CALIBURN and the evaluated baselines.

<table><tr><td>Setting</td><td>Value</td></tr><tr><td>Run-length truncation  $L$ </td><td>500 retained run lengths</td></tr><tr><td>Hazard rate  $H$ </td><td>1/1000 per flow</td></tr><tr><td>Warm-up period  $W_0$ </td><td>30 flows</td></tr><tr><td>Observation model</td><td>Diagonal Gaussian, online sufficient statistics</td></tr><tr><td>Variance floor</td><td> $10^{-4}$ </td></tr><tr><td>Feature scaling</td><td>Numeric features min-max scaled to [0, 1]</td></tr><tr><td>Categorical handling</td><td>Protocol-like categorical fields one-hot encoded</td></tr><tr><td>Dropped identifiers</td><td>IP addresses, ports, labels, high-cardinality identifiers</td></tr><tr><td>Cost ratio  $C = C_{FN}/C_{FP}$ </td><td>10 by default</td></tr><tr><td>Threshold  $\tau^*$ </td><td> $1/(1+C)=0.091$ </td></tr><tr><td>Alert-budget windows</td><td>5/60 min, 30/360 min, 360/4320 min</td></tr><tr><td>Random seeds</td><td>11, 23, 47</td></tr><tr><td>Hardware</td><td>AWS c7i.2xlarge, 8 vCPU, 16 GB RAM</td></tr><tr><td>Software</td><td>Python 3.11, NumPy, scikit-learn, River, PySAD</td></tr></table>

full per-method configuration is included in the released code. Batch reference methods are fit on the training split and evaluated on the held-out test split; they are included as reference points rather than direct streaming competitors.

The primary evaluation metric is area under the precision-recall curve, or AUC-PR. We use AUC-PR as the main metric because it is more informative than ROC-AUC under class imbalance (Saito and Rehmsmeier, 2015). Since most real network trafic is benign, a detector can achieve a misleadingly high ROC-AUC while still producing poor precision. We also report ROC-AUC, F1 score, precision, recall, and Brier score. For operational interpretation, we report latency statistics, including p50, p95, and p99 update latency, as well as throughput in events per second.

For variance-reportable methods, we use three random seeds: 11, 23, and 47. These seeds are low-numbered primes and were fixed before running the experiments. For deterministic methods, including CALIBURN, KitNET, ECOD, COPOD, and LOF, the variance across seeds is zero by construction. For methods with stochastic components, we report the mean and variance across the three seeds on LITNET-2020 and CICIDS2017. UNSW-NB15 is reported with a single seed due to compute cost and because it is used mainly as a stress case rather than the primary operational benchmark.

Pairwise comparisons between CALIBURN and each baseline are reported using the Wilcoxon signed-rank test (Wilcoxon, 1945) on per-seed AUC-PR values. We report exact p-values rather than significance asterisks, following the recommendation of recent ML methodology critiques (Arp et al., 2022).

All experiments were run on AWS EC2 c7i.2xlarge in the eu-north-1 region. The machine used 8 vCPUs and 16 GB of RAM. The implementation used Python 3.11 with NumPy, scikit-learn, River, PySAD, KitNET-py, and rrcf. All preprocessing scripts, configuration files, and fixed seeds are preserved so that the experimental protocol can be reproduced exactly.

## 5. Results

This section reports the empirical results across the three evaluation regimes. We present the results in the same order as the experimental design: LITNET-2020 as the rare-attack regime, CICIDS2017 as the moderateprevalence regime, and UNSW-NB15 as the high-prevalence stress case. The main pattern is clear. CALIBURN is strongest when attacks are rare, remains competitive among streaming methods when attacks become more common, and loses its advantage when the stream is dominated by attacks.

The primary metric is AUC-PR because precision-recall evaluation is more informative than ROC-based evaluation under class imbalance, especially when the positive class is rare (Saito and Rehmsmeier, 2015). This matters here because the datasets intentionally cover very diferent attackprevalence regimes.

## 5.1. LITNET-2020: Rare-Attack Regime

On LITNET-2020, the rare-attack regime closest to the operational setting targeted by this paper, CALIBURN achieves an AUC-PR of 0.943. This is the strongest result in the study. It outperforms the best streaming baseline, LODA, by 2.21× and the best batch reference, ECOD, by 4.12× under the same evaluation protocol. Notably, LOF, which becomes the strongest batch method on CICIDS2017, performs poorly on LITNET-2020 with AUC-PR 0.099. This already shows that no single baseline dominates across regimes.

The gap is large. LODA is the next strongest streaming method, with mean AUC-PR of 0.425. HST follows at 0.261 mean, but with markedly larger variance, with standard deviation 0.097, than the other stochastic baselines. This variance reflects HST’s sensitivity to randomized tree initialization and is itself a notable result. It means that HST’s reported performance in any single-seed evaluation may be unreliable. Among the batch reference methods, ECOD performs best at 0.229, followed by COPOD at 0.208. KitNET and RRCF also fail to identify a useful rare-attack signal under this configuration.

The operational profile of CALIBURN is also important. Its precision is 0.976, meaning that when the system raises an alert, it is correct 97.6 percent of the time. Its recall is 0.451, meaning that it catches less than half of all attacks. We do not treat this as a weakness hidden by the aggregate score. It is the trade-of produced by the SLO-aware threshold. CALIBURN is tuned to spend alerting budget carefully, not to maximize recall at any cost. In an operational setting, that profile is useful when false positives are expensive and the team wants high-confidence alerts.

Figure 4 visualizes the AUC-PR comparison across all evaluated methods. The visual gap between CALIBURN and the rest of the methods is consistent with the AUC-PR margin reported above and shows that the advantage is not a tail-of-the-curve artifact but is visible at the headline metric.

Table 4 reports the full results.

Table 4: AUC-PR, AUC-ROC, and F1 on LITNET-2020 (3-seed mean ± std). Deterministic methods are marked “det.” because repeated seeds produce identical results.

<table><tr><td>Method</td><td>AUC-PR</td><td>AUC-ROC</td><td>F1</td></tr><tr><td>CALIBURN</td><td>0.943 det.</td><td>0.998 det.</td><td>0.617 det.</td></tr><tr><td>LODA</td><td>0.425 ± 0.016</td><td>0.845 ± 0.008</td><td>0.453 ± 0.013</td></tr><tr><td>HST</td><td>0.261 ± 0.097</td><td>0.848 ± 0.041</td><td>0.366 ± 0.129</td></tr><tr><td>ECOD</td><td>0.229 det.</td><td>0.737 det.</td><td>0.325 det.</td></tr><tr><td>COPOD</td><td>0.208 det.</td><td>0.780 det.</td><td>0.273 det.</td></tr><tr><td>iForest_ASD</td><td>0.130 ± 0.009</td><td>0.784 ± 0.011</td><td>0.251 ± 0.006</td></tr><tr><td>LOF</td><td>0.099 det.</td><td>0.509 det.</td><td>0.125 det.</td></tr><tr><td>KitNET</td><td>0.086 det.</td><td>0.600 det.</td><td>0.145 det.</td></tr><tr><td>RRCF</td><td>0.074 ± 0.001</td><td>0.546 ± 0.005</td><td>0.127 ± 0.000</td></tr></table>

LITNET-2020: AUC-PR comparison  
![](images/df64f87bf57b8b56729979e8e4a300685786386ba9688e1bf18c8f0442723adf.jpg)  
Figure 4: LITNET-2020 AUC-PR across all evaluated methods. Bars show the 3-seed mean. Error bars denote seed-to-seed standard deviation for stochastic methods (LODA, HST, iForest\_ASD, RRCF); deterministic methods (CALIBURN, ECOD, COPOD, LOF, KitNET) produce identical results across seeds and have no error bars. CALIBURN’s AUC-PR of 0.943 exceeds the next-best method (LODA, 0.425) by 2.21× and the best batch reference (ECOD, 0.229) by 4.12×.

## 5.2. CICIDS2017: Moderate-Prevalence Regime

On CICIDS2017, the shift to 22.06 percent attack prevalence changes the result substantially. LOF achieves the best overall AUC-PR at 0.863, while CALIBURN achieves 0.545. However, CALIBURN remains the strongest streaming method. It outperforms HST at 0.433, LODA at 0.342, iForest\_ASD at 0.306, RRCF at 0.252, and KitNET at 0.191.

This result is not a generic failure of CALIBURN. It shows where the method’s advantage begins to narrow. BOCPD learns a streaming reference distribution from the data it sees. When attacks become a large part of the stream, the reference distribution can become contaminated by attack behavior. A batch method such as LOF is not subject to the same online constraint. It can use the full training distribution and isolate dense abnormal regions more efectively in this setting.

This is consistent with the central claim of the paper. CALIBURN is designed for the regime where streaming detection is operationally needed most: rare attacks in a mostly benign stream. CICIDS2017 sits in a middle regime. CALIBURN still performs well among streaming detectors, but a strong batch reference can outperform it when the prevalence is high enough and the full training distribution is available.

Why LOF dominates here but not on LITNET-2020.. A natural question is why LOF’s AUC-PR swings from approximately 0.10 on LITNET-2020 (Section 5.1) to 0.863 on CICIDS2017 — a roughly nine-fold improvement in the same algorithm under diferent data. Two structural properties explain the crossover. First, LOF (Breunig et al., 2000) estimates local density and is most efective when the minority (attack) class forms coherent local clusters in feature space rather than appearing as isolated, sparsely distributed points. CICIDS2017 includes campaigns such as DDoS, brute-force, and port-scan that produce dense flow clusters with strongly homogeneous feature signatures; LOF flags these eficiently because each attack flow has many other attack flows as local-density neighbours. LITNET-2020 has a diferent attack mix dominated by short volumetric bursts inside otherwise heterogeneous benign academic-network trafic; attack flows are sparse and isolated in the 85-dimensional feature space, the regime where LOF degrades. Second, LOF is known to be vulnerable to the curse of dimensionality: in high-dimensional feature spaces without coherent local structure, local-density estimates lose discriminative power. CICIDS2017 has lower efective dimensionality after standard preprocessing than LITNET-2020 and dense minority pockets, both of which favour LOF; LITNET-2020 has the opposite profile. This is consistent with the regime-sensitivity framing of the paper: no single method dominates uniformly, and CALIBURN’s strength lies precisely in the rare-attack regime where local-density methods like LOF lose discriminative power.

Variance also changes on CICIDS2017. CALIBURN is deterministic and produces the same AUC-PR across seeds. HST shows the largest variance among the stochastic baselines, with standard deviation 0.078 in AUC-PR and 0.087 in F1. LODA, RRCF, and iForest\_ASD are more stable, although they remain below CALIBURN in AUC-PR. The deterministic batch methods produce fixed values under the same preprocessing and split. Table 5 reports the full results.

Table 5: AUC-PR, AUC-ROC, and F1 on CICIDS2017 (3-seed mean ± std). CALIBURN remains the best streaming method but trails the LOF batch reference.

<table><tr><td>Method</td><td>AUC-PR</td><td>AUC-ROC</td><td>F1</td></tr><tr><td>LOF</td><td>0.863 det.</td><td>0.972 det.</td><td>0.893 det.</td></tr><tr><td>CALIBURN</td><td>0.545 det.</td><td>0.880 det.</td><td>0.639 det.</td></tr><tr><td>HST</td><td> $0.433 \pm 0.078$ </td><td> $0.803 \pm 0.058$ </td><td> $0.512 \pm 0.087$ </td></tr><tr><td>COPOD</td><td>0.423 det.</td><td>0.812 det.</td><td>0.632 det.</td></tr><tr><td>ECOD</td><td>0.419 det.</td><td>0.808 det.</td><td>0.661 det.</td></tr><tr><td>LODA</td><td> $0.342 \pm 0.005$ </td><td> $0.720 \pm 0.006$ </td><td> $0.533 \pm 0.003$ </td></tr><tr><td>iForest_ASD</td><td> $0.306 \pm 0.018$ </td><td> $0.672 \pm 0.027$ </td><td> $0.455 \pm 0.013$ </td></tr><tr><td>RRCF</td><td> $0.252 \pm 0.001$ </td><td> $0.475 \pm 0.001$ </td><td> $0.403 \pm 0.000$ </td></tr><tr><td>KitNET</td><td>0.191 det.</td><td>0.344 det.</td><td>0.403 det.</td></tr></table>

## 5.3. UNSW-NB15: High-Prevalence Stress Case

UNSW-NB15 gives a diferent picture. As described in Section 4.1, we combine the published Moustafa and Slay (2015) training and testing files into a single 257,673-record corpus and apply our standard chronological $7 0 / 1 5 / 1 5$ split. The resulting test set has 38,652 records and approximately 64 percent attack prevalence. In this setting, the advantage of streaming change-point detection largely disappears. CALIBURN reaches AUC-PR 0.653, which is essentially indistinguishable from the positive-class prevalence floor of 0.6764 and therefore not strong evidence of useful separation. Its AUC-ROC is 0.488, which confirms that the detector is not ranking attack flows above benign flows in a useful way. All other streaming methods cluster in the same narrow range: RRCF 0.675, KitNET 0.673, HST 0.641, LODA 0.611, iForest\_ASD 0.610, and xStream 0.599. None of the streaming methods, including CALIBURN, escapes the prevalence floor by a meaningful margin.

The batch reference methods perform better, but even there the result should be interpreted carefully. LOF reaches AUC-PR 0.899, ECOD reaches 0.741, and COPOD reaches 0.704. These scores are higher than the streaming methods, but they are being measured in a setting where attacks are no longer rare. This changes the meaning of the detection problem. When the majority of the stream is attack trafic, the online reference distribution is no longer mainly benign. That is a base-rate inversion relative to the operational setting this paper targets.

For this reason, we treat UNSW-NB15 as a stress case rather than as the main operating regime. It is useful because it shows where CALIBURN should not be expected to dominate. Streaming change-point detection is structurally limited when the stream is already attack-heavy. We return to this issue in Section 6.2, where we discuss the partition structure and its implications for evaluation. Table 6 reports the full results.

Table 6: AUC-PR and AUC-ROC on UNSW-NB15 (single seed; test set = 38,652 records, attack prevalence ≈ 64%, prevalence floor 0.6764). Methods are ordered by AUC-PR. AUC-PR values close to the prevalence floor indicate near-trivial ranking performance.

<table><tr><td>Method</td><td>AUC-PR</td><td>AUC-ROC</td></tr><tr><td>LOF</td><td>0.899</td><td>0.777</td></tr><tr><td>ECOD</td><td>0.741</td><td>0.625</td></tr><tr><td>COPOD</td><td>0.704</td><td>0.539</td></tr><tr><td>RRCF</td><td>0.675</td><td>0.497</td></tr><tr><td>KitNET</td><td>0.673</td><td>0.496</td></tr><tr><td>CALIBURN</td><td>0.653</td><td>0.488</td></tr><tr><td>HST</td><td>0.641</td><td>0.381</td></tr><tr><td>LODA</td><td>0.611</td><td>0.396</td></tr><tr><td>iForest_ASD</td><td>0.610</td><td>0.374</td></tr><tr><td>xStream</td><td>0.599</td><td>0.380</td></tr></table>

## 5.4. Cross-Dataset Comparison and Statistical Tests

Across the three datasets, the ranking pattern supports the regime-sensitivity hypothesis. CALIBURN ranks first on LITNET-2020, second overall on CI-

CIDS2017, and sixth out of ten on UNSW-NB15. This is not the pattern expected from a method that simply wins everywhere. It is the pattern expected from a streaming detector whose advantage depends on the attack base rate. Figure 5 visualizes this dependence.

Regime sensitivity across attack-prevalence settings  
![](images/372da1adf91f88063411b91632bc93642748044ab89ad6c0e71f5c628a4aadf1.jpg)  
Figure 5: Regime sensitivity of AUC-PR across the three NIDS datasets, ordered by attack prevalence. CALIBURN dominates in the rare-attack regime (LITNET-2020, 5.2%), trails the LOF batch reference at moderate prevalence (CICIDS2017, 22.06%), and converges with the streaming-method cluster at high prevalence (UNSW-NB15, 64%). The orange line shows the strongest non-CALIBURN streaming baseline at each dataset (LODA on LITNET, HST on CICIDS, RRCF on UNSW); the green line shows the best batch reference (ECOD on LITNET, LOF on CICIDS and UNSW). The pattern supports the regime-sensitivity hypothesis: CALIBURN is most useful where streaming detection is operationally needed most.

The strongest result is the rare-attack case. On LITNET-2020, CAL-IBURN is not only the best method, but substantially ahead of both streaming and batch alternatives. On CICIDS2017, it remains the best streaming method, but LOF becomes the strongest overall method. On UNSW-NB15, the attack prevalence is high enough that streaming reference estimation becomes unreliable, all streaming methods cluster near the prevalence floor, and batch methods dominate. Among streaming methods at this regime, RRCF marginally outperforms CALIBURN (0.675 versus 0.653), but the entire streaming group sits within a 0.08 AUC-PR band that is consistent with near-prevalence-floor behavior. We therefore avoid claiming a winner among streaming methods on UNSW. Table 7 summarizes this pattern.

Table 7: Cross-dataset ranking summary. CALIBURN’s rank is its position in the AUC-PR ordering on each dataset. “Best method” is the highest AUC-PR overall; “best streaming baseline” is the highest AUC-PR among the streaming methods, excluding CALIBURN itself.

<table><tr><td>Dataset</td><td>Attack rate</td><td>CALIBURN rank</td><td>Best method</td><td>Best streaming baseline</td></tr><tr><td>LITNET-2020</td><td>5.2%</td><td>1st of 9</td><td>CALIBURN (0.943)</td><td>LODA (0.425)</td></tr><tr><td>CICIDS2017</td><td>22.06%</td><td>2nd of 9</td><td>LOF (0.863)</td><td>CALIBURN (0.545)</td></tr><tr><td>UNSW-NB15</td><td>64%</td><td>6th of 10</td><td>LOF (0.899)</td><td>RRCF (0.675)</td></tr></table>

Pairwise statistical comparisons are handled carefully because several methods are deterministic under the fixed preprocessing and split. The Wilcoxon signed-rank test (Wilcoxon, 1945) is appropriate for paired samples and tests whether the paired diferences are symmetric around zero, but it is not very meaningful when one or both methods have zero variance across seeds. On LITNET-2020, CALIBURN’s deterministic AUC-PR of 0.943 exceeds the upper end of every other method’s variance interval. The closest streaming comparison is LODA at $0 . 4 2 5 \pm 0 . 0 1 6$ , where the gap exceeds 32 standard deviations of LODA’s seed-to-seed variation. This margin does not require formal hypothesis testing to establish practical significance. Exact Wilcoxon p-values for stochastic baseline comparisons are reported in the supplementary statistical table.

Table 8 reports CALIBURN’s operational latency profile on the three datasets. The mean per-flow update is approximately 6 ms on LITNET-2020 and approximately 61 ms on CICIDS2017, with throughput in the range of 400-600 events per second. The higher CICIDS2017 mean latency reflects its larger feature space and heavier per-row preprocessing. UNSW-NB15 shows a markedly elevated tail latency, which is consistent with the regimesensitivity story: when the prevalence assumption is strongly violated, the BOCPD posterior dynamics become less stable and the per-flow update path is harder to amortize. We treat this as another reason to position UNSW-NB15 as a stress case rather than a primary operational benchmark. For the rare-attack regime that motivates this paper, the latency profile is compatible with flow-level monitoring pipelines, where events are typically aggregated before detection.

Table 8: CALIBURN operational latency and throughput per dataset. Values are computed over the evaluated test stream. Mean latency is the per-flow average; throughput is the streaming rate in events per second. Per-flow updates frequently complete in less than one timer tick (the mean reflects the small fraction of computationally expensive updates).

<table><tr><td>Dataset</td><td>Mean per-flow latency</td><td>Throughput</td></tr><tr><td>LITNET-2020</td><td>5.75 ms</td><td>561 events/s</td></tr><tr><td>CICIDS2017</td><td>61.03 ms</td><td>435 events/s</td></tr><tr><td>UNSW-NB15*</td><td>1741 ms</td><td>550 events/s</td></tr></table>

<sup>∗</sup> Elevated tail latency on UNSW-NB15 reflects degenerate posterior dynamics in the high-prevalence stress case.

## 5.5. Calibration and Operational Metrics

This section evaluates the calibration layer introduced in Section 3.4. The goals are: (a) measure how well the BOCPD score $s _ { t }$ approximates an attack probability before and after calibration; (b) verify that the Conformal Risk Control threshold $\hat { \tau } _ { \alpha }$ produces an empirical test FPR at or below the nominal alert budget α; (c) compare the cost-sensitive threshold $\tau ^ { * }$ on calibrated probabilities to the budget-derived threshold $\hat { \tau } _ { \alpha }$

Calibration metrics.. Table 9 reports Brier score, expected calibration error (ECE) with 15 equal-width bins, and binary log-loss for raw, Platt-scaled, and isotonic-regression-calibrated BOCPD scores on each test set. Calibrators are fit on the validation split. Lower is better for all three metrics.

The raw BOCPD scores are measurably miscalibrated, especially on UNSW-NB15 (raw Brier 0.59, ECE 0.58). This is consistent with our position in Section 3.4 that $s _ { t } ~ = ~ P ( r _ { t } = 0 ~ | ~ x _ { 1 : t } )$ is a regime-shift posterior, not an attack probability. Both calibration methods produce substantial improvements: isotonic regression reduces Brier by 30% on LITNET-2020, 32% on CICIDS2017, and 63% on UNSW-NB15 relative to raw scores. Platt scaling produces comparable Brier reductions and lower ECE on UNSW-NB15. We adopt isotonic regression as the default calibrator in CALIBURN because its non-parametric monotone form is well-matched to the heterogeneous shape of the BOCPD posterior across regimes; full Platt-Isotonic comparisons are reported here for completeness.

CRC validity on the test set.. Table 10 reports the Conformal Risk Control threshold $\hat { \tau } _ { \alpha }$ derived from validation negatives, along with the empirical falsepositive rate measured on test negatives. The CRC bound from Equation 17 requires that the empirical test FPR be at or below α under exchangeability of validation and test negatives. All twelve dataset-by-budget combinations satisfy this bound on our chronological splits; we discuss the small-α overshoot regime $2 B / ( n _ { 0 } + 1 )$ separately in Section 5.6.

Table 9: Calibration metrics on the test set for raw, Platt-scaled, and isotonic-regressioncalibrated BOCPD scores. Calibrators are fit on the validation split. Lower is better. Best result per dataset and metric is shown in bold.

<table><tr><td>Dataset</td><td>Method</td><td>Brier</td><td>ECE</td><td>Log-loss</td></tr><tr><td rowspan="3">LITNET-2020</td><td>Raw</td><td>0.0148</td><td>0.0455</td><td>0.0744</td></tr><tr><td>Platt</td><td>0.0108</td><td>0.0135</td><td>0.0402</td></tr><tr><td>Isotonic</td><td>0.0104</td><td>0.0118</td><td>0.1889</td></tr><tr><td rowspan="3">CICIDS2017</td><td>Raw</td><td>0.1724</td><td>0.1393</td><td>2.1411</td></tr><tr><td>Platt</td><td>0.1527</td><td>0.1110</td><td>0.4728</td></tr><tr><td>Isotonic</td><td>0.1166</td><td>0.1411</td><td>0.3767</td></tr><tr><td rowspan="3">UNSW-NB15</td><td>Raw</td><td>0.5875</td><td>0.5761</td><td>4.6918</td></tr><tr><td>Platt</td><td>0.2186</td><td>0.0028</td><td>0.6289</td></tr><tr><td>Isotonic</td><td>0.2190</td><td>0.0026</td><td>0.6297</td></tr></table>

The empirical test FPR is in fact lower than α in every case, sometimes substantially so. This conservatism is expected when the validation negative score distribution is skewed toward the lower end of [0, 1], which makes the CRC threshold-search step land on a value at which very few test negatives produce calibrated scores above $\hat { \tau } _ { \alpha } .$ . The CRC procedure is sound regardless: the FPR guarantee is an upper bound, not a target.

Cost-sensitive vs. budget-derived thresholds.. Section 3.3 derives a cost-sensitive threshold $\tau ^ { * } = 1 / ( 1 + C ) = 0 . 0 9 1$ for $C = 1 0$ . Table 11 compares this fixed threshold against $\hat { \tau } _ { \alpha = 0 . 0 1 }$ on the calibrated probabilities, in terms of test alert rate, FPR, and recall.

The two thresholds behave very diferently across regimes, and this is informative. On LITNET-2020, the rare-attack regime, the cost-sensitive threshold $\tau ^ { * } = 0 . 0 9 1$ produces a 6.6% alert rate, a 0.6% FPR, and 92% recall on the calibrated probabilities. This is the operationally desirable behavior: high recall, low FPR, modest alert rate. On CICIDS2017 and UNSW-NB15 the same threshold becomes degenerate: nearly 100% of test flows produce calibrated probabilities above 0.091. This happens because in regimes with substantial benign-flow density at higher score bins, the calibrator legitimately maps many scores to large $\hat { p } _ { t }$ , and a fixed cost-sensitive cutof of 0.091 no longer separates classes. The CRC threshold $\hat { \tau } _ { \alpha = 0 . 0 1 }$ adapts: it self-selects up to 0.486 on CICIDS2017 and 0.686 on UNSW-NB15 to honor the alert budget.

Table 10: Conformal Risk Control: nominal alert budget $\alpha ,$ fitted threshold ${ \hat { \tau } } _ { \alpha } ,$ and empirical test-set FPR on isotonic-calibrated scores. CRC validity requires the empirical FPR to be at or below $\underline { { \alpha } } .$

<table><tr><td>Dataset</td><td> $\alpha$ </td><td> $\hat{\tau}_{\alpha}$ </td><td>Empirical test FPR</td><td>Within bound</td></tr><tr><td rowspan="4">LITNET-2020</td><td>0.001</td><td>0.9615</td><td>0.0000</td><td>yes</td></tr><tr><td>0.005</td><td>0.1530</td><td>0.0015</td><td>yes</td></tr><tr><td>0.010</td><td>0.1530</td><td>0.0015</td><td>yes</td></tr><tr><td>0.050</td><td>0.0005</td><td>0.0063</td><td>yes</td></tr><tr><td rowspan="4">CICIDS2017</td><td>0.001</td><td>0.4855</td><td>0.0000</td><td>yes</td></tr><tr><td>0.005</td><td>0.4855</td><td>0.0000</td><td>yes</td></tr><tr><td>0.010</td><td>0.4855</td><td>0.0000</td><td>yes</td></tr><tr><td>0.050</td><td>0.4855</td><td>0.0000</td><td>yes</td></tr><tr><td rowspan="4">UNSW-NB15</td><td>0.001</td><td>0.6860</td><td>0.0000</td><td>yes</td></tr><tr><td>0.005</td><td>0.6860</td><td>0.0000</td><td>yes</td></tr><tr><td>0.010</td><td>0.6860</td><td>0.0000</td><td>yes</td></tr><tr><td>0.050</td><td>0.6860</td><td>0.0000</td><td>yes</td></tr></table>

Table 11: Comparison of the cost-sensitive threshold $\tau ^ { * } = 0 . 0 9 1$ (Section 3.3, $C = 1 0 )$ and the CRC-derived threshold $\hat { \tau } _ { \alpha = 0 . 0 1 }$ (Section 3.4) on isotonic-calibrated BOCPD scores. Alert rate is the fraction of test flows above the threshold. Recall is the fraction of true attacks above the threshold. Both thresholds operate on calibrated scores.

<table><tr><td>Dataset</td><td>Threshold</td><td>Test alert rate</td><td>Test FPR</td><td>Test recall</td></tr><tr><td rowspan="2">LITNET-2020</td><td> $\tau^{*} = 0.091$ </td><td>0.0660</td><td>0.0063</td><td>0.9239</td></tr><tr><td> $\hat{\tau}_{0.01} = 0.153$ </td><td>-</td><td>0.0015</td><td>-</td></tr><tr><td rowspan="2">CICIDS2017</td><td> $\tau^{*} = 0.091$ </td><td>0.9993</td><td>0.9991</td><td>1.0000</td></tr><tr><td> $\hat{\tau}_{0.01} = 0.486$ </td><td>-</td><td>0.0000</td><td>-</td></tr><tr><td rowspan="2">UNSW-NB15</td><td> $\tau^{*} = 0.091$ </td><td>1.0000</td><td>1.0000</td><td>1.0000</td></tr><tr><td> $\hat{\tau}_{0.01} = 0.686$ </td><td>-</td><td>0.0000</td><td>-</td></tr></table>

The practical implication is that the cost-sensitive threshold $\tau ^ { * }$ is an explicit operator-facing quantity that reflects a cost judgment, while the CRC threshold $\hat { \tau } _ { \alpha }$ is a regime-adaptive operator-facing quantity that reflects an alert-budget commitment. Both are derived from operator inputs without test-set tuning. In rare-attack regimes the two thresholds are operationally similar; in dense-attack regimes the CRC threshold is the only one that produces a usable alert rate.

Determinism of the calibration metrics.. CALIBURN’s scoring pipeline is fully deterministic: BOCPD’s update equations contain no stochastic component, and the seed parameter is accepted by the runner only for protocol symmetry with the stochastic baselines (LODA, HST, iForest\_ASD, RRCF). Re-running CALIBURN with seeds {11, 23, 47} on LITNET-2020 and CICIDS2017 produces identical per-flow scores and therefore identical calibration metrics. The values reported in Table 9 and Table 10 are therefore exact rather than averaged; the reported standard deviation across seeds is zero by construction. This is consistent with the deterministic-by-design footnote in the main results tables.

## 5.6. Ablation: Identifying the Operational Scope of Each Component

To isolate the contribution of each post-hoc layer in CALIBURN, we compare four variants that difer in which of the calibration and Conformal Risk Control layers are present. All variants share the same BOCPD scoring stage and the same cost ratio $C = 1 0$ where applicable. The variants are:

• V1 (Full). Isotonic calibration of $s _ { t }$ to $\hat { p } _ { t }$ , followed by the CRC threshold $\hat { \tau } _ { \alpha = 0 . 0 1 }$ (Equation 16).

• V2 (No isotonic). CRC at $\alpha = 0 . 0 1$ applied directly to the raw BOCPD posterior $s _ { t } ,$ without isotonic calibration.

• V3 (No CRC). Isotonic calibration followed by the cost-sensitive threshold $\tau ^ { * } = 0 . 0 9 1$ from Section 3.3.

• V4 (No calibration, no CRC). The cost-sensitive threshold $\tau ^ { * } =$ 0.091 applied directly to the raw BOCPD posterior $s _ { t }$

V1 is the recommended pipeline in the rare-attack regime. V2 isolates the contribution of isotonic calibration. V3 isolates the contribution of CRC. V4 is the strawman variant: BOCPD score thresholded at the Elkan rule with no calibration and no risk-control layer. Table 12 reports test alert rate, FPR, recall, precision, and F1 for each variant on each dataset.

Table 12: Ablation of the calibration and Conformal Risk Control layers. All variants share the same BOCPD scoring stage. V1 is the recommended pipeline; V4 omits both calibration and CRC. The variants reveal regime-dependent contributions of each layer. Threshold τ denotes the operating threshold applied to the appropriate score (calibrated or raw, depending on variant). NaN in the threshold column indicates that CRC at $\alpha = 0 . 0 1$ was infeasible on raw scores for that dataset because no $\tau \in [ 0 , 1 ]$ produced an upperbounded FPR below α.

<table><tr><td>Dataset</td><td>Variant</td><td>τ</td><td>Alert rate</td><td>FPR</td><td>Recall</td><td>Precision</td><td>F1</td></tr><tr><td rowspan="4">LITNET-2020</td><td>V1 (Iso + CRC)</td><td>0.153</td><td>0.057</td><td>0.001</td><td>0.850</td><td>0.976</td><td>0.909</td></tr><tr><td>V2 (raw + CRC)</td><td>0.399</td><td>0.061</td><td>0.003</td><td>0.885</td><td>0.949</td><td>0.916</td></tr><tr><td>V3 (Iso + Elkan)</td><td>0.091</td><td>0.066</td><td>0.006</td><td>0.924</td><td>0.910</td><td>0.917</td></tr><tr><td>V4 (raw + Elkan)</td><td>0.091</td><td>0.155</td><td>0.096</td><td>1.000</td><td>0.419</td><td>0.591</td></tr><tr><td rowspan="4">CICIDS2017</td><td>V1 (Iso + CRC)</td><td>0.486</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td></tr><tr><td>V2 (raw + CRC)</td><td>N/A</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td></tr><tr><td>V3 (Iso + Elkan)</td><td>0.091</td><td>0.999</td><td>0.999</td><td>1.000</td><td>0.253</td><td>0.403</td></tr><tr><td>V4 (raw + Elkan)</td><td>0.091</td><td>0.296</td><td>0.141</td><td>0.756</td><td>0.644</td><td>0.695</td></tr><tr><td rowspan="4">UNSW-NB15</td><td>V1 (Iso + CRC)</td><td>0.686</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td></tr><tr><td>V2 (raw + CRC)</td><td>N/A</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.000</td></tr><tr><td>V3 (Iso + Elkan)</td><td>0.091</td><td>1.000</td><td>1.000</td><td>1.000</td><td>0.676</td><td>0.807</td></tr><tr><td>V4 (raw + Elkan)</td><td>0.091</td><td>0.284</td><td>0.289</td><td>0.282</td><td>0.671</td><td>0.397</td></tr></table>

What the ablation reveals.. Read together with the prevalence regimes, the ablation identifies the operational scope of each post-hoc component rather than a uniform “every component is essential” claim.

In the rare-attack regime (LITNET-2020, 5.2 percent prevalence), V1 (the full pipeline) achieves F1 of 0.909 with FPR of 0.001. Removing isotonic calibration (V2) leaves CRC to operate on raw scores; this still works because CRC adapts the threshold to the observed score distribution. Removing CRC (V3) yields a slightly higher F1 of 0.917 but with FPR 4-6 times higher than

V1. The strawman V4 collapses to F1 of 0.591 with FPR of 0.096, meaning roughly one in ten benign flows is alerted. This is the operational profile CALIBURN is designed for and where the four-layer composition pays of.

In higher-prevalence regimes (CICIDS2017, 22.06 percent; UNSW-NB15, 64 percent), V1 and V2 produce $F _ { 1 } = 0$ . This is not algorithmic failure but a documented property of Conformal Risk Control: Theorem 2 of Angelopoulos et al. (2024) shows that the CRC procedure can over-shoot the target α by up to $2 B / ( n _ { 0 } + 1 )$ , where $B = 1$ is the loss upper bound for the indicator loss and $n _ { 0 }$ is the size of the validation negative set. Numerically, for our chronological splits: on CICIDS2017 with $n _ { 0 } ^ { \mathrm { v a l } } = 1 8 7 , 1 8 8$ , the overshoot bound is $2 / ( n _ { 0 } + 1 ) \approx 1 . 0 7 \times 1 0 ^ { - 5 }$ , far below $\alpha = 0 . 0 1$ ; on UNSW-NB15 with $n _ { 0 } ^ { \mathrm { v a l } } = 1 2 { , } 4 0 4$ , the overshoot is $\approx 1 . 6 1 \times 1 0 ^ { - 4 }$ , also far below $\alpha = 0 . 0 1$ The $F _ { 1 } = 0$ outcome on these datasets does not therefore reflect the small-α overshoot regime. It reflects a diferent feature of the empirical score distribution: when the calibrated-score density of validation negatives is heavily concentrated below the CRC threshold candidates, the procedure selects $\hat { \tau } _ { \alpha }$ at a value that no test point exceeds, producing zero alerts. The CRC bound is satisfied vacuously. V3 (calibrated isotonic with the cost-derived threshold $\tau ^ { * } = 0 . 0 9 1 )$ produces near-full recall on these datasets but at unusable precision because the isotonic map legitimately moves most attack scores above $\tau ^ { * }$ when attack prevalence is high. V4 (raw scores with $\tau ^ { * } )$ produces the most operationally usable F1 in these regimes (0.695 on CICIDS, 0.397 on UNSW).

Operational scope, not a universal claim.. The ablation supports a scope claim rather than a uniform dominance claim. CALIBURN is best suited to deployments where (a) attack prevalence is below approximately 25 percent, (b) the operator-specified alert budget α is comfortably above $2 B / ( n _ { 0 } + 1 )$ for the chosen validation set size, and (c) the calibrated-score density on the operational stream is approximately exchangeable with the validation distribution. In settings that violate (a) or (c), V4 (raw scores with the cost-sensitive threshold) is the more usable variant. We frame this not as a weakness of the pipeline but as an explicit operational deployment guideline: practitioners should check the $2 B / ( n _ { 0 } + 1 )$ bound against their α before deploying the full V1 pipeline, and should expect degenerate alerting if the BOCPD score density and the alert budget produce a no-alert intersection.

## 6. Discussion and Limitations

The results show that CALIBURN is not a universal replacement for all intrusion detection methods. Its strength is more specific: it is a streaming, operationally calibrated detector for the rare-attack regime. This section discusses where that positioning is appropriate, why the high-prevalence UNSW-NB15 partition changes the problem, and which limitations remain.

## 6.1. When CALIBURN Works and When It Does Not

The experiments suggest a clear operational rule. CALIBURN should be preferred when attacks are rare, the stream is mostly benign, and the operator needs an alerting policy that can be specified before test labels are available. In the experiments, this is most visible on LITNET-2020, where the attack prevalence is 5.2 percent and CALIBURN achieves its strongest performance. This is also the regime where streaming detection makes the most operational sense: the detector is observing a continuous flow of mostly normal trafic and is trying to detect meaningful changes without retraining a batch model.

CALIBURN is also appropriate when the operator can specify a cost ratio between missed attacks and false positives. That cost ratio does not have to be perfect, but it must be explicit. The point is not that C = 10 is universally correct. The point is that the threshold should reflect an operational judgment rather than a hidden validation-set search. CALIBURN is also a good fit when the deployment requires explainable alerting behavior. The system can explain why a flow crossed the posterior threshold, why it consumed alerting budget, and why the burn-rate policy escalated or did not escalate.

The method should not be preferred in every setting. When attack prevalence rises above roughly 20 to 30 percent, the reference distribution learned from the stream becomes less clearly benign. In that regime, a batch method with access to full training data may be stronger, as shown by LOF on CI-CIDS2017. CALIBURN is also not the best choice when there is no streaming constraint, when full historical retraining is available, or when the attack structure forms dense clusters that are better captured by ofline densitybased methods.

We position CALIBURN as a streaming detector tailored to the rareattack regime typical of real monitoring: it performs best when attacks are infrequent and predictably loses its advantage when attacks become prevalent. That is the scenario where the online constraint matters, where false positives are operationally expensive, and where a threshold selected after seeing labels is not realistic.

Deployment surface and throughput.. CALIBURN’s measured per-flow update cost is approximately 6 milliseconds on LITNET-2020 and approximately 61 milliseconds on CICIDS2017, with sustained throughput in the range of 400–600 events per second on the evaluation hardware (Table 8). These figures are not adequate for in-line wire-speed inspection at multigigabit gateway throughput, where per-flow budgets are routinely sub-microseco CALIBURN is therefore appropriate as a Security Operations Centre triage layer over already-aggregated NetFlow or IPFIX summaries, for sampled telemetry pipelines, for SIEM-side enrichment of flow records, or for ofline forensic streaming against captured trafic. It is not appropriate as an inline packet inspector on core routers, where deterministic sub-millisecond latency is a hard requirement. Operators considering tighter throughput budgets should explore the dynamic-truncation and adaptive-hazard directions discussed in Section 6.5, both of which would reduce the per-flow runlength-hypothesis update cost.

## 6.2. The UNSW-NB15 Partition: Base-Rate Inversion

UNSW-NB15 behaves diferently because the resulting evaluation corpus has a much higher attack prevalence than the other datasets used in this paper. After applying our chronological 70/15/15 split to the combined published files (Moustafa and Slay, 2015), approximately 64 percent of the records in the test set are attacks. This is not a small technical detail. It changes the meaning of the detection problem. A streaming detector usually assumes that the stream is mostly normal and that attacks appear as deviations from that background. In UNSW-NB15, that assumption is inverted.

For CALIBURN, the mechanical reason is straightforward. BOCPD tracks how long the current data-generating regime has remained stable. If benign behavior dominates the stream, then attack behavior is more likely to appear as a change-point. But if attack trafic dominates the stream, the model can converge to a regime that is itself attack-heavy. Subsequent attack records are then no longer surprising relative to the model’s current belief. They are consistent with the regime the detector has already learned.

This explains why CALIBURN can produce an AUC-PR near the attack prevalence while having an AUC-ROC near random.

The same base-rate problem afects other streaming baselines, although through diferent mechanisms. Autoencoder methods can learn to reconstruct attack-heavy trafic if that trafic dominates the stream. Projection and histogram methods can absorb attack behavior into their estimated density. Tree-based streaming methods can split around the dominant attack distribution rather than treating it as exceptional. In all cases, the key issue is the same: if the majority of the stream is attack trafic, “normal” no longer means benign.

This is why UNSW-NB15 is treated here as a stress case rather than the primary operational benchmark. Future evaluations of streaming IDS methods should report results across multiple prevalence regimes, not only on a single high-prevalence dataset. A method that performs well at 64 percent attack prevalence may not be useful in a real monitoring stream, and a method that performs poorly there may still be valuable in the rareattack regime where streaming detection is actually needed.

## 6.3. Testing the TTL Artifact Hypothesis on UNSW-NB15

A natural alternative explanation for CALIBURN’s collapse on UNSW-NB15 is that the dataset itself contains synthetic feature artifacts that confound the base-rate-inversion claim. A line of prior work has documented that the UNSW-NB15 Time-To-Live features (sttl, dttl, and ct\_state\_ttl) are correlated with class labels through deterministic structure introduced by the IXIA PerfectStorm testbed topology (Moustafa and Slay, 2015). In the testbed, benign and malicious flows originate from diferent virtual machines behind fixed routers, so observed TTL values encode the initial TTL of the originating VM minus a constant hop count, deterministically reflecting class membership. Empirically, sttl in benign flows concentrates near 31 and 62 while in attack flows it concentrates near 254; similar bimodality holds for dttl and ct\_state\_ttl. Multiple subsequent studies (Mohy-Eddine et al., 2023; Komisarek et al., 2021) have shown that classifiers trained on UNSW-NB15 with these features included become brittle on transfer, and routinely exclude these features from their feature vectors. An expert reviewer asked whether CALIBURN’s observed collapse on UNSW-NB15 might be confounded by these synthetic feature artifacts rather than reflecting a genuine streamingdetection limitation.

We tested this hypothesis directly. We re-ran the entire CALIBURN scoring and calibration pipeline on UNSW-NB15 with sttl, dttl, and ct\_state\_ttl removed from the feature vector (37 features remaining from 41), holding all other splits, hyperparameters, and the BOCPD configuration fixed. Table 13 reports the comparison.

Table 13: UNSW-NB15 TTL ablation. We re-run the full pipeline with sttl, dttl, and ct\_state\_ttl removed from the feature vector and compare against the full-feature baseline. The artifact hypothesis predicts a substantial drop in detection metrics when the TTL features are removed. Empirically, we observe small improvements across all metrics, indicating that CALIBURN’s collapse on UNSW-NB15 is intrinsic to the streaming setting at 64 percent attack prevalence rather than caused by removable feature leakage.

<table><tr><td>Metric</td><td>Full features</td><td>TTL ablated</td><td>Δ</td></tr><tr><td>AUC-PR (raw BOCPD)</td><td>0.6544</td><td>0.6634</td><td>+0.009</td></tr><tr><td>AUC-PR (isotonic)</td><td>0.6767</td><td>0.6935</td><td>+0.017</td></tr><tr><td>AUC-ROC (raw BOCPD)</td><td>0.4930</td><td>0.5169</td><td>+0.024</td></tr><tr><td>AUC-ROC (isotonic)</td><td>0.4996</td><td>0.5312</td><td>+0.032</td></tr><tr><td>Brier (isotonic)</td><td>0.2190</td><td>0.2182</td><td>-0.001</td></tr><tr><td>ECE (isotonic, 15 bins)</td><td>0.0026</td><td>0.0088</td><td>+0.006</td></tr></table>

The result is surprising: AUC-PR and AUC-ROC both rise modestly when the alleged label-correlated features are removed, rather than dropping as the artifact hypothesis would predict. Brier score is essentially unchanged. The expected calibration error rises slightly because the isotonic map has fewer informative features to work with, but the absolute magnitudes remain very small $\left( \leq \ 0 . 0 1 \right)$ . The most informative number is the AUC-ROC: it remains near random $( 0 . 5 0  0 . 5 3 )$ regardless of whether the TTL features are included. CALIBURN simply cannot rank-order attacks against benign trafic on a stream that is 64 percent attack-dominated.

We interpret this as positive evidence that CALIBURN’s collapse on UNSW-NB15 is intrinsic to the high-prevalence streaming setting, consistent with our base-rate-inversion analysis in Section 6.2, rather than an artifact of removable feature leakage. The 64 percent attack prevalence corrupts the running reference distribution that BOCPD maintains; no monotone posthoc map can recover meaningful attack probabilities from a score that has lost its physical meaning. This is, we think, a useful finding for the practitioner literature on UNSW-NB15: streaming change-point detection methods do not benefit from the TTL features that batch classifiers extract signal from, and the streaming-detection limitation at high prevalence is a genuine limitation of the approach rather than a measurement artifact.

## 6.4. Threats to Validity

The first threat is the choice of observation model. CALIBURN uses BOCPD with a Gaussian observation model. Other models, including Gaussian process (Saatçi et al., 2010), beta-Bernoulli, multinomial, or heavy-tailed likelihoods, may behave diferently. We use the Gaussian model for tractability and streaming eficiency, but this choice should not be treated as final.

The second threat is dataset correction. This paper uses the corrected CICIDS2017 version rather than the original 2017 release. This is the right methodological choice because the original dataset has documented errors in trafic generation, feature extraction, and labeling (Engelen et al., 2021; Liu et al., 2022). However, it also means the results should not be compared naively against papers that used the uncorrected release.

The third threat is deterministic versus stochastic baselines. Several baselines are deterministic under the fixed preprocessing and split, while others depend on random seeds. We report three-seed variance for stochastic methods on LITNET-2020 and CICIDS2017, but deterministic comparisons remain point estimates. This is why we avoid overstating Wilcoxon tests across deterministic-stochastic boundaries.

The fourth threat is cost-ratio specification. CALIBURN assumes that the operator can specify the relative cost of a false negative and a false positive. In production, this may require incident-response cost estimates that are not always available. The default C = 10 is reasonable for experimentation, but the real value should be chosen by the organization deploying the detector.

The fifth threat is posterior calibration. The threshold derivation in Section 3.3 assumes a calibrated probability $p _ { t }$ . The BOCPD posterior $s _ { t }$ is not such a probability by default. Section 3.4 introduces an explicit isotonic calibration layer to bridge this gap and a Conformal Risk Control wrapper to provide marginal FPR bounds under exchangeability of validation and test negatives. The empirical results in Section 5.5 confirm that isotonic calibration substantially reduces Brier score (by 30 to 63 percent across the three datasets) and that the CRC threshold satisfies the target alert budget on every dataset and every operator-relevant value of $\alpha$ . The remaining residual threats are two: first, exchangeability is at best approximate in streaming

NIDS with drift, evolving service mixes, and adversarial behaviour, and under heavy concept drift periodic recalibration would be required; second, the CRC procedure exhibits a documented small-α overshoot of up to $2 B / ( n _ { 0 } + 1 )$ that bounds the operator’s choice of alert budget from below.

Hazard rate sensitivity.. The hazard parameter H encodes the prior probability of a regime change per flow and is held fixed at $H = 1 0 ^ { - 3 }$ throughout the evaluation. We conducted pilot sensitivity experiments varying H across the operationally relevant range $[ 1 0 ^ { - 2 } , 2 \times 1 0 ^ { - 4 } ]$ on a 200,000-flow LITNET-2020 prefix. The downstream detection metrics (AUC-PR, AUC-ROC, F1) showed variation below the reporting precision of this paper. We attribute this to a structural property of BOCPD on real network-flow streams: the data-likelihood term in the run-length update dominates the change-point prior at the per-flow scale, so within the operationally relevant range the hazard parameter has minimal influence on the detection metrics. Outside this range, particularly at $H \to 1$ or $H  0$ , BOCPD becomes pathological for unrelated reasons (degenerate posterior dynamics or numerical instability), so we do not report a formal hazard sensitivity table; we recommend $H = 1 0 ^ { - 3 }$ as a robust default and leave adaptive hazard estimation to future work.

## 6.5. Future Directions

The most important future direction is online recalibration. CALIBURN currently fits the isotonic calibration map once on the validation split. Under heavy concept drift, the calibration map becomes stale and CRC validity can degrade. Streaming variants of isotonic regression and online conformal calibration are natural next steps for production deployment.

A second direction is sensitivity analysis over the run-length truncation L and adaptive hazard estimation. Within the operationally relevant range of H, our pilot experiments suggest the data likelihood dominates the prior, so the choice of H has minimal impact (Section 6.4). Adaptive hazard estimators that update H from observed change-point intervals could nevertheless improve detection latency under regime shifts.

A third direction is online cost-ratio adaptation. In this paper, the cost ratio is operator-specified. In a production SOC, that ratio could be updated from incident-response outcomes, analyst workload, or escalation cost.

A fourth direction is multi-class detection. CALIBURN currently treats the problem as binary: attack or non-attack. Extending the framework to distinguish attack families would make it more useful for triage and response.

Finally, CALIBURN currently runs as a single streaming detector. Future work could study federated or distributed change-point detection across multiple sensors, sites, or network segments. The same threshold and burnrate logic should extend naturally to that setting, but the statistical model would need to account for correlated alerts across monitoring points.

## 7. Conclusion

CALIBURN is a streaming network intrusion detector that integrates truncated Bayesian online change-point detection, isotonic calibration of the run-length posterior to an empirical conditional attack probability $\hat { P } ( y _ { t } = 1$ $s _ { t } )$ , a Conformal Risk Control wrapper that converts an alert-budget specification into a marginally-valid threshold under exchangeability, cost-sensitive threshold derivation, and multi-window burn-rate alerting from Site Reliability Engineering practice. Its main architectural point is the separation of statistical scoring, posterior calibration, operational decision, and alerting policy. This separation allows operators to specify alerting behavior before deployment using quantities they can reason about, such as false-negative cost, false-positive cost, and alerting budget, rather than relying on thresholds tuned after observing labeled validation data.

The empirical results show clear regime sensitivity across the three evaluated NIDS datasets. On LITNET-2020, with 5.2 percent attack prevalence, CALIBURN achieves AUC-PR 0.943, outperforming the best streaming baseline by 2.21× and the best batch reference by 4.12×. On CICIDS2017, with 22.06 percent attack prevalence, CALIBURN remains the strongest streaming method but trails LOF, a batch reference method. On UNSW-NB15, with approximately 64 percent attack prevalence, all streaming methods including CALIBURN collapse to near-random ranking behavior. These results support a specific claim: CALIBURN is strongest where streaming detection is operationally needed most, namely rare attacks in a mostly benign stream, and it breaks down when the data regime no longer matches that assumption.

The most important next step is online recalibration to handle concept drift, since the current calibration layer is fit once on the validation split and assumes exchangeability of validation and test negatives. Other directions include online cost-ratio adaptation, multi-class extensions for attack-family discrimination, and federated streaming detection across multiple monitoring nodes. Code, configurations, and experimental artifacts are released to

support replication and extension.

## Data and Code Availability

Code, configuration files, plotting scripts, processed metric tables, and reproducibility instructions are available on GitHub at https://github. com/MichelYsf/rcbsid-paper. An archived release of the repository is permanently available on Zenodo at https://doi.org/10.5281/zenodo. 20074590. The repository includes the scripts used to generate the reported tables and figures, fixed random seeds, environment specifications, and configuration files for CALIBURN and the evaluated baselines. The original datasets are not redistributed; the repository provides preprocessing scripts and instructions for obtaining LITNET-2020, CICIDS2017, and UNSW-NB15 from their original sources.

## Appendix A. Baseline Configurations

For reproducibility, Table A.14 documents the exact configuration of every baseline used in this study. All streaming baselines are run through the PySAD framework (Yilmaz and Kozat, 2020) version 0.2.0 with their authors’ default hyperparameters and random\_state set per seed in {11, 23, 47}. All batch baselines are run through PyOD (Zhao et al., 2019) version 1.1.3, fitted on the training partition only, with default hyperparameters per the PyOD documentation as of February 2025. Per-baseline tuning was not performed: we report out-of-the-box performance to reflect the operational reality of production teams who rarely tune anomaly detectors per dataset, and because per-dataset tuning would invalidate the streaming, label-free framing of the paper. The reported AUC-PR margins should therefore be read as “CAL-IBURN versus best-efort default-configuration baselines” rather than as a tuned comparison.

Table A.14: Baseline implementations and hyperparameter configurations. PySAD baselines are streaming detectors; PyOD baselines are batch references included for context. All settings reflect framework defaults at the time of evaluation. CALIBURN’s run\_length\_truncation $( L = 5 0 0 )$ and hazard $( H = 1 0 ^ { - 3 } )$ are documented in the main text.

<table><tr><td>Baseline</td><td>Framework</td><td>Hyperparameters</td></tr><tr><td>Half-Space Trees (HST)</td><td>PySAD 0.2.0</td><td>num_trees=25, max_depth=15, window_size=250</td></tr><tr><td>LODA</td><td>PySAD 0.2.0</td><td>n_bins=10, n_random_cuts=100</td></tr><tr><td>RRCF</td><td>PySAD 0.2.0</td><td>num_trees=40, tree_size=256</td></tr><tr><td>KitNET</td><td>PySAD 0.2.0</td><td>max_size_ae=10, grace_feature_mapping=5000, grace_anon</td></tr><tr><td>iForestASD</td><td>PySAD 0.2.0</td><td>n_estimators=100, window_size=2048</td></tr><tr><td>LOF</td><td>PyOD 1.1.3</td><td>n_neighbors=20, algorithm=&#x27;auto&#x27;, leaf_size=30</td></tr><tr><td>ECOD</td><td>PyOD 1.1.3</td><td>default (no tunable hyperparameters)</td></tr><tr><td>COPOD</td><td>PyOD 1.1.3</td><td>default (no tunable hyperparameters)</td></tr></table>

## References

Adams, R.P., MacKay, D.J.C., 2007. Bayesian online changepoint detection. arXiv preprint arXiv:0710.3742 .

Alahmadi, B.A., Axon, L., Martinovic, I., 2022. 99% false positives: a qualitative study of SOC analysts’ perspectives on security alarms. 31st USENIX Security Symposium (USENIX Security 22) , 2783–2800.

Angelopoulos, A.N., Bates, S., Fisch, A., Lei, L., Schuster, T., 2024. Conformal risk control, in: International Conference on Learning Representations (ICLR). ArXiv:2208.02814.

Arp, D., Quiring, E., Pendlebury, F., Warnecke, A., Pierazzi, F., Wressnegger, C., Cavallaro, L., Rieck, K., 2022. Dos and don’ts of machine learning in computer security. 31st USENIX Security Symposium (USENIX Security 22) , 3971–3988.

Barber, R.F., Candès, E.J., Ramdas, A., Tibshirani, R.J., 2023. Conformal prediction beyond exchangeability. Annals of Statistics 51, 816–845. doi:10.1214/23-AOS2276.

Barrett, S., Li, L., Dorai, G., Rajaganapathy, S., 2026. FIRCE: A framework for intrusion response and conformal evaluation. arXiv preprint arXiv:2605.01962 .

Bates, S., Angelopoulos, A., Lei, L., Malik, J., Jordan, M.I., 2021. Distribution-free, risk-controlling prediction sets. Journal of the ACM 68, 1–34.

Beyer, B., Jones, C., Petof, J., Murphy, N.R., 2016. Site Reliability Engineering: How Google Runs Production Systems. O’Reilly Media.

Beyer, B., Murphy, N.R., Rensin, D.K., Kawahara, K., Thorne, S., 2018. The Site Reliability Workbook: Practical Ways to Implement SRE. O’Reilly Media.

Breunig, M.M., Kriegel, H.P., Ng, R.T., Sander, J., 2000. Lof: identifying density-based local outliers, in: Proceedings of the 2000 ACM SIGMOD International Conference on Management of Data, pp. 93–104.

Cao, Y., et al., 2025. Revisiting streaming anomaly detection: benchmark and evaluation. Artificial Intelligence Review Survey of streaming anomaly detection methods.

Catillo, M., Pecchia, A., Villano, U., 2023. Machine learning on public intrusion datasets: Academic hype or concrete advances in NIDS?, in: 53rd Annual IEEE/IFIP International Conference on Dependable Systems and Networks Supplementary Volume (DSN-S), IEEE. pp. 132–136. doi:10.1109/DSN-S58398.2023.00038.

Damaševičius, R., Venckauskas, A., Grigaliunas, Š., Toldinas, J., Morkevičius, N., Aleliunas, T., Smuikys, P., 2020. LITNET-2020: an annotated real-world network flow dataset for network intrusion detection. Electronics 9, 800.

Ding, Z., Fei, M., 2013. An anomaly detection approach based on isolation forest algorithm for streaming data using sliding window, in: 3rd IFAC International Conference on Intelligent Control and Automation Science (ICONS), pp. 12–17.

Domingos, P., 1999. Metacost: a general method for making classifiers costsensitive, in: Proceedings of the Fifth ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp. 155–164.

Elkan, C., 2001. The foundations of cost-sensitive learning, in: Proceedings of the Seventeenth International Joint Conference on Artificial Intelligence (IJCAI), pp. 973–978.

Engelen, G., Rimmer, V., Joosen, W., 2021. Troubleshooting an intrusion detection dataset: the CICIDS2017 case study, in: 2021 IEEE Security and Privacy Workshops (SPW), pp. 7–12.

Farinhas, A., Zerva, C., Ulmer, D.T., Martins, A.F.T., 2024. Nonexchangeable conformal risk control, in: International Conference on Learning Representations (ICLR).

Fearnhead, P., Liu, Z., 2007. On-line inference for multiple changepoint problems. Journal of the Royal Statistical Society: Series B (Statistical Methodology) 69, 589–605.

Gibbs, I., Candès, E.J., 2021. Adaptive conformal inference under distribution shift, in: Advances in Neural Information Processing Systems (NeurIPS). ArXiv:2106.00170.

Gibbs, I., Candès, E.J., 2024. Conformal inference for online prediction with arbitrary distribution shifts. Journal of Machine Learning Research 25, 1–36. ArXiv:2208.08401.

Guha, S., Mishra, N., Roy, G., Schrijvers, O., 2016. Robust random cut forest based anomaly detection on streams, in: Proceedings of the 33rd International Conference on Machine Learning (ICML), pp. 2712–2721.

Gurjar, A., Camp, L.J., 2026. Predicting tail-risk escalation in IDS alert time series. arXiv preprint arXiv:2601.14299 .

Knoblauch, J., Damoulas, T., 2018. Spatio-temporal bayesian on-line changepoint detection with model selection, in: Proceedings of the 35th International Conference on Machine Learning (ICML), pp. 2718–2727.

Knoblauch, J., Jewson, J.E., Damoulas, T., 2018. Doubly robust bayesian inference for non-stationary streaming data with β-divergences, in: Advances in Neural Information Processing Systems 31 (NeurIPS), pp. 64–75.

Komisarek, M., Pawlicki, M., Kozik, R., Hołubowicz, W., Choraś, M., 2021. How to efectively collect and process network data for intrusion detection? Entropy 23, 1532.

Lanvin, M., Gimenez, P.F., Han, Y., Majorczyk, F., Mé, L., Totel, E., 2023. Errors in the CICIDS2017 dataset and the significant diferences in detection performances it makes, in: Risks and Security of Internet and Systems (CRiSIS 2022), Springer. pp. 18–33. doi:10.1007/978-3-031-31108-6\_2.

Li, Z., Zhao, Y., Botta, N., Ionescu, C., Hu, X., 2020. Copod: copula-based outlier detection. 2020 IEEE International Conference on Data Mining (ICDM) , 1118–1123.

Li, Z., Zhao, Y., Hu, X., Botta, N., Ionescu, C., Chen, G.H., 2022. Ecod: unsupervised outlier detection using empirical cumulative distribution functions. IEEE Transactions on Knowledge and Data Engineering 35, 12181– 12193.

Liu, L., Engelen, G., Lynar, T., Essam, D., Joosen, W., 2022. Error prevalence in NIDS datasets: a case study on CIC-IDS-2017 and CSE-CIC-IDS-2018. 2022 IEEE Conference on Communications and Network Security (CNS) , 254–262.

Lorden, G., 1971. Procedures for reacting to a change in distribution. The Annals of Mathematical Statistics 42, 1897–1908. doi:10.1214/aoms/ 1177693055.

Manzoor, E., Lamba, H., Akoglu, L., 2018. xstream: outlier detection in feature-evolving data streams, in: Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (KDD), pp. 1963–1972.

Mirsky, Y., Doitshman, T., Elovici, Y., Shabtai, A., 2018. Kitsune: an ensemble of autoencoders for online network intrusion detection. Proceedings of the Network and Distributed System Security Symposium (NDSS) .

Mohy-Eddine, M., Guezzaz, A., Benkirane, S., Azrour, M., 2023. Feature selection method for intrusion detection systems based on unsw-nb15 dataset. Big Data Mining and Analytics 6, 273–287.

Moustafa, N., Slay, J., 2015. UNSW-NB15: a comprehensive data set for network intrusion detection systems, in: 2015 Military Communications and Information Systems Conference (MilCIS), pp. 1–6.

Niculescu-Mizil, A., Caruana, R., 2005. Predicting good probabilities with supervised learning, in: Proceedings of the 22nd International Conference on Machine Learning (ICML), pp. 625–632.

Page, E.S., 1954. Continuous inspection schemes. Biometrika 41, 100–115.doi:10.1093/biomet/41.1-2.100.

Pevný, T., 2016. Loda: Lightweight on-line detector of anomalies. Machine Learning 102, 275–304.

Saatçi, Y., Turner, R.D., Rasmussen, C.E., 2010. Gaussian process change point models, in: Proceedings of the 27th International Conference on Machine Learning (ICML-10), pp. 927–934.

Saito, T., Rehmsmeier, M., 2015. The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PLoS ONE 10, e0118432.

Sharafaldin, I., Lashkari, A.H., Ghorbani, A.A., 2018. Toward generating a new intrusion detection dataset and intrusion trafic characterization, in: Proceedings of the 4th International Conference on Information Systems Security and Privacy (ICISSP), pp. 108–116.

Shiryaev, A.N., 1978. Optimal Stopping Rules. Springer-Verlag, Berlin, Heidelberg.

Tan, S.C., Ting, K.M., Liu, T.F., 2011. Fast anomaly detection for streaming data, in: Proceedings of the Twenty-Second International Joint Conference on Artificial Intelligence (IJCAI), pp. 1511–1516.

Tibshirani, R.J., Foygel Barber, R., Candès, E.J., Ramdas, A., 2019. Conformal prediction under covariate shift, in: Advances in Neural Information Processing Systems (NeurIPS). ArXiv:1904.06019.

Wald, A., 1945. Sequential tests of statistical hypotheses. The Annals of Mathematical Statistics 16, 117–186. doi:10.1214/aoms/1177731118.

Wilcoxon, F., 1945. Individual comparisons by ranking methods. Biometrics Bulletin 1, 80–83.

Yang, M., Bi, X., 2024. Cost-aware calibration of classifiers. INFORMS Journal on Data Science 4, 101–113. doi:10.1287/ijds.2024.0038.

Yilmaz, S.F., Kozat, S.S., 2020. PySAD: A streaming anomaly detection framework in Python. arXiv preprint arXiv:2009.02572 .

Zadrozny, B., Elkan, C., 2002. Transforming classifier scores into accurate multiclass probability estimates, in: Proceedings of the Eighth ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp. 694–699.

Zhao, Y., Nasrullah, Z., Li, Z., 2019. PyOD: A Python toolbox for scalable outlier detection. Journal of Machine Learning Research 20, 1–7.