---
title: "Enhancing_Intrusion_Detection_in_Electric_Networks_Using_Physics-Informed_Random_Forest"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/Enhancing_Intrusion_Detection_in_Electric_Networks_Using_Physics-Informed_Random_Forest.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Enhancing Intrusion Detection in Electric Networks Using Physics-Informed Random Forest

Mehmet Bozdal

Abdullah Gül University

Kayseri, Türkiye

0000-0002-2081-7101

Alper Savaşcı

Abdullah Gül University

Kayseri, Türkiye

0000-0001-7870-9712

Abstract— The increasing complexity of electric power networks has heightened their vulnerability to cyber-attacks, challenging traditional Intrusion Detection Systems (IDS) that rely on manually crafted rules. This paper introduces a novel approach that integrates physics-informed features and feature selection into a Random Forest (RF) model to enhance IDS performance. By deriving features such as complex power and impedance from fundamental electrical principles and applying SelectKBest for optimal feature selection, our method not only improves detection accuracy but also enhances efficiency by using fewer than half the features. Specifically, the featureenriched RF model utilizing 55 features achieves an accuracy of 0.9667 and an F1-score of 0.9664, compared to 0.9576 and 0.9570 for the baseline RF model. This approach demonstrates the effectiveness of advanced feature engineering and selection techniques for improving the security and reliability of power network monitoring systems.

Keywords—intrusion detection systems, electric networks, random forest, physics-informed features, cybersecurity

## I. INTRODUCTION

Electric power networks form the backbone of modern infrastructure, providing essential services that support various sectors such as healthcare, transportation, and communication. The reliable operation of these networks is crucial for societal well-being and economic stability. As these power systems evolve, integrating advanced technologies like Intelligent Electronic Devices (IEDs) and digital communication, they become more efficient but also more complex and interconnected. This digital transformation, while offering numerous benefits, introduces new challenges, particularly in terms of cybersecurity [1].

Cyber-attacks on electric power systems can lead to significant disruptions, causing power outages that impact critical infrastructures such as water supply, natural gas distribution, and transportation networks [2]. The potential for cascading failures across these interconnected systems underscores the importance of robust cybersecurity measures in power networks. To safeguard these vital systems, it is essential to detect and mitigate cyber vulnerabilities comprehensively [3]. This involves employing multi-faceted strategies that include rigorous risk assessments and proactive management protocols. Regular vulnerability assessments are crucial for identifying and addressing potential security gaps within the grid infrastructure [4]. While firewalls and other traditional security measures are commonly used to protect communication between substations and control centers, some sophisticated cyber-attacks, such as those involving spoofed messages that mimic legitimate devices, can evade detection [5].

Intrusion Detection Systems (IDS) play a pivotal role in identifying unauthorized access and anomalies within power networks. In design of IDS, detection technique, IDS type and having active/passive detection are three main characterizing parts. Detection technique can be knowledge-based (or signature-based) and behavior-based (or anomaly-based). Basically, knowledge-based IDS compares the event signatures with a pre-defined database of attack patterns in identifying the intrusion events. However, anomaly-based IDS establishes the standard of normal conditions, referred to as baseline of normal behavior, and flags deviations from this baseline as potential threats. Although both techniques have their respective advantages and disadvantages, a hybrid approach that combines signature-based and anomaly-based detection methods leverages the strengths of each, enhancing overall detection capabilities.

IDS types can also be categorized as network-based and host-based. Network-based IDS, typically positioned at strategic points within the network, monitors network traffic for suspicious activity by examining the data packets flowing across the network. Unlike network-based IDS, host-based IDS monitors the activities on a single host or device, including the operating system and applications.

A passive IDS monitors network traffic and identifies unusual patterns or behaviors, such as given in [6], that monitors power flow results and detects anomalies. In contrast, an active IDS, also called intrusion detection and prevention system (IDPS) [5], can take actions to prevent intrusion events. A comprehensive review on IDPS applications using advanced metering infrastructure (AMI), supervisory control and data acquisition (SCADA) systems, substations, and synchrophasors can be found in [7].

Among the existing technologies for monitoring and control of power grids, synchrophasor systems provide a huge volume of low-latency, high-precision, and timesynchronized measurements to improve the power grid observability and controllability [8]. Since synchrophasor systems integrated with physical communication networks some limitations and risks exist in terms of cyber intrusions [9]. In this context, building an IDS with traditional methods becomes challenging as traditional IDSs are significantly based on manually constructed rules developed by field experts. To automatically construct IDS rules for the detection of cyber-attacks and classify substation events, a Bayesian network was adopted in [10] to form the causal relationships among the available event information. In [11], a hybrid IDS is proposed based on synchrophasor measurement data and audit logs from multiple system devices to classify the power system scenarios involving specific disturbances, normal operations and cyber-attacks. Particularly, data mining technique called common path mining is employed to learn a sequence of execution events or system states. Using the datasets provided by [11] and [12], the reference [13] proposes a classifier that is based on liquid-time constant network, a particular type of continuous-time recurrent neural network, to separate power system faults and cyber-attacks.

The primary objective of this research is to enhance the performance and efficiency of IDS for power system network through the application of physics-informed machine learning technique. Specifically, this study leverages the random forest algorithm enriched with physics-based features and utilizes the SelectKBest feature selection method to optimize model performance. The key contributions of this research are as follows:

Integration of physics-based features such as complex power and impedance.

Implementation of SelectKBest feature selection to enhance model efficiency.

Comparative analysis of baseline and physics informed random forest models.

The remainder of this paper is structured as follows: Section II provides an overview of the power system dataset, details the process of physics-informed feature engineering, and describes the feature selection methodology. Section III presents the experimental results and performance evaluations of the models. Section IV discusses the findings, limitations, and implications of the study, while Section V concludes the paper.

## II. METHODOLOGY

## A. Power System Attack Dataset

The dataset employed in this study, constructed collaboratively by Oak Ridge National Laboratory and Mississippi State University. To create power system test scenarios involving normal operating conditions, faulty states and cases with attacks, a three-bus two-line network topology has been adopted as shown in Fig. 1 [14]. This network involves two generators represented by G1 and G2, which are feeding a load center located at Bus 2. Moreover, 4 relays, denoted by R1-R4, are deployed at each terminal of both transmission lines L1 and L2. These relays control the circuit breakers indicated by BR1-BR4 to provide protection in the case of line faults.

A real-time simulation and measurement of this network is conducted using the real-time power system simulator (RTDS) with a hardware-in-the-loop design using commercial phasor measurement units (PMUs), phasor data concentrators (PDCs) and protective relays as illustrated in Fig. 2.

The dataset includes 128 distinct measurements from PMUs, which record essential system parameters including voltage and current phase angles, magnitudes, frequency, and complex impedance. Apart from the measurement of electrical quantities, device logs are also collected. The dataset is designed to simulate a range of attack scenarios such as data injection attacks, relay setting modifications, and remote tripping command injections. It comprises 15 distinct datasets, each containing some of the 37 events; categorized into 8 natural events, 1 no-event scenario, and 28 attack scenarios. For this study, only the three-class classification dataset was utilized, which distinguishes between normal operations, natural events, and attack incidents.

![](images/8b5416307c132d349f56b9820790b37cce810e5ba192c44470019ed26cb82af8.jpg)  
Fig. 1. One-line diagram of test network [14].

## B. Feature Engineering / Physics Informed Machiene Learning

Physics-informed machine learning methodologies integrate domain-specific physical principles into the feature engineering process, thereby enhancing model performance and interpretability. This approach leverages fundamental physical laws to generate features that reflect complex, realworld phenomena, thereby providing models with a deeper understanding of the underlying processes governing the data.

In the context of electrical power systems, the following physics-based features were engineered:

Complex Power (S): Complex power provides a comprehensive metric of total power consumption in the electrical network, which is critical for assessing system load and stability. It is calculated using (1),

$$
\left[ \begin{array}{c} S _ {a, i} \\ S _ {b, i} \\ S _ {c, i} \end{array} \right] = \left[ \begin{array}{c} V _ {a, i} \\ V _ {b, i} \\ V _ {c, i} \end{array} \right] \circ \left[ \begin{array}{c} I _ {a, i} ^ {*} \\ I _ {b, i} ^ {*} \\ I _ {c, i} ^ {*} \end{array} \right]\tag{1}
$$

where V and I represent the voltage and the current, phasors, respectively. The subindex i represent the bus number, and the letters $\{ a , b , c \}$ denote the phases. The symbol ° represents element-wise multiplication, and ∗ denotes the complexconjugate.

Impedance (Z): Impedance captures the resistive and reactive components of the network's electrical behavior, offering insights into potential anomalies and system performance. The self-impedance of each phase conductor can be determined using (2),

$$
\left[ \begin{array}{l} Z _ {a, i j} \\ Z _ {b, i j} \\ Z _ {c, i j} \end{array} \right] = \left(\left[ \begin{array}{l} V _ {a, i} \\ V _ {b, i} \\ V _ {c, i} \end{array} \right] - \left[ \begin{array}{l} V _ {a, j} \\ V _ {b, j} \\ V _ {c, j} \end{array} \right]\right) \triangle \left[ \begin{array}{l} I _ {a, i} \\ I _ {b, i} \\ I _ {c, i} \end{array} \right]\tag{2}
$$

where ij indicates that the electrical quantity belongs to the line between bus i and j. The symbol $\triangle$ represents the element-wise division.

![](images/cdc8f6946375065ef18a7d04b03b6c8f629f814c30fdeffdcbf5103dbcd421c0.jpg)  
Fig. 2. Hardware-in-the-loop setup of test network [14].

These features, derived from fundamental electrical principles, were incorporated into the datasets to augment the model's ability to detect deviations and predict outcomes with increased precision and reliability.

## C. Feature Selection

Feature selection represents a critical phase in the data preprocessing pipeline, aimed at dimensionality reduction, overfitting mitigation, and performance enhancement of machine learning models. In high-dimensional datasets, feature selection techniques are employed to identify the most relevant features that enhance the model’s predictive capabilities.

In this research, the SelectKBest feature selection method, a widely recognized univariate statistical technique, was utilized to select the top k features based on their statistical significance with respect to the target variable. The process was structured as follows:

Random forest models were trained on both the raw power system attack dataset, which includes fundamental features such as current and voltage, and the physics-informed dataset, which integrates additional features such as complex power (S) and impedance (Z).

For both datasets, SelectKBest was applied to select the top features by iterating through feature counts from 5 to 110 in increments of 5. The mutual information criterion was employed to quantify the dependency between each feature and the target variable, ensuring the selection of features with the highest informational value.

After feature selection, random forest models were trained on the selected feature subsets. The performance of these models was assessed to identify the optimal number of features that achieved the best balance between model accuracy and computational efficiency.

## III. EXPERIMENTAL RESULTS

## A. Model Implementation

This research aims to optimize machine learning model performance by enhancing the feature set through the generation of physics-based new features while simultaneously increasing efficiency by feature selection.

The random forest algorithm, selected for its robust capability in handling large number of input features [15], serves as the baseline methodology. Initially, the baseline random forest model is trained using the provided features from phasor measurement unit (PMU). Subsequently, it is trained with an enhanced feature set that includes complex power and impedance features in addition to the existing features. All experiments were conducted using Google Colab with an Intel(R) Xeon(R) CPU @ 2.20GHz. The performance was evaluated using key metrics such as accuracy, precision, recall, and F1-score, which are essential for assessing model effectiveness in detecting intrusions.

## B. Performance of Physics-Informed Model

The incorporation of generated features into the random forest model demonstrated consistent improvements in performance across the datasets as shown in Fig. 3. On average, the baseline random forest model achieved an accuracy of 0.9579 and an F1-score of 0.9576, whereas the feature-enriched model showed enhanced performance with an accuracy of 0.9637 and an F1-score of 0.9633. These improvements underscore the performance improvement of incorporating physics-based features into the model.

![](images/1d93c4676df4c816bd98dc2856a2361a0e4e9b7b3261c1064fbe7ad9dfc76cf6.jpg)

Fig. 3. Comparison of standart random forest with physicsinformed random forest across 15 datasets.  
![](images/8d236d0633943bcd7bfd16fa0e093a6d5b62a5a44b5544cb335b4c2c1351b418.jpg)  
Fig. 4. Comparison of average accuracy between the standard random forest with feature selection and the physicsinformed random forest with feature selection across different numbers of features.

The performance of the physics-informed random forest model was compared against existing methods to assess its effectiveness. The comparative analysis is summarized in Table I, which includes average performance metrics for various models including random forest (ML-RF) [16], Adaboost+JRipper[17]. The result shows that physics - informed random forest provides best accuracy and F1-score.

TABLE I. AVERAGE PERFORMANCE METRICS COMPARISON

<table><tr><td>Ref</td><td>F1</td><td>Accuracy</td><td>Precision</td><td>Recall</td></tr><tr><td>ML-RF[15]</td><td>0.9413</td><td>0.9395</td><td>0.9156</td><td>0.9691</td></tr><tr><td>ADA-JRIP[18]</td><td>0.955</td><td>0.9461</td><td>0.991</td><td>0.93</td></tr><tr><td>Random Forest</td><td>0.9576</td><td>0.9579</td><td>0.9576</td><td>0.9570</td></tr><tr><td>Physics-Informed Random Forest</td><td>0.9633</td><td>0.9637</td><td>0.9633</td><td>0.9627</td></tr></table>

## C. Analysis of Feature selection

An in-depth analysis of feature selection was conducted to optimize model performance while minimizing computational overhead. The iterative experimentation revealed that a significant reduction in feature count was achievable without compromising model efficacy.

Fig 4. presents a comparison of average accuracy between a standard random forest model with feature selection and a physics-informed random forest model with feature selection across varying numbers of features. Both models show a rapid increase in accuracy with the initial addition of features, reaching a plateau around 45 features. Prior to this threshold, a noticeable decline in accuracy was observed, underscoring the importance of selecting features that significantly contribute to the predictive power of the model. It was determined that utilizing 55 features yielded optimal performance across the 15 datasets examined.

![](images/00a4480e3f55fd3911c56865166226f5d76aa71b573d598a9bcbf09218941448.jpg)  
Fig. 5. Comparison of random forest and physics-informed random forest models with (K=55) and without feature selection.

Fig. 5 presents a comparison of random forest and physicsinformed random forest models with and without feature selection. The results, summarized in Table II, indicate that the incorporation of physics-informed features leads to a slight but statistically significant improvement in model accuracy and F1 score. The physics-informed random forest model achieved an average accuracy of 0.9633 and an average F1 score of 0.9627, compared to 0.9576 and 0.9570 for the standard random forest model, respectively. When feature selection was applied with 55 features, the physicsinformed random forest model achieved an average accuracy of 0.9667 and an average F1 score of 0.9664, compared to 0.9596 and 0.9591 for the standard random forest model, respectively.

These findings underscore the effectiveness of integrating physics-based features into machine learning models for power system anomaly detection, both with and without feature selection.

TABLE II. EVALUATION OF FEATURE SELECTION(K=55)

<table><tr><td>Model</td><td>Accuracy</td><td>F1-Score</td><td>Precision</td><td>Recall</td></tr><tr><td>Random Forest</td><td>0.9576</td><td>0.9570</td><td>0.9579</td><td>0.9576</td></tr><tr><td>Physics-Informed Random Forest</td><td>0.9633</td><td>0.9627</td><td>0.9637</td><td>0.9633</td></tr><tr><td>Random Forest (Feature Selected)</td><td>0.9596</td><td>0.9591</td><td>0.9596</td><td>0.9596</td></tr><tr><td>Physics-Informed Random Forest (Feature Selected)</td><td>0.9667</td><td>0.9664</td><td>0.9668</td><td>0.9667</td></tr></table>

## IV. DISCUSSION

The findings presented in this study underscore the significant advancements achieved through physics-informed feature engineering and efficient feature selection in enhancing IDS for electric networks. By integrating physicsbased features such as complex power and impedance, derived from fundamental electrical principles, the model gains a nuanced understanding of network behaviors that traditional metrics like current and voltage alone may not fully capture. This enriched feature set not only enhances anomaly detection but also bolsters the model's predictive accuracy and robustness.

Feature selection, specifically employing SelectKBest, further optimizes model efficiency by identifying the most informative features while reducing computational complexity. Our findings indicate that utilizing 55 selected features strikes a balance between maintaining model performance and minimizing computational overhead. Prior to this threshold, a noticeable decline in accuracy highlights the critical role these selected features play in enhancing predictive power.

Comparative analysis against existing methods demonstrates that our physics-informed approach consistently outperforms conventional techniques in terms of accuracy and F1-score metrics. This superiority validates the effectiveness of incorporating domain knowledge into feature engineering, thereby ensuring that the IDS not only detects anomalies effectively but also generalizes well across different operational scenarios.

However, it is important to acknowledge several limitations of this study:

Scope of Physics-Informed Features: The study focused primarily on integrating complex power and impedance as physics-informed features. Future research could explore additional physical parameters such as power factor and mutual impedance between phase conductors. Investigating the individual and combined effects of these features may further enrich the research.

Generalizability: While our approach has shown promising results on a specific power network dataset, further validation across diverse datasets is essential to assess its broader applicability and robustness across varying network conditions and operational contexts.

Model Selection: While Random Forests were chosen for their robustness and suitability in this research, exploring the performance of alternative machine learning algorithms or ensemble techniques could provide additional insights into alternative modeling approaches for IDS in electric networks.

## V. CONCLUSION

This research demonstrates that enhancing electric power networks with physics-informed data like complex power and impedance information can lead to improved detection performance. While the improvements were marginal, they highlight the potential benefits of incorporating derived metrics in machine learning models. Future work will explore the integration of additional derived features and the application of more advanced machine learning techniques to further enhance IDS performance.

## REFERENCES

[1] Ankitdeshpandey and R. Karthi, “Development of Intrusion Detection System Using Deep Learning for Classifying Attacks in Power Systems,” Advances in Intelligent Systems and Computing, vol. 1154, pp. 755–766, 2020, doi: 10.1007/978-981-15-4032- 5\_68.

[2] M. Lehto, “Cyber-Attacks Against Critical Infrastructure,” Computational Methods in Applied Sciences, vol. 56, pp. 3–42, 2022, doi: 10.1007/978-3-030-91293-2\_1.

[3] T. Talaei Khoei, H. Ould Slimane, N. Kaabouch, T. Talaei Khoei, H. Ould Slimane, and N. Kaabouch, “A Comprehensive Survey on the Cyber-Security of Smart Grids: Cyber-Attacks, Detection, Countermeasure Techniques, and Future Directions,” ArXiv, p. arXiv:2207.07738, Jun. 2022, Accessed: Jun. 27, 2024. [Online]. Available: https://arxiv.org/abs/2207.07738v1

[4] J. Yu, A. Mao, and Z. Guo, “Vulnerability assessment of cyber security in power industry,” 2006 IEEE PES Power Systems Conference and Exposition, PSCE 2006 - Proceedings, pp. 2200– 2205, 2006, doi: 10.1109/PSCE.2006.296283.

[5] C. C. Sun, A. Hahn, and C. C. Liu, “Cyber security of a power grid: State-of-the-art,” International Journal of Electrical Power & Energy Systems, vol. 99, pp. 45–56, Jul. 2018, doi: 10.1016/J.IJEPES.2017.12.020.

[6] J. Valenzuela, J. Wang, and N. Bissinger, “Real-Time Intrusion Detection in Power System Operations,” IEEE Transactions on Power Systems, vol. 28, no. 2, pp. 1052–1062, 2013, doi: 10.1109/TPWRS.2012.2224144.

[7] P. I. Radoglou-Grammatikis and P. G. Sarigiannidis, “Securing the Smart Grid: A Comprehensive Compilation of Intrusion Detection and Prevention Systems,” IEEE Access, vol. 7, pp. 46595–46620, 2019, doi: 10.1109/ACCESS.2019.2909807.

[8] D. Zhou et al., “Distributed data analytics platform for wide-area synchrophasor measurement systems,” IEEE Trans Smart Grid, vol. 7, no. 5, pp. 2397–2405, Sep. 2016, doi: 10.1109/TSG.2016.2528895.

[9] A. Sundararajan, T. Khan, A. Moghadasi, and A. I. Sarwat, “Survey on synchrophasor data quality and cybersecurity challenges, and evaluation of their interdependencies,” Journal of Modern Power Systems and Clean Energy, vol. 7, no. 3, pp. 449– 467, May 2019, doi: 10.1007/S40565-018-0473-6.

[10] S. Pan, T. H. Morris, and U. Adhikari, “A Specification-based Intrusion Detection Framework for Cyber-physical Environment in Electric Power System,” International Journal of Network Security, 2015.

[11] S. Pan, T. Morris, and U. Adhikari, “Developing a Hybrid Intrusion Detection System Using Data Mining for Power Systems,” IEEE Trans Smart Grid, vol. 6, no. 6, pp. 3104–3113, Nov. 2015, doi: 10.1109/TSG.2015.2409775.

[12] S. Pan, T. Morris, and U. Adhikari, “Classification of disturbances and cyber-attacks in power systems using heterogeneous timesynchronized data,” IEEE Trans Industr Inform, vol. 11, no. 3, pp. 650–662, Jun. 2015, doi: 10.1109/TII.2015.2420951.

[13] M. Samadi, H. Kharrati, M. A. Badamchizadeh, H. Hassani, and S. Nikan, “Diagnosing Faults in Smart Grids using Liquid Time-Constant Network,” 9th International Conference on Engineering and Emerging Technology, ICEET 2023, 2023, doi: 10.1109/ICEET60227.2023.10525812.

[14] U. Adhikari, S. Pan, T. Morris, R. Borges, and J. Beaver, “Power System Attack Datasets - Mississippi State University and Oak Ridge National Laboratory,” 2014. Accessed: Jun. 29, 2024. [Online]. Available: https://sites.google.com/a/uah.edu/tommymorris-uah/ics-data-sets?authuser=0

[15] M. Zaman, D. Upadhyay, and C. H. Lung, “Validation of a Machine Learning-Based IDS Design Framework Using ORNL Datasets for Power System with SCADA,” IEEE Access, vol. 11, no. October, pp. 118414–118426, 2023, doi: 10.1109/ACCESS.2023.3326751

[16] M. Zaman, D. Upadhyay, and C. H. Lung, “Validation of a Machine Learning-Based IDS Design Framework Using ORNL Datasets for Power System with SCADA,” IEEE Access, vol. 11, no. October, pp. 118414–118426, 2023, doi: 10.1109/ACCESS.2023.3326751.

[17] R. C. Borges Hink, J. M. Beaver, M. A. Buckner, T. Morris, U. Adhikari, and S. Pan, “Machine learning for power system disturbance and cyber-attack discrimination,” 7th International Symposium on Resilient Control Systems, ISRCS 2014, pp. 1–8, 2014, doi: 10.1109/ISRCS.2014.6900095.

[18] R. C. Borges Hink, J. M. Beaver, M. A. Buckner, T. Morris, U. Adhikari, and S. Pan, “Machine learning for power system disturbance and cyber-attack discrimination,” 7th International Symposium on Resilient Control Systems, ISRCS 2014, pp. 1–8, 2014, doi: 10.1109/ISRCS.2014.6900095.