---
title: "2026-Inan-Proximity-Anomaly-Calibration-Leakage-Safety"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Inan-Proximity-Anomaly-Calibration-Leakage-Safety.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Proximit<sub>y</sub>-based ex<sub>p</sub>lainable anomal<sub>y</sub> detection for time-series data with calibration<sub>,</sub> leaka<sub>g</sub>e safet<sub>y</sub>

![](images/6b0769187e677d5aaee0f4228124a1c264094d68fd96f41f84c88b3b951a79e7.jpg)

Ebubekir <sup>˙</sup>Inan

Kayseri University, Faculty of Engineering, Architecture and Design, Department of Engineering Basic Sciences, Kayseri, 38000, Türkiye

## a r t i c l e i n f o

2000 MSC: 62M10 62H30 68T05

Keywords: Time series anomal<sub>y</sub> detection Proximit<sub>y</sub>-based modelin<sub>g</sub> Adaptive epsilon (rollin<sub>g</sub> MAD) Ex lainable AI (SHAP) Semi-su ervised learnin De<sub>p</sub>lo<sub>y</sub>ment-oriented evaluation

## a b s t r a c t

Anomal detection in non-stationar time-series streams is dificult when events are rare<sub>,</sub> score distributions drift<sub>,</sub> and o<sub>p</sub>erators can ins<sub>p</sub>ect onl<sub>y</sub> a fixed fraction of alarms. We introduce a de lo ment-oriented framework built on an unsu ervised<sub>,</sub> train-referenced roximit score computed in a compact Principal Component Anal<sub>y</sub>sis (PCA) embeddin<sub>g</sub> and stabilized b<sub>y</sub> a causal rollin Median Absolute Deviation (MAD) scale. The score is converted into decision-read out-<sub>p</sub>uts throu<sub>g</sub>h a strictl<sub>y</sub> leaka<sub>g</sub>e-safe <sub>p</sub>rotocol: <sub>p</sub>er-series tem<sub>p</sub>oral s<sub>p</sub>littin<sub>g,</sub> train-onl<sub>y</sub> isotonic calibration on a calibration-fit block and deterministic tie-safe to -� selection to enforce an explicit alert budget (e.g., �=1%) on a held-out evaluation block. Across three public labeled benchmarks—the Numenta Anomal Benchmark (NAB) the Server Machine Dataset (SMD) and the UCR Time Series Anomal Archive (UCR)—we re ort ooled ointwise area under the receiver operatin<sub>g</sub> characteristic curve (ROC–AUC) and area under the precision–recall curve (PR– AUC) to ether with fixed-bud et recision and recall at an alert fraction $q = 1 \% ,$ and seriesaware bootstrap confidence intervals. The method achieves the best PR–AUC on SMD (0.500) and NAB (0.359) under the leak-free protocol, while remainin<sub>g</sub> computationall<sub>y</sub> feasible compared with forecastin<sub>g</sub>-residual baselines. On UCR<sub>,</sub> results indicate an ex<sub>p</sub>licit trade-of on sha<sub>p</sub>e-driven anomalies motivatin o eratin - olic tunin . For the unlabeled Intel Berkele Lab telemetr we make no detection-accurac<sub>y</sub> claims<sub>;</sub> instead<sub>,</sub> we evaluate bud<sub>g</sub>eted screenin<sub>g</sub> utilit<sub>y</sub> via a Com osite Tria e Score that summarizes covera e stabilit concentration event duration and runtime.

## 1. Introduction

We stud<sub>y</sub> time-series anomal<sub>y</sub> detection under non-stationarit<sub>y,</sub> extreme class imbalance<sub>,</sub> and o<sub>p</sub>erational alarm bud<sub>g</sub>ets<sub>,</sub> where de lo ment re uires calibrated anomal robabilities and leaka e-safe evaluation. Anomal detection in time series is central to reliable decision makin in finance, ener , and lar e-scale Internet of Thin s (IoT), where rare events must be surfaced under non-stationarit<sub>y</sub>, noise, and severe class imbalance [1,2]. Communit<sub>y</sub> benchmarks such as the Numenta Anomal<sub>y</sub> Benchmark (NAB) [3–6] and o en telemetr cor ora (e. . Intel Berkele Lab [7]) t if these de lo ment realities: evolvin re imes incom lete or dela ed su ervision and stron constraints on latenc and memor . NAB su orts streamin evaluation with labeled anomalies (and event-window conventions), whereas Intel-scale telemetr<sub>y</sub> stresses lon<sub>g</sub>-duration operation in the presence of missin<sub>g</sub>ness and limited labelin —to ether enablin assessment under controlled scorin as well as de lo ment-like conditions.

A wide spectrum of detectors has been proposed. Classical baselines—Local Outlier Factor (LOF) [8], one-class support vector machine (SVM) [9], and Isolation Forest [10]—o erationalize densit , su ort, or isolation rinci les and remain indis ensable ref erence oints. Distance- and densit -based clusterin extensions [11] im rove flexibilit in hetero eneous data. Dee learnin further expanded the modelin<sub>g</sub> space throu<sub>g</sub>h sequence and reconstruction paradi<sub>g</sub>ms: lon<sub>g</sub> short-term memor<sub>y</sub> (LSTM) encoder–decoders [12], convolutional forecasters (Dee AnT) [13], and variational autoencoder (VAE)-based seasonal ke erformance indicator (KPI) modelin<sub>g</sub> [14] established re<sub>p</sub>resentation learnin<sub>g</sub> as a stron<sub>g</sub> alternative [15,16], followed b<sub>y</sub> stochastic recurrent networks (Om niAnomal ) [17], h brid autoencoders (USAD) [18], and Transformer-based detectors [19] that ca ture multi-scale and non-local <sup>t</sup>empora<sup>l</sup> s<sup>t</sup>ruc<sup>t</sup>ure. <sup>R</sup>ecen<sup>t</sup> wor<sup>k h</sup>as emp<sup>h</sup>as<sup>i</sup>ze<sup>d</sup> ro<sup>b</sup>us<sup>t</sup>ness <sup>t</sup>o con<sup>t</sup>am<sup>i</sup>na<sup>t</sup>e<sup>d t</sup>ra<sup>i</sup>n<sup>i</sup>ng <sup>d</sup>a<sup>t</sup>a <sup>[20]</sup>, <sup>t</sup>empora<sup>l</sup>-re<sup>l</sup>a<sup>ti</sup>ons<sup>hi</sup>p grap<sup>h</sup>s an<sup>d</sup> a<sup>d</sup>ap<sup>ti</sup>ve smoo<sup>thi</sup>ng <sup>[21]</sup>, <sup>i</sup>n<sup>d</sup>us<sup>t</sup>r<sup>i</sup>a<sup>l d</sup>ep<sup>l</sup>oymen<sup>t</sup>s w<sup>ith</sup> grap<sup>h</sup> a<sup>tt</sup>en<sup>ti</sup>on un<sup>d</sup>er s<sup>t</sup>r<sup>i</sup>c<sup>t l</sup>a<sup>t</sup>ency <sup>b</sup>u<sup>d</sup>ge<sup>t</sup>s <sup>[22]</sup>, re<sup>t</sup>en<sup>ti</sup>ve ne<sup>t</sup>wor<sup>k</sup>-<sup>b</sup>ase<sup>d</sup> anomal<sub>y</sub> detection in c<sub>y</sub>ber-ph<sub>y</sub>sical s<sub>y</sub>stems [23], and li<sub>g</sub>htwei<sub>g</sub>ht federated pipelines for industrial control s<sub>y</sub>stems (ICS)/IoT en v<sup>i</sup>ronmen<sup>t</sup>s <sup>[24]</sup>. <sup>A</sup>pp<sup>li</sup>ca<sup>ti</sup>on-<sup>d</sup>r<sup>i</sup>ven s<sup>t</sup>u<sup>di</sup>es <sup>f</sup>ur<sup>th</sup>er con<sup>fi</sup>rm prac<sup>ti</sup>ca<sup>l i</sup>mpac<sup>t i</sup>n manu<sup>f</sup>ac<sup>t</sup>ur<sup>i</sup>ng an<sup>d</sup> op<sup>ti</sup>m<sup>i</sup>za<sup>ti</sup>on con<sup>t</sup>ex<sup>t</sup>s <sup>[25</sup>,<sup>26]</sup>, an<sup>d d</sup>oma<sup>i</sup>n-groun<sup>d</sup>e<sup>d</sup> p<sup>i</sup>pe<sup>li</sup>nes repor<sup>t</sup> exp<sup>l</sup>a<sup>i</sup>na<sup>bl</sup>e per<sup>f</sup>ormance on m<sup>i</sup>ss<sup>i</sup>on-cr<sup>iti</sup>ca<sup>l t</sup>e<sup>l</sup>eme<sup>t</sup>ry <sup>[27]</sup>. <sup>S</sup>urveys conso<sup>lid</sup>a<sup>t</sup>e <sup>th</sup>ese <sup>di</sup>rec tions and hi<sub>g</sub>hli<sub>g</sub>ht <sub>p</sub>ersistent <sub>g</sub>a<sub>p</sub>s at the intersection of accurac<sub>y,</sub> scalabilit<sub>y,</sub> and inter<sub>p</sub>retabilit<sub>y</sub> in multivariate streamin<sub>g</sub> settin<sub>g</sub>s [28–31].

Des<sub>p</sub>ite this <sub>p</sub>ro<sub>g</sub>ress<sub>,</sub> de<sub>p</sub>lo<sub>y</sub>ment-<sub>g</sub>rade anomal<sub>y</sub> detection under drift and extreme rarit<sub>y</sub> still faces recurrin<sub>g</sub> obstacles. First<sub>,</sub> when ositives are scarce, receiver o eratin characteristic (ROC)-based summaries can be overl o timistic; recision–recall measures rovide a more faithful characterization of o erational utilit [32 33]. Second drift and heav -tailed noise induce score instabilit robust dis ersion estimators such as the (rollin ) median absolute deviation (MAD) can stabilize scalin , et the remain under inte<sub>g</sub>rated in end-to-end anomal<sub>y</sub> s<sub>y</sub>stems [34]. Third, decision-makin<sub>g</sub> is often bud<sub>g</sub>eted (e.<sub>g</sub>., a fixed fraction of <sub>p</sub>oints can be reviewed), but man detectors out ut uncalibrated scores rather than decision-read robabilities. While isotonic re ression is a rinci led monotone ost-hoc calibrator [35 36] anomal i elines rarel inte rate calibration under a strictl leak-free train-onl <sub>p</sub>rotocol where the calibrator and the o<sub>p</sub>eratin<sub>g p</sub>oint are learned without <sub>p</sub>eekin<sub>g</sub> at the final re<sub>p</sub>ortin<sub>g</sub> block. Finall<sub>y,</sub> althou<sub>g</sub>h explainabilit<sub>y</sub> has advanced from post-hoc attributions (e.<sub>g</sub>., Shaple<sub>y</sub> Additive exPlanations (SHAP)) [37] toward more intrinsicall<sub>y</sub> <sup>i</sup>n<sup>t</sup>erpre<sup>t</sup>a<sup>bl</sup>e <sup>d</sup>es<sup>i</sup>gns <sup>[38</sup>,<sup>39]</sup>, prac<sup>titi</sup>oners s<sup>till</sup> nee<sup>d</sup> exp<sup>l</sup>ana<sup>ti</sup>ons <sup>th</sup>a<sup>t</sup> a<sup>li</sup>gn w<sup>ith th</sup>e <sup>d</sup>e<sup>t</sup>ec<sup>t</sup>or<sup>’</sup>s na<sup>ti</sup>ve ev<sup>id</sup>ence an<sup>d</sup> rema<sup>i</sup>n s<sup>t</sup>a<sup>bl</sup>e under drift and hetero<sub>g</sub>eneous re<sub>g</sub>imes.

This work is positioned around a deployment-oriented objective: capturing time-series anomalies under drift and extreme imbalance in com<sub>p</sub>ute-constrained settin<sub>g</sub>s via a train-referenced ada<sub>p</sub>tive score<sub>,</sub> rollin<sub>g</sub>-MAD stabilization<sub>,</sub> and leak-free decision makin<sub>g</sub>. In this paper, proximity is used in the data-mining sense to denote train-referenced neighborhood deviation cues—distance-based depar ture<sub>,</sub> densit -oriented irre ularit <sub>,</sub> and tem oral-chan e si nals—that are transformed into actionable anomal scores and calibrated probabilities. We do not assume or invoke a proximity relation in the axiomatic/topological sense; the term is strictly descriptive of the nei<sub>g</sub>hborhood evidence extracted relative to the trainin<sub>g</sub> reference.

Throughout the paper, Proposed refers to the unsupervised detection core: (i) the proximity-based anomaly score and (ii) train-only ca<sup>lib</sup>rat<sup>i</sup>on <sup>l</sup>earne<sup>d</sup> str<sup>i</sup>ct<sup>l</sup> on calib\_fit. <sup>A</sup>n su erv<sup>i</sup>se<sup>d</sup> mo<sup>d</sup>e<sup>l</sup> use<sup>d f</sup>or <sup>i</sup>nter reta<sup>bili</sup>t (e. . a <sup>Li h</sup>t <sup>G</sup>ra<sup>di</sup>ent-<sup>B</sup>oost<sup>i</sup>n <sup>M</sup>ac<sup>hi</sup>ne (LightGBM) head with SHAP) is an optional analysis layer and is not required to produce the reported detection results.

<sup>B</sup>u<sup>ildi</sup>ng on <sup>th</sup>e <sup>d</sup>r<sup>ift</sup>-res<sup>i</sup>s<sup>t</sup>an<sup>t b</sup>e<sup>h</sup>av<sup>i</sup>or o<sup>f MAD</sup> sca<sup>li</sup>ng <sup>[34]</sup>, we <sup>i</sup>n<sup>t</sup>ro<sup>d</sup>uce an <sup>i</sup>n<sup>t</sup>egra<sup>t</sup>e<sup>d f</sup>ramewor<sup>k th</sup>a<sup>t</sup> c<sup>l</sup>oses prac<sup>ti</sup>ca<sup>l d</sup>ep<sup>l</sup>oy ment <sub>g</sub>a<sub>p</sub>s without increasin<sub>g</sub> model com<sub>p</sub>lexit<sub>y</sub>:

• Train-referenced adaptive anomaly scoring: a train-referenced evidence la er that com utes com lementar normalized cues (level departure, a densit cue with a safe fallback, velocit in embeddin -increment space, and protot pe distance) and fuses them into a label-a nostic score �(�) ∈ [0, 1] under an ada tive rollin -MAD scale to im rove stabilit under non-stationarit while remainin<sub>g p</sub>arameter-li<sub>g</sub>ht.

• Leak-free calibration and budgeted decision policy: on labeled benchmarks isotonic re ression is fitted only on a calibration fit block to map �(�) to calibrated probabilities, and a fixed-budget operating threshold (e.g., top-1%) is learned on the same calibration-fit block and transferred unchan ed to a held-out calibration-evaluation block for final re ortin [35].

• Actionable explainability and deployment triage: On labeled benchmarks SHAP attributions are com uted on the leak-free eva<sup>l</sup>uat<sup>i</sup>on <sup>bl</sup>oc<sup>k</sup> (calib\_eval) <sup>f</sup>or t<sup>h</sup>e <sup>d</sup>ep<sup>l</sup>oye<sup>d d</sup>ec<sup>i</sup>s<sup>i</sup>on score, <sup>i</sup>.e., t<sup>h</sup>e <sup>i</sup>soton<sup>i</sup>c-ca<sup>lib</sup>rate<sup>d</sup> anoma<sup>l</sup>y pro<sup>b</sup>a<sup>bili</sup>ty [<sup>37</sup>]. <sup>O</sup>n t<sup>h</sup>e unlabeled Intel Berkele Lab telemetr we do not claim su ervised detection erformance instead we re ort de lo ment-tria e utilit under a fixed alert bud et usin label-free distributional normalization, Em irical Cumulative Distribution Function (ECDF) / Chunked Em irical Cumulative Distribution Function (ChECDF) and o erational criteria (covera e stabilit concentration and event characteristics).

<sup>O</sup>pera<sup>ti</sup>ona<sup>ll</sup> , <sup>th</sup>e <sup>f</sup>ramewor<sup>k t</sup>ar e<sup>t</sup>s s<sup>t</sup>ron per<sup>f</sup>ormance un<sup>d</sup>er prec<sup>i</sup>s<sup>i</sup>on–reca<sup>ll</sup> eva<sup>l</sup>ua<sup>ti</sup>on <sup>[32</sup>,<sup>33]</sup> an<sup>d b</sup>u<sup>d</sup> e<sup>t</sup>-<sup>t</sup>empere<sup>d</sup> a<sup>l</sup>arm re<sub>g</sub>imes<sub>,</sub> while su<sub>pp</sub>ortin<sub>g</sub> an accurac<sub>y</sub>–runtime trade-of that remains sustainable relative to com<sub>p</sub>ute-heav<sub>y</sub> forecastin<sub>g</sub> baselines <sup>[19]</sup>. <sup>Gi</sup>ven <sup>th</sup>e rare-even<sup>t</sup> na<sup>t</sup>ure o<sup>f</sup> anoma<sup>li</sup>es, we emp<sup>h</sup>as<sup>i</sup>ze <sup>PR</sup>-<sup>AUC</sup> an<sup>d b</sup>u<sup>d</sup>ge<sup>t</sup>-a<sup>li</sup>gne<sup>d</sup> prec<sup>i</sup>s<sup>i</sup>on<sup>/</sup>reca<sup>ll</sup> me<sup>t</sup>r<sup>i</sup>cs; <sup>ROC</sup>-<sup>AUC i</sup>s re orted for com leteness but can be o timistic under severe imbalance.

Across com lementar settin s the a roach exhibits robust behavior under the stated leak-free rotocol. On NAB [3–6] we observe stron PR-oriented rankin and conservative fixed-bud et alertin (e. ., PR–AUC = 0.359 with PR@1% = 1.000 under oint wise ooled re ortin on ) while maintainin low runtime relative to forecastin residual baselines. On Server Machine Dataset (SMD), the ro osed method achieves stron PR–AUC (= 0.500) and com etitive bud eted erformance, with ex licit trade ofs a<sub>g</sub>ainst fast classical baselines. On UCR at scale<sub>,</sub> absolute PR values remain small due to extreme s<sub>p</sub>arsit<sub>y</sub> and hetero<sub>g</sub>eneit<sub>y, y</sub>et th d th d i ld f bl fi d b d t b h i ith t t bl ti O I t l l t [7] h l b l b sent<sub>,</sub> the method <sub>p</sub>roduces stable hots<sub>p</sub>ot rankin<sub>g</sub>s and inter<sub>p</sub>retable alert <sub>p</sub>atterns under a fixed bud<sub>g</sub>et<sub>,</sub> summarized b<sub>y</sub> a Com<sub>p</sub>osite Tria e Score constructed from covera e<sub>,</sub> stabilit <sub>,</sub> concentration<sub>,</sub> event duration<sub>,</sub> and runtime. Ablations indicate that rollin -MAD stabilization im roves tem oral stabilit and that the decision la er reduces o eratin - oint volatilit under severe imbalance

The remainder of the <sub>p</sub>a<sub>p</sub>er details the <sub>p</sub>roximit<sub>y</sub>-based scorin<sub>g</sub> and rollin<sub>g</sub>-MAD stabilization<sub>,</sub> the strictl<sub>y</sub> leak-free calibration and bud<sub>g</sub>eted thresholdin<sub>g p</sub>rotocol<sub>,</sub> and the ex<sub>p</sub>lainabilit<sub>y</sub> and tria<sub>g</sub>e <sub>p</sub>i<sub>p</sub>elines<sub>,</sub> followed b<sub>y</sub> com<sub>p</sub>rehensive ex<sub>p</sub>eriments<sub>,</sub> ablations<sub>,</sub> and a discussion of de lo ment considerations and limitations.

## 2. Method: Adaptive proximity framework

The ro osed framework out uts ointwise anomal scores usin an unsu ervised roximit core and converts them to calibrated anomaly probabilities using a calibrator fit on calib\_fit only. A separate supervised head (LightGBM) is introduced solely to enable feature attribution (SHAP) and is kept outside the detection pipeline used in all quantitative comparisons

## 2.1. Overview of the proposed framework

We ro ose a de lo ment-oriented anomal detection framework for non-stationar time series that tar ets three ractical con straints: (i) severe class imbalance, (ii) re<sub>g</sub>ime shifts and drift, and (iii) the need for transparent, actionable outputs under limited com<sub>p</sub>ute bud<sub>g</sub>ets. The framework is desi<sub>g</sub>ned to o<sub>p</sub>erate in both labeled benchmarks and unlabeled o<sub>p</sub>erational telemetr<sub>y</sub>. Its core out ut is a er-time- oint anomal score which can be further converted into calibrated anomal robabilities when labels are available<sub>,</sub> and into ranked event candidates and stream-level tria<sub>g</sub>e summaries when labels are absent.

Pipeline at a glance: For each time series (or sensor stream) processed independently, the framework follows the steps below:

1. Causal preprocessing (leak-free): Numeric features are forward-filled with a bounded limit and missing values are imputed usin<sub>g</sub> train-onl<sub>y</sub> medians.

2. Train-only embedding: A com act re resentation is learned on the trainin refix via standardization and PCA, ieldin a fixed three-dimensional embeddin<sub>g p</sub>er time index.

3. Proximity evidence cues: Four complementary proximity cues are computed relative to the training reference: (a) drift-adaptive level departure, (b) a densit<sub>y</sub> cue via train-fitted outlier scorin<sub>g</sub> (with a safe fallback), (c) a velocit<sub>y</sub> cue in embeddin<sub>g</sub>-increment space, and (d) distance to a robust trainin<sub>g</sub> protot<sub>y</sub>pe.

4. Fusion into a single score: The train-normalized evidence cues are aggregated by a monotone fusion operator to form a label agnostic anoma<sup>l</sup>y score $s ( t ) \in [ 0 , 1 ]$

5. Calibration and decision policy (labeled setting): Usin a strictl leak-free tem oral s lit, isotonic re ression is fitted on a calibration-fit block to obtain calibrated robabilities and a bud eted threshold is learned on calibration-fit and a lied to a held-out calibration-evaluation block.

6. Deployment triage (unlabeled setting): On unlabeled telemetry, the same score is used to extract candidate events and compute stream-level tria e statistics (covera e, stabilit , concentration, and duration) without an label de endence.

A complete, implementation-faithful pseudocode of Steps 1–6 is provided in Appendix A (Al<sub>g</sub>orithms 1–3).

All o<sub>p</sub>erations that involve fittin<sub>g</sub>—includin<sub>g</sub> im<sub>p</sub>utation statistics<sub>,</sub> scalin<sub>g,</sub> PCA<sub>,</sub> o<sub>p</sub>tional densit<sub>y</sub> modelin<sub>g,</sub> calibration<sub>,</sub> and threshold selection—are learned exclusivel from the desi nated trainin or calibration-fit se ments and are never informed b future sam les. Each series is rocessed inde endentl enablin a manifest/ arts workflow that bounds memor usa e and su orts <sup>l</sup>arge corpora.

Consider a sin<sub>g</sub>le series indexed b<sub>y</sub> $t \in X = \{ 1 , \ldots , n \}$ . Let $X _ { \mathrm { t r } } \subset X$ denote the leak-free trainin<sub>g p</sub>refix used to fit <sub>p</sub>re<sub>p</sub>rocessin<sub>g</sub> and the embeddin<sub>g</sub>. The train-fitted embeddin<sub>g</sub> is denoted b<sub>y</sub> $\mathbf { z } _ { t } \in \mathbb { R } ^ { 3 }$ . The <sub>p</sub>roximit<sub>y</sub> la<sub>y</sub>er <sub>p</sub>roduces four train-normalized evidence cues in [0, 1], which are fused into �(�). In labeled settin s, �(�) is ma ed to calibrated robabilities ̂�(�) and thresholded under a fixed bud<sub>g</sub>et <sub>p</sub>olic<sub>y</sub>.

To miti ate re ime shifts, we rescale scores with a rollin MAD computed causall (no future access), ensurin stabilit under drift while <sub>p</sub>reservin<sub>g</sub> anomal<sub>y</sub> rankin<sub>g</sub>. Rollin<sub>g</sub>-MAD scalin<sub>g p</sub>rovides a robust<sub>,</sub> causal mechanism to ada<sub>p</sub>t <sub>p</sub>roximit<sub>y</sub> to drift. Train referenced nei<sub>g</sub>hborhoods ensure that all <sub>p</sub>roximit<sub>y</sub> cues are com<sub>p</sub>arable across time while remainin<sub>g</sub> leak-free. Finall<sub>y,</sub> the framework rioritizes o erational feasibilit : it ields com etitive accurac under extreme imbalance while maintainin redictable runtime and resilience to lon -job interru tions, which is critical when contrastin with heav dee forecastin baselines.

## 2.2. Leak-free embedding and adaptive reference scale

<sup>W</sup>e cons<sup>t</sup>ruc<sup>t</sup> a per-ser<sup>i</sup>es prox<sup>i</sup>m<sup>it</sup>y <sup>l</sup>ayer <sup>th</sup>a<sup>t i</sup>s s<sup>t</sup>r<sup>i</sup>c<sup>tl</sup>y <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree an<sup>d d</sup>ep<sup>l</sup>oymen<sup>t</sup>-a<sup>li</sup>gne<sup>d</sup>. <sup>E</sup>ac<sup>h</sup> o<sup>b</sup>serva<sup>ti</sup>on a<sup>t ti</sup>me <sup>i</sup>n<sup>d</sup>ex � <sup>i</sup>s treated as a sin leton set {�} and roximit is evaluated relative to a training reference within the same series. Let $X = \{ 1 , \ldots , n \}$ index the time-ordered sam<sub>p</sub>les of a sin<sub>g</sub>le stream and let $X _ { \mathrm { t r } } \subset X$ denote the leak-free trainin refix used to fit all re rocessin and re<sub>p</sub>resentation ste<sub>p</sub>s. We be<sub>g</sub>in from a numeric feature ma<sub>p</sub> $\Phi ( t ) \in \mathbb { R } ^ { p }$ (base statistical features and robust transforms) and enforce causalit<sub>y</sub> via forward-fill with a bounded limit<sub>,</sub> followed b<sub>y</sub> train-median im<sub>p</sub>utation<sub>;</sub> both o<sub>p</sub>erations are com<sub>p</sub>uted without usin<sub>g</sub> future sam les.

The concrete causal feature construction used to form Φ(�) is summarized in Algorithm 1, while the leak-free sanitization, train di i t ti t i l t d di ti d PCA b ddi t i i Al ith 2

All re<sub>p</sub>resentation learnin<sub>g</sub> is fitted on $X _ { \mathrm { t r } }$ onl<sub>y</sub>. S<sub>p</sub>ecificall<sub>y,</sub> we a<sub>pp</sub>l<sub>y</sub> a train-onl<sub>y</sub> standardization and then a train-onl<sub>y</sub> PCA ma<sub>p</sub> $\Psi : \mathbb { R } ^ { p }  \mathbb { R } ^ { 3 }$ to obtain a com<sub>p</sub>act embeddin<sub>g</sub>

$$
\mathbf {z} _ {t} := \Psi (\Phi (t)) \in \mathbb {R} ^ {3}, \qquad t \in X,\tag{1}
$$

where we denote $\mathbf { z } _ { t } = ( \phi _ { 1 } ( t ) , \phi _ { 2 } ( t ) , \phi _ { 3 } ( t ) )$ . This three-dimensional embeddin<sub>g</sub> is intentionall<sub>y</sub> fixed across datasets to kee<sub>p</sub> the <sub>p</sub>roximit<sub>y</sub> la<sub>y</sub>er li<sub>g</sub>htwei<sub>g</sub>ht and com<sub>p</sub>arable across streams<sub>,</sub> while avoidin<sub>g</sub> unstable hi<sub>g</sub>h-dimensional densit<sub>y</sub> estimation.

To stabilize roximit under drift, we introduce a time-local scale usin a causal rollin median absolute deviation (MAD) com <sub>p</sub>uted on the first embeddin<sub>g</sub> coordinate $\phi _ { 1 }$ . For a window len<sub>g</sub>th $W _ { i }$ <sub>,</sub> define

$$
\operatorname{MAD} _ {W} (t) := \operatorname{median} \left(\left| \phi_ {1} (u) - \operatorname{median} \left(\phi_ {1} \left(u ^ {\prime}\right): u ^ {\prime} \in \mathcal {W} _ {t}\right) \right|: u \in \mathcal {W} _ {t}\right),\tag{2}
$$

where ${ \mathcal { W } } _ { t } \subseteq \{ 1 , \dots , t \}$ is the causal window (with the same minimum-period rule as in the released implementation). The adaptive scale is

$$
\varepsilon_ {t} := k _ {\mathrm{MAD}} \cdot \mathrm{MAD} _ {W} (t), \qquad \varepsilon_ {t} \geq \varepsilon_ {\min} > 0,\tag{3}
$$

where $k _ { \mathrm { M A D } } > 0$ controls the scale (default and tuned settin<sub>g</sub>s are reported in Section 4.3) and $\varepsilon _ { \mathrm { { m i n } } }$ is enforced numericall<sub>y</sub> for stabilit<sub>y</sub>. Missin<sub>g</sub> MAD values are filled b<sub>y</sub> a train-onl<sub>y</sub> fallback statistic to <sub>p</sub>reserve leak-freedom.

Al<sub>g</sub>orithm 2 <sub>p</sub>rovides the exact leak-free com<sub>p</sub>utation of the ada<sub>p</sub>tive causal scale $\varepsilon _ { t }$ (includin<sub>g</sub> train-onl<sub>y</sub> fallback handlin<sub>g</sub> for missin<sub>g</sub> MAD values).

## 2.3. Proximity evidence cues: Level, density cue, velocity, and prototype distance

The <sub>p</sub>roximit<sub>y</sub> com<sub>p</sub>onent reacts to local deviations<sub>,</sub> whereas the densit<sub>y</sub> com<sub>p</sub>onent <sub>p</sub>enalizes sustained de<sub>p</sub>artures from t<sub>yp</sub>ica nei<sub>g</sub>hborhoods<sub>,</sub> im<sub>p</sub>rovin<sub>g</sub> robustness under noise and <sub>g</sub>radual drift. The <sub>p</sub>roximit<sub>y</sub> la<sub>y</sub>er <sub>y</sub>ields four com<sub>p</sub>lementar<sub>y</sub> evidence ma<sub>p</sub>s in [0, 1] per time index �, each computed in a train-referenced manner. The end-to-end construction of the proximity evidence cues (includin train-referenced kNN distances, optional HDBSCAN with a leak-free fallback, and train-onl min–max normalization) is summarized in Al orithm 2.

Let � ∈ ℕ be the neighborhood size. For any $t \in X$ , define the mean �NN distance from $\mathbf { z } _ { t }$ to the training embeddin $\{ \mathbf { z } _ { s } : s \in X _ { \operatorname { t r } } \}$ by

$$
d _ {k} (t \mid X _ {\mathrm{tr}}) := \frac {1}{k} \sum_ {s \in \mathrm{kNN} (\mathbf {z} _ {t}; X _ {\mathrm{tr}})} \| \mathbf {z} _ {t} - \mathbf {z} _ {s} \| _ {2}.\tag{4}
$$

All subse<sub>q</sub>uent evidence cues are com<sub>p</sub>uted from train-referenced distances and normalized usin<sub>g</sub> train-onl<sub>y</sub> statistics<sub>,</sub> ensurin<sub>g</sub> leak freedom and makin<sub>g</sub> scores com<sub>p</sub>arable over time within each stream.

Level evidence cue prox\_level\_mu: We quantify level departure relative to the training reference set via an adaptively scaled distance transform. Usin<sub>g</sub> the rollin<sub>g</sub> scale $\varepsilon _ { t } ,$ we define the raw cue

$$
\widetilde {\mu} _ {\mathrm{level}} (t) := 1 - \exp \Bigl (- \frac {d _ {k} (t \mid X _ {\mathrm{tr}})}{\varepsilon_ {t} + \delta} \Bigr), \qquad \delta > 0,\tag{5}
$$

where $d _ { k } ( t \mid X _ { \mathrm { t r } } ) \geq 0$ <sup>i</sup>s a <sup>t</sup>ra<sup>i</sup>n-re<sup>f</sup>erence<sup>d di</sup>s<sup>t</sup>ance quan<sup>tit</sup>y an<sup>d</sup> � ensures numer<sup>i</sup>ca<sup>l</sup> s<sup>t</sup>a<sup>bilit</sup>y. <sup>Si</sup>nce <sup>th</sup>e mapp<sup>i</sup>ng $x \mapsto 1 - e ^ { - x }$ is bounded in [0, 1) for $x \geq 0 , \widetilde { \mu } _ { \mathrm { l e v e l } } ( t )$ is intrinsically bounded. We then apply train-only min–max normalization

$$
\mu_ {\text { level }} (t) := \operatorname{MinMax} _ {X _ {\mathrm{tr}}} \left(\widetilde {\mu} _ {\text { level }} (t)\right) \in [ 0, 1 ],\tag{6}
$$

which <sub>g</sub>uarantees leak-freedom and <sub>y</sub>ields a com<sub>p</sub>arable scale over time within a stream. Intuitivel<sub>y,</sub> $\mu _ { \mathrm { l e v e l } } ( t )$ increases as � becomes more at<sub>yp</sub>ical with res<sub>p</sub>ect to the trainin<sub>g</sub> reference set<sub>,</sub> while $\varepsilon _ { t }$ ada<sub>p</sub>ts the sensitivit<sub>y</sub> to re<sub>g</sub>ime-de<sub>p</sub>endent dis<sub>p</sub>ersion.

Density evidence cue prox\_level\_outlier: To complement distance-based departure with a density-oriented signal, we compute a train-fitted outlier cue on the embeddin . When feasible (suficient trainin len th and availabilit ) HDBSCAN is fitted on $\{ \mathbf { z } _ { s }$ ∶ $s \in X _ { \mathrm { t r } } \}$ and <sub>y</sub>ields outlier scores $o _ { \mathrm { H D B } } ( t )$ for $t \in X _ { \mathrm { t r } }$ . Im lementation details for the densit cue and the leak-free kNN fallback olic id d i Al i h 2 W d fi h li

$$
\widetilde {\mu} _ {\mathrm{out}} (t) := \left\{ \begin{array}{l l} o _ {\mathrm{dens}} (\mathbf {z} _ {t}), & \text { if   a   train - fitted   density   scorer   is   feasible }, \\ d _ {k} (t \mid X _ {\mathrm{tr}}), & \text { otherwise   (fallback) }, \end{array} \right.\tag{7}
$$

and a<sub>g</sub>ain a<sub>pp</sub>l<sub>y</sub> train-onl<sub>y</sub> min–max normalization

$$
\mu_ {\mathrm{out}} (t) := \mathrm{MinMax} _ {X _ {\mathrm{tr}}} \big (\widetilde {\mu} _ {\mathrm{out}} (t) \big) \in [ 0, 1 ].\tag{8}
$$

<sup>Thi</sup>s cons<sup>t</sup>ruc<sup>ti</sup>on rema<sup>i</sup>ns ro<sup>b</sup>us<sup>t</sup> un<sup>d</sup>er s<sup>h</sup>or<sup>t</sup> ser<sup>i</sup>es or cons<sup>t</sup>ra<sup>i</sup>ne<sup>d</sup> env<sup>i</sup>ronmen<sup>t</sup>s, s<sup>i</sup>nce <sup>it d</sup>egra<sup>d</sup>es grace<sup>f</sup>u<sup>ll</sup>y <sup>t</sup>o <sup>th</sup>e �<sup>NN di</sup>s<sup>t</sup>ance <sub>p</sub>rox<sub>y</sub> without afectin<sub>g</sub> leak-freedom.

Velocity evidence cue : Abru t chan es are often ca tured more reliabl in the derivative s ace. We define the embeddin increment $\Delta \mathbf { z } _ { t } : = \mathbf { z } _ { t } - \mathbf { z } _ { t - 1 }$ for $t \geq 2$ and $\Delta \mathbf { z } _ { 1 } : = \mathbf { 0 }$ . Usin the same train-referenced nei hborhood rinci le<sub>,</sub> we com ute

$$
d _ {k} ^ {\Delta} (t \mid X _ {\mathrm{tr}}) := \frac {1}{k} \sum_ {s \in \mathrm{kNN} (\Delta \mathbf {z} _ {t}; \Delta X _ {\mathrm{tr}})} \| \Delta \mathbf {z} _ {t} - \Delta \mathbf {z} _ {s} \| _ {2}, \quad \Delta X _ {\mathrm{tr}} := \{\Delta \mathbf {z} _ {s}: s \in X _ {\mathrm{tr}} \},\tag{9}
$$

and set

$$
\mu_ {\mathrm{vel}} (t) := \operatorname{MinMax} _ {X _ {\mathrm{tr}}} \bigl (d _ {k} ^ {\Delta} (t \mid X _ {\mathrm{tr}}) \bigr) \in [ 0, 1 ].\tag{10}
$$

Prototype-distance evidence cue proto\_dist\_1: Finally, we measure departure from a robust training prototype. Let

$$
\mathbf {p} := \text { median } \{\mathbf {z} _ {s}: s \in X _ {\mathrm{tr}} \} \in \mathbb {R} ^ {3}\tag{11}
$$

be the coordinate-wise median <sub>p</sub>rotot<sub>yp</sub>e in the embeddin<sub>g</sub>. Define

$$
d _ {\text { proto }} (t) := \| \mathbf {z} _ {t} - \mathbf {p} \| _ {2}, \quad \mu_ {\text { proto }} (t) := \operatorname{MinMax} _ {X _ {\mathrm{tr}}} \left(d _ {\text { proto }} (t)\right) \in [ 0, 1 ].\tag{12}
$$

The <sub>p</sub>rotot <sub>p</sub>e cue is <sub>p</sub>articularl stable under heav imbalance<sub>,</sub> since it relies on a robust summar of the trainin reference rather than on labels or event fre<sub>q</sub>uenc<sub>y</sub>.

## 2.4. Proximity fusion and score formation

The four evidence cues $\mu _ { \mathrm { l e v e l } } ( t ) , \ \mu _ { \mathrm { o u t } } ( t ) , \ \mu _ { \mathrm { v e l } } ( t ) ,$ , and $\mu _ { \mathrm { p r o t o } } ( t )$ characterize com<sub>p</sub>lementar<sub>y</sub> as<sub>p</sub>ects of deviation from the trainin<sub>g</sub> reference: <sub>g</sub>eometric level de<sub>p</sub>arture<sub>,</sub> densit<sub>y</sub> irre<sub>g</sub>ularit<sub>y,</sub> d<sub>y</sub>namical disru<sub>p</sub>tion<sub>,</sub> and <sub>p</sub>rotot<sub>yp</sub>e distance. For each series<sub>,</sub> we <sub>p</sub>roduce a ointwise anomal score $s ( t )$ usin onl information available u to time �, ieldin a stream-com atible detector. We combine them into a sin<sub>g</sub>le <sub>p</sub>roximit<sub>y</sub> score via a fusion o<sub>p</sub>erator

$$
s (t) := \mathrm{Fuse} \Big (\mu_ {\mathrm{level}} (t), \mu_ {\mathrm{out}} (t), \mu_ {\mathrm{vel}} (t), \mu_ {\mathrm{proto}} (t) \Big) \in [ 0, 1 ].\tag{13}
$$

In the released framework, Fuse(⋅) is implemented as a small family of monotone aggregators to support ablation and deployment constraints. Exam les include arithmetic mean to -2 mean max nois -or softmax oolin with tem erature arameter �-norm <sub>p</sub>oolin<sub>g,</sub> and an inverse-MAD wei<sub>g</sub>hted fusion that em<sub>p</sub>hasizes cues com<sub>p</sub>uted under locall<sub>y</sub> reliable scale. Since all in<sub>p</sub>uts are alread<sub>y</sub> train-normalized to [0, 1] fusion is numericall stable and com arable across time within a stream.

The output $s ( t )$ is an unsupervised anomaly score: it does not use labels and can be computed on fully unlabeled telemetry. In labeled settings, �(�) is subsequently calibrated and thresholded using leak-free splits (Section 2.5). In unlabeled deployment triage, �(�) can be used directl to roduce ranked event candidates and stream-level summaries (Section 2.7).

## 2.5. Leak-free calibration and threshold selection

To obtain well-behaved anomal robabilities suitable for o erational decision-makin we a l a strictl leak-free calibration and thresholdin<sub>g</sub> protocol. For each series, data are split into three chronolo<sub>g</sub>ical blocks: a trainin<sub>g</sub> block (used for feature fittin<sub>g</sub> and the proximit<sub>y</sub> la<sub>y</sub>er), a calibration-fit block, and a calibration-evaluation block. The proximit<sub>y</sub> la<sub>y</sub>er defined in Sections 2.2-2.3 is com uted usin train-fitted re rocessin onl <sub>;</sub> labels are not used in roximit construction. The leaka e-safe calibration and operating-point learning protocol (train-only / calib\_fit-only fitting, isotonic calibration, deterministic exact top-� budget selection, and strict transfer to calib eval) is detailed in Al orithm 3.

On labeled datasets<sub>,</sub> calibration is fitted usin<sub>g</sub> the calibration-fit block and evaluated on the held-out calibration-evaluation block. We em lo isotonic re ression as a non- arametric, monotone calibrator ma in raw scores �(�) to calibrated robabilities $\widehat { p } ( t ) \in$ [0, 1]. All calibration fittin is erformed only on calibration-fit data, and erformance metrics are re orted only on calibration evaluation data to avoid o<sub>p</sub>timistic bias

Thresholds are learned on calibration-fit under a fixed bud<sub>g</sub>et <sub>p</sub>olic<sub>y</sub>. Concretel<sub>y,</sub> for a tar<sub>g</sub>et rate $q ~ ( { \bf e . g . } , ~ q = 1 \% )$ , we se<sup>t</sup> $k _ { \mathrm { f i t } } = \lceil q \rceil \mathsf { c a l i b \_ f i t } | \rceil$ and select the exact to<sub>p</sub>- $\cdot k _ { \mathrm { f i t } }$ scores on calib\_fit us<sup>i</sup>ng <sup>d</sup>eterm<sup>i</sup>n<sup>i</sup>st<sup>i</sup>c t<sup>i</sup>e-sa<sup>f</sup>e se<sup>l</sup>ect<sup>i</sup>on. <sup>W</sup>e recor<sup>d</sup> t<sup>h</sup>e <sup>i</sup>m-<sub>p</sub>lied threshold $\tau _ { \mathrm { f i t } } ( q )$ (t<sup>h</sup>e m<sup>i</sup>n<sup>i</sup>mum score w<sup>i</sup>t<sup>hi</sup>n t<sup>h</sup>e se<sup>l</sup>ecte<sup>d</sup> set) <sup>f</sup>or report<sup>i</sup>ng (<sup>Th</sup>r@<sup>fi</sup>t). <sup>F</sup>or <sup>fi</sup>na<sup>l</sup> report<sup>i</sup>ng on calib\_eval, we do not re-estimate an threshold instead we transfer the bud et $k _ { \mathrm { f i t } }$ and select exactl $k _ { \mathrm { f i t } }$ alarms on usin the same tie-safe rule. This ields directl actionable fixed-bud et o eratin metrics (PR@1% and R@1%) without usin an information from to set the bud et.

## 2.6. Computational profile, scalability, and practical baselines

A central desi<sub>g</sub>n <sub>g</sub>oal is de<sub>p</sub>lo<sub>y</sub>ment feasibilit<sub>y</sub> under resource constraints and lon<sub>g</sub>-runnin<sub>g</sub> streams. The <sub>p</sub>roximit<sub>y</sub> la<sub>y</sub>er o<sub>p</sub>erates er series with train-onl fitted re rocessin and its dominant costs are: (i) PCA transform in $\mathbb { R } ^ { p } \to \mathbb { R } ^ { 3 }$ (ii) re eated NN ueries a<sub>g</sub>ainst the trainin<sub>g</sub> embeddin<sub>g</sub>, and (iii) optional HDBSCAN fittin<sub>g</sub> on the trainin<sub>g</sub> embeddin<sub>g</sub>. All components are li<sub>g</sub>htwei<sub>g</sub>ht relative to dee<sub>p</sub> se<sub>q</sub>uence models and can be executed with bounded memor via <sub>p</sub>er-series <sub>p</sub>rocessin and manifest-based streamin .

Transformer-based forecastin residual baselines $( \boldsymbol { \mathrm { e . g . } }$ Informer PatchTST iTransformer) can be com etitive in settin s where substantial com<sub>p</sub>ute bud<sub>g</sub>ets and stable execution environments are available. However<sub>,</sub> under strict runtime and connectivit<sub>y</sub> con straints the ma become im ractical: trainin and inference times can exceed interactive execution bud ets and lon jobs are vulnerable to session interru tion. For this reason we include transformer baselines in a budgeted confi uration (bounded ste s / earl sto in ), and we inter ret their results jointl with their runtime. This re ortin ali ns with de lo ment riorities: methods that do not reliabl finish within the o erational bud et cannot be assumed available in real-time monitorin

To ensure fair com arison all baselines are evaluated under the same leak-free s littin and threshold-learnin rotocol as the ro osed method. In addition to classical unsu ervised detectors (e. . Isolation Forest LOF COPOD) and time-series residual base lines (e. ., ETS residuals, Matrix Profile), we report ablations that isolate the contribution of the proximit la er (e. ., base statistical features onl<sub>y</sub>) and anal<sub>y</sub>ze sensitivit<sub>y</sub> to the proximit<sub>y</sub> h<sub>y</sub>perparameters $( W , k _ { \mathrm { M A D } } ,$ , min\_cluster\_size) and fusion choice. This combination of accurac <sub>,</sub> calibration<sub>,</sub> and runtime evidence su orts a de lo ment-oriented conclusion: the ro osed roximit framework ofers a stron accurac –eficienc trade-of across labeled benchmarks and remains usable on unlabeled telemetr streams.

## 2.7. Unlabeled deployment triage (Intel)

The Intel Berkele telemetr is lar el unlabeled therefore we do not claim detection accurac on Intel. Instead we osition Intel as an unlabeled deployment triage setting: under a fixed alert budget, the goal is to prioritize nodes and time periods for inspection usin risk scores that are o erationall useful—broadl coverin the fleet<sub>,</sub> suficientl stable under calibration transfer<sub>,</sub> not overl concentrated on a few nodes, producin<sub>g</sub> actionable (non-de<sub>g</sub>enerate) alert durations, and remainin<sub>g</sub> computationall<sub>y</sub> feasible.

<sup>W</sup>e app<sup>l</sup>y a t<sup>i</sup>me-or<sup>d</sup>ere<sup>d 3</sup>-way sp<sup>li</sup>t train / calib\_fit / calib\_eval per no<sup>d</sup>e. <sup>All</sup> ca<sup>lib</sup>rat<sup>i</sup>on mapp<sup>i</sup>ngs (<sup>ECDF</sup>/<sup>ChECDF</sup>) are fitted only on calib\_fit and then applied unchanged to calib\_eval. To reflect alert-rate constraints, we learn a budgeted threshold on calib\_fit us<sup>i</sup>ng a <sup>d</sup>eterm<sup>i</sup>n<sup>i</sup>st<sup>i</sup>c, t<sup>i</sup>e-sa<sup>f</sup>e top-� ru<sup>l</sup>e at $q = 1 \% :$

$$
k _ {\text { fit }} = \lceil q   N _ {\text { fit }} \rceil , \qquad \tau (q) = \text { the   score   at   rank } k _ {\text { fit }} \text { on   calib\_fit. }
$$

The learned $\tau ( q )$ is then applied unchanged to calib\_eval, ensuring that no information from calib\_eval influences threshold selection. For the ro osed famil , roximit channels are not recom uted on Intel in this tria e block; we onl fuse the recom uted prox<sup>i</sup>m<sup>i</sup>ty scores an<sup>d</sup> ca<sup>lib</sup>rate t<sup>h</sup>em us<sup>i</sup>ng calib\_fit. <sup>Th</sup>e un<sup>l</sup>a<sup>b</sup>e<sup>l</sup>e<sup>d</sup> tr<sup>i</sup>age trans<sup>f</sup>er protoco<sup>l</sup> (<sup>l</sup>a<sup>b</sup>e<sup>l</sup>-<sup>f</sup>ree norma<sup>li</sup>zat<sup>i</sup>on <sup>fi</sup>t on ca<sup>lib</sup>\_<sup>fi</sup>t, unchan ed a lication to calib\_eval, and fixed-bud et to -� alertin ) follows Al orithm 3.

We summarize each method b<sub>y</sub> a Composite Tria<sub>g</sub>e Score (CTS) constructed from five deplo<sub>y</sub>ment-oriented criteria. Let $\mathcal { N }$ be the set of nodes and let $A _ { i }$ <sup>b</sup>e t<sup>h</sup>e a<sup>l</sup>erte<sup>d</sup> po<sup>i</sup>nts on no<sup>d</sup>e � <sup>i</sup>n calib\_eval (po<sup>i</sup>nts w<sup>i</sup>t<sup>h</sup> score $\geq \tau ( q ) )$ .

1. Coverage (C): fraction of nodes exhibiting at least one alert,

$$
C = \frac {1}{| \mathcal {N} |} \sum_ {i \in \mathcal {N}} \mathbf {1} \{| A _ {i} | > 0 \}.
$$

2. Stability (S): rank-consistency of node-level risk between calib\_fit and calib\_eval. Let $\bar { s } _ { i } ^ { \mathrm { c f } }$ and $\bar { s } _ { i } ^ { \mathrm { c e } }$ be the mean calibrated score on node � in and res ectivel . We com ute S earman correlation across nodes:

$$
S = \rho_ {\mathrm{Spearman}} \Big (\{\bar {s} _ {i} ^ {\mathrm{cf}} \} _ {i \in \mathcal {N}}, \{\bar {s} _ {i} ^ {\mathrm{ce}} \} _ {i \in \mathcal {N}} \Big).
$$

3. Concentration (H): Herfindahl–Hirschman Index (HHI) of alert mass across nodes. Let $\begin{array} { r } { p _ { i } = \frac { | A _ { i } | } { \sum _ { j \in \mathcal { N } } | A _ { j } | + \varepsilon } . } \end{array}$ , then

$$
H H I = \sum_ {i \in \mathcal {N}} p _ {i} ^ {2},
$$

where lower values indicate a more evenl<sub>y</sub> distributed alert allocation.

4. Duration (D): mean alert-event duration on calib\_eval. An event is a maximal contiguous segment of points with score $\geq \tau ( q )$ We re ort the mean event duration in minutes usin dataset timestam s (or the known sam lin interval when timestam s are re ular).

5. Runtime (R): wall-clock inference time for producing calibrated risk scores on calib\_eval (seconds).

To combine hetero<sub>g</sub>eneous units<sub>,</sub> each com<sub>p</sub>onent is min–max normalized across the com<sub>p</sub>ared methods. For criteria to be maxi mized (Covera e Stabilit ) we use

$$
\mathrm{mm} (x) = \frac {x - \min (x)}{\max (x) - \min (x) + \epsilon}.
$$

For criteria to be minimized (HHI, Duration, Runtime), we use the inverted min–max transform

$$
\mathrm{mm} ^ {\downarrow} (x) = \frac {\max (x) - x}{\max (x) - \min (x) + \epsilon}.
$$

We then define

$$
C T S = \frac {1}{5} \left(\operatorname{mm} (C) + \operatorname{mm} (S) + \operatorname{mm} ^ {\downarrow} (H H I) + \operatorname{mm} ^ {\downarrow} (D) + \operatorname{mm} ^ {\downarrow} (R)\right).
$$

CTS is a triage score: it ranks methods b o erational screenin utilit under an alert bud et it is not a substitute for accurac on labeled benchmarks.

Results and o<sub>p</sub>erational im<sub>p</sub>lications are re<sub>p</sub>orted in Section 4.4.

## 2.8. Complexity and practical deployment notes

This section characterizes the com<sub>p</sub>utational and memor<sub>y</sub> foot<sub>p</sub>rint of the <sub>p</sub>ro<sub>p</sub>osed <sub>p</sub>i<sub>p</sub>eline and summarizes im<sub>p</sub>lementation choices that matter for deplo<sub>y</sub>ment. We report as<sub>y</sub>mptotic costs in terms of <sub>g</sub>eneric problem sizes (no dataset-specific timin<sub>g</sub>s).

<sup>C</sup>ons<sup>id</sup>er one s<sup>t</sup>ream o<sup>f l</sup>eng<sup>th</sup> � w<sup>ith</sup> a <sup>t</sup>ra<sup>i</sup>n<sup>i</sup>ng pre<sup>fi</sup>x $X _ { \mathrm { t r } }$ of size $n _ { \mathrm { t r } } = | X _ { \mathrm { t r } } |$ . Let $\Phi ( t ) \in \mathbb { R } ^ { p }$ denote the <sub>p</sub>er-time feature ma<sub>p</sub> after causa<sup>l</sup> preprocess<sup>i</sup>n , $d = 3$ d = 3 th fi d b ddi di i th i hb h d i f NN i d $W$ th l i d i used for rollin -MAD stabilization (and where a licable rollin feature com utations).

Feature computation and causal preprocessing: Most base features used in Φ(⋅) are rollin statistics and robust transforms com uted causall . With standard streamin im lementations rollin means/medians/variances and robust �-st le transforms are �(� �) time overall, with $O ( W _ { P } )$ workin<sub>g</sub> memor<sub>y</sub> for window bufers (or equivalent summaries). Forward-fill with a bounded limit is linear in $n ,$ and train-median im<sub>p</sub>utation and standardization re<sub>q</sub>uire one <sub>p</sub>ass over $X _ { \mathrm { t r } } , \mathrm { i . e . , } O ( n _ { \mathrm { t r } } p )$ time and $O ( p )$ state. The causa rollin -feature and robust-transform construction referenced here is s ecified in Al orithm 1

Train-only embedding (standardization and PCA): All re resentation learnin is fitted on $X _ { \mathrm { t r } }$ onl . Standardization i $O ( n _ { \mathrm { t r } } p ) .$ For PCA with fixed $d { = } 3 ,$ <sub>,</sub> a truncated/SVD-st le fit scales as $O ( n _ { \mathrm { t r } } p d )$ in t ical im lementations and stores $O ( p d )$ arameters for the projection. Applying the learned projection to the full stream is linear, $O ( n p d )$ .

Rolling-MAD stabilization (causal scale): The adaptive scale $\varepsilon _ { t }$ uses a causal window ${ \mathcal { W } } _ { t } \subseteq \{ 1 , \dots , t \}$ o<sup>f</sup> s<sup>i</sup>ze at most �. <sup>R</sup>egar<sup>dl</sup>ess of the s<sub>p</sub>ecific rollin<sub>g</sub>-MAD im<sub>p</sub>lementation<sub>,</sub> the u<sub>p</sub>date de<sub>p</sub>ends onl<sub>y</sub> on <sub>p</sub>ast values and therefore <sub>p</sub>reserves causalit<sub>y</sub>. The online state is �(�) (or an equivalent compact summary) for the selected embedding coordinate(s).

Train-referenced neighborhood queries (dominant term): The proximity evidence cues in Sections 2.3-2.4 rely on �NN dis tances from (i) $\mathbf { z } _ { t }$ to the training embedding $\{ \mathbf { z } _ { s } : s \in X _ { \operatorname { t r } } \}$ and (ii) $\Delta \mathbf { z } _ { t }$ to the training increment set $\Delta X _ { \mathrm { t r } }$ . With naive exact search<sub>,</sub> eac<sup>h</sup> query compares aga<sup>i</sup>ns<sup>t</sup> $n _ { \mathrm { t r } }$ reference points, <sub>g</sub>ivin<sub>g</sub> per-stream time

$$
O (n n _ {\mathrm{tr}} d)
$$

for each �NN-based evidence cue, plus $O ( n _ { \mathrm { t r } }$ �) memory to store the reference set (and similarly for increments). In practice, exact or a<sub>pp</sub>roximate nearest-nei<sub>g</sub>hbor indexin<sub>g</sub> can reduce avera<sub>g</sub>e <sub>q</sub>uer<sub>y</sub> time<sub>;</sub> the framework is a<sub>g</sub>nostic to the index choice and remains leak-free as lon<sub>g</sub> as the index is built on $X _ { \mathrm { t r } }$ only.

Optional density cue and safe fallback: The density/outlier cue is trained on the training embedding only (Section 2.3). Its cost is incurred once per stream (train-onl<sub>y</sub>) and is therefore amortized over � timestamps. When the densit<sub>y</sub> model is infeasible (e.<sub>g</sub>., insuficient $n _ { \mathrm { t r } }$ or constrained environments), the method falls back to a train-referenced �NN-distance proxy. This guarantees that the <sub>p</sub>i<sub>p</sub>eline remains executable without chan<sub>g</sub>in<sub>g</sub> the leak-free <sub>p</sub>rotocol.

Normalization, fusion, and score formation: Train-only min–max normalization of evidence-cue maps requires computing train statistics and is linear in $n _ { \mathrm { t r } }$ <sub>p</sub>er ma<sub>p</sub>. Fusion into the final score $s ( t ) \in [ 0 ,$ 1] is pointwise and constant time, �(1) per timestamp (hence �(�) per stream), and does not introduce additional fitting.

Calibration and budgeted operating point: On labeled benchmarks isotonic calibration is fitted on onl . If $n _ { \mathrm { c f } } =$ |calib\_fit|, isotonic fitting is dominated by sorting and costs $O ( n _ { \mathrm { c f } } \log n _ { \mathrm { c f } } )$ time with ${ \cal O } ( n _ { \mathrm { c f } } )$ memor<sub>y</sub>. Learnin<sub>g</sub> the bud<sub>g</sub>eted threshold at rate � via deterministic tie-safe top-� selection can be implemented in ${ \cal O } ( n _ { \mathrm { c f } } )$ expected time (selection) or $O ( n _ { \mathrm { c f } } \log n _ { \mathrm { c f } } )$ (sortin<sub>g</sub>), and is a lied unchan ed to . On unlabeled Intel tria e the same threshold-transfer mechanism is used and CTS com onents are com<sub>p</sub>uted b<sub>y</sub> linear-time a<sub>gg</sub>re<sub>g</sub>ates over alerted <sub>p</sub>oints and conti<sub>g</sub>uous events. These calibration and bud<sub>g</sub>eted o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oin ste s corres ond to Al orithm 3.

Memory profile and streaming alignment: The pipeline is series-local and can be executed independently per stream. The dominant persistent state per stream consists of: (i) preprocessin<sub>g</sub> statistics $O ( p ) _ { \it \bot }$ , (ii) PCA parameters $O ( p d )$ , (iii) trainin<sub>g</sub> reference sets in embeddin<sub>g</sub> and increment s<sub>p</sub>aces $O ( n _ { \mathrm { t r } } d )$ , and (iv) rolling bufers �(� �) (feature windows) and �(�) (MAD scale). This structure supports a manifest/parts workflow that processes one stream (or a small batch) at a time, boundin<sub>g</sub> peak memor<sub>y</sub> and allowin<sub>g</sub> strai<sub>g</sub>htforward <sub>p</sub>arallelization across streams.

Deployment options (fixed reference vs. controlled refresh): The experiments in this paper use a fixed training reference per stream to ensure strict com<sub>p</sub>arabilit<sub>y</sub> under a leak-free <sub>p</sub>rotocol. In o<sub>p</sub>erational settin<sub>g</sub>s<sub>,</sub> one ma<sub>y</sub> o<sub>p</sub>tionall<sub>y</sub> refresh the reference set (and re-fit the embeddin ) on a controlled schedule, provided that updates are restricted to past data and are not influenced b<sub>y</sub> the evaluation horizon. Similarl<sub>y,</sub> calibration can be u<sub>p</sub>dated when labels become available<sub>,</sub> without chan<sub>g</sub>in<sub>g</sub> the underl<sub>y</sub>in<sub>g</sub> unsu ervised scorin mechanism.

The com utational cost is dominated b train-referenced nei hborhood ueries the remainin com onents (rollin features PCA transform, normalization, fusion, calibration, and bud eted thresholdin ) are li htwei ht and naturall streamin -com atible. This desi<sub>g</sub>n matches the de<sub>p</sub>lo<sub>y</sub>ment <sub>g</sub>oal of <sub>p</sub>roducin<sub>g</sub> actionable<sub>,</sub> trans<sub>p</sub>arent scores under constrained com<sub>p</sub>ute<sub>,</sub> while maintainin<sub>g</sub> a strictl<sub>y</sub> leak-free train/calibration/evaluation se<sub>p</sub>aration.

## 3. Experimental protocol

## 3.1. Datasets

To stress-test de lo ment-oriented anomal detection under non-stationarit and extreme class imbalance we select four datasets that are deliberatel hetero eneous in (i) labelin availabilit (full labeled vs. unlabeled) (ii) dimensionalit (univariate vs. multi variate telemetr ) (iii) annotation semantics ( ointwise vs. interval/event conventions) (iv) scale (from ∼ $1 0 ^ { 5 } ~ \mathrm { t o } > 1 0 ^ { 7 }$ oints) and (v) m lin irr l riti nd mi in n Thi d i n r v nt v r-fittin th n rr tiv t in l b n hm rk nd n bl ni fied evaluation of (a) rankin<sub>g</sub> qualit<sub>y</sub> under imbalance (PR–AUC), (b) bud<sub>g</sub>eted alertin<sub>g</sub> re<sub>g</sub>imes (PR@1%, R@1%), (c) leaka<sub>g</sub>e-safe calibration, and (d) com ute sustainabilit under realistic runtime constraints, as summarized in Table 1.

## 3.1.1. NAB (Labeled, univariate; pointwise vs. event semantics)

<sup>NAB i</sup>s a s<sup>t</sup>ream<sup>i</sup>ng <sup>b</sup>enc<sup>h</sup>mar<sup>k d</sup>es<sup>i</sup>gne<sup>d f</sup>or rea<sup>l</sup>-<sup>ti</sup>me anoma<sup>l</sup>y <sup>d</sup>e<sup>t</sup>ec<sup>ti</sup>on w<sup>h</sup>ere concep<sup>t d</sup>r<sup>ift</sup> an<sup>d i</sup>m<sup>b</sup>a<sup>l</sup>ance are prom<sup>i</sup>nen<sup>t [5]</sup>. <sup>W</sup>e use 13 canonical NAB streams s annin artificial and real sources (e. ., ambient tem erature, re uest latenc , taxi demand, trafic, an<sup>d</sup> soc<sup>i</sup>a<sup>l</sup> vo<sup>l</sup>ume). <sup>I</sup>n our processe<sup>d</sup> su<sup>b</sup>set, t<sup>h</sup>e poo<sup>l</sup>e<sup>d</sup> ta<sup>bl</sup>e eva<sup>l</sup>uates po<sup>i</sup>ntw<sup>i</sup>se <sup>l</sup>a<sup>b</sup>e<sup>l</sup>s on t<sup>h</sup>e <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree calib\_eval segment; we ex<sub>p</sub>licitl<sub>y</sub> note that NAB also su<sub>pp</sub>orts event/window-based scorin<sub>g</sub> and treat it as a com<sub>p</sub>lementar<sub>y</sub> view rather than a re<sub>p</sub>lacement for <sub>p</sub>ointwise<sub>,</sub> bud<sub>g</sub>eted alertin<sub>g</sub>.

Table 1  
Datasets used in this stud<sub>y</sub> (Dataset-level statistics from our processed splits).

<table><tr><td>Dataset</td><td>Streams/Nodes</td><td>Dim.</td><td>Labeled?</td><td>Scale (rows)</td></tr><tr><td>NAB (subset)</td><td>13</td><td>1</td><td>Yes</td><td>98,288</td></tr><tr><td>SMD</td><td>28</td><td>38</td><td>Yes</td><td>1,416,825 (train + test)</td></tr><tr><td>UCR (full)</td><td>250</td><td>1</td><td>Yes</td><td>≈15,911,730</td></tr><tr><td>Intel Lab</td><td>54</td><td>4</td><td>No</td><td>2,303,286</td></tr></table>

## 3.1.2. SMD (Labeled, multivariate server telemetry)

<sup>SMD</sup> prov<sup>id</sup>es mu<sup>lti</sup>var<sup>i</sup>a<sup>t</sup>e server-mac<sup>hi</sup>ne <sup>t</sup>e<sup>l</sup>eme<sup>t</sup>ry w<sup>ith</sup> a <sup>fi</sup>xe<sup>d t</sup>ra<sup>i</sup>n<sup>/t</sup>es<sup>t</sup> sp<sup>lit</sup> an<sup>d d</sup>ense <sup>l</sup>a<sup>b</sup>e<sup>l</sup>s on <sup>th</sup>e <sup>t</sup>es<sup>t</sup> par<sup>titi</sup>on <sup>[40]</sup>. <sup>Thi</sup>s dataset is a primary “multivariate deployment” vignette: it couples correlated metrics (� = 38) with non-trivial anomaly structure, bli l ti f i it b d f i d i t ti I l d 28 hi t il bl ith 708<sub>,</sub>405 train rows<sub>,</sub> 708<sub>,</sub>420 test rows<sub>,</sub> and 29<sub>,</sub>444 anomalous test <sub>p</sub>oints.

SMD rovi<sup>d</sup>es an o<sup>fi</sup>cia<sup>l</sup> i / s <sup>l</sup>it w<sup>h</sup>ere <sup>l</sup>a<sup>b</sup>e<sup>l</sup>s are avai<sup>l</sup>a<sup>bl</sup>e <sup>f</sup>or t<sup>h</sup>e artition on<sup>l</sup> . To <sup>k</sup>ee ca<sup>l</sup>i<sup>b</sup>ration an<sup>d</sup> o eratin <sub>p</sub>oint selection strictl<sub>y</sub> out-of-sam<sub>p</sub>le while usin<sub>g</sub> labels in a de<sub>p</sub>lo<sub>y</sub>ment-ali<sub>g</sub>ned wa<sub>y,</sub> we instantiate our leak-free three-wa<sub>y</sub> re<sub>g</sub>ime within the oficial test stream in chronological order: an initialization prefix (test\_train\_prefix, 70%) for fitting the score-related components t<sup>h</sup>at requ<sup>i</sup>re a re<sup>f</sup>erence, a ca<sup>lib</sup>rat<sup>i</sup>on-<sup>fi</sup>t <sup>bl</sup>oc<sup>k</sup> (calib\_fit, <sup>15%</sup>) <sup>f</sup>or <sup>i</sup>soton<sup>i</sup>c ca<sup>lib</sup>rat<sup>i</sup>on an<sup>d b</sup>u<sup>d</sup>gete<sup>d</sup> t<sup>h</sup>res<sup>h</sup>o<sup>ld l</sup>earn<sup>i</sup>ng, and a held-out calibration-evaluation block (calib\_eval, 15%) used only for final reporting. Crucially, we do not assume that the initialization refix is erfectl anomal -free this mirrors real de lo ments where earl telemetr ma alread contain incidents. <sup>L</sup>ea<sup>k</sup>-<sup>f</sup>ree<sup>d</sup>om <sup>i</sup>s ensure<sup>d b d</sup>es<sup>i</sup> n <sup>b</sup>ecause no <sup>i</sup>n<sup>f</sup>ormat<sup>i</sup>on <sup>f</sup>rom calib\_eval <sup>i</sup>s use<sup>d i</sup>n <sup>fi</sup>tt<sup>i</sup>n , ca<sup>lib</sup>rat<sup>i</sup>on, or t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup> se<sup>l</sup>ect<sup>i</sup>on.

## 3.1.3. UCR time series anomaly archive (Labeled; scale and heterogeneity stress test)

The UCR anomal<sub>y</sub> archive a<sub>gg</sub>re<sub>g</sub>ates hetero<sub>g</sub>eneous univariate series with interval-st<sub>y</sub>le anomal<sub>y</sub> annotations<sub>,</sub> s<sub>p</sub>annin<sub>g</sub> multi<sub>p</sub>le domains and len ths [41,42]. It functions as a scale and eneralization stress test: in our full run, the rocessed archive contains 250 series and ≈15.9M points with severe imbalance (total positives ≈45,614). This setting is intentionally hostile to compute-heavy baselines<sub>,</sub> therefore hi hli htin Pareto trade-ofs amon rankin ualit <sub>,</sub> bud et metrics<sub>,</sub> and runtime.

## 3.1.4. Intel berkeley research lab (Unlabeled; deployment triage)

Intel Lab sensor telemetr<sub>y</sub> provides lon<sub>g</sub>-duration, real-world multivariate measurements collected from a sensor network (tem erature humidit li ht volta e) with irre ular sam lin and non-ne li ible missin ness [7]. As the cor us is unlabeled we do not claim su<sub>p</sub>ervised accurac<sub>y;</sub> instead<sub>,</sub> we use it to validate whether calibrated<sub>,</sub> bud<sub>g</sub>eted scorin<sub>g p</sub>roduces o<sub>p</sub>erationall<sub>y p</sub>lausible alert atterns (covera e stabilit concentration event statistics) under realistic de lo ment artifacts. Our rocessed version contains 54 no<sup>d</sup>es, <sup>2</sup>.<sup>30M</sup> rows, an<sup>d</sup> m<sup>i</sup>ss<sup>i</sup>ngness t<sup>h</sup>at <sup>i</sup>s concentrate<sup>d i</sup>n t<sup>h</sup>e value/voltage c<sup>h</sup>anne<sup>l</sup>.

On the Intel Berkele Lab cor<sub>p</sub>us<sub>,</sub> round-truth anomal labels are not available<sub>;</sub> therefore<sub>,</sub> we do not <sub>p</sub>erform <sub>p</sub>robabilit cal ibration in the su ervised sense (i.e. ma in scores to calibrated class robabilities a ainst labels). Instead we a l label-free distributional normalization learned on calib\_fit and transferred to calib\_eval to obtain a normalized risk score that is com arable across sensors and time. Concretel we fit an em irical CDF (ECDF) or its chunked variant (ChECDF) on and transform raw anomal scores into quantile-scale values in [0, 1]. This transformation preserves the within-stream rankin while stabilizin thresholds under drift and sensor-s<sub>p</sub>ecific score distributions<sub>,</sub> enablin<sub>g</sub> de<sub>p</sub>lo<sub>y</sub>ment-st<sub>y</sub>le tria<sub>g</sub>e without claimin<sub>g</sub> calibrated <sub>p</sub>robabil ities.

## 3.2. Experimental coverage

We evaluate a de lo ment-oriented anomal detection framework across three labeled benchmarks and one unlabeled de lo - ment tria e cor us with method families selected to reflect ractical o eratin constraints (drift severe class imbalance and com ute limits). On the labeled benchmarks (NAB SMD and UCR) we re ort results for:

(i) the proposed adaptive proximit<sub>y</sub> scorin<sub>g</sub> pipeline (adaptive proximit<sub>y</sub> score with rollin<sub>g</sub>-MAD stabilization and train-onl<sub>y</sub> calibration),

(ii) re resentative classical outlier detectors (Isolation Forest LOF COPOD) (iii) residual-based forecastin baselines (ETS residual) and

(iv) a subsequence/shape-based baseline (Matrix Profile).

Transformer forecaster residual baselines (Informer iTransformer and PatchTST) are included where com utationall feasible (NAB and SMD) reflectin realistic de lo ment bud ets for the lar e-scale UCR benchmark we restrict the com arison set to methods that remain tractable under the same evaluation re ime and we additionall include a statistical-onl ablation to isolate the contribution of the <sub>p</sub>roximit com<sub>p</sub>onents. For the unlabeled Intel Berkele Lab sensor cor<sub>p</sub>us<sub>,</sub> we do not claim su<sub>p</sub>ervised detection <sub>p</sub>erformance<sub>;</sub> instead, we perform deplo<sub>y</sub>ment tria<sub>g</sub>e under a fixed alert bud<sub>g</sub>et usin<sub>g</sub> label-free distributional normalization (ECDF/ChECDF) fitted on calib\_fit an<sup>d</sup> trans<sup>f</sup>erre<sup>d</sup> unc<sup>h</sup>an e<sup>d</sup> to calib\_eval, an<sup>d</sup> we re ort o erat<sup>i</sup>ona<sup>l</sup> stat<sup>i</sup>st<sup>i</sup>cs (covera e, sta<sup>bili</sup>t , concentrat<sup>i</sup>on, an<sup>d</sup> event characteristics) for multi le ProxFuse variants alon side re resentative classical scorers.

## 3.3. Leakage-safe splitting and evaluation regime

Reliable anomal<sub>y</sub> detection under drift and extreme class imbalance is hi<sub>g</sub>hl<sub>y</sub> sensitive to evaluation leaka<sub>g</sub>e<sub>, p</sub>articularl<sub>y</sub> when thresholds and calibrators are tuned on information that overla<sub>p</sub>s with the re<sub>p</sub>orted test se<sub>g</sub>ment. To ensure a strictl<sub>y</sub> out-of-sam<sub>p</sub>le assessment, we ado t a leakage-safe, temporally ordered, per-series evaluation re ime that ex licitl se arates (i) re resentation/score learnin<sub>g</sub>, (ii) calibration and operatin<sub>g</sub>-point selection, and (iii) final reportin<sub>g</sub>.

Temporal splitting (per series): For each time series, samples are ordered chronologically (timestamp for NAB/Intel; integer index � for UCR; test-time index � for SMD). We then construct a three-way split that respects time:

Train ∶ 70% Calib ∶ 15% Eval ∶ 15%,

im<sub>p</sub>lemented as conti<sub>g</sub>uous blocks to <sub>p</sub>revent an<sub>y</sub> look-ahead. This <sub>p</sub>er-series s<sub>p</sub>littin<sub>g</sub> avoids cross-series leaka<sub>g</sub>e and <sub>p</sub>reserves realistic de<sub>p</sub>lo<sub>y</sub>ment conditions where decisions are made forward in time.

Calibration block: vs. : The 15% calibration se ment is further treated as an ex licit decision la er. In our main Table 5 <sub>p</sub>rotocol<sub>,</sub> we distin<sub>g</sub>uish:

• calib\_fit: used only to (a) fit the probability calibrator and (b) learn the operating policy under a fixed alert budget (e.g., top-1%).

• calib\_eval: used only for final metric reporting.

This se<sub>p</sub>aration <sub>p</sub>revents o<sub>p</sub>timistic bias that would arise if the same calibration data were used both to choose the o<sub>p</sub>eratin<sub>g p</sub>oint and to report performance.

Train-only calibration (leak-free):

Our core detector produces a label-agnostic anomaly score �(�) by fusing train-referenced proximity evidence cues with robust, train-onl tem oral normalization. On labeled benchmarks (e. ., NAB, SMD), we o tionall train a li htwei ht su ervised ma in on (Li htGBM) to combine the feature set—includin the roximit -derived com onents and �(�)—into a sin le decision score. This supervised head is used only when labels are available and is trained strictly within the leak-free split; it is then calibrated $( \boldsymbol { \mathrm { e . g . } }$ <sup>i</sup>soton<sup>i</sup>c) on calib\_fit an<sup>d</sup> eva<sup>l</sup>uate<sup>d</sup> on t<sup>h</sup>e <sup>h</sup>e<sup>ld</sup>-out calib\_eval. <sup>F</sup>or un<sup>l</sup>a<sup>b</sup>e<sup>l</sup>e<sup>d I</sup>nte<sup>l</sup> streams, t<sup>h</sup>e superv<sup>i</sup>se<sup>d h</sup>ea<sup>d i</sup>s <sup>di</sup>sa<sup>bl</sup>e<sup>d</sup> an<sup>d</sup> the i eline o erates urel on followed b label-free normalization (ECDF/ChECDF) for de lo ment-st le tria e. Accordin l SHAP ex<sub>p</sub>lanations are re<sub>p</sub>orted for the calibrated out<sub>p</sub>ut of the su<sub>p</sub>ervised head on labeled datasets<sub>,</sub> ensurin<sub>g</sub> that inter<sub>p</sub>retabilit<sub>y</sub> is com<sub>p</sub>uted on the same score used for decisions.

When a method <sub>y</sub>ields real-valued anomal<sub>y</sub> scores or raw <sub>p</sub>robabilities<sub>,</sub> we ma<sub>p</sub> them to calibrated anomal<sub>y p</sub>robabilities via <sup>i</sup>soton<sup>i</sup>c regress<sup>i</sup>on <sup>fi</sup>t on calib\_fit on<sup>l</sup>y. <sup>C</sup>oncrete<sup>l</sup>y, <sup>l</sup>et �(⋅) <sup>d</sup>enote t<sup>h</sup>e met<sup>h</sup>o<sup>d</sup> score on calib\_fit an<sup>d</sup> $y \in \{ 0 , 1 \}$ the corres<sub>p</sub>ondin<sub>g</sub> labels (available for labeled benchmarks). We fit an isotonic map � on (�, �) and apply $g$ to calib\_eval w<sup>i</sup>t<sup>h</sup>out re<sup>fi</sup>tt<sup>i</sup>ng. <sup>If</sup> calib\_fit contains a sin le class (ill- osed calibration) we fall back to the identit ma in reservin strict leak-freeness and avoidin de<sub>g</sub>enerate fits.

All detection metrics are com uted on the de lo ed decision score: (i) on labeled datasets ROC/PR and fixed-bud et selection are evaluated on the calibrated core decision score $p _ { b } ( t ) = g ( s ( t ) )$ <sub>,</sub> where the isotonic calibrator $g$ <sup>i</sup>s <sup>fi</sup>tte<sup>d</sup> on calib\_fit an<sup>d</sup> a lied unchan ed to (ii) on unlabeled Intel streams the evaluation uses the core score with label-free normalization (ECDF/ChECDF) for deplo<sub>y</sub>ment-st<sub>y</sub>le tria<sub>g</sub>e. The supervised Li<sub>g</sub>htGBM head is used onl<sub>y</sub> as an optional surro<sub>g</sub>ate for SHAP attribu tions and does not afect an re orted detection metric.

Budget-aware operating point learned on calib\_fit: Deployment commonly constrains the alert rate. We therefore learn the o eratin olic under a fixed alert bud et $q$ (default $q = 1 \% )$ on calib\_fit an<sup>d</sup> a <sup>l i</sup>t unc<sup>h</sup>an e<sup>d</sup> to calib\_eval. <sup>S</sup> ec<sup>ifi</sup>ca<sup>ll</sup> , we compu<sup>t</sup>e

$$
k _ {\mathrm{fit}} = \lceil q \cdot | \text { calib\_fit } | \rceil ,
$$

select the exact to $\cdot k _ { \mathrm { f i t } }$ scores on with deterministic tie handlin and record the im lied threshold $\tau _ { \mathrm { { f i t } } }$ (the minimum score within the selected set). Here, $\tau _ { \mathrm { { f i t } } }$ <sup>i</sup>s re orte<sup>d</sup> on<sup>l</sup> as a <sup>di</sup>a nost<sup>i</sup>c summar o<sup>f</sup> t<sup>h</sup>e o erat<sup>i</sup>n re <sup>i</sup>me on calib\_fit; t<sup>h</sup>e <sup>d</sup>e <sup>l</sup>o e<sup>d</sup> <sup>d</sup>ec<sup>i</sup>s<sup>i</sup>on ru<sup>l</sup>e on calib\_eval <sup>i</sup>s <sup>fi</sup>xe<sup>d</sup>-<sup>b</sup>u<sup>d</sup>get se<sup>l</sup>ect<sup>i</sup>on <sup>b</sup>y trans<sup>f</sup>err<sup>i</sup>ng $k _ { \mathrm { f i t } } ( \mathrm { e x a c t t o p } { \cdot } k _ { \mathrm { f i t } }$ w<sup>i</sup>t<sup>h</sup> t<sup>i</sup>e-sa<sup>f</sup>e <sup>d</sup>eterm<sup>i</sup>n<sup>i</sup>sm). <sup>O</sup>n calib\_eval, we then evaluate PR@1% and R@1% b selectin exactly $k _ { \mathrm { f i t } }$ alarms (tie-safe exact to -�). This rocedure ields a faithful, olic -ali ned estimate of fixed-bud et alertin erformance and avoids unstable thresholdin in the resence of ties or heav score uantization.

Pooled reporting and uncertainty: For each dataset, we report pointwise pooled ROC–AUC and PR–AUC on calib\_eval, along with the fixed-bud et o eratin metrics PR@1% and R@1%. Confidence intervals $\mathbf { ( C I _ { 9 5 } ) }$ are computed via series-aware bootstrap, resamplin<sub>g</sub> complete series (not individual points) to respect temporal dependence and hetero<sub>g</sub>eneous stream characteristics. Where relevant<sub>,</sub> we also re<sub>p</sub>ort <sub>p</sub>aired delta $\mathrm { C I _ { 9 5 } }$ for method com<sub>p</sub>arisons usin<sub>g</sub> matched bootstra<sub>p</sub> resam<sub>p</sub>les<sub>, y</sub>ieldin<sub>g</sub> uncertaint<sub>y</sub> on <sub>p</sub>er formance diferences without inflating optimism through pointwise resampling.

Dataset-specific instantiations (controlled diferences): The above protocol is applied uniformly across labeled benchmarks, with onl<sub>y</sub> dataset-im<sub>p</sub>osed ada<sub>p</sub>tations:

• NAB (labeled, univariate): evaluation is reported as pointwise pooled on calib\_eval. Since NAB also provides event/window based scorin we ex licitl distin uish our ointwise Table 5 rotocol from NAB’s event scorin to avoid conflation of objectives.

• SMD (labeled, multivariate): labels are provided only for the oficial test partition. Therefore, to preserve the same leak free se aration between (i) reference fittin , (ii) calibration/threshold learnin , and (iii) final re ortin , we a l an internal, time-ordered 70/15/15 split within the oficial test stream (test\_train\_prefix/calib\_fit /calib\_eval). We do not require the <sup>i</sup>n<sup>i</sup>t<sup>i</sup>a<sup>li</sup>zat<sup>i</sup>on pre<sup>fi</sup>x to <sup>b</sup>e anoma<sup>l</sup>y-<sup>f</sup>ree; <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree<sup>d</sup>om <sup>i</sup>s en<sup>f</sup>orce<sup>d b</sup>y restr<sup>i</sup>ct<sup>i</sup>ng a<sup>ll fi</sup>tt<sup>i</sup>ng an<sup>d d</sup>ec<sup>i</sup>s<sup>i</sup>on se<sup>l</sup>ect<sup>i</sup>on to calib\_fit an<sup>d</sup> report<sup>i</sup>ng on<sup>l</sup>y on calib\_eval.

• UCR (labeled, large-scale): each series is ordered by integer index � and split into contiguous 70/15/15 blocks; budget $k _ { \mathrm { f i t } }$ i <sup>l</sup>earne<sup>d</sup> on calib\_fit an<sup>d</sup> app<sup>li</sup>e<sup>d</sup> to calib\_eval us<sup>i</sup>ng exact top-� se<sup>l</sup>ect<sup>i</sup>on.

• Intel Berkeley Lab (unlabeled): supervised metrics are not available; we therefore retain the same fixed-budget alerting policy (top-1%) and report deplo<sub>y</sub>ment tria<sub>g</sub>e statistics (covera<sub>g</sub>e, stabilit<sub>y</sub>, concentration, and event characteristics) rather than ROC/PR.

<sup>B</sup>y (<sup>i</sup>) en<sup>f</sup>orc<sup>i</sup>ng tempora<sup>l</sup>, per-ser<sup>i</sup>es sp<sup>li</sup>tt<sup>i</sup>ng, (<sup>ii</sup>) separat<sup>i</sup>ng calib\_fit <sup>f</sup>rom calib\_eval, an<sup>d</sup> (<sup>iii</sup>) <sup>l</sup>earn<sup>i</sup>ng <sup>fi</sup>xe<sup>d</sup>-<sup>b</sup>u<sup>d</sup>get operat<sup>i</sup>ng po<sup>i</sup>nts exc<sup>l</sup>us<sup>i</sup>ve<sup>l</sup>y on calib\_fit, t<sup>h</sup>e eva<sup>l</sup>uat<sup>i</sup>on <sup>i</sup>so<sup>l</sup>ates genu<sup>i</sup>ne genera<sup>li</sup>zat<sup>i</sup>on un<sup>d</sup>er <sup>d</sup>r<sup>if</sup>t an<sup>d i</sup>m<sup>b</sup>a<sup>l</sup>ance. <sup>Thi</sup>s protoco<sup>l</sup> a<sup>li</sup>gns t<sup>h</sup>e re<sub>p</sub>orted <sub>p</sub>erformance with realistic de<sub>p</sub>lo<sub>y</sub>ment constraints while <sub>p</sub>reventin<sub>g</sub> threshold- and calibration-induced leaka<sub>g</sub>e.

## 3.4. Baselines, compute budget, and reporting

We benchmark the ro osed framework a ainst baseline families that reflect de lo ment-realistic desi n choices: (i) com ute feasible classical detectors that score observations directl<sub>y</sub>, and (ii) forecastin<sub>g</sub>-residual baselines that capture recent forecaster driven i elines but t icall re uire substantiall hi her wall-clock cost. All methods follow the leaka e-safe evaluation re ime <sup>i</sup>n <sup>S</sup>ect<sup>i</sup>on <sup>3</sup>.<sup>3</sup>. <sup>I</sup>n part<sup>i</sup>cu<sup>l</sup>ar, any operat<sup>i</sup>ng t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup> (<sup>i</sup>nc<sup>l</sup>u<sup>di</sup>ng <sup>b</sup>u<sup>d</sup>get-<sup>d</sup>er<sup>i</sup>ve<sup>d</sup> t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup>s) <sup>i</sup>s <sup>l</sup>earne<sup>d</sup> on calib\_fit an<sup>d</sup> app<sup>li</sup>e<sup>d</sup> unc<sup>h</sup>ange<sup>d</sup> to calib\_eval.

Baselines: The classical detector suite consists of IsolationForest (IF) Local Outlier Factor in novelt mode (LOF) COPOD ETS residual scorin<sub>g,</sub> and MatrixProfile. This selection s<sub>p</sub>ans com<sub>p</sub>lementar<sub>y</sub> mechanisms—isolation-based scorin<sub>g,</sub> local densit<sub>y</sub> devia tion<sub>,</sub> co<sub>p</sub>ula-based tail behavior<sub>,</sub> classical residual modelin<sub>g,</sub> and sha<sub>p</sub>e-based discord discover<sub>y</sub>—and re<sub>p</sub>resents the methods most fre<sub>q</sub>uentl<sub>y</sub> considered when trainin<sub>g</sub> and servin<sub>g</sub> dee<sub>p</sub> se<sub>q</sub>uence models is im<sub>p</sub>ractical. To re<sub>p</sub>resent modern forecaster-driven de tection<sub>,</sub> we include Informer<sub>,</sub> iTransformer<sub>,</sub> and PatchTST in a residual confi<sub>g</sub>uration: a forecaster is fit on the desi<sub>g</sub>nated trainin<sub>g</sub> <sub>p</sub>ortion<sub>, p</sub>rediction residuals <sub>y</sub>ield <sub>p</sub>ointwise anomal<sub>y</sub> scores<sub>,</sub> and those scores are subse<sub>q</sub>uentl<sub>y</sub> calibrated and thresholded usin<sub>g</sub> the same calib\_fit → calib\_eval rotoco<sup>l</sup> as a<sup>ll</sup> ot<sup>h</sup>er met<sup>h</sup>o<sup>d</sup>s.

Compute budget and fairness: To ensure controlled and reproducible comparisons, we enforce a fixed compute policy across methods. All runs are executed in the same environment and measured usin<sub>g</sub> wall-clock seconds with a consistent timin<sub>g p</sub>rocedure. <sup>F</sup>orecast<sup>i</sup>ng <sup>b</sup>ase<sup>li</sup>nes are eva<sup>l</sup>uate<sup>d</sup> un<sup>d</sup>er exp<sup>li</sup>c<sup>i</sup>t compute <sup>li</sup>m<sup>i</sup>ts (e.g., max\_steps an<sup>d</sup> assoc<sup>i</sup>ate<sup>d</sup> ear<sup>l</sup>y-stop/t<sup>i</sup>meout ru<sup>l</sup>es) toget<sup>h</sup>er with deterministic fail-safe behavior: if a forecaster exceeds the bud et<sub>,</sub> diver es<sub>,</sub> or cannot be roduced for a subset of series<sub>,</sub> the event is recorded and a redefined fallback scorin rule is a lied for that subset so that evaluation remains com lete and com arable. This <sub>p</sub>olic<sub>y</sub> is ali<sub>g</sub>ned with the manuscri<sub>p</sub>t’s de<sub>p</sub>lo<sub>y</sub>ment focus: the <sub>g</sub>oal is not unconstrained state-of-the-art trainin<sub>g,</sub> but an accurac<sub>y</sub>–cost com arison under realistic resource limits.

A rdin l w tr t th f r tin -r id l m d l m t -b nd d r f r n r th r th n n n tr in d t t - f-th - rt s<sub>y</sub>stems<sub>,</sub> and we <sub>p</sub>osition the com<sub>p</sub>arison around com<sub>p</sub>ute-feasible baselines that are realistic for continuous monitorin<sub>g</sub> de<sub>p</sub>lo<sub>y</sub>ments. Metrics and operating policy: We report threshold-free ranking quality, fixed-budget operating behavior, wall-clock cost, and uncertaint estimates. As threshold-free metrics we com ute ROC–AUC and PR–AUC b swee in a decision threshold � over the de lo ed decision score (the calibrated robabilit ). Let $y ( t ) \in \{ 0 , 1 \}$ } denote the ointwise round-truth label and let $\hat { y } _ { \tau } ( t ) \in \{ 0 , 1 \}$ be t<sup>h</sup>e <sup>bi</sup>nar <sup>d</sup>ec<sup>i</sup>s<sup>i</sup>on o<sup>b</sup>ta<sup>i</sup>ne<sup>d b</sup> t<sup>h</sup>res<sup>h</sup>o<sup>ldi</sup>n at <sup>l</sup>eve<sup>l</sup> �. <sup>O</sup>n t<sup>h</sup>e re ort<sup>i</sup>n <sup>bl</sup>oc<sup>k</sup> (calib\_eval), we <sup>f</sup>orm t<sup>h</sup>e con<sup>f</sup>us<sup>i</sup>on-matr<sup>i</sup>x counts $T P ( \tau ) , F P ( \tau ) , T N ( \tau ) , F N ( \tau )$ by pointwise pooling over all timestamps (and all streams) in the dataset, and define

$$
\operatorname{Precision} (\tau) = \frac {T P (\tau)}{T P (\tau) + F P (\tau)}, \quad \operatorname{Recall} (\tau) = \frac {T P (\tau)}{T P (\tau) + F N (\tau)}. [ 4 3 ]
$$

The ROC curve <sub>p</sub>lots $( \mathrm { F P R } ( \tau ) , \mathrm { T P R } ( \tau ) )$ with $\mathrm { T P R } ( \tau ) = \mathrm { R e c a l l } ( \tau )$ and $\begin{array} { r } { \mathrm { F P R } ( \tau ) = \frac { F P ( \tau ) } { F P ( \tau ) + T N ( \tau ) } } \end{array}$ , and ROC-AUC is the area under this curve [43]. The PR curve <sub>p</sub>lots

d i th d thi Gi l i b l PR AUC i t t d th i t i throu hout while ROC–AUC is re orted for com leteness PR-based summaries are enerall more informative for o erational utilit in this re ime [32,33].

Because o erational monitorin constrains the alert rate we additionall re ort PR@1% and R@1% under a fixed 1% alert bud et. <sup>Th</sup>e <sup>b</sup>u<sup>d</sup> et <sup>i</sup>s <sup>l</sup>earne<sup>d</sup> on calib\_fit <sup>b</sup> se<sup>l</sup>ect<sup>i</sup>n t<sup>h</sup>e exact $\mathrm { t o p } { - } k _ { \mathrm { f i t } } = \left\lceil 0 . 0 1 \cdot \right\rceil \mathbf { c a l i b } _ { - } \mathbf { f i t } | \rceil$ alarms usin<sub>g</sub> tie-safe selection<sub>;</sub> the same $k _ { \mathrm { f i t } }$ <sup>i</sup>s t<sup>h</sup>en a <sup>li</sup>e<sup>d</sup> on calib\_eval to com ute rec<sup>i</sup>s<sup>i</sup>on an<sup>d</sup> reca<sup>ll</sup> at t<sup>h</sup>e o erat<sup>i</sup>n o<sup>i</sup>nt. <sup>W</sup>e a<sup>l</sup>so re ort Thr@fit(1%) <sup>d</sup>e<sup>fi</sup>ne<sup>d</sup> as t<sup>h</sup>e m<sup>i</sup>n<sup>i</sup>mum score among t<sup>h</sup>e se<sup>l</sup>ecte<sup>d</sup> a<sup>l</sup>arms on calib\_fit, as an <sup>i</sup>nterpreta<sup>bl</sup>e summary o<sup>f</sup> t<sup>h</sup>e <sup>l</sup>earne<sup>d</sup> operat<sup>i</sup>ng reg<sup>i</sup>me. For unlabeled Intel data, su ervised detection metrics are unavailable; we therefore re ort fixed-bud et tria e statistics (covera e, stabilit concentration and event characteristics) under the same 1% alert olic .

Runtime: Runtime is re orted as wall-clock seconds under the com ute olic above and is used in the Pareto anal sis in Sec tion 4.2 to uantif the de lo ment-relevant accurac –cost trade-of.

Uncertainty and paired comparisons: To quantify variability across heterogeneous streams, we compute $\mathrm { C I _ { 9 5 } }$ usin<sub>g</sub> seriesaware bootstra<sub>pp</sub>in<sub>g,</sub> resam<sub>p</sub>lin<sub>g</sub> com<sub>p</sub>lete series rather than individual <sub>p</sub>oints. For selected com<sub>p</sub>arisons<sub>,</sub> we also re<sub>p</sub>ort <sub>p</sub>aired delta $\mathrm { C I } _ { 9 5 }$ b com utin metric diferences on matched bootstra resam les $( \mathrm { e . g . , } \Delta = \mathrm { m e t r i c } ( \mathrm { P r o p o s e d } ) - \mathrm { m e t r i c } ( \mathrm { B a s e l i n e } ) ) _ { \mathrm { : } }$ <sub>,</sub> which directl characterizes uncertaint in erformance a s while reservin the er-series de endence structure as summarized in Table 2.

## 3.5. Reproducibility and configuration summary

We summarize the ex<sub>p</sub>erimental <sub>p</sub>olic<sub>y</sub> and the minimal set of confi<sub>g</sub>uration choices re<sub>q</sub>uired to re<sub>p</sub>roduce the re<sub>p</sub>orted results. <sup>F</sup>u<sup>ll</sup> run-t<sup>i</sup>me env<sup>i</sup>ronment snaps<sup>h</sup>ots (<sup>i</sup>nc<sup>l</sup>u<sup>di</sup>ng a pip freeze) are exporte<sup>d b</sup>y t<sup>h</sup>e <sup>i</sup>mp<sup>l</sup>ementat<sup>i</sup>on an<sup>d</sup> re<sup>f</sup>erence<sup>d</sup> as supp<sup>l</sup>ementary artifacts.

Leakage-safe evaluation policy: All datasets are processed per series in chronological order. We use a per-series contiguous t<sup>h</sup>ree-way sp<sup>li</sup>t w<sup>i</sup>t<sup>h</sup> a tra<sup>i</sup>n<sup>i</sup>ng pre<sup>fi</sup>x (TRAIN\_FRAC=<sup>0</sup>.<sup>70</sup>) an<sup>d</sup> a rema<sup>i</sup>n<sup>i</sup>ng ca<sup>lib</sup>rat<sup>i</sup>on <sup>bl</sup>oc<sup>k</sup> (<sup>30%</sup>), w<sup>hi</sup>c<sup>h i</sup>s sp<sup>li</sup>t <sup>i</sup>nto calib\_fit an<sup>d</sup> calib\_eval us<sup>i</sup>ng CALIB\_FIT\_FRAC=<sup>0</sup>.<sup>50</sup> (<sup>i</sup>.e., a <sup>70</sup>/<sup>15</sup>/<sup>15</sup> sp<sup>li</sup>t). <sup>A</sup>ny ca<sup>lib</sup>rator an<sup>d</sup> any operat<sup>i</sup>ng-po<sup>i</sup>nt se<sup>l</sup>ect<sup>i</sup>on ru<sup>l</sup>e (<sup>i</sup>nc<sup>l</sup>u<sup>di</sup>ng <sup>b</sup>u<sup>d</sup>get-<sup>d</sup>er<sup>i</sup>ve<sup>d</sup> t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup>s) are <sup>l</sup>earne<sup>d</sup> on calib\_fit an<sup>d</sup> app<sup>li</sup>e<sup>d</sup> unc<sup>h</sup>ange<sup>d</sup> to calib\_eval. <sup>All</sup> preprocess<sup>i</sup>ng steps (<sup>i</sup>mputat<sup>i</sup>on, scalin<sub>g</sub>, PCA) are fitted on the trainin<sub>g</sub> prefix onl<sub>y</sub>.

Fixed-budget operating point (1%) and deterministic selection: We enforce a fixed alert bud et $q = \mathtt { B U D G E T \_ Q } = 0 . 0 1$ . On calib\_fit, we set $k _ { \mathrm { f i t } } = \lceil q \rceil \mathsf { c a l i b \_ f i t } | \rceil$ and select the exact $\mathrm { { t o p } } { \cdot } k _ { \mathrm { { f i t } } }$ scores. Selection is deterministic and tie-safe: after com<sub>p</sub>utin<sub>g</sub> thr = min $\{ s _ { i } : i \in \mathrm { T o p } \ – k _ { \mathrm { f i t } } \}$ <sub>,</sub> we take all indices with $s _ { i } >$ thr and fill the remaining quota from $s _ { i } =$ thr in ascending index order. The learned $k _ { \mathrm { f i t } }$ <sup>i</sup>s t<sup>h</sup>en trans<sup>f</sup>erre<sup>d</sup> to calib\_eval to report <sup>PR</sup>@<sup>1%</sup> an<sup>d R</sup>@<sup>1%</sup>.

Uncertainty (series-aware): $\mathrm { C I _ { 9 5 } }$ values are computed via series-aware bootstrappin (resamplin complete series with replacement). We use N\_BOOT=500 re licates and re ort the [0.025, 0.975] uantiles. Paired $\Delta { \cdot } \mathrm { C I } _ { 9 5 }$ values are com<sub>p</sub>uted on matched bootstra<sub>p</sub> draws.

Run-time artifacts: The implementation exports a machine-readable environment snapshot (JSON) and a full pip freeze text file alon<sub>g</sub>side the produced result tables (paths printed at run time). These artifacts provide the complete packa<sub>g</sub>e inventor<sub>y</sub> and enable exact re la of the ex erimental environment.

## 4. Main results

## 4.1. Labeled benchmarks: Main results

Tables 3–5 summarize the rimar labeled-benchmark results under our leaka e-safe rotocol with train-onl calibration and bud<sub>g</sub>et-aware thresholdin<sub>g</sub>. Across all benchmarks, we report both rankin<sub>g</sub>-oriented metrics (ROC–AUC, PR–AUC) and operational, olic -driven metrics under a fixed alert bud et (PR@1% R@1%). This dual view is essential because under severe class imbalance and non-stationarit <sub>,</sub> hi h ROC–AUC does not necessaril translate into de lo able alertin erformance at low bud ets<sub>;</sub> conversel <sub>,</sub> bud<sub>g</sub>et metrics can reveal <sub>p</sub>ractical trade-ofs that are invisible to <sub>g</sub>lobal AUC measures.

Minimal confi<sub>g</sub>uration summar<sub>y</sub> (as implemented). Full environment snapshots and complete packa<sub>g</sub>e lists are ex <sub>p</sub>orted as su<sub>pp</sub>lementar artifacts

<table><tr><td>Item</td><td>Setting</td></tr><tr><td>Randomness control</td><td>SEED=42; NumPy seed set; LightGBM random_state=42</td></tr><tr><td>NAB split policy</td><td>Per-series contiguous split: TRAIN_FRAC=0.70; calibration 30% split by CALIB_FIT_FRAC=0.50 into calib_fit/calib_eval (i.e., 70/15/15).</td></tr><tr><td>Alert budget</td><td>BUDGET_Q=0.01; exact top- $k_{fit}$  on calib_fit; tie-safe deterministic selection</td></tr><tr><td>CI protocol</td><td>Series-aware bootstrap; N_BOOT=500; CI95 via quantiles (0.025, 0.975)</td></tr><tr><td>Causal feature windows (NAB)</td><td>Rolling stats at windows (5, 15, 30); robust z-score window w=200</td></tr><tr><td>Missing/Inf handling</td><td>Causal forward fill (FFILL_LIMIT=5); train-median imputation (NaN median → 0.0); Inf/NaN sanitized to finite</td></tr><tr><td>Embedding</td><td>StandardScaler fit on train prefix; train-only PCA up to 3 components; padded to ( $\phi_1, \phi_2, \phi_3$ )</td></tr><tr><td>Proximity parameters</td><td>DEFAULT: k_MAD=1.4826, W=200, min_cluster_size=30; TUNED: k_MAD=2.0, W=250, min_cluster_size=40</td></tr><tr><td>Neighborhood cue</td><td>Train-referenced kNN with K_FOR_KNN=5</td></tr><tr><td>Density cue</td><td>USE_HDBSCAN=True; trained on train embedding when feasible; otherwise leak-free kNN fallback</td></tr><tr><td>Supervised head</td><td>LightGBM + (optional) isotonic calibration fit on calib_fit only (identity if single-class)</td></tr><tr><td>Compute-bounded forecasters</td><td>If enabled: max_steps=100, INPUT_SIZE=64, WBS=32, LR= $10^{-3}$ ; fail-soft fallback preserves completeness</td></tr><tr><td>Run-time snapshot (this study)</td><td>Google Colab; Python 3.12.12; Linux kernel 6.6.105+; RAM ≈12 GiB; no GPU detected; key libs: NumPy 2.0.2, Pandas 2.2.2, scikit-learn 1.6.1, LightGBM 4.6.0, statsmodels 0.14.6, STUMPY 1.13.0</td></tr></table>

SMD (multivariate, labeled): robust ranking with competitive budget behavior: On SMD (Table 3), the proposed Adaptive Proximity framework achieves the strongest precision–recall ranking performance (PR–AUC = 0.500), indicating improved ordering of anomalous oints in an imbalanced multivariate settin . At the same time, classical outlier detectors (e. ., IsolationForest and COPOD) attain higher ROC–AUC and, in the strict 1% budget regime, IsolationForest yields higher PR@1% and R@1%. We therefore avoid an claim of uniform dominance and instead em hasize the o erational trade-of: our method rioritizes robust PR rank in<sub>g</sub> while remainin<sub>g</sub> com<sub>p</sub>etitive under fixed-bud<sub>g</sub>et alertin<sub>g</sub>. Consistent with this inter<sub>p</sub>retation<sub>,</sub> the confidence intervals indicate that improvements a<sub>g</sub>ainst compute-feasible forecastin<sub>g</sub> baselines (e.<sub>g</sub>., Informer residual) are substantial, while diferences to the stron<sub>g</sub>est classical baselines ma<sub>y</sub> remain within uncertaint<sub>y</sub> bounds and should be inter<sub>p</sub>reted cautiousl<sub>y</sub>.

## Table 3

SMD ooled-calibration ( ointwise) results with leak-free evaluation. To -1% bud et is learned on calib fit and evaluated on calib eval. $\mathrm { C I _ { 9 5 } }$ com-<sub>p</sub>uted via series-aware bootstra<sub>pp</sub>in<sub>g</sub>.

<table><tr><td colspan="2">Method</td><td>ROC-AUC</td><td>PR-AUC</td><td>PR@1%</td><td>R@1%</td><td>Thr@fit</td><td>k</td><td>Runtime(s)</td><td>CI95 (ROC/PR)</td><td colspan="3">CI95 (PR@1/R@1)</td><td></td></tr><tr><td rowspan="2">Adaptive posed)</td><td rowspan="2">Proximity</td><td rowspan="2">(Pro-</td><td rowspan="2">0.871327</td><td rowspan="2">0.500174</td><td rowspan="2">0.623706</td><td rowspan="2">0.170525</td><td rowspan="2">0.985229</td><td rowspan="2">1063</td><td rowspan="2">483.611989</td><td rowspan="2">[0.722, 0.949] / [0.060, 0.813]</td><td rowspan="2">[0.021, 0.334]</td><td rowspan="2">/</td><td rowspan="2">[0.005,</td></tr><tr></tr><tr><td colspan="2">IsolationForest</td><td>0.896975</td><td>0.480147</td><td>0.938852</td><td>0.256687</td><td>0.612336</td><td>1063</td><td>43.717737</td><td>[0.820, 0.948] / [0.302, 0.729]</td><td>[0.467, 0.520]</td><td>0.991]</td><td>/</td><td>[0.114,</td></tr><tr><td colspan="2">COPOD</td><td>0.907725</td><td>0.439436</td><td>0.757291</td><td>0.207047</td><td>786.853027</td><td>1063</td><td>192.291184</td><td>[0.845, 0.944] / [0.323, 0.590]</td><td>[0.488, 0.458]</td><td>0.898]</td><td>/</td><td>[0.108,</td></tr><tr><td colspan="2">Ablation: Base Statistical Only</td><td>0.861571</td><td>0.379802</td><td>0.493885</td><td>0.135031</td><td>0.975787</td><td>1063</td><td>474.241205</td><td>[0.726, 0.942] / [0.052, 0.762]</td><td>[0.014, 0.305]</td><td>0.975]</td><td>/</td><td>[0.003,</td></tr><tr><td colspan="2">LOF (novelty)</td><td>0.827215</td><td>0.144129</td><td>0.256820</td><td>0.070216</td><td>52.213554</td><td>1063</td><td>510.281173</td><td>[0.719, 0.919] / [0.084, 0.384]</td><td>[0.100, 0.218]</td><td>0.529]</td><td>/</td><td>[0.025,</td></tr><tr><td colspan="2">Informer (forecast residual, max_steps=100)</td><td>0.629989</td><td>0.053922</td><td>0.032926</td><td>0.009002</td><td>0.944912</td><td>1063</td><td>66.607002</td><td>[0.515, 0.772] / [0.032, 0.118]</td><td>[0.005, 0.050]</td><td>0.154]</td><td>/</td><td>[0.001,</td></tr><tr><td colspan="2">MatrixProfile (m=64)</td><td>0.600219</td><td>0.047779</td><td>0.011289</td><td>0.003086</td><td>8.444966</td><td>1063</td><td>71.065019</td><td>[0.399, 0.721] / [0.013, 0.116]</td><td>[0.000, 0.015]</td><td>0.060]</td><td>/</td><td>[0.000,</td></tr><tr><td colspan="2">PatchTST (forecast residual, max_steps=100)</td><td>0.479981</td><td>0.037337</td><td>0.031044</td><td>0.008488</td><td>0.957984</td><td>1063</td><td>3077.263019</td><td>[0.363, 0.615] / [0.023, 0.070]</td><td>[0.014, 0.038]</td><td>0.096]</td><td>/</td><td>[0.003,</td></tr><tr><td colspan="2">iTransformer (forecast residual, max_steps=100)</td><td>0.459508</td><td>0.035904</td><td>0.029163</td><td>0.007973</td><td>0.954249</td><td>1063</td><td>3151.234861</td><td>[0.345, 0.583] / [0.025, 0.071]</td><td>[0.019, 0.045]</td><td>0.118]</td><td>/</td><td>[0.004,</td></tr><tr><td colspan="2">ETS-residual</td><td>0.367337</td><td>0.025970</td><td>0.001881</td><td>0.000514</td><td>7.538135</td><td>1063</td><td>208.953632</td><td>[0.239, 0.547] / [0.011, 0.051]</td><td>[0.000, 0.007]</td><td>0.032]</td><td>/</td><td>[0.000,</td></tr></table>

NAB (univariate, labeled): deployment-oriented performance under drift with strong precision at low budget: On NAB (Ta<sup>bl</sup>e 4), t<sup>h</sup>e propose<sup>d</sup> met<sup>h</sup>o<sup>d</sup> aga<sup>i</sup>n atta<sup>i</sup>ns t<sup>h</sup>e <sup>hi</sup>g<sup>h</sup>est PR–<sup>A</sup>UC (= 0.359) un<sup>d</sup>er po<sup>i</sup>ntw<sup>i</sup>se poo<sup>l</sup>e<sup>d</sup> eva<sup>l</sup>uat<sup>i</sup>on on calib\_eval, su<sub>pp</sub>ortin<sub>g</sub> the central claim that <sub>p</sub>roximit<sub>y</sub>-driven scorin<sub>g</sub> with rollin<sub>g</sub> robust stabilization is efective under drift and extreme im <sup>b</sup>a<sup>l</sup>ance. Nota<sup>bl</sup>y, at a <sup>fi</sup>xe<sup>d 1</sup>% a<sup>l</sup>ert <sup>b</sup>u<sup>d</sup>get <sup>l</sup>earne<sup>d</sup> on calib\_fit, t<sup>h</sup>e met<sup>h</sup>o<sup>d</sup> pro<sup>d</sup>uces very <sup>hi</sup>g<sup>h</sup> prec<sup>i</sup>s<sup>i</sup>on (PR@<sup>1</sup>% = 1.000) w<sup>i</sup>t<sup>h</sup> non-trivial recall (R@1% = 0.061) reflectin a conservative et clean alertin re ime suitable for de lo ment scenarios where false alarms are costl<sub>y</sub>. Runtime remains orders-of-ma<sub>g</sub>nitude lower than heav<sub>y</sub> transformer forecasters (e.<sub>g</sub>., Informer residual) while <sub>p</sub>rovidin<sub>g</sub> stron<sub>g</sub>er PR–AUC<sub>,</sub> althou<sub>g</sub>h we stress that runtime should be inter<sub>p</sub>reted under the stated com<sub>p</sub>ute <sub>p</sub>olic<sub>y</sub> and im<sub>p</sub>lementation details. Paired delta intervals further su ort a cautious readin : while the method is com etitive a ainst LOF in terms of PR measures<sub>,</sub> diferences ma<sub>y</sub> not be uniforml<sub>y</sub> si<sub>g</sub>nificant across all metrics<sub>,</sub> motivatin<sub>g</sub> our later o<sub>p</sub>eratin<sub>g</sub>-curve anal<sub>y</sub>sis over a ran<sub>g</sub>e of bud<sub>g</sub>ets.

UCR (large-scale, labeled) - scale and generalization with explicit trade-ofs: UCR constitutes the most challenging generalization and scale test (Table 5), where absolute PR–AUC values are small due to extreme sparsit<sub>y</sub> and hetero<sub>g</sub>eneous series h t i ti I thi i th d th d d t d i t ROC AUC d h b d h h M t i P <sup>fil</sup>e a<sup>tt</sup>a<sup>i</sup>n <sup>hi</sup>g<sup>h</sup>er <sup>ROC</sup>–<sup>AUC</sup>. <sup>H</sup>owever, un<sup>d</sup>er <sup>th</sup>e opera<sup>ti</sup>ona<sup>l 1%</sup> a<sup>l</sup>er<sup>t b</sup>u<sup>d</sup>ge<sup>t</sup>, our me<sup>th</sup>o<sup>d</sup> y<sup>i</sup>e<sup>ld</sup>s su<sup>b</sup>s<sup>t</sup>an<sup>ti</sup>a<sup>ll</sup>y <sup>hi</sup>g<sup>h</sup>er <sup>PR</sup>@<sup>1%</sup> an<sup>d</sup> R@1% than MatrixProfile, alon side a lar e runtime advanta e over both MatrixProfile and LOF. Importantl , paired delta intervals confirm that LOF can out erform our method in ROC–AUC on UCR and we re ort this ex licitl our contribution is therefore best characterized as a de<sub>p</sub>lo<sub>y</sub>ment-oriented Pareto <sub>p</sub>oint: im<sub>p</sub>roved bud<sub>g</sub>eted alertin<sub>g q</sub>ualit<sub>y</sub> with tractable com<sub>p</sub>ute at scale<sub>,</sub> rather than universal su eriorit on all lobal metrics.

Summary of labeled-benchmark evidence: Taken to ether, the labeled results support the manuscript’s central positionin : the <sub>p</sub>ro<sub>p</sub>osed <sub>p</sub>roximit<sub>y</sub>-based ada<sub>p</sub>tive scorin<sub>g,</sub> combined with rollin<sub>g</sub> robust stabilization and leaka<sub>g</sub>e-safe calibration<sub>, y</sub>ields stron<sub>g</sub> PR rankin erformance on two labeled benchmarks (SMD and NAB) and rovides com etitive olic -relevant bud et behavior with favorable runtime characteristics across datasets. Where classical or sha<sub>p</sub>e-based baselines excel on ROC–AUC or at s<sub>p</sub>ecific o<sub>p</sub>eratin<sub>g</sub> <sub>p</sub>oints<sub>,</sub> we treat these as meanin<sub>g</sub>ful trade-ofs rather than contradictions<sub>,</sub> and we anal<sub>y</sub>ze them ex<sub>p</sub>licitl<sub>y</sub> via Pareto and bud<sub>g</sub>et-swee<sub>p</sub> i b t ti

Finall<sub>y,</sub> because real de<sub>p</sub>lo<sub>y</sub>ments often involve missin<sub>g</sub> or dela<sub>y</sub>ed labels<sub>,</sub> we com<sub>p</sub>lement the labeled evaluations with an un labeled deplo<sub>y</sub>ment tria<sub>g</sub>e stud<sub>y</sub> on the Intel Berkele<sub>y</sub> Lab corpus (Table 6), reported separatel<sub>y</sub> to avoid over-claimin<sub>g</sub> supervised <sub>p</sub>erformance in an unlabeled settin<sub>g</sub>.

<sup>NAB</sup> poo<sup>l</sup>e<sup>d</sup>-ca<sup>lib</sup>rat<sup>i</sup>on (po<sup>i</sup>ntw<sup>i</sup>se) resu<sup>l</sup>ts w<sup>i</sup>t<sup>h l</sup>ea<sup>k</sup>-<sup>f</sup>ree eva<sup>l</sup>uat<sup>i</sup>on. <sup>P</sup>er-ser<sup>i</sup>es <sup>70</sup>/<sup>30</sup> sp<sup>li</sup>t; t<sup>h</sup>e ca<sup>lib</sup>rat<sup>i</sup>on <sup>bl</sup>oc<sup>k i</sup>s sp<sup>li</sup>t <sup>i</sup>nto calib\_fit/calib\_eval. <sup>A</sup> top-<sup>1% b</sup>u<sup>d</sup>get <sup>i</sup>s <sup>l</sup>earne<sup>d</sup> on calib\_fit (t<sup>i</sup>e-sa<sup>f</sup>e exact top-�); on calib\_eval, t<sup>h</sup>e <sup>d</sup>ep<sup>l</sup>oye<sup>d</sup> ru<sup>l</sup>e trans<sup>f</sup>ers $k _ { \mathrm { f i t } }$ (with $\tau _ { \mathrm { { f i t } } }$ re<sub>p</sub>orted for dia<sub>g</sub>nostics on<sup>l</sup>y). <sup>M</sup>etr<sup>i</sup>cs are reporte<sup>d</sup> on calib\_eval. $\mathrm { C I _ { 9 5 } }$ is com<sub>p</sub>uted via series-aware bootstra<sub>pp</sub>in<sub>g</sub>. Note: NAB also defines event/window-based scorin<sub>g;</sub> this table re<sub>p</sub>orts <sub>p</sub>ointwise <sub>p</sub>ooled metrics.

<table><tr><td colspan="2">Method</td><td>ROC-AUC</td><td>PR-AUC</td><td>PR@1%</td><td>R@1%</td><td>Thr@fit</td><td>k</td><td>Runtime(s)</td><td>CI95 (ROC/PR)</td><td colspan="3">CI95 (PR@1/R@1)</td></tr><tr><td>Adaptive Proximity (Proposed)</td><td>0.636</td><td>0.359</td><td>1.000</td><td>0.061</td><td>0.5486</td><td>148</td><td>23.77</td><td>[0.507, 0.827] / [0.136, 0.646]</td><td>[0.247, 0.108]</td><td>1.000]</td><td>/</td><td>[0.016,</td></tr><tr><td>LOF (novelty)</td><td>0.655</td><td>0.266</td><td>0.466</td><td>0.029</td><td>3.1000</td><td>148</td><td>61.43</td><td>[0.561, 0.771] / [0.119, 0.398]</td><td>[0.166, 0.049]</td><td>0.802]</td><td>/</td><td>[0.015,</td></tr><tr><td>PatchTST (forecast residual, max_steps=100)</td><td>0.552</td><td>0.208</td><td>0.230</td><td>0.014</td><td>9.7518e+03</td><td>148</td><td>355.04</td><td>[0.312, 0.772] / [0.066, 0.600]</td><td>[0.000, 0.066]</td><td>1.000]</td><td>/</td><td>[0.000,</td></tr><tr><td>ETS-residual</td><td>0.501</td><td>0.202</td><td>0.081</td><td>0.005</td><td>2.8527e+06</td><td>148</td><td>29.61</td><td>[0.338, 0.713] / [0.070, 0.281]</td><td>[0.000, 0.041]</td><td>0.450]</td><td>/</td><td>[0.000,</td></tr><tr><td>Ablation: Base Statistical Only</td><td>0.528</td><td>0.193</td><td>0.541</td><td>0.033</td><td>0.5284</td><td>148</td><td>15.54</td><td>[0.508, 0.557] / [0.117, 0.281]</td><td>[0.173, 0.081]</td><td>0.919]</td><td>/</td><td>[0.009,</td></tr><tr><td>iTransformer (forecast residual, max_steps=100)</td><td>0.510</td><td>0.189</td><td>0.216</td><td>0.013</td><td>1.0344e+04</td><td>148</td><td>465.10</td><td>[0.285, 0.732] / [0.062, 0.573]</td><td>[0.000, 0.066]</td><td>1.000]</td><td>/</td><td>[0.000,</td></tr><tr><td>IsolationForest</td><td>0.521</td><td>0.183</td><td>0.176</td><td>0.011</td><td>0.1876</td><td>148</td><td>2.08</td><td>[0.330, 0.632] / [0.066, 0.343]</td><td>[0.079, 0.049]</td><td>0.654]</td><td>/</td><td>[0.007,</td></tr><tr><td>Informer (forecast residual, max_steps=100) | fallback_series=1/13</td><td>0.484</td><td>0.176</td><td>0.318</td><td>0.019</td><td>1.1006e+04</td><td>148</td><td>6073.60</td><td>[0.229, 0.738] / [0.059, 0.385]</td><td>[0.000, 0.047]</td><td>0.712]</td><td>/</td><td>[0.000,</td></tr><tr><td>MatrixProfile (m=64)</td><td>0.488</td><td>0.147</td><td>0.000</td><td>0.000</td><td>9.0147</td><td>148</td><td>2.22</td><td>[0.366, 0.601] / [0.065, 0.248]</td><td>[0.000, 0.001]</td><td>0.022]</td><td>/</td><td>[0.000,</td></tr><tr><td>COPOD</td><td>0.393</td><td>0.145</td><td>0.142</td><td>0.009</td><td>60.0168</td><td>148</td><td>2.88</td><td>[0.188, 0.579] / [0.053, 0.253]</td><td>[0.022, 0.022]</td><td>0.438]</td><td>/</td><td>[0.002,</td></tr></table>

UCR ooled-calibration ( ointwise) results with leak-free evaluation at lar e scale. To -1% bud et is learned on calib\_fit and evaluated on calib\_eval. $\mathrm { C I _ { 9 5 } }$ com<sub>p</sub>uted via series-aware bootstra<sub>pp</sub>in<sub>g</sub>.

<table><tr><td>Method</td><td>ROC-AUC</td><td>PR-AUC</td><td>PR@1%</td><td>R@1%</td><td>Thr@fit</td><td>k</td><td>Runtime(s)</td><td colspan="3">CI95 (ROC/PR)</td><td colspan="3">CI95 (PR@1/R@1)</td></tr><tr><td>Adaptive Proximity (Proposed)</td><td>0.579138</td><td>0.016549</td><td>0.041939</td><td>0.099920</td><td>1.540493e-02</td><td>23,868</td><td>394.630502</td><td>[0.525, 0.028]</td><td>0.646]</td><td>/</td><td>[0.008, [0.022, 0.145]</td><td>0.064]</td><td>/ [0.057,</td></tr><tr><td>MatrixProfile (m=64)</td><td>0.709964</td><td>0.009935</td><td>0.020823</td><td>0.049611</td><td>6.447163e+00</td><td>23,868</td><td>2186.026975</td><td>[0.658, 0.017]</td><td>0.758]</td><td>/</td><td>[0.006, [0.007, 0.082]</td><td>0.036]</td><td>/ [0.017,</td></tr><tr><td>LOF (novelty)</td><td>0.658774</td><td>0.009424</td><td>0.024594</td><td>0.058595</td><td>5.547092e-01</td><td>23,868</td><td>17890.948818</td><td>[0.597, 0.017]</td><td>0.711]</td><td>/</td><td>[0.005, [0.009, 0.090]</td><td>0.045]</td><td>/ [0.028,</td></tr><tr><td>COPOD</td><td>0.494981</td><td>0.004951</td><td>0.007039</td><td>0.016770</td><td>-1.231583e+01</td><td>23,868</td><td>106.348866</td><td>[0.377, 0.008]</td><td>0.628]</td><td>/</td><td>[0.003, [0.003, 0.030]</td><td>0.012]</td><td>/ [0.009,</td></tr><tr><td>IsolationForest</td><td>0.498687</td><td>0.004832</td><td>0.000000</td><td>0.000000</td><td>2.179272e-01</td><td>23,868</td><td>45.645328</td><td>[0.361, 0.009]</td><td>0.610]</td><td>/</td><td>[0.002, [0.000, 0.008]</td><td>0.004]</td><td>/ [0.000,</td></tr><tr><td>Ablation: Base Statistical Only</td><td>0.507773</td><td>0.004686</td><td>0.008128</td><td>0.019365</td><td>1.591403e-02</td><td>23,868</td><td>328.521006</td><td>[0.454, 0.007]</td><td>0.571]</td><td>/</td><td>[0.003, [0.001, 0.050]</td><td>0.021]</td><td>/ [0.003,</td></tr><tr><td>ETS-residual</td><td>0.477130</td><td>0.004064</td><td>0.000042</td><td>0.000100</td><td>1.981570e+06</td><td>23,868</td><td>519.279710</td><td>[0.352, 0.008]</td><td>0.596]</td><td>/</td><td>[0.002, [0.000, 0.000]</td><td>0.000]</td><td>/ [0.000,</td></tr></table>

## 4.2. Pareto analysis: Accuracy vs runtime

Be ond sin le-metric rankin de lo ment-oriented anomal detection re uires ex licit trade-of anal sis between detection ual it and wall-clock cost. To this end we erform a Pareto anal sis where each method is re resented as a oint with accurac on the vertical axis and runtime on the horizontal axis. We use PR–AUC as the rimar accurac metric due to extreme class imbal ance, and visualize runtime on a lo arithmic scale (i.e., PR–AUC vs. log(runtime)) to account for the multi-order-of-ma nitude spread induced b forecastin -based baselines. Runtime is re orted as wall-clock seconds under the fixed com ute olic described in Sec tion 4 (same environment and measurement rocedure as in Tables 3–5). Wall-clock runtime is measured end-to-end under the fixed com ute olic includin re rocessin scorin and ost- rocessin (calibration/thresholdin where a licable. A method is Pareto-dominated if there exists another method that achieves hi her (or e ual) PR–AUC at lower (or e ual) runtime with at least one strict im<sub>p</sub>rovement.

PR–AUC vs. runtime: deployment-sustainable accuracy: Across datasets the ro osed Ada tive Proximit framework consistentl occu ies a favorable re ion of the accurac –runtime lane. On NAB (Table 4) the ro osed method attains the hi hest PR–AUC while remainin<sub>g</sub> orders-of-ma<sub>g</sub>nitude faster than transformer forecasters (Informer, iTransformer, PatchTST residual base lines), ieldin a clear de lo ment-sustainable o eratin oint when com ute is constrained. On SMD (Table 3), the ro osed method achieves the stron<sub>g</sub>est PR–AUC<sub>,</sub> while li<sub>g</sub>hter classical baselines such as IsolationForest <sub>p</sub>rovide a com<sub>p</sub>lementar<sub>y p</sub>oint on the frontier b tradin a small PR–AUC decrease for substantiall reduced runtime. This attern is consistent with the intended ositionin of the ro osed framework: shiftin the Pareto frontier u ward in PR ualit without rel in on com ute-heav forecastin backbones.

Intel unlabeled tria<sub>g</sub>e: CTS rankin<sub>g</sub> and ke<sub>y</sub> com<sub>p</sub>onents under the leak-free $q = 1 \%$ bud et (threshold learned on and a lied unchan ed to calib\_eval). <sup>C</sup>omponent scores $( C T S _ { C } – C T S _ { R } )$ are the min–max normalized terms used in CTS; ��� and � are re orted in raw units for inter<sub>p</sub>retabilit<sub>y</sub>.

<table><tr><td>Method</td><td>CTS</td><td> $CT S_C$ </td><td> $CT S_S$ </td><td> $CT S_H$ </td><td> $CT S_D$ </td><td> $CT S_R$ </td><td>HHI</td><td>D (min)</td><td>Runtime (s)</td></tr><tr><td>Proposed (invMAD-weighted) + ChECDF + ECDF</td><td>0.823952</td><td>0.792</td><td>0.777</td><td>0.930</td><td>0.668</td><td>1.000</td><td>0.108986</td><td>35.9</td><td>0.0314</td></tr><tr><td>Proposed (p-norm, p=4) + ChECDF + ECDF</td><td>0.800732</td><td>0.708</td><td>0.815</td><td>0.923</td><td>0.646</td><td>1.000</td><td>0.115828</td><td>40.1</td><td>0.0314</td></tr><tr><td>Proposed (mean) + ChECDF + ECDF</td><td>0.789645</td><td>0.708</td><td>0.770</td><td>0.923</td><td>0.646</td><td>1.000</td><td>0.115828</td><td>40.1</td><td>0.0314</td></tr><tr><td>Proposed (softmax, α=6) + ChECDF + ECDF</td><td>0.758518</td><td>0.625</td><td>0.848</td><td>0.639</td><td>1.000</td><td>1.000</td><td>0.387571</td><td>6.2</td><td>0.0314</td></tr><tr><td>COPOD + ECDF</td><td>0.657870</td><td>0.583</td><td>0.826</td><td>0.808</td><td>0.595</td><td>0.261</td><td>0.225385</td><td>51.8</td><td>14.5946</td></tr><tr><td>IsolationForest + ECDF</td><td>0.650034</td><td>0.625</td><td>0.592</td><td>0.937</td><td>0.449</td><td>0.510</td><td>0.102496</td><td>106.9</td><td>5.2482</td></tr><tr><td>MatrixProfile (m=64) + ECDF</td><td>0.641433</td><td>0.458</td><td>0.576</td><td>0.900</td><td>0.912</td><td>0.658</td><td>0.137933</td><td>10.1</td><td>2.6198</td></tr><tr><td>Proposed (top2_mean) + ChECDF + ECDF</td><td>0.496494</td><td>0.167</td><td>0.848</td><td>0.620</td><td>0.022</td><td>1.000</td><td>0.405903</td><td>878.7</td><td>0.0314</td></tr><tr><td>Proposed (max) + ChECDF + ECDF</td><td>0.465328</td><td>0.167</td><td>0.723</td><td>0.631</td><td>0.000</td><td>1.000</td><td>0.395290</td><td>978.7</td><td>0.0314</td></tr><tr><td>Proposed (noisy_or) + ChECDF + ECDF</td><td>0.465328</td><td>0.167</td><td>0.723</td><td>0.631</td><td>0.000</td><td>1.000</td><td>0.395290</td><td>978.7</td><td>0.0314</td></tr><tr><td>ETS-residual + ECDF</td><td>0.310380</td><td>0.125</td><td>0.924</td><td>0.093</td><td>0.170</td><td>0.000</td><td>0.911057</td><td>424.7</td><td>39.7434</td></tr></table>

$C T S = { \textstyle { \frac { 1 } { 5 } } } ( C T S _ { C } + C T S _ { S } + C T S _ { H } + C T S _ { D } + C T S _ { R } )$ with $C T S _ { H }$ based on $1 { - } H H I ,$ and $C T S _ { D } , C T S _ { R }$ based on inverted (smaller-is-better) scalin<sub>g</sub>.

![](images/08e481cd664c67953926fc82766b28fd299dddd70242a749309a054bce11477a.jpg)  
(a) SMD: PR–AUC vs. log(runtime).

![](images/4b1294c36f6ffec03b058f24616d46be31c37958aed0a0d5f2c079c5f7cbc3ce.jpg)  
(b) NAB: PR–AUC vs. log(runtime)

![](images/a7485e5342a3a4f3683c6ad820dec261f6251991c78ff54dee738c9416c94b38.jpg)  
(c) UCR: PR-AUC vs. log(runtime)  
Fig. 1. Pareto analysis of accuracy vs. runtime using PR–AUC (vertical) and log(runtime) in seconds (horizontal). Each point corresponds to a method re orted in Tables 3–5. Lo scalin reflects multi-order-of-ma nitude runtime diferences. Pareto-dominated methods are those for which another method achieves hi<sub>g</sub>her PR–AUC at lower runtime.

On UCR at scale<sub>,</sub> as shown in Fi<sub>g</sub>. 1 and Table 3<sub>,</sub> forecastin<sub>g</sub>-based a<sub>pp</sub>roaches are not com<sub>p</sub>etitive in either runtime or PR rankin<sub>g,</sub> whereas the <sub>p</sub>ro<sub>p</sub>osed method <sub>p</sub>rovides the stron est PR-AUC amon evaluated baselines with tractable runtime<sub>,</sub> confirmin that the a roach remains viable under lar e-scale hetero eneous streams.

PR@1% vs. runtime for operational alerting: While PR–AUC ca tures rankin ualit , ractical de lo ments often o erate under ex licit alert bud ets. We therefore o tionall re eat the Pareto anal sis with PR@1% on the vertical axis (and runtime on the horizontal axis) ali nin the evaluation with fixed-bud et alertin olicies re orted in Tables 3–5. This view com lements PR–AUC b hi<sub>g</sub>hli<sub>g</sub>htin<sub>g</sub> o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oint behavior: on SMD<sub>,</sub> IsolationForest is advanta<sub>g</sub>eous at the strict 1% bud<sub>g</sub>et<sub>,</sub> whereas the <sub>p</sub>ro<sub>p</sub>osed method reserves stron bud et erformance while rovidin substantiall im roved lobal PR rankin . On NAB the ro osed method ields ver hi h PR@1% with moderate runtime su ortin conservative alertin when false alarms are costl . On UCR where absolute PR values are small PR@1% em hasizes the ractical advanta e of the ro osed a roach over slower sha e-based baselines even when ROC–AUC ma<sub>y</sub> favor alternative methods. We stress that these o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oint com<sub>p</sub>arisons are <sub>p</sub>olic<sub>y</sub>-de<sub>p</sub>endent<sub>;</sub> conse<sub>q</sub>uentl<sub>y,</sub> Section 4.3 further re<sub>p</sub>orts bud<sub>g</sub>et-swee<sub>p</sub> curves to avoid over-inter<sub>p</sub>retin<sub>g</sub> an<sub>y</sub> sin<sub>g</sub>le threshold.

Overall<sub>,</sub> the Pareto anal sis rovides an inter retable and de lo ment-relevant summar of the main results: the ro osed frame work consistentl<sub>y</sub> delivers stron<sub>g</sub> PR-based accurac<sub>y</sub> with runtime characteristics that are com<sub>p</sub>atible with real-time or near-real-time monitorin <sub>,</sub> while classical baselines remain useful as fast alternatives at s<sub>p</sub>ecific bud et re imes. This reinforces the manuscri<sub>p</sub>t’s cen tral claim that <sub>p</sub>roximit<sub>y</sub>-based ada<sub>p</sub>tive scorin<sub>g</sub> with robust stabilization and leaka<sub>g</sub>e-safe calibration tar<sub>g</sub>ets a <sub>p</sub>racticall<sub>y</sub> favorable accuracy–compute tra<sup>d</sup>e-o<sup>f</sup>; see <sup>Fi</sup>g. <sup>2</sup>.

## 4.3. Budget sensitivity

We re ort the main-text bud et-swee anal sis on NAB and SMD because to ether the bracket the two de lo ment re imes tar eted b our stud and therefore make the o erational oint with minimal redundanc . NAB re resents rare-event streaming telemetry with ti ht alert bud ets where false alarms dominate o erational cost SMD re resents heterogeneous multi-sensor server telemetry where anomal mechanisms var across series and the ractical uestion is how uickl recall can be ex anded as review ca acit increases. <sup>I</sup>n <sup>b</sup>ot<sup>h</sup> cases, t<sup>h</sup>e same <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup>-trans<sup>f</sup>er protoco<sup>l i</sup>s use<sup>d</sup>—�(�) <sup>i</sup>s <sup>l</sup>earne<sup>d</sup> exc<sup>l</sup>us<sup>i</sup>ve<sup>l</sup>y on calib\_fit v<sup>i</sup>a a <sup>d</sup>eterm<sup>i</sup>n<sup>i</sup>st<sup>i</sup>c t<sup>i</sup>e sa<sup>f</sup>e to -� ru<sup>l</sup>e an<sup>d</sup> a <sup>li</sup>e<sup>d</sup> unc<sup>h</sup>an e<sup>d</sup> to calib\_eval—so t<sup>h</sup>e resu<sup>l</sup>t<sup>i</sup>n <sup>P</sup>rec<sup>i</sup>s<sup>i</sup>on@�/<sup>R</sup>eca<sup>ll</sup>@� curves <sup>di</sup>rect<sup>l</sup> uant<sup>if</sup> t<sup>h</sup>e rec<sup>i</sup>s<sup>i</sup>on– recall trade-of under fixed alarm-rate constraints.

![](images/67b3ee1ab8ff2e8926edf2a183d84bf07da4f6c0d02e2de4a7a9c898d8b27ba9.jpg)  
(a) SMD: PR@1% vs. runtime.

![](images/48f96589f243c636b85e2dadb16c430afd76e9d849315524a5d978ffe55c1db2.jpg)  
(b) NAB: PR@1% vs. runtime.

![](images/9ca482b6277b84d456d4c5d8294bbab2304dc2ab33f2aad6b6742266c40f9cc8.jpg)  
(c) UCR: PR@1% vs. runtime.  
Fig. 2. Optional Pareto analysis under a fixed 1% alert budget, using PR@1% (vertical) and runtime in seconds (horizontal). This view emphasizes <sub>p</sub>olic<sub>y</sub>-driven o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oint <sub>p</sub>erformance and com<sub>p</sub>lements the PR–AUC anal<sub>y</sub>sis in Fi<sub>g</sub>. 1.

We deliberatel do not include a third full set of bud et curves for UCR in the main text. UCR follows the same threshold-transfer <sub>p</sub>rotocol and <sub>y</sub>ields the same t<sub>yp</sub>e of o<sub>p</sub>erational conclusion<sub>,</sub> but adds substantial visual and narrative re<sub>p</sub>etition while increasin<sub>g</sub> fi<sub>g</sub>ure count without ex<sub>p</sub>andin<sub>g</sub> the covera<sub>g</sub>e of de<sub>p</sub>lo<sub>y</sub>ment conditions be<sub>y</sub>ond what is alread<sub>y</sub> established b<sub>y</sub> NAB and SMD. Accordin<sub>g</sub>l<sub>y,</sub> the main text focuses on the two benchmarks that most clearl<sub>y</sub> ex<sub>p</sub>ose the o<sub>p</sub>erational extremes of interest<sub>,</sub> kee<sub>p</sub>in<sub>g</sub> the <sub>p</sub>resentation com act and non-redundant.

## 4.3.1. Budget sensitivity on NAB (Operational trade-of)

We anal<sub>y</sub>ze how performance varies under an explicit alert bud<sub>g</sub>et � (fraction of points fla<sub>gg</sub>ed). For each method, the decision threshold $\tau ( q )$ is learned exclusively on calib\_fit via a deterministic, tie-safe top-� rule and then applied unchanged to calib\_eval. This strictl leak-free protocol ields Precision@� and Recall@� curves that reflect deplo ment-time bud et constraints

Im ortantl our method is most advanta eous in the o erationall relevant low-bud et re ime. For $q \in \{ 0 . 1 \% , 0 . 2 \% , 0 . 5 \% , 1 \% \}$ , it maintains near-<sub>p</sub>erfect <sub>p</sub>recision $( \mathrm { i . e . } ,$ , essentially no false alarms at the smallest budgets), while Recall@� increases monotonically as the bud<sub>g</sub>et is relaxed. This indicates that additional alerts <sub>p</sub>rimaril<sub>y</sub> recover missed anomalies rather than introducin<sub>g</sub> s<sub>p</sub>urious detections. Consistent with this behavior the Precision@ curves remain ositive a ainst both the statistical-onl ablation and LOF across t<sup>h</sup>e exp<sup>l</sup>ore<sup>d b</sup>u<sup>d</sup>gets, s<sup>h</sup>ow<sup>i</sup>ng t<sup>h</sup>at, w<sup>h</sup>en t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup>s are <sup>l</sup>earne<sup>d</sup> on calib\_fit an<sup>d</sup> trans<sup>f</sup>erre<sup>d</sup> to calib\_eval, prox<sup>i</sup>m<sup>i</sup>ty aware scorin<sub>g</sub> translates directl<sub>y</sub> into fewer false <sub>p</sub>ositives <sub>p</sub>er unit bud<sub>g</sub>et and a more favorable <sub>p</sub>recision–recall trade-of under realistic alertin constraints as shown in Fi . 3.

## 4.3.2. Budget sensitivity on SMD (Operational trade-of)

We anal ze erformance under an ex licit alert bud et $q ,$ defined as the fraction of time oints fla ed as anomalous. For each method<sub>,</sub> the o<sub>p</sub>eratin<sub>g</sub> threshold $\tau ( q )$ is learned exclusively on calib\_fit using a deterministic, tie-safe top-� rule $( k = \lceil q \rceil { \mathsf { c a l i b \_ f i t } } | ] )$ and then applied unchanged on calib\_eval. This yields leak-free Precision@� and Recall@� curves that match deployment constraints where the alarm rate is fixed in advance.

Fi<sub>g</sub>. 4 shows that at extremel<sub>y</sub> ti<sub>g</sub>ht bud<sub>g</sub>ets $( q \leq 0 . 5 \% )$ <sub>,</sub> heav<sub>y</sub>-tail outlier detectors $\left( \mathbf { e . g . } \right.$ ., IsolationForest/COPOD) can achieve ver hi h Precision@� b selectin onl the most extreme oints albeit with limited recall. In contrast the ro osed roximit -fused scorin<sub>g</sub> becomes com<sub>p</sub>etitive from moderate o<sub>p</sub>erational bud<sub>g</sub>ets onward. At $q \approx 1 \%$ <sub>,</sub> OUR reaches a substantiall<sub>y</sub> hi<sub>g</sub>her o<sub>p</sub>eratin<sub>g</sub> oint balance and for $q \in [ 2 \% , 5 \% ]$ it rovides the stron est recall while maintainin ractical recision indicatin that additional alarm ca<sub>p</sub>acit<sub>y</sub> is used to surface diverse anomal<sub>y</sub> re<sub>g</sub>imes rather than re<sub>p</sub>eatedl<sub>y</sub> concentratin<sub>g</sub> on a narrow subset of <sub>p</sub>oints.

To isolate o erational ains, Fi . 5 re orts ΔPrecision $@ q$ and $\Delta \mathrm { R e c a l l } @ q$ versus two relevant baselines: the statistical-onl ablation (ABL) and LOF. For $q \geq 1 \%$ OUR ields consistentl ositive ΔRecall@� and ositive ΔPrecision@� a ainst LOF with the mar in widenin as the bud et increases. A ainst ABL<sub>,</sub> OUR <sub>p</sub>rovides a stable recall im<sub>p</sub>rovement across $q ,$ while <sub>p</sub>recision ains are more modest and most ronounced in the mid-bud et re ime. Overall the swee indicates that the ro osed method is most efective in realistic monitorin<sub>g</sub> settin<sub>g</sub>s where o<sub>p</sub>erators can allocate $q \approx 1 \% - 5 \%$ of <sub>p</sub>oints for review<sub>,</sub> deliverin<sub>g</sub> a favorable <sub>p</sub>recision–recal trade-of under a strictl leak-free thresholdin rotocol.

## 4.4. Unlabeled intel: Triage results

Intel Berkele<sub>y</sub> telemetr<sub>y</sub> is unlabeled<sub>;</sub> therefore<sub>,</sub> we evaluate de<sub>p</sub>lo<sub>y</sub>ment tria<sub>g</sub>e utilit<sub>y</sub> usin<sub>g</sub> the leak-free <sub>p</sub>rotocol and Com<sub>p</sub>osite Tria e Score (CTS) defined in Section 2.7.

CTS-ranked results: Table 6 reports the CTS ranking together with the normalized CTS components and the key raw uant<sup>i</sup>t<sup>i</sup>es (<sup>HHI</sup>, mean event <sup>d</sup>urat<sup>i</sup>on, runt<sup>i</sup>me) com ute<sup>d</sup> on calib\_eval at $q = 1 \% .$ . The hi hest CTS is achieved b Proposed(ProxFuse=invMAD\_ weighted\_on\_cf) +ChECDF(cf)+ECDF(cf), <sup>i</sup>n<sup>di</sup>cat<sup>i</sup>ng t<sup>h</sup>e most <sup>f</sup>avora<sup>bl</sup>e overa<sup>ll</sup> tr<sup>i</sup>age pro<sup>fil</sup>e un der the chosen o<sub>p</sub>eratin <sub>p</sub>olic : broad fleet covera e<sub>,</sub> ade<sub>q</sub>uate cross-s<sub>p</sub>lit stabilit after calibration transfer<sub>,</sub> low concentration of alerts across nodes<sub>,</sub> and non-de<sub>g</sub>enerate event durations<sub>,</sub> all at ne<sub>g</sub>li<sub>g</sub>ible runtime.

Operational trade-ofs and failure modes: On unlabeled telemetry, a high score alone is insuficient; the triage objective penal izes operationally degenerate behaviors. Several fusion rules can be com utationall inex ensive et ield weak screenin utilit b

Budget g (fraction of points flagged; learned on calib fit)  
AB Budget Sweep: Precision@q (threshold learned on calib\_fit, applied on cal  
![](images/98d3a67a04a64fc88810b57984cbadcbce9eb0aa697f9060b595a7347245baa5.jpg)  
Budget q (fraction of points flagged; learned on calib\_fit)

NAB Budget Sweep: Recall@q (threshold learned on calib fit, applied on calil  
![](images/dfef5cc1a5f583edf76328b9455eb303f4f42cb9044a5022651e1b52bd1538bb.jpg)

NAB Budget Sweep: ∆ Precision@q  
![](images/f146d8cda92b6651fac697122db383fece652ead691625e29793a54a00ce109a.jpg)  
Fig. 3. NAB bud et swee on : Precision@� (to ) Recall@� (middle) and Precision ain ΔPrecision@� relative to ke baselines (bot tom). <sup>Th</sup>res<sup>h</sup>o<sup>ld</sup>s are <sup>l</sup>earne<sup>d</sup> on calib\_fit an<sup>d</sup> app<sup>li</sup>e<sup>d l</sup>ea<sup>k</sup>-<sup>f</sup>ree to calib\_eval.

SMD Budget Sweep: Precision@g (thr learned on calib fit, applied on calib eval)  
![](images/781e0499d57b06f0e6e874591c45ef46a6780fb8324bcfeb100c6a8b40a83cce.jpg)

SMD Budget Sweep: Recall@g (thr learned on calib fit, applied on calib eval)  
![](images/03da2d235aefd4f96d9f5c3241bc02b4d4ef53e3b2be4d57d674c778951fc2a1.jpg)  
SMD bud et swee on : Precision@ (left) and Recall@ (ri ht) with learned on and a lied unchan ed on calib\_eval.

Budget q (fraction flagged; threshold learned on calib fit)

![](images/0f496f5c04ded8b5e64c0be9062d7239aaeba46e262bf3d399f7205da779f9c0.jpg)  
Budget q (fraction flagged; threshold learned on calib fit)

SMD Budget Sweep: ∆Recall@g (OUR – baseline)  
![](images/78fe012e91a3a5b0c41a14b52d6400530c244c573f5cb958e5066edfe4531a56.jpg)  
Fig. 5. SMD operational deltas: ΔPrecision@� and ΔRecall@� for OUR relative to ABL and LOF. Positive values indicate an advantage for OUR at t<sup>h</sup>e same a<sup>l</sup>ert <sup>b</sup>u<sup>d</sup>get �.

Intel Unlabeled Triage: Coverage vs Stability (CTS-ranked)  
![](images/3300c9d1deff5210eb84c124f89283b4863ca5eae974ff3d2bb08c36efe93b19.jpg)  
I t l l b l d t i d l k f l t b d t E h i t i th d iti d b d d node-wise stabilit (S earman a reement of mean scores between and ). The CTS-best method is hi hli hted.

(i) concentratin<sub>g</sub> alerts on a small subset of nodes (hi<sub>g</sub>h HHI), or (ii) producin<sub>g</sub> extremel<sub>y</sub> persistent alert se<sub>g</sub>ments (inflated mean duration), which collapses operator attention into lon<sub>g</sub> low-<sub>g</sub>ranularit<sub>y</sub> intervals. Conversel<sub>y</sub>, methods that appear stable in a rank sense across and can still be unattractive if covera e is low or runtime is rohibitive. CTS makes these tensions ex licit b combinin the five criteria into a sin le<sub>,</sub> leak-free rankin ali ned with de lo ment screenin rather than accurac .

Coverage–stability view: Fig. 6 provides a compact view of the dominant trade-of between node coverage on calib\_eval and cross-s <sup>li</sup>t sta<sup>bili</sup>t (<sup>S</sup> earman a reement o<sup>f</sup> no<sup>d</sup>e-w<sup>i</sup>se mean scores <sup>b</sup>etween calib\_fit an<sup>d</sup> calib\_eval), w<sup>i</sup>t<sup>h</sup> t<sup>h</sup>e <sup>CTS</sup>-se<sup>l</sup>ecte<sup>d</sup> o eratin oint hi hli hted.

## 4.5. Explainability (SHAP)

The <sub>p</sub>roximit<sub>y</sub> core is unsu<sub>p</sub>ervised and does not ex<sub>p</sub>ose a native <sub>p</sub>arametric ma<sub>pp</sub>in<sub>g</sub> from in<sub>p</sub>ut features to scores. Therefore<sub>,</sub> for inter retabilit we train a li htwei ht su ervised surrogate head (Li htGBM) on to redict the calibrated anomal robabilit and we re ort SHAP attributions of this head. This anal sis is o tional and does not alter the core detector or an re<sub>p</sub>orted detection metric.

## SHAP for NAB:

To ensure that the <sub>p</sub>ro<sub>p</sub>osed detector remains trans<sub>p</sub>arent at de<sub>p</sub>lo<sub>y</sub>ment time<sub>,</sub> we anal<sub>y</sub>ze its decision lo<sub>g</sub>ic usin<sub>g</sub> SHa<sub>p</sub>le<sub>y</sub> Additive exPlanations (SHAP). Im ortantl , all ex lanations re orted for NAB are com uted on the leak-free evaluation block (calib\_eval) roduced b the external 3-wa tem oral s litter the model is trained without usin labels and SHAP is com uted with respect to the model output calibrated probability (i.e., the post-calibration anomaly probability used for ranking and thresholding). For NAB<sub>,</sub> the SHAP evaluation set contains 14<sub>,</sub>744 <sub>p</sub>oints from 13 series with 3141 <sub>p</sub>ositives<sub>,</sub> and we use a series-balanced sam<sub>p</sub>lin<sub>g</sub> scheme (169 oints er series 5, 132 total) so that lon streams do not dominate the lobal ex lanation.

NAB SHAP (Leak-free: calib\_eval (3-way, leak-free) [external splitter]) — series-balanced sample  
![](images/364c33cefa36430a6c315d2058ca990b3dbbeb9440a5754e28dc6a41956e0ada.jpg)  
Fig. 7. NAB SHAP summar (leak-free calib\_eval, external 3-wa splitter; series-balanced sample). SHAP values are computed for the calibrated anomaly probability. Each point corresponds to an evaluation instance; color encodes the feature value (low to high), and the horizontal axis shows the si ned contribution to the model out ut.

Fi . 7 summarizes lobal attribution atterns via a SHAP beeswarm lot. The rankin is driven rimaril b robust statistical <sup>d</sup>escr<sup>i</sup>ptors compute<sup>d</sup> over me<sup>di</sup>um w<sup>i</sup>n<sup>d</sup>ows, <sup>l</sup>e<sup>d b</sup>y roll\_med\_30, roll\_mean\_30, an<sup>d</sup> roll\_std\_30. <sup>P</sup>rox<sup>i</sup>m<sup>i</sup>ty-<sup>d</sup>r<sup>i</sup>ven <sup>d</sup>escr<sup>i</sup>ptors t<sup>h</sup>en appear prom<sup>i</sup>nent<sup>l</sup> , w<sup>i</sup>t<sup>h</sup> prox\_velocity\_mu, proto\_dist\_1, an<sup>d</sup> prox\_level\_mu amon t<sup>h</sup>e top contr<sup>ib</sup>utors. <sup>Th</sup>ese resu<sup>l</sup>ts are consistent with the intended desi n: statistical features encode local level and dis ersion shifts while roximit features uantif deviation relative to learned nei<sub>g</sub>hborhood structure<sub>,</sub> thereb<sub>y</sub> su<sub>pp</sub>ortin<sub>g</sub> detection under drift and hetero<sub>g</sub>eneous re<sub>g</sub>imes.

Table 7 re<sub>p</sub>orts the to<sub>p</sub>-10 features b<sub>y</sub> mean absolute SHAP ma<sub>g</sub>nitude. To <sub>p</sub>rovide a hi<sub>g</sub>her-level view<sub>,</sub> we also a<sub>gg</sub>re<sub>g</sub>ate mean absolute attributions b feature famil (Statistical, Proximit , Latent, Raw). The resultin roup shares indicate that Statistical features account for 61.0% of the total mean|SHAP|, Proximit features account for 25.2%, Latent features contribute 8.0%, and the Raw si nal contributes 5.8%. This decom osition hi hli hts that the model relies on a blend of classical time-series statistics and nei hborhood-aware roximit cues with latent com onents rovidin a smaller but non-ne li ible su ortin si nal as summarized in Table 8.

Be ond a re ate im ortance<sub>,</sub> we assess whether the lobal ex lanation is re resentative across hetero eneous NAB streams. For each of the 13 series<sub>,</sub> we com<sub>p</sub>ute a <sub>p</sub>er-series feature-im<sub>p</sub>ortance rankin<sub>g</sub> and com<sub>p</sub>are it to the <sub>g</sub>lobal rankin<sub>g</sub> usin<sub>g</sub> S<sub>p</sub>earman l ti Th ( di ) k l ti i ( ) i di ti th t th l ti i b dl t bl i th than bein<sub>g</sub> driven b<sub>y</sub> a small subset of streams. At the same time<sub>, p</sub>roximit<sub>y</sub>-related features consistentl<sub>y</sub> a<sub>pp</sub>ear amon<sub>g</sub> the to<sub>p</sub>

Table 7  
<sup>NAB</sup> (<sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree calib\_eval) top-<sup>10 f</sup>eatures <sup>b</sup>y mean absolute SHAP value (series-balanced sample).

<table><tr><td>Feature</td><td>mean|SHAP|</td><td>Group</td></tr><tr><td>roll_med_30</td><td>0.612431</td><td>Statistical</td></tr><tr><td>roll_mean_30</td><td>0.423493</td><td>Statistical</td></tr><tr><td>roll_std_30</td><td>0.388476</td><td>Statistical</td></tr><tr><td>prox_velocity_mu</td><td>0.352357</td><td>Proximity</td></tr><tr><td>proto_dist_1</td><td>0.324283</td><td>Proximity</td></tr><tr><td>prox_level_mu</td><td>0.323765</td><td>Proximity</td></tr><tr><td>roll_med_15</td><td>0.307884</td><td>Statistical</td></tr><tr><td>value</td><td>0.278519</td><td>Raw</td></tr><tr><td>robust_z_200</td><td>0.225833</td><td>Statistical</td></tr><tr><td>roll_std_15</td><td>0.225606</td><td>Statistical</td></tr></table>

## Table 8

NAB SHAP <sub>g</sub>roup contributions (sum of mean|SHAP|) and shares.

<table><tr><td>Group</td><td>Sum mean|SHAP|</td><td>Share (%)</td></tr><tr><td>Statistical</td><td>2.906821</td><td>61.0%</td></tr><tr><td>Proximity</td><td>1.201264</td><td>25.2%</td></tr><tr><td>Latent</td><td>0.382476</td><td>8.0%</td></tr><tr><td>Raw</td><td>0.278519</td><td>5.8%</td></tr></table>

contributors for most series (t<sub>y</sub>picall<sub>y</sub> 2–4 proximit<sub>y</sub> features within the per-series top-10), reflectin<sub>g</sub> that nei<sub>g</sub>hborhood deviation si<sub>g</sub>nals are repeatedl<sub>y</sub> useful across diverse re<sub>g</sub>imes (e.<sub>g</sub>., trafic, operational metrics, and known-cause failures).

Global im ortance ex lains which si nals the model uses on avera e, whereas local ex lanations clarif why a s ecific times tamp rece<sup>i</sup>ves a <sup>hi</sup>g<sup>h</sup> ca<sup>lib</sup>rate<sup>d</sup> anoma<sup>l</sup>y pro<sup>b</sup>a<sup>bili</sup>ty. <sup>Si</sup>nce <sup>SHAP</sup> va<sup>l</sup>ues are compute<sup>d di</sup>rect<sup>l</sup>y on calib\_eval <sup>f</sup>or t<sup>h</sup>e ca<sup>lib</sup>rate<sup>d</sup> out ut, local attributions can be examined at an evaluation oint (includin around known NAB anomal intervals) to se arate (i) level/dispersion-driven evidence captured b<sub>y</sub> rollin<sub>g</sub> statistics from (ii) nei<sub>g</sub>hborhood-deviation evidence captured b<sub>y</sub> proximit<sub>y</sub> descri<sub>p</sub>tors. This calibrated-<sub>p</sub>robabilit<sub>y</sub> view su<sub>pp</sub>orts o<sub>p</sub>erational inter<sub>p</sub>retabilit<sub>y</sub>: the same ex<sub>p</sub>lanation s<sub>p</sub>ace that drives rankin<sub>g</sub> and bud<sub>g</sub>et-based decision rules also drives the <sub>p</sub>er-<sub>p</sub>oint narratives used durin<sub>g</sub> investi<sub>g</sub>ation.

## SHAP for SMD:

We next examine the inter retabilit of the ro osed detector on the Server Machine Dataset (SMD) usin SHa le Additive exPlanations (SHAP). In contrast to sin<sub>g</sub>le-stream benchmarks, SMD contains multiple hetero<sub>g</sub>eneous servers with distinct operatin<sub>g</sub> re<sub>g</sub>imes. To obtain a faithful <sub>g</sub>lobal ex<sub>p</sub>lanation while res<sub>p</sub>ectin<sub>g</sub> this hetero<sub>g</sub>eneit<sub>y,</sub> we ado<sub>p</sub>t the followin<sub>g</sub> strate<sub>gy</sub>: for each of the 28 series, we re-train the model on that series (leak-free, series-wise), compute SHAP values on an evaluation subset, sample 800 evaluation oints er series and then a re ate SHAP values across series to form a lobal summar . This a re ation revents an sin<sub>g</sub>le lon<sub>g</sub> or hi<sub>g</sub>h-variance stream from dominatin<sub>g</sub> the ex<sub>p</sub>lanation.

Fi . 8 re orts the a re ated SHAP beeswarm lot across 28 series. The dominant contributors are rollin statistical descri tors compute<sup>d</sup> per c<sup>h</sup>anne<sup>l</sup> (e.g., roll\_mean\_30\_x05, roll\_mean\_30\_x06, roll\_mean\_30\_x15), <sup>i</sup>n<sup>di</sup>cat<sup>i</sup>ng t<sup>h</sup>at me<sup>di</sup>um-<sup>h</sup>or<sup>i</sup>zon s<sup>hif</sup>ts <sup>i</sup>n local level remain the <sub>p</sub>rimar<sub>y</sub> drivers of anomal<sub>y p</sub>robabilit<sub>y</sub> in SMD. Proximit<sub>y</sub>-aware si<sub>g</sub>nals also a<sub>pp</sub>ear amon<sub>g</sub> the to<sub>p</sub> contributors<sub>,</sub> notabl and consistent with the role of nei hborhood deviation in ca turin de artures that are not full ex lained b univariate statistics. An additional hi h-rankin in ut is x04 ( rou ed as Other), reflectin that certain raw channels can carr direct discriminative si nal de endin on the server and metric (Table 9).

The to<sub>p</sub>-10 <sub>g</sub>lobal features b<sub>y</sub> mean absolute SHAP ma<sub>g</sub>nitude are:

x04 (<sup>0</sup>.<sup>1004</sup>),

roll\_mean\_30\_x05 (<sup>0</sup>.<sup>0772</sup>),

roll\_mean\_30\_x06 (<sup>0</sup>.<sup>0766</sup>),

roll\_mean\_30\_x15 (<sup>0</sup>.<sup>0754</sup>),

proto\_dist\_1 (<sup>0</sup>.<sup>0736</sup>),

roll\_mean\_5\_x00 (<sup>0</sup>.<sup>0627</sup>),

roll\_std\_30\_x13 (<sup>0</sup>.<sup>0582</sup>),

roll\_mean\_15\_x06 (<sup>0</sup>.<sup>0520</sup>),

roll\_std\_30\_x34 (<sup>0</sup>.<sup>0515</sup>),

an<sup>d</sup> prox\_level\_mu (<sup>0</sup>.<sup>0515</sup>).

At the feature-famil level, Statistical descri tors account for 76.38% of the total mean|SHAP|, followed b Other (12.73%), Proximit (7.17%) and Latent (3.71%). This rofile indicates that SMD anomalies are redominantl ex ressed as sustained distributional shifts h l hil i it d l t t t id l t id f h l ti i hb h d structure or more com ressed re resentations are informative.

![](images/92b298114000b798711b42aded8894d284930c17b1b78e69f5544e037813cacc.jpg)  
Fig. 8. SMD global SHAP summary aggregated from 28 series. SHAP values are aggregated from series-wise models using 800 evaluation samples per series. Each point corresponds to an evaluated timestamp; color encodes feature ma<sub>g</sub>nitude (low to hi<sub>g</sub>h), and the horizontal axis indicates si ned contribution to the model out ut.

To <sub>q</sub>uantif<sub>y</sub> whether the <sub>g</sub>lobal ex<sub>p</sub>lanation is consistent across servers<sub>,</sub> we com<sub>p</sub>ute series-level im<sub>p</sub>ortance rankin<sub>g</sub>s and com<sub>p</sub>are them a ainst the a re ated rankin . The mean S earman rank correlation is 0.5891 and the avera e to -5 overla is 0.69∕5. This i di d bili h d f i i l d i hil h h l l l d i i i h server-s ecific o eratin conditions and sensor semantics

In ractical terms, SMD benefits from a lobal inter retabilit narrative (rollin level/dis ersion shifts dominate), while root-cause anal<sub>y</sub>sis at the server level should still rel<sub>y</sub> on local attributions to identif<sub>y</sub> which channels and mechanisms are res<sub>p</sub>onsible in a <sub>g</sub>iven stream with the a re ate feature-famil contributions summarized in Table 10.

## 4.5.1. SHAP for UCR (Calibrated probability; leak-free calib\_eval)

To interpret the proposed detector beyond aggregate accuracy, we compute SHAP values on the deployment-like evaluation block (calib\_eval) o<sup>b</sup>ta<sup>i</sup>ne<sup>d</sup> v<sup>i</sup>a a er-ser<sup>i</sup>es, t<sup>i</sup>me-or<sup>d</sup>ere<sup>d</sup> t<sup>h</sup>ree-wa s <sup>li</sup>t (tra<sup>i</sup>n / calib\_fit / calib\_eval). <sup>I</sup>m ortant<sup>l</sup> , <sup>SHAP i</sup>s com uted on the model out ut ex ressed as (i.e. the ost-calibration anomal robabilit ) so feature attributions directl ex lain the final decision score used in thresholdin and bud et-based selection.

For UCR, the leak-free evaluation pool contains 2,386,845 points across 250 series, with 10,018 positives. To prevent long series from dominatin the ex lanation, we construct a series-balanced SHAP sam le with a tar et of ∼80 oints er series, ca ed at 20,000 total oints (resultin in with 100 ositives). Fi . 9 summarizes lobal feature efects.

A h l b l ki i i l d i d i h l i i f f h d b l SHAP while roximit features contribute a substantial 20.5% and raw si nal terms ex lain the remainin 2.9%. The to contributors

Table 9  
SMD to<sub>p</sub>-10 <sub>g</sub>lobal features b<sub>y</sub> mean absolute SHAP value (a<sub>gg</sub>re<sub>g</sub>ated from 28 series).

<table><tr><td>Feature</td><td>mean|SHAP|</td><td>Group</td></tr><tr><td>x04</td><td>0.100395</td><td>Other</td></tr><tr><td>roll_mean_30_x05</td><td>0.077171</td><td>Statistical</td></tr><tr><td>roll_mean_30_x06</td><td>0.076557</td><td>Statistical</td></tr><tr><td>roll_mean_30_x15</td><td>0.075419</td><td>Statistical</td></tr><tr><td>proto_dist_1</td><td>0.073640</td><td>Proximity</td></tr><tr><td>roll_mean_5_x00</td><td>0.062703</td><td>Statistical</td></tr><tr><td>roll_std_30_x13</td><td>0.058228</td><td>Statistical</td></tr><tr><td>roll_mean_15_x06</td><td>0.052011</td><td>Statistical</td></tr><tr><td>roll_std_30_x34</td><td>0.051520</td><td>Statistical</td></tr><tr><td>prox_level_mu</td><td>0.051466</td><td>Proximity</td></tr></table>

Table 10

SMD SHAP <sub>g</sub>roup contributions (sum of mean|SHAP|) and shares.

<table><tr><td>Group</td><td>Sum mean|SHAP|</td><td>Share</td></tr><tr><td>Statistical</td><td>1.630793</td><td>76.38%</td></tr><tr><td>Other</td><td>0.271878</td><td>12.73%</td></tr><tr><td>Proximity</td><td>0.153117</td><td>7.17%</td></tr><tr><td>Latent</td><td>0.079220</td><td>3.71%</td></tr></table>

Table 11

UCR SHAP <sub>g</sub>roup contributions (sum of mean|SHAP|) and percentage shares compute<sup>d</sup> on t<sup>h</sup>e <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree calib\_eval <sup>bl</sup>oc<sup>k</sup> (<sup>3</sup>- wa<sub>y</sub> split; local splitter).

<table><tr><td>Group</td><td>Sum mean|SHAP|</td><td>Share (%)</td></tr><tr><td>Statistical</td><td>3.871848</td><td>76.6</td></tr><tr><td>Proximity</td><td>1.036067</td><td>20.5</td></tr><tr><td>Raw</td><td>0.146547</td><td>2.9</td></tr></table>

b mean(|SHAP|) are (0.7098) (0.5283) (0.4544) (0.3982) (<sup>0</sup>.<sup>3676</sup>), proto\_dist\_1 (<sup>0</sup>.<sup>3496</sup>), roll\_std\_30

(<sup>0</sup>.<sup>3272</sup>), robust\_z\_200 (<sup>0</sup>.<sup>3260</sup>), pct\_change (<sup>0</sup>.<sup>2484</sup>), an<sup>d</sup> roll\_mean\_5 (<sup>0</sup>.<sup>1646</sup>). <sup>C</sup>o<sup>ll</sup>ect<sup>i</sup>ve<sup>l</sup>y, t<sup>hi</sup>s pro<sup>fil</sup>e <sup>i</sup>n<sup>di</sup>cates t<sup>h</sup>at t<sup>h</sup>e mo<sup>d</sup>e<sup>l</sup> rimaril res onds to robust local level and scale chan es (rollin median/mean, MAD/STD, robust z-scores), while the roximit <sup>bl</sup>oc<sup>k</sup> (prox\_level\_mu, proto\_dist\_1, an<sup>d</sup> re<sup>l</sup>ate<sup>d</sup> terms) prov<sup>id</sup>es a<sup>ddi</sup>t<sup>i</sup>ona<sup>l</sup> geometr<sup>i</sup>c ev<sup>id</sup>ence t<sup>h</sup>at systemat<sup>i</sup>ca<sup>ll</sup>y s<sup>hif</sup>ts ca<sup>lib</sup>rate<sup>d</sup> anomal <sub>p</sub>robabilit be ond what classical statistics alone ca<sub>p</sub>ture.

The UCR ex<sub>p</sub>lanation is also stable across series: the mean S<sub>p</sub>earman rank correlation between series-wise feature ranks and the global rank is 0.822 (median 0.829; � = 250 series). This indicates that, despite heterogeneity in signal morphology, the model relies on a consistent set of mechanisms across the benchmark. In articular roximit descri tors re eatedl a ear amon the to features in man<sub>y</sub> series<sub>,</sub> su<sub>pp</sub>ortin<sub>g</sub> the intended role of <sub>p</sub>roximit<sub>y</sub>-aware modelin<sub>g</sub> as a transferable com<sub>p</sub>lement to robust statistical chan<sub>g</sub>e descri tors under leak-free time-forward evaluation (Table 11).

## 4.5.2. Intel (Unlabeled): Distillation-SHAP for interpreting the proximity score

The Intel Berkele<sub>y</sub> Lab corpus is lar<sub>g</sub>el<sub>y</sub> unlabeled, which prevents label-driven local case studies (e.<sub>g</sub>., explainin<sub>g</sub> wh<sub>y</sub> a specific timestam is trul anomalous). Instead, we focus on ex lainin the internal proximity score that drives our detector in de lo ment. Concretel we a l a distillation-based SHAP anal sis: we train a li htwei ht surro ate model (Li htGBM re ressor) to mimic the learned roximit score l l usin only raw and statistical in uts and then com ute SHAP on a leak-free evaluation s lit.

Why proximity features do not appear in Intel SHAP: In this block, prox\_level\_mu is the distillation target. To avoid circular exp<sup>l</sup>anat<sup>i</sup>ons, we exp<sup>li</sup>c<sup>i</sup>t<sup>l</sup>y exc<sup>l</sup>u<sup>d</sup>e prox\_\*, proto\_\*, phi\_\*, an<sup>d</sup> knn\_\* <sup>f</sup>rom t<sup>h</sup>e surrogate <sup>i</sup>nputs (ant<sup>i</sup>-c<sup>i</sup>rcu<sup>l</sup>ar <sup>f</sup>eature <sup>fil</sup>ter<sup>i</sup>ng). Therefore SHAP is com uted over raw/statistical variables that drive the roximit score rather than the roximit features them selves. This desi n ensures that the attributions answer the intended uestion: which measurable sensorpatterns (raw and rolling statistics) make the proximity score increase or decrease?

UCR SHAP (Leak-free: calib\_eval (3-way, leak-free) [local splitter]) — series-balanced sample Hiah  
![](images/0af823aefa7edb7723ed5f4d857014daaf34e394d9569483ee8c74729760dc76.jpg)  
Fig. 9. UCR global SHAP summary on the leak-free calib\_eval block (3-way split; local splitter), using a series-balanced sample. SHAP values ex lain the calibrated anomal robabilit : oints to the ri ht (left) increase (decrease) the redicted anomal robabilit and color encodes the feature value (blue: low, red: hi<sub>g</sub>h).

Leak-free protocol and SHAP sampling: We enforce time causality by splitting each sensor node (24 nodes) in chronological or<sup>d</sup>er <sup>i</sup>nto a <sup>70%</sup> tra<sup>i</sup>n<sup>i</sup>ng pre<sup>fi</sup>x an<sup>d</sup> a <sup>30%</sup> ca<sup>lib</sup>rat<sup>i</sup>on <sup>bl</sup>oc<sup>k</sup>, w<sup>hi</sup>c<sup>h i</sup>s <sup>f</sup>urt<sup>h</sup>er sp<sup>li</sup>t <sup>i</sup>nto calib\_fit/calib\_eval (<sup>50</sup>/<sup>50</sup>). <sup>All fi</sup>tte<sup>d</sup> re rocessin (im utation statistics scalin PCA) is learned on the trainin refix onl an im utation on held-out blocks uses train-only medians. SHAP is computed post hoc on a node-balanced sample drawn from calib\_eval (total � = 1488, ≈ 62 points per node) reventin lon node traces from dominatin lobal im ortance. SHAP is used for inter retabilit onl and does not influence an<sub>y</sub> fittin<sub>g</sub> or o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oint selection

Global drivers of : Fi . 10 re orts the lobal SHAP summar for the distilled model under the leak free evaluation rotocol. The dominant contributors are volta e-related robust deviations and residual terms followed b illumination and humidit /tem erature rollin statistics. This attern is consistent with the intended semantics of : the roximit score rises when multi le sensor channels exhibit structured de artures from their recent baseline (robust �-scores residuals and short-horizon variabilit ), rather than reactin to raw levels in isolation. Since the dataset is unlabeled, we treat these results as an inter<sub>p</sub>retabilit<sub>y</sub> audit of the scorin<sub>g</sub> mechanism<sub>,</sub> not as a claim about <sub>g</sub>round-truth anomal<sub>y</sub> causation.

![](images/6b2d10b6e26d0a8e3fcee87de2b0d22f64792a9a83a55b90edc77d52962237c7.jpg)  
Fig. 10. Intel Distillation-SHAP summary on the leak-free evaluation block, balanced by node. The surrogate model predicts prox\_level\_mu using on<sup>l</sup>y raw and statistica<sup>l f</sup>eatures (no prox/phi/knn/proto) to avoid circu<sup>l</sup>ar attri<sup>b</sup>utions.

## 5. Discussion

## 5.1. What the results mean

The results should be interpreted through the manuscript’s deployment objective: reliable ranking and fixed-budget alerting under <sup>d</sup>r<sup>if</sup>t, extreme <sup>i</sup>m<sup>b</sup>a<sup>l</sup>ance, an<sup>d</sup> constra<sup>i</sup>ne<sup>d</sup> com ute, eva<sup>l</sup>uate<sup>d</sup> un<sup>d</sup>er a str<sup>i</sup>ct<sup>l l</sup>ea<sup>k</sup>a e-sa<sup>f</sup>e re <sup>i</sup>me (tra<sup>i</sup>n / calib\_fit / calib\_eval). Under this objective, three consistent patterns emerge.

PR-oriented ranking strength on NAB and SMD: On NAB, the proposed framework attains the strongest pooled PR–AUC (0.359) un<sup>d</sup>er po<sup>i</sup>ntw<sup>i</sup>se eva<sup>l</sup>uat<sup>i</sup>on on calib\_eval (<sup>T</sup>a<sup>bl</sup>e <sup>4</sup>), an<sup>d i</sup>t y<sup>i</sup>e<sup>ld</sup>s a conservat<sup>i</sup>ve <sup>b</sup>ut operat<sup>i</sup>ona<sup>ll</sup>y c<sup>l</sup>ean a<sup>l</sup>ert<sup>i</sup>ng reg<sup>i</sup>me at a <sup>1%</sup> budget (PR@1%= 1.000, R@1%= 0.061). On SMD, the proposed method achieves the strongest PR–AUC (0.500) (Table 3), indicating im<sub>p</sub>roved <sub>g</sub>lobal orderin<sub>g</sub> of <sub>p</sub>ositives in a multivariate<sub>,</sub> hetero<sub>g</sub>eneous telemetr<sub>y</sub> settin<sub>g</sub>. These outcomes ali<sub>g</sub>n with the desi<sub>g</sub>n choice to fuse multi<sub>p</sub>le train-referenced <sub>p</sub>roximit<sub>y</sub> cues under rollin<sub>g</sub> robust stabilization: the detector is o<sub>p</sub>timized to <sub>p</sub>roduce stable rankin<sub>g</sub>s under drift and heav<sub>y</sub>-tailed noise<sub>,</sub> where PR-based summaries are more re<sub>p</sub>resentative of o<sub>p</sub>erational utilit<sub>y</sub> than ROC-based summaries [32,33].

Trade-ofs at fixed budgets and on UCR scale: The evaluation explicitly separates ranking metrics (ROC–AUC/PR–AUC) from policy-driven fixed-budget behavior (PR@1%, R@1%). This separation matters in practice: a method can achieve a favorable PR– AUC while bein<sub>g</sub> less com<sub>p</sub>etitive at a s<sub>p</sub>ecific ti<sub>g</sub>ht bud<sub>g</sub>et<sub>,</sub> and the reverse can hold for heav<sub>y</sub>-tail detectors that concentrate alarms on ex<sup>t</sup>reme po<sup>i</sup>n<sup>t</sup>s. <sup>O</sup>n <sup>SMD</sup>, <sup>I</sup>so<sup>l</sup>a<sup>ti</sup>on<sup>F</sup>ores<sup>t</sup> a<sup>tt</sup>a<sup>i</sup>ns <sup>hi</sup>g<sup>h</sup>er <sup>PR</sup>@<sup>1%</sup> an<sup>d R</sup>@<sup>1%</sup> a<sup>t th</sup>e <sup>1% b</sup>u<sup>d</sup>ge<sup>t</sup>, w<sup>hil</sup>e our me<sup>th</sup>o<sup>d</sup> a<sup>tt</sup>a<sup>i</sup>ns <sup>hi</sup>g<sup>h</sup>er PR–AUC. This is a <sub>g</sub>enuine o<sub>p</sub>eratin<sub>g</sub> trade-of rather than an inconsistenc<sub>y</sub>: it reflects diferent scorin<sub>g g</sub>eometries and how the<sub>y</sub> interact with an alarm-rate constraint. On UCR, where the benchmark is intentionall<sub>y</sub> hostile (hetero<sub>g</sub>eneous series, extreme sparsit<sub>y</sub>, ≈15.9M oints), absolute PR–AUC values are small across methods (Table 5). In this re ime, sha e-based scorin (Matrix Profile) improves ROC–AUC, while the proposed method improves budgeted alerting quality (PR@1% and R@1%) with tractable runtime. The a<sub>pp</sub>ro<sub>p</sub>riate conclusion is therefore de<sub>p</sub>lo<sub>y</sub>ment-oriented: the <sub>p</sub>ro<sub>p</sub>osed framework <sub>p</sub>rovides a favorable Pareto <sub>p</sub>oint for bud<sub>g</sub>eted screenin<sub>g</sub> at scale<sub>,</sub> rather than uniform dominance on all <sub>g</sub>lobal metrics.

Intel is a triage validation, not an accuracy claim: Intel Berkele Lab telemetr is unlabeled. We therefore avoid an su ervised detection claims on Intel and instead evaluate de lo ment tria e utilit under a fixed alert bud et usin leak-free threshold transfer and the Com osite Tria e Score (CTS) defined in Section 2.7. The hi hest CTS is achieved b the ro osed invMAD-wei hted ProxFuse variant with calibration-transfer components (Table 6), reflectin<sub>g</sub> a balanced operational profile across covera<sub>g</sub>e, cross-split stabilit<sub>y</sub>, concentration<sub>,</sub> event duration<sub>,</sub> and runtime. This evidence su orts the intended role of Intel in the stud : demonstratin that the calibrated<sub>,</sub> bud<sub>g</sub>eted scorin<sub>g</sub> mechanism <sub>y</sub>ields non-de<sub>g</sub>enerate and o<sub>p</sub>erationall<sub>y p</sub>lausible alert <sub>p</sub>atterns under realistic missin<sub>g</sub>ness and lon<sub>g</sub>-duration streams<sub>,</sub> without overstatin<sub>g g</sub>round-truth detection <sub>p</sub>erformance.

## 5.2. Transformer baselines: Why compute budget matters

Transformer forecaster residual baselines (Informer iTransformer PatchTST) are included as contem orar references where computat<sup>i</sup>ona<sup>ll</sup>y <sup>f</sup>eas<sup>ibl</sup>e, eva<sup>l</sup>uate<sup>d</sup> un<sup>d</sup>er an exp<sup>li</sup>c<sup>i</sup>t compute po<sup>li</sup>cy (max\_steps=<sup>100</sup> w<sup>i</sup>t<sup>h f</sup>a<sup>il</sup>-so<sup>f</sup>t <sup>f</sup>a<sup>llb</sup>ac<sup>k</sup>) an<sup>d</sup> t<sup>h</sup>e same <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree calibration/threshold <sub>p</sub>rotocol. Two observations motivate this desi<sub>g</sub>n choice.

First the wall-clock s read is multi-order-of-ma nitude. Even with bounded ste s forecaster residual i elines can be substantiall slower than proximity-based scoring, and they can become vulnerable to long-job interruption in constrained environments. This is visible on NAB and SMD where transformer residual runtimes are orders of ma nitude lar er than the ro osed a roach (Tables 3 and 4). Second, compute bud<sub>g</sub>ets afect the realized model qualit<sub>y</sub> of forecasters; a bounded trainin<sub>g</sub> schedule is an operational realit for man de lo ments and should be reflected in ex erimental com arisons. Accordin l <sub>,</sub> we inter ret transformer baselines as com<sub>p</sub>ute-bounded references rather than unconstrained state-of-the-art trainin<sub>g</sub> runs. Under this inter<sub>p</sub>retation<sub>,</sub> the results su<sub>pp</sub>ort a ractical conclusion: the ro osed method can match or exceed PR-oriented rankin ualit while maintainin a redictable runtime <sub>p</sub>rofile that is com<sub>p</sub>atible with continuous monitorin<sub>g</sub>.

## 5.3. Deployment guidance

The framework is desi<sub>g</sub>ned to be actionable under limited su<sub>p</sub>ervision and fixed review ca<sub>p</sub>acit<sub>y</sub>. The followin<sub>g g</sub>uidance summa rizes how the re<sub>p</sub>orted <sub>p</sub>rotocol translates to de<sub>p</sub>lo<sub>y</sub>ment.

Selecting an alarm budget: The alert budget � encodes operational review capacity (fraction of points flagged per stream). In this stud <sub>,</sub> we use $q = 1 \%$ as a representative ti ht-bud et re ime and report bud et sweeps on NAB and SMD (Section 5.3). In <sup>d</sup>ep<sup>l</sup>oymen<sup>t</sup>, � s<sup>h</sup>ou<sup>ld b</sup>e c<sup>h</sup>osen v<sup>i</sup>a a capac<sup>it</sup>y-<sup>d</sup>r<sup>i</sup>ven <sup>b</sup>u<sup>d</sup>ge<sup>t</sup> sweep: s<sup>t</sup>ar<sup>t</sup> w<sup>ith</sup> a conserva<sup>ti</sup>ve range $( \mathbf { e } . \mathbf { g } . , q \in [ 0 . 1 \% , 1 \% ] )$ when false alarms are costl<sub>y,</sub> then ex<sub>p</sub>and toward moderate bud<sub>g</sub>ets $( \mathbf { e } . \mathbf { g } . , q \in [ 1 \% , 5 \% ] )$ when the <sub>g</sub>oal is broader covera<sub>g</sub>e and hi<sub>g</sub>her recall. The tie-safe exact to -� rule used here is recommended when scores are uantized or when ties are fre uent since it revents unstable thresholdin<sub>g</sub>.

Calibration when labels exist: On labeled benchmarks isotonic re ression is used as a monotone calibrator trained strictl on calib\_fit an<sup>d</sup> app<sup>li</sup>e<sup>d</sup> unc<sup>h</sup>ange<sup>d</sup> to calib\_eval. <sup>Thi</sup>s separat<sup>i</sup>on <sup>i</sup>s essent<sup>i</sup>a<sup>l</sup>: <sup>fi</sup>tt<sup>i</sup>ng ca<sup>lib</sup>rat<sup>i</sup>on or c<sup>h</sup>oos<sup>i</sup>ng an operat<sup>i</sup>ng po<sup>i</sup>nt on h bl k d f i i fl f I i l i h l b l i i h d l lib i h ld be u dated onl on ast labeled se ments and validated on a held-out block that simulates future data. If the calibration-fit block contains a sin<sub>g</sub>le class (rare anomalies), the identit<sub>y</sub> fallback is a safe option that preserves leak-freedom and avoids ill-posed fits.

Unlabeled fleets and triage: When labels are unavailable (Intel-like settings), label-free score normalization (e.g., ECDF/ChECDF) can still be used for screenin and rioritization under a fixed bud et<sub>,</sub> combined with stabilit and concentration checks. The CTS com<sub>p</sub>onents <sub>p</sub>rovide a <sub>p</sub>ractical audit: broad covera<sub>g</sub>e<sub>,</sub> stable node rankin<sub>g</sub> across time blocks<sub>,</sub> low alert concentration<sub>,</sub> non-de<sub>g</sub>enerate event durations<sub>,</sub> and bounded runtime. This o<sub>p</sub>erational lens hel<sub>p</sub>s distin uish methods that enerate su<sub>p</sub>erficiall hi h scores from those that <sub>y</sub>ield actionable screenin<sub>g</sub> behavior.

Edge/streaming execution: The method is series-local and naturally streaming compatible: preprocessing and embedding are train-onl rollin -MAD scalin is causal and scorin can be roduced er timestam . Peak memor is controlled b rocessin streams independentl<sub>y</sub> (manifest/parts workflow). The dominant computational term is train-referenced nei<sub>g</sub>hborhood quer<sub>y</sub>in<sub>g</sub>; deplo<sub>y</sub>ments with strict latenc<sub>y</sub> constraints should consider a<sub>pp</sub>roximate nearest-nei<sub>g</sub>hbor indexin<sub>g</sub> built on the fixed trainin<sub>g</sub> reference<sub>,</sub> which reserves the leak-free ro ert as lon as the index is constructed usin ast data onl (Section 2.8).

## 5.4. Limitations and future work

The stud<sub>y</sub> has several limitations that <sub>p</sub>oint to concrete future directions.

Score construction and multiscale structure: Rollin -MAD stabilization is a lied to a sin le embeddin coordinate and the proximity cues operate at a fixed embedding dimension (� = 3). While this choice improves robustness and feasibility, it can miss multiscale anomal<sub>y</sub> si<sub>g</sub>natures or re<sub>g</sub>ime-dependent temporal structure. Extensions could incorporate multiscale proximit<sub>y</sub> (multiple window sizes and scale channels) and explicit chan<sub>g</sub>e-point awareness to better separate abrupt transitions from persistent drift.

Scalability of train-referenced neighborhoods: The computational bottleneck is the train-referenced neighborhood queries. <sup>Whil</sup>e ser<sup>i</sup>es-<sup>l</sup>oca<sup>l</sup> process<sup>i</sup>ng <sup>b</sup>oun<sup>d</sup>s memory, �<sup>NN</sup> quer<sup>i</sup>es <sup>d</sup>om<sup>i</sup>na<sup>t</sup>e run<sup>ti</sup>me <sup>f</sup>or <sup>l</sup>ong s<sup>t</sup>reams. <sup>F</sup>u<sup>t</sup>ure wor<sup>k i</sup>nc<sup>l</sup>u<sup>d</sup>es approx<sup>i</sup>ma<sup>t</sup>e or incremental variants: a<sub>pp</sub>roximate nearest-nei hbor indices<sub>, p</sub>rotot <sub>p</sub>e-based com<sub>p</sub>ression of the trainin reference<sub>,</sub> and controlled reference refresh schedules that remain strictl time-forward.

Benchmark coverage and evaluation semantics: Intel is unlabeled and is used for triage validation; supervised accuracy can not be assessed there. On NAB<sub>,</sub> the main tables re<sub>p</sub>ort <sub>p</sub>ointwise <sub>p</sub>ooled metrics under a bud<sub>g</sub>et <sub>p</sub>olic<sub>y,</sub> while NAB also su<sub>pp</sub>orts event-window scorin<sub>g</sub>. Ex<sub>p</sub>andin<sub>g</sub> the evaluation to additional industrial multivariate datasets with dense labels<sub>,</sub> and re<sub>p</sub>ortin<sub>g</sub> com lementar event-based scorin views where a ro riate<sub>,</sub> would stren then covera e across annotation conventions and de lo ment regimes.

Calibration under distribution shift: Calibration is label-dependent and can degrade under major distribution shifts. The present <sub>p</sub>rotocol enforces leak-freedom and demonstrates stable behavior across the evaluation blocks<sub>, y</sub>et real de<sub>p</sub>lo<sub>y</sub>ments ma<sub>y</sub> re<sub>q</sub>uire <sub>p</sub>eri odic recalibration on recent labeled data (when available), to<sub>g</sub>ether with drift monitorin<sub>g</sub> and reliabilit<sub>y</sub> dia<sub>g</sub>nostics (e.<sub>g</sub>., calibration curves over time blocks).

Threats to validit<sub>y p</sub>rimaril<sub>y</sub> include tem<sub>p</sub>oral leaka<sub>g</sub>e<sub>,</sub> tunin<sub>g</sub> bias in o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oint selection<sub>,</sub> and runtime com<sub>p</sub>arabilit<sub>y</sub> across methods. We miti<sub>g</sub>ate these risks via per-series chronolo<sub>g</sub>ical splits, train-onl<sub>y</sub> calibration and threshold learnin<sub>g</sub> (applied unchan<sub>g</sub>ed to calib\_eval), an<sup>d fi</sup>xe<sup>d</sup> compute po<sup>li</sup>c<sup>i</sup>es w<sup>i</sup>t<sup>h</sup> wa<sup>ll</sup>-c<sup>l</sup>oc<sup>k</sup> en<sup>d</sup>-to-en<sup>d</sup> runt<sup>i</sup>me report<sup>i</sup>ng on <sup>id</sup>ent<sup>i</sup>ca<sup>l h</sup>ar<sup>d</sup>ware. <sup>R</sup>ema<sup>i</sup>n<sup>i</sup>ng <sup>dif</sup>er ences reflect inherent method cost <sub>p</sub>rofiles and are inter<sub>p</sub>reted throu<sub>g</sub>h Pareto and bud<sub>g</sub>et-swee<sub>p</sub> anal<sub>y</sub>ses rather than sin<sub>g</sub>le-metric claims.

## 6. Conclusion

We resent a de lo ment-oriented anomal detection framework for non-stationar time series that inte rates: (i) a train referenced ada tive score formed b fusin com lementar normalized membershi cues (level de arture a densit cue with a safe fallback, velocit<sub>y</sub> in embeddin<sub>g</sub>-increment space, and protot<sub>y</sub>pe distance), (ii) rollin<sub>g</sub>-MAD stabilization for robustness under drift and heav -tailed noise and (iii) leak-free decision makin with train-onl fittin isotonic calibration on and fixed <sup>b</sup>u<sup>d</sup> et t<sup>h</sup>res<sup>h</sup>o<sup>ld</sup> trans<sup>f</sup>er to calib\_eval. <sup>E</sup>va<sup>l</sup>uat<sup>i</sup>on <sup>i</sup>s str<sup>i</sup>ct<sup>l l</sup>ea<sup>k</sup>a e-sa<sup>f</sup>e an<sup>d</sup> ser<sup>i</sup>es-w<sup>i</sup>se, ex <sup>li</sup>c<sup>i</sup>t<sup>l</sup> se arat<sup>i</sup>n score <sup>f</sup>ormat<sup>i</sup>on, calibration and o<sub>p</sub>eratin<sub>g</sub>-<sub>p</sub>oint selection<sub>,</sub> and final re<sub>p</sub>ortin<sub>g</sub>.

Across three labeled benchmarks (NAB, SMD, UCR) and one unlabeled deplo<sub>y</sub>ment tria<sub>g</sub>e corpus (Intel Berkele<sub>y</sub> Lab), the method rovides consistent evidence of ractical utilit . On NAB and SMD it achieves the stron est PR–AUC under the leak-free rotocol while bud eted metrics ex ose meanin ful o eratin trade-ofs a ainst classical baselines at ti ht bud ets. On UCR at scale<sub>,</sub> it delivers a favorable bud eted screenin oint with tractable runtime<sub>,</sub> even when alternatives achieve hi her ROC–AUC. On unlabeled Intel telemetr<sub>y,</sub> we avoid su<sub>p</sub>ervised accurac<sub>y</sub> claims and instead demonstrate o<sub>p</sub>erational screenin<sub>g</sub> value under a fixed alert bud<sub>g</sub>et usin<sub>g</sub> CTS-based tria<sub>g</sub>e criteria<sub>,</sub> com<sub>p</sub>lemented b<sub>y</sub> distillation-based inter<sub>p</sub>retabilit<sub>y</sub> audits of the <sub>p</sub>roximit<sub>y</sub> score.

Overall the contribution is a cohesive com ute-feasible i eline that roduces de lo able anomal scores and calibrated rob abilities under strict leak-free evaluation<sub>,</sub> su<sub>pp</sub>orts fixed-bud<sub>g</sub>et o<sub>p</sub>eratin<sub>g p</sub>olicies<sub>,</sub> and <sub>p</sub>rovides ali<sub>g</sub>ned inter<sub>p</sub>retabilit<sub>y</sub> throu<sub>g</sub>h SHAP-based anal<sub>y</sub>ses. The results motivate <sub>p</sub>roximit<sub>y</sub>-based ada<sub>p</sub>tive scorin<sub>g</sub> as a <sub>p</sub>ractical alternative to com<sub>p</sub>ute-heav<sub>y</sub> forecaster residual i elines in continuous monitorin and the identif clear future directions in multiscale roximit chan e- oint awareness and scalable nei<sub>g</sub>hborhood a<sub>pp</sub>roximations for lar<sub>g</sub>e fleets and lon<sub>g</sub>-duration streams.

## Data availability statement

The datasets used in this stud are ublicl available from their ori inal sources: the Numenta Anomal Benchmark (NAB) [5] the Server Machine Dataset (SMD) [40] the UCR Time Series Anomal Archive [41 42] and the Intel Berkele Research Lab sensor telemetr [7]. No new ro rietar dataset is introduced.

To su ort re roducibilit we rovide as su lementar materials the scri ts to download and re rocess the data construc er-ser<sup>i</sup>es <sup>l</sup>ea<sup>k</sup>-<sup>f</sup>ree tra<sup>i</sup>n/calib\_fit/calib\_eval s <sup>li</sup>ts, re ro<sup>d</sup>uce a<sup>ll</sup> ta<sup>bl</sup>es/<sup>fi</sup> ures, an<sup>d</sup> env<sup>i</sup>ronment sna s<sup>h</sup>ots (<sup>i</sup>nc<sup>l</sup>u<sup>di</sup>n a <sup>f</sup>u<sup>ll</sup> pip freeze), raw <sup>d</sup>ata are o<sup>b</sup>ta<sup>i</sup>ne<sup>d f</sup>rom t<sup>h</sup>e or<sup>i</sup>g<sup>i</sup>na<sup>l</sup> sources un<sup>d</sup>er t<sup>h</sup>e<sup>i</sup>r respect<sup>i</sup>ve <sup>li</sup>censes.

## CRediT authorship contribution statement

Ebubekir <sup>˙</sup>Inan: Writing – review & editing, Writing – original draft, Visualization, Validation, Software, Resources, Methodology, Formal anal<sub>y</sub>sis<sub>,</sub> Data curation<sub>,</sub> Conce<sub>p</sub>tualization.

## Data availability

Public datasets (NAB, Intel Berkele<sub>y</sub> Lab, UCR, KPI). We do not redistribute; repo/SI provide scripts to download ori<sub>g</sub>inals plus leaka<sub>g</sub>e-safe s<sub>p</sub>lits<sub>,</sub> OOF calibration<sub>,</sub> and artifacts.

## Declaration of competing interest

The author declares that he has no known com<sub>p</sub>etin<sub>g</sub> financial interests or <sub>p</sub>ersonal relationshi<sub>p</sub>s that could have influenced the work re<sub>p</sub>orted in this <sub>p</sub>a<sub>p</sub>er.

Appendix A. Algorithmic summary of the leakage-safe adaptive proximity pipeline

## A.1. Notation and split policy

For each series<sub>,</sub> sam les are rocessed chronolo icall and s lit into conti uous blocks: train refix $X _ { \mathrm { t r } }$ (70%), calibration-fit $X _ { \mathrm { c f } }$ (15%) and calibration-eval $X _ { \mathrm { c e } }$ (15%). All fittin (causal feature en ineerin im utation scalin PCA roximit construction supervised head training, probability calibration, and operating-point learning) is restricted to the appropriate train-only or calib\_fit only segment, and then applied unchanged to $X _ { \mathrm { c e } }$ (strictl<sub>y</sub> out-of-sample). We use a fixed alert bud<sub>g</sub>et � (default $q = 1 \% )$ learned on $X _ { \mathrm { c f } }$ via deterministic exact top-� selection (ar<sub>g</sub>partition-based in the implementation).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 A1. Causal feature engineering and timestamp hygiene (per series).

Require: Raw series $\{(t_i, x_i)\}_{i=1}^n$ (timestamps and values), windows $\mathcal{W} = \{5, 15, 30\}$, robust-z window $w_z$ (default 200).

Ensure: Feature matrix $\Phi \in \mathbb{R}^{n \times p}$ with causal rolling statistics.

1: Sort samples by timestamp $t_i$ ascending (stable).

2: Timestamp uniqueness (recommended): if duplicate timestamps exist, make them unique by adding deterministic nanosecond offsets within each duplicate group (preserves chronological order).

3: for all $u \in \mathcal{W}$ do

4: Compute causal rolling mean, std, median on $\{x_{i-u+1}, \ldots, x_i\}$ with minimum periods $\max(2, \lfloor u/3 \rfloor)$.

5: Compute causal rolling MAD on the same window: $\text{MAD}(S) = \text{median}(|S - \text{median}(S)|)$.

6: end for

7: First differences: $\Delta x_i \leftarrow x_i - x_{i-1}$, $\Delta^2 x_i \leftarrow x_i - x_{i-2}$.

8: Percent change: $\text{pct}_i \leftarrow (x_i - x_{i-1}) / (|x_{i-1}| + \epsilon)$ and map $\pm\infty \mapsto \text{NaN}$.

9: Causal robust z-score:

$z_i \leftarrow \frac{x_i - \text{median}(x_{i-w_z+1:i})}{1.4826 \cdot \text{MAD}(x_{i-w_z+1:i})}$,

where the rolling MAD is computed causally; forward-fill the MAD for initial stability and apply a small floor if needed.

10: Assemble $\Phi(i)$ by concatenating rolling features, differences, percent change, and $z_i$.

11: return $\Phi$
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 A2. ProxFuse proximity features (Leak-free, per series).

Require: Feature stream $\Phi(t) \in \mathbb{R}^p$ (time-ordered), split blocks ($X_{\text{tr}}, X_{\text{cf}}, X_{\text{ce}}$), FFILL limit $L$ (default 5), scaler and PCA (target dim $d = 3$), rolling-MAD window $W$, $k_{\text{MAD}}$, kNN size $K$, HDBSCAN option with safe fallback.

Ensure: Proximity feature-augmented outputs: prox_level_mu, prox_level_outlier, prox_velocity_mu, proto_dist_1.

1: Causal sanitization: forward-fill $\Phi(\cdot)$ with limit $L$ in time order; replace $\pm\infty$ with NaN; do not backfill.

2: Train-median imputation (fit on $X_{\text{tr}}$ only): compute per-feature medians on $X_{\text{tr}}$; fill NaNs in all blocks with these medians (all-NaN median $\rightarrow 0$).

3: Train-only standardization: fit scaler on $X_{\text{tr}}$; transform all blocks.

4: Train-only PCA embedding: fit PCA on $X_{\text{tr}}$ with $d' = \min(d, \#rows, \#features)$; transform all blocks to $Z(t) \in \mathbb{R}^{d'}$; pad with zeros to 3 dims ($\phi_1(t), \phi_2(t), \phi_3(t)$) if $d' &lt; 3$.

5: Let $n_{\text{tr}} = |X_{\text{tr}}|$, and define $Z_{\text{tr}} = \{Z(t) : t \in X_{\text{tr}}\}$.

6: Train-referenced KNN mean distance: for each $t$, compute mean KNN distance from $Z(t)$ to $Z_{\text{tr}}$ (for train points, use a train-internal KNN reference; for all points, use $Z_{\text{tr}}$ as the reference set), yielding knn_mean($t$).

7: Adaptive causal scale (rolling MAD on $\phi_1$): compute rolling $\text{MAD}_W(\phi_1(t))$ causally; set $\varepsilon_t \leftarrow \max(10^{-6}, k_{\text{MAD}} \cdot \text{MAD}_W(\phi_1(t)))$ with train-median fallback for NaNs.

8: Level membership (distance-to-scale): $\mu_{\text{level}}(t) \leftarrow 1 - \exp(-k_{\text{mn\_mean}}(t)/(\varepsilon_t + \delta))$; apply train-only min-max scaling (fit on $X_{\text{tr}}$) and store as prox_level_mu.

9: Level outlier cue (density): if HDBSCAN is enabled and $n_{\text{tr}}$ is large enough, fit HDBSCAN on $Z_{\text{tr}}$ and take train outlier scores; otherwise fallback to knn_mean on train. For non-train points, use knn_mean as the outlier proxy. Apply train-only min-max scaling and store as prox_level_outlier.

10: Velocity cue: compute increments $\Delta Z(t) = Z(t) - Z(t-1)$ (zero at the first point); compute train-referenced KNN mean distances in $\Delta Z$ space; apply train-only min-max scaling and store as prox_velocity_mu.

11: Prototype distance: let proto = median($Z_{\text{tr}}$) (component-wise); compute $d_1(t) = \|Z(t) - proto\|_2$; apply train-only min-max scaling and store as proto_dist_1.

12: return proximity-augmented series frame
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 A3. Leak-free supervised head, train-only isotonic calibration, exact top-k budget policy, metrics, and Intel triage.

Require: For each labeled series: feature set (including proximity features), labels  $y(t) \in \{0,1\}$  on  $X_{cf} \cup X_{ce}$ . Budget q (default 1%), bootstrap replicates  $N_{boot}$  (default 500). For Intel (unlabeled): core score or proximity-based operating score only.

Ensure: Deployed decision score and evaluation under strict out-of-sample protocol.

1: Stable ids (recommended for mapping): assign __row_id__ over the full pooled table. Reset  $X_{cf}$  to assign __cf_id__ and  $X_{ce}$  to assign __ce_id__. (Used to avoid timestamp collisions when mapping per-series scorers.)

2: (Labeled) Supervised head (train-only): train LightGBM on  $X_{tr}$  using the selected numeric feature columns (excluding label, series_id, ids). Obtain raw probabilities  $\hat{p}_{cf}$  on  $X_{cf}$  and  $\hat{p}_{ce}$  on  $X_{ce}$ .

3: (Labeled) Probability calibration (calib_fit-only): if y on  $X_{cf}$  contains both classes, fit isotonic regression g on ( $\hat{p}_{cf}, y_{cf}$ ); otherwise set g to identity (single-class fallback). Define deployed score  $p_b(t) \leftarrow g(\hat{p}(t))$  and apply unchanged to  $X_{ce}$ .

4: (Operating point learned on  $X_{cf}$ ):  $k_{fit} \leftarrow \lceil q \cdot |X_{cf}| \rceil$ ; select the indices of the top- $k_{fit}$  values of  $p_b$  on  $X_{cf}$  (deterministic exact top-k); report  $\tau_{fit}$  as the minimum selected score.

5: (Evaluation on  $X_{ce}$ ): apply the same  $k_{fit}$  by selecting exact top- $k_{fit}$  on  $X_{ce}$ . Compute ROC-AUC and PR-AUC on  $p_b(t)$  over  $X_{ce}$  (when both classes are present), and compute PR@q and R@q from the top- $k_{fit}$  alarm set.

6: (Uncertainty): compute CI95 via series-aware bootstrap: resample complete series with replacement, recompute pooled metrics, and report quantiles [0.025, 0.975]. Optionally compute paired Δ-CI95 on matched resamples.

7: (Intel unlabeled triage): disable the supervised head and do not claim supervised performance. Use the operating score and fit a label-free normalizer (ECDF/ChECDF) on  $X_{cf}$ ; transfer it unchanged to  $X_{ce}$ . Under the same budget q, select top- $k_{fit}$  alarms on  $X_{ce}$  and report triage statistics (coverage, stability, concentration, and event characteristics), alongside representative classical scorers.

8: return Reported metrics (labeled) or triage statistics (Intel), all under strict leak-free transfer.
</div>

## References

[1] A. Chatterjee, B.S. Ahmed, IoT anomaly detection methods and applications: a survey, Internet Things 19 (2022) 100568. https://doi.org/10.1016/j.iot.2022. 100568

[2] C.C. A arwal, An introduction to outlier anal sis, Commun ACM 65 (1) (2022) 80–90. https://doi.or /10.1145/3439950

[3] A L i S Ah d E l ti l ti l d t ti l ith th t l b h k i P IEEE 14th I t ti l C f Machine Learnin and A lications (ICMLA) Miami FL USA 2015 . 38–44. htt s://doi.or /10.1109/ICMLA.2015.141

[4] S. Ahmad A. Lavin S. Purd Z. A ha Unsu ervised real-time anomal detection for streamin data Neurocom utin 262 (2017) 134–147. htt s://doi.or / 10.1016/j.neucom.2017.04.070

[5] Numenta, Numenta anomal<sub>y</sub> benchmark (NAB) repositor<sub>y</sub>, 2026 GitHub. Available at,https://<sub>g</sub>ithub.com/numenta/NAB.

[6] S. Schmidl, P. Weni<sub>g</sub>, T. Papenbrock, Anomal<sub>y</sub> detection in time series: a comprehensive evaluation, Proc. VLDB Endowment 15 (2022) 1779–1797. https: //doi.or /10.14778/3538598.3538602

<sup>[7] P</sup>. <sup>B</sup>o<sup>dík</sup>, <sup>W</sup>. <sup>H</sup>ong, <sup>C</sup>. <sup>G</sup>ues<sup>t</sup>r<sup>i</sup>n, <sup>S</sup>. <sup>M</sup>a<sup>dd</sup>en, <sup>M</sup>. <sup>P</sup>as<sup>ki</sup>n, <sup>R</sup>. <sup>Thib</sup>aux, <sup>I</sup>n<sup>t</sup>e<sup>l b</sup>er<sup>k</sup>e<sup>l</sup>ey researc<sup>h l</sup>a<sup>b</sup> sensor <sup>d</sup>a<sup>t</sup>a, <sup>k</sup>agg<sup>l</sup>e <sup>d</sup>a<sup>t</sup>ase<sup>t 2026</sup>, ava<sup>il</sup>a<sup>bl</sup>e a<sup>t</sup>: <sup>htt</sup>ps:<sup>//</sup>www. ka le.com/datasets/div ansh22/intel-berkele -research-lab-sensor-data/data.

[8] M. Breuni H.-P. Krie el R. N J. Sander LOF: identif in densit -based local outliers SIGMOD Rec. 29 (2) (2000) 93–104. htt s://doi.or /10.1145/342009 335388

[9] B. Schölko f J.C. Platt J. Shawe-Ta lor A.J. Smola R.C. Williamson Estimatin the su ort of a hi h-dimensional distribution Neural Com ut. 13 (7) (2001) 1443–1471. htt s://doi.or /10.1162/089976601750264965

[10] F.T. Liu, K.M. Tin<sub>g</sub>, Z.-H. Zhou, Isolation forest. Ei<sub>g</sub>hth IEEE International Conference on Data Minin<sub>g</sub>, 2008, 413–422. htt<sub>p</sub>s://doi.or<sub>g</sub>/10.1109/ICDM.2008.17

[11] J. Li, H. Izakian, W. Pedr<sub>y</sub>cz, I. Jamal, Clusterin<sub>g</sub>-based anomal<sub>y</sub> detection in multivariate time series data, Appl. Soft Comput. 100 (2021) 106919. https: //doi.or /10.1016/j.asoc.2020.106919

[12] P. Malhotra A. Ramakrishnan G. Anand L. Vi P. A arwal G. Shrof LSTM-based encoder-decoder for multi-sensor anomal detection 2016 htt s://arxiv. or<sub>g</sub>/abs/1607.00148.

[13] M. Munir, S.A. Siddi ui, A. Den el, S. Ahmed, Dee AnT: a dee learnin a roach for unsu ervised anomal detection in time series, IEEE Access 7 (2019) 1991–2005. htt<sub>p</sub>s://doi.or<sub>g</sub>/10.1109/ACCESS.2018.2886457

[14] H. Xu, W. Chen, N. Zhao, Z. Li, J. Bu, Z. Li, Y. Liu, Y. Zhao, D. Pei, Y. Fen<sub>g</sub>, J. Chen, Z. Wan<sub>g</sub>, H. Qiao, Unsu<sub>p</sub>ervised anomal<sub>y</sub> detection via variational auto-encoder for seasonal KPIs in web a lications, in: Proceedin s of the 2018 World Wide Web Conference (WWW ’18), 2018, . 187–196. CHE. htt s: d i 10 1145 3178876 3185996

<sup>[15] G</sup>. <sup>Li</sup>, <sup>J</sup>.<sup>J</sup>. <sup>J</sup>un , <sup>D</sup>eep <sup>l</sup>earn<sup>i</sup>n <sup>f</sup>or anoma<sup>l d</sup>e<sup>t</sup>ec<sup>ti</sup>on <sup>i</sup>n mu<sup>lti</sup>var<sup>i</sup>a<sup>t</sup>e <sup>ti</sup>me ser<sup>i</sup>es: approac<sup>h</sup>es, app<sup>li</sup>ca<sup>ti</sup>ons, an<sup>d</sup> c<sup>h</sup>a<sup>ll</sup>en es, <sup>I</sup>n<sup>f</sup>. <sup>F</sup>us<sup>i</sup>on, <sup>91 2023 93</sup>–<sup>102</sup>. https://doi.org/10.1016/j.infus.2022.10.008

[16] X. Xia, X. Pan, N. Li, X. He, L. Ma, X. Zhan<sub>g</sub>, N. Din<sub>g</sub>, GAN-based anomal<sub>y</sub> detection: a review, Neurocomputin<sub>g</sub> 493 (2022) 497–535. https://doi.or<sub>g</sub>/10.1016/ j.neucom.2021.12.093

[<sup>1</sup>7] Y. Su, Y. Z<sup>h</sup>ao, C. N<sup>i</sup>u, R. L<sup>i</sup>u, W. Sun, D. Pe<sup>i</sup>, Ro<sup>b</sup>ust anoma<sup>l</sup>y <sup>d</sup>etect<sup>i</sup>on <sup>f</sup>or mu<sup>l</sup>t<sup>i</sup>var<sup>i</sup>ate t<sup>i</sup>me ser<sup>i</sup>es t<sup>h</sup>roug<sup>h</sup> stoc<sup>h</sup>ast<sup>i</sup>c recurrent neura<sup>l</sup> networ<sup>k</sup>, <sup>i</sup>n: Proc. <sup>A</sup>CM SIGKDD Int. Conf. Knowl. Discov. Data Min<sub>,</sub> 2019<sub>, pp</sub>. 2828–2837. htt<sub>p</sub>s://doi.or<sub>g</sub>/10.1145/3292500.3330672

<sup>[18] J</sup>. <sup>A</sup>u<sup>dib</sup>er<sup>t</sup>, <sup>P</sup>. <sup>Mi</sup>c<sup>hi</sup>ar<sup>di</sup>, <sup>F</sup>. <sup>G</sup>uyar<sup>d</sup>, <sup>S</sup>. <sup>M</sup>ar<sup>ti</sup>, <sup>M</sup>.<sup>A</sup>. <sup>Z</sup>u<sup>l</sup>uaga, <sup>USAD</sup>: unsuperv<sup>i</sup>se<sup>d</sup> anoma<sup>l</sup>y <sup>d</sup>e<sup>t</sup>ec<sup>ti</sup>on on mu<sup>lti</sup>var<sup>i</sup>a<sup>t</sup>e <sup>ti</sup>me ser<sup>i</sup>es, <sup>i</sup>n: <sup>P</sup>roc. <sup>ACM SIGKDD I</sup>n<sup>t</sup>. Conf. Knowl. Discov. Data Min<sub>,</sub> 2020<sub>, pp</sub>. 3395–3404. htt<sub>p</sub>s://doi.or<sub>g</sub>/10.1145/3394486.3403392

[19] J. Xu H. Wu J. Wan M. Lon A. Transformer Time series anomal detection with association discre anc in: Proc. Int. Conf. Learn. Re resent. (ICLR) 2022. https://openreview.net/forum?id=LzQQ89U1qm\_.

[20] Z. Chen, Z. Li, X. Chen, X. Chen, H. Fan, R. Hu, Rectif<sub>y</sub>in<sub>g</sub> inaccurate unsupervised learnin<sub>g</sub> for robust time series anomal<sub>y</sub> detection, Inf. Sci. 662 (2024) 120222. https://doi.org/10.1016/j.ins.2024.120222

[21] R. Ma, Y. Ma, X. Liu, Time series anomal<sub>y</sub> detection via temporal relationship <sub>g</sub>raphs and adaptive smoothin<sub>g</sub>, Appl. Soft Comput. 179 (2025) 113298. https: //doi.or /10.1016/j.asoc.2025.113298

<sup>[22] J</sup>. <sup>H</sup>an, <sup>Z</sup>. <sup>Ch</sup>en, <sup>D</sup>. <sup>Zh</sup>ou, <sup>B</sup>. <sup>H</sup>u, <sup>T</sup>. <sup>Xi</sup>a, <sup>E</sup>. <sup>P</sup>an, <sup>U</sup>nsuperv<sup>i</sup>se<sup>d</sup> mo<sup>ti</sup>on-<sup>b</sup>ase<sup>d</sup> anoma<sup>l</sup>y <sup>d</sup>e<sup>t</sup>ec<sup>ti</sup>on w<sup>ith</sup> grap<sup>h</sup> a<sup>tt</sup>en<sup>ti</sup>on ne<sup>t</sup>wor<sup>k</sup>s <sup>f</sup>or <sup>i</sup>n<sup>d</sup>us<sup>t</sup>r<sup>i</sup>a<sup>l</sup> ro<sup>b</sup>o<sup>t</sup>s <sup>l</sup>a<sup>b</sup>e<sup>li</sup>ng, <sup>E</sup>ng. A l. Artif. Intell. 146 (2025) 110298. htt s://doi.or /10.1016/ .en a ai.2025.110298

[23] Z. Min Q. Xiao M. Abbas D. Zhan Retentive network-based time series anomal detection in c ber- h sical s stems En . A l. Artif. Intell. 145 (2025) 110215. https://doi.org/10.1016/j.engappai.2025.110215

[24] H.T. Truon B.P. Ta Q.A. Le D.M. N u en C.T. Le H.X. N u en H.T. Do H.T. N u en K.P. Tran Li ht-wei ht federated learnin -based anomal detection for time-series data in industrial control s stems Com ut. Ind. 140 (2022) 103692. htt s://doi.or /10.1016/j.com ind.2022.103692

<sup>[25] R</sup>. <sup>Li</sup>, <sup>H</sup>. <sup>M</sup>a, <sup>R</sup>. <sup>W</sup>ang, <sup>H</sup>. <sup>S</sup>ong, <sup>X</sup>. <sup>Zh</sup>ou, <sup>L</sup>. <sup>W</sup>ang, <sup>H</sup>. <sup>Zh</sup>ang, <sup>K</sup>. <sup>Z</sup>eng, <sup>C</sup>. <sup>Xi</sup>a, <sup>A</sup>pp<sup>li</sup>ca<sup>ti</sup>on o<sup>f</sup> unsuperv<sup>i</sup>se<sup>d l</sup>earn<sup>i</sup>ng me<sup>th</sup>o<sup>d</sup>s <sup>b</sup>ase<sup>d</sup> on v<sup>id</sup>eo <sup>d</sup>a<sup>t</sup>a <sup>f</sup>or rea<sup>l</sup>-<sup>ti</sup>me anomal detection in wire arc additive manufacturin J. Manuf. Process. 143 (2025) 37–55. htt s://doi.or /10.1016/j.jma ro.2025.03.113

[26] Y. Son C. Son Ada tive evolutionar multitask o timization based on anomal detection transfer of multi le similar sources Ex ert S st. A l. 283 (2025) 127599. htt s://doi.or /10.1016/j.eswa.2025.127599

[27] S. Cuéllar M. Santos F. Alonso E. Fabre as G. Farias Ex lainable anomal detection in s acecraft telemetr En . A l. Artif. Intell. 133 (2024) 108083. https://doi.org/10.1016/j.engappai.2024.108083

[28] F. Wan , Y. Jian , R. Zhan , A. Wei, J. Xie, X. Pan , A surve of dee anomal detection in multivariate time series: taxonom , a lications, and directions, Sensors 25 (1) (2025) 190. htt s://doi.or /10.3390/s25010190

[29] K. Choi, J. Yi, C. Park, S. Yoon, Dee learnin for anomal detection in time-series data: review, anal sis, and uidelines, IEEE Access 9 (2021) 120043–120065. htt s://doi.or /10.1109/ACCESS.2021.3107975

[30] Y. Jia, X. Gu, J. Liu, Z. Huan , J. Zhou, Dee anomal detection for time series: a surve , Com ut. Sci. Rev. 58 (2025) 100787. htt s://doi.or /10.1016/j.cosrev. 2025.100787

[31] M. Chala ath , S. Chawla, Dee learnin for anomal detection: a surve , IEEE Trans. Knowl. Data En . 34 (5) (2022) 2227–2246. htt s://doi.or /10.1109/ TKDE.2021.3079966

[32] J. Davis, M. Goadrich, The relationshi between recision-recall and ROC curves, in: Proc. Int. Conf. Mach. Learn. (ICML), 2006, . 233–240. htt s://doi.or / 10.1145/1143844.1143874

[33]. T. Saito, M. Rehmsmeier, The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets, PLoS ONE 10 (3) (2015) 118432. htt s://doi.or /10.1371/ ournal. one.0118432

34 P J R C C Alt ti t th di b l t d i ti J A St t A 88 424 1993 1273 1283 htt d i 10 1080 01621459 1993.10476408

[35] A. Niculescu-Mizil, R. Caruana, Predictin<sub>g g</sub>ood probabilities with supervised learnin<sub>g</sub>, in: Proc. Int. Conf. Mach. Learn. (ICML), 2005, pp. 625–632. https: //doi.or<sub>g</sub>/10.1145/1102351.1102430

[36] C. Guo, G. Pleiss, Y. Sun, K.Q. Weinber<sub>g</sub>er, On calibration of modern neural networks, Proc. Int. Conf. Mach. Learn. 70 (2017) 1321–1330. http://proceedin<sub>g</sub>s. mlr. ress/v70/ uo17a.html.

[37] S.M. Lundber<sub>g</sub>, S.-I. Lee, A unified approach to interpretin<sub>g</sub> model predictions, Adv. Neural Inf. Process. S<sub>y</sub>st. (NeurIPS) 30, 2017. https://proceedin<sub>g</sub>s.neurips. cc/<sub>p</sub>a<sub>p</sub>er/2017/file/8a20a8621978632d76c43dfd28b67767-Pa<sub>p</sub>er.<sub>p</sub>df.

[38] D. Lee, S. Malacarne, E. Aune, Explainable time series anomal<sub>y</sub> detection usin<sub>g</sub> masked latent <sub>g</sub>enerative modelin<sub>g</sub>, Pattern Reco<sub>g</sub>nit. 156 (2024) 110826. htt s://doi.or /10.1016/ . atco .2024.110826

[39] I. Ferfo lia G. Saveri L. Nenzi L. Bortolussi ECATS: ex lainable-b -desi n conce t-based anomal detection for time series In T.R. Besold A. d’Avila Garcez E. Jimenez-Ruiz R. Confalonieri P. Madh astha B. Wa ner (Eds.) Neural-S mbolic Learnin and Reasonin (NeS 2024) Lect. Notes Com ut. Sci. 14980 of Cham S rin er 2024. htt s://doi.or /10.1007/978-3-031-71170-1 16

<sup>[40] N</sup>e<sup>tM</sup>an<sup>AIO</sup>ps, <sup>O</sup>mn<sup>iA</sup>noma<sup>l</sup>y: unsuperv<sup>i</sup>se<sup>d</sup> an<sup>d</sup> sem<sup>i</sup>-superv<sup>i</sup>se<sup>d</sup> anoma<sup>l</sup>y <sup>d</sup>e<sup>t</sup>ec<sup>ti</sup>on <sup>f</sup>or <sup>ti</sup>me ser<sup>i</sup>es, g<sup>ith</sup>u<sup>b</sup> repos<sup>it</sup>ory, <sup>2025</sup>. <sup>A</sup>va<sup>il</sup>a<sup>bl</sup>e a<sup>t</sup>: <sup>htt</sup>ps:<sup>//</sup>g<sup>ith</sup>u<sup>b</sup>.com<sup>/</sup> NetManAIO s/OmniAnomal . it.

[41] Y. Chen E. Keo h B. Hu N. Be um A. Ba nall A. Mueen G. Batista The UCR time series classification archive 2015. Available at: htt s://www.cs.ucr.edu/ eamonn/time series data/.

i l d d d l i i l hi i b i il bl h i h b fi l usad-on-ucr-data.

[43] T. Fawcett, An introduction to ROC anal<sub>y</sub>sis, Pattern Reco<sub>g</sub>nit. Lett. 27 (8) (2006) 861–874. https://doi.or<sub>g</sub>/10.1016/j.patrec.2005.10.010