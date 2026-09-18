---
title: "robust-industrial-iot-security-leveraging-parallel-physics-informed-neural-networks-to-combat-false-data-injection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/robust-industrial-iot-security-leveraging-parallel-physics-informed-neural-networks-to-combat-false-data-injection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Robust Industrial IoT Security Leveraging Parallel Physics-Informed Neural Networks to Combat False Data Injection

Basi Reddy A.∗<sup>,</sup>‡, R. Yogesh†<sup>,</sup>§ and M. Sriram∗

∗Department of Computer Science and Engineering Bharath Institute of Higher Education and Research Selaiyur, Tambaram, Chennai 600073, Tamil Nadu, India

†Department of Information Technology Bharath Institute of Higher Education and Research Selaiyur, Tambaram, Chennai 600073, India ‡basireddy.a@gmail.com §yogeshrajkumar.it@bharathuniv.ac.in

Received 10 September 2024 Revised 28 February 2025 Accepted 14 August 2025 Published 1 December 2025

The extensive adoption of the Industrial Internet of Things (IIoT) concept has resulted in several security flaws. The “False Data Injection Attack” (FDIA) is a major security risk afected by IIoT. The goal of FDIA is to mislead industrial platforms by inflating measurements of sensors. The traditional threat detection methods have been successfully defeated by FDI attacks. In this paper, Robust Industrial IoT Security Leveraging Parallel Physics Informed Neural Networks to Combat False Data Injection (PPINN-FDIA-IIOT) is proposed. Here, the input data are gathered from a real-time dataset. Then, input data are given to preprocessing. In preprocessing, Distributed Set-Membership Fusion Filtering (DSMFF) is used for eliminating noise, irrelevant informa tion. The pre-processing data is given to the classification phase for detecting Fault Data Injection Attack as Simple FDIA, Stealthy FDIA, Stealthy and collusive FDIA utilizing Parallel Physics-Informed Neural Network (PPINN). Generally, PPINN does not adopt any optimization methods to determine optimal parameters to ensure fault data injec tion attacks. Hence, Giza Pyramid Construction Optimization (GPCO) is employed to improve the weight parameters of PPINN. The proposed method is implemented in MATLAB and its eficiency is evaluated under performance metrics, like accuracy, precision, F1-score, Roc, mean square error, and computational time. The proposed PPINN FDIA-IIOT method attains 23.32%, 24.07%, and 28.51% higher F1-score and 18.92%, 25.03%, and 29.15% higher accuracy compared with existing methods.

Keywords: Distributed set-membership fusion filtering; false data injection attacks; Giza Pyramid construction optimization algorithm; industrial Internet of Things; parallel physics-informed neural networks.

## 1. Introduction

The industrial sector is rapidly adopting Internet of Things (IoT) technologies, which have made vital infrastructure vulnerable to cyberattacks.<sup>1–3</sup> By enabling system self-control and providing real-time response systems, IIoT has assisted in the resolution of several unsolvable problems in the industry<sup>4–6</sup> Security concerns for Industrial Internet of Things (IIoT) applications are thoroughly researched and taken care to guarantee the successful launch of these apps.<sup>7–9</sup> IIoT sensor readings at key industrial locations are essential subjects, whose loss as a result of attacks or other circumstances causes significant losses, possibly even resulting in the loss of human life.<sup>10</sup> The Stuxnet attack on the Iranian nuclear system resulted in severe losses and interruptions.<sup>11–13</sup> Interest in keeping an eye out for cyberattacks on industrial systems like oil, gas, and hydraulic stations has significantly increased in current years<sup>14–16</sup> Major kinds of attacks that could impact these kinds of systems are False Data Injection attacks (FDIA).<sup>17–19</sup> FDIA is particularly damaging kind of cyberattack against industrial systems. They deceive the industrial platform under attack by fabricating sensor readings.<sup>20–22</sup> According to the study, an attacker can launch a distributed denial-of-service attack (FDI) without using conventional techniques like state estimation and bad data detection.<sup>23–25</sup> State estimation is a basic technique for detecting FDIA in important facilities.<sup>26</sup> Measuring fabrication or alteration results from depending on state estimates to achieve comprehensive sensing accuracy.<sup>27</sup> Industrial Control Systems (ICS) are the backbone of modern industry, responsible for the smooth operation of a wide range of critical infrastructure, including energy, water, and trafic management.<sup>28</sup> By precisely controlling complex machines and processes, these systems play a major role in ensuring the reliable operation of infrastructure and supporting the nation’s economic prosperity and public safety.<sup>29,44–46</sup> The reliability and security of these critical systems is more than a technical issue; it is a serious national security concern, which means that ICS goes beyond mere industrial function and is linked to societal and national resilience.<sup>30,47–49</sup>

Traditional approaches, such as anomaly detection and rule-based systems, sufer from scalability, resulting in significant false positive and false negative rates, especially in large-scale systems. These approaches also struggle to detect modest FDI attacks, particularly in noisy or fluctuating sensor data and are computationally expensive, making real-time detection dificult. Furthermore, most current techniques lack contextual awareness, limiting their capacity to detect attack patterns that depart from routine operations but remain valid. As a result, there is a critical need for more robust, flexible and eficient security solutions with deep learning providing a possible option to address these dificulties. Parallel Physics-Informed Neural Networks (PPINNs) ofer a promising solution to overcome the challenges faced by traditional approaches in securing IIoT systems against FDIA.

This work presents a Robust Industrial IoT Security Leveraging Parallel Physics-Informed Neural Networks to Combat False Data Injection, which innovatively exploits temporal and spatial data correlations in sensor networks. The novelty lies in the use of Parallel Physics-Informed Neural Network (PPINN) to derive latent feature representations that capture intricate relationships in sensor data, bypassing the need for a labeled dataset. The method enhances its robustness against data corruption, thereby improving detection accuracy by integrating denoising PPINN. The Giza Pyramid Construction Optimization (GPCO) is employed to fine-tune the network’s weight parameters to enhance the accuracy of PPINN in detecting FDIA. This approach not only advances the capability to detect subtle FDI attacks that evade traditional methods but also optimizes the resource utilization of sensor networks, making it a pioneering solution in the area of anomaly detection in industrial IoT environments.

Major contributions of this work are as follows:

• The proposed method enhances IIoT security by accurately detecting and mitigating false data injection attacks, ensuring reliable industrial automation and process control.

• Distributed Set-membership Fusion Filtering (DSMFF) enhances data integrity by removing noise and redundant information, ensuring that only relevant and high-quality data is given to the detection system. This increases the reliability of the IIoT security framework.

• PPINN identifies and classifies various types of FDIA, such as Simple FDIA, Stealthy FDIA and Stealthy Collusive FDIA. This classification allows for proac tive threat mitigation by recognizing diferent levels of attack complexity.

• The GPCO method refines the weight parameters of the PPINN, increasing the accuracy and strength of the method.

This paper is arranged as follows. Section 2 delineates the literature review. Section 3 defines the proposed approach. Section 4 illustrates results and discussions. Section 5 concludes.

## 2. Literature Review

Many studies have been presented in the literature on Machine Learning (ML) approach dependent detection of fault data injection attacks IIoT utilizing DL; among these, a few recent works are reviewed here.

Li et al.<sup>31</sup> suggested a secure federated deep learning method for detecting FDI attacks in smart grids. The presented transformer-dependent FDIA detection model trains each node locally. A federated learning architecture that allows all nodes to work together to train a detection method while maintaining the confidentiality of each local training data was presented. Furthermore, secure federated learning was provided by fusing the Paillier cryptosystem with a federated learning framework. The suggested method efectively safeguards federated learning’s privacy during training. It has higher accuracy and lower precision.

Pedroso and Santos<sup>32</sup> suggested controlling data distribution, dynamic data clustering for dense IIoT against FDI attacks. Consensus Depend Data Filtering for IIoT (CONFINIT) system was introduced to prevent FDI attacks in dense IIoT networks. To identify nodes by malicious behavior concerning others, a watchdog strategy, cooperative consensus to observe misbehavior nodes relating to neighbors, and reading information aggregate readings were employed. The simulation outcomes demonstrated the eficiency of CONFINIT against false data injection attacks, guaranteeing legitimate data accessibility for IIoT applications. It has greater precision and lesser F1-score.

Takiddin et al.<sup>33</sup> introduced a robust graph autoencoder-dependent recognition of data poisoning in smartgrids by means of FDI assaults. The presented study examined the efects of adversarial data poisoning on data-driven FDIAs detectors in topology-exact with generalized contexts using various attack injection levels. Based on comprehensive simulation tests, the following conclusions were drawn: data poisoning caused up to 29% DR degradation in benchmark detectors. When compared to topology-specific detectors, DR robustness of generalized detectors trained on various topological reconfigurations increases by 8–16%. However, it was impossible to record undetected attacks due to its controlled training methods. It attains high F1-score and less RoC.

Tian et al.<sup>34</sup> suggested data-driven FDI attacks against cyber-physical power schemes. The presented study compares and evaluates various data-driven tech niques for creating FDIAs. Robust Linear Regression (RLR) technique considers some environmental elements and assumptions (four criteria were considered on intercepted measurement data). Simulation research shows that the RLR technique executes better in most case studies. The sparse low-rank decomposition strategy depends on the RLR method, provides superior outcomes in exceedingly complicated situations. Depending on case studies, it can be concluded that in situations where there is much ambiguity, attackers are cautious and try to either launch small attacks or otherwise avoid them entirely. It has a higher RoC and lower accuracy.

Bhattacharjee et al.<sup>35</sup> introduced false data injection eforts that target the AC state estimation of power systems via deep latent space clustering. It suggested an unsupervised deep latent space clustering process to find hidden FDIA in the smart grids. It includes greedy layer-wise training for a stacked autoencoder network, followed by sophisticated layer-by-layer fine-tuning of a stacked encoder–decoder scheme. The pre-trained encoder network, clustering head with trainable cluster centers, was then modified, minimizing the KL Divergence error among the clustering head’s soft cluster assignment outputs and an auxiliary target distribution. The encoder network weights and cluster centers were changed to more enhance clustering performance through the self-training process. It has higher F1-score and lower precision.

Ahmad et al.<sup>36</sup> suggested IIoT using a Deep Random Neural Network (DRNN) along with Particle Swarm Optimization (PSO) for intrusion finding. A reliable attack recognition approach for IIoT environments was presented. A difficult version of a typical RNN has superior generalization abilities. Extensively dispersed was best trained by combining hybrid PSO with sequential quadratic programming to achieve a greater attack detection accuracy. The neural network chooses the best hyperparameters using SQP-enabled PSO. It has higher RoC and lower F1-score

Gaber et al.<sup>37</sup> introduced ML and optimization approaches to perform an IIoT detection solution. The suggested study work classifies NIDS in IIoT-based trafic using a feature selection approach with ML-dependent methods. The IIoT-based dataset was classified using fewer parameters through feature selection using the PSO and BA. The dataset was classified using three distinct ML-based methods. After implementing feature section approaches to the dataset, ML techniques were employed to tackle novel forms of attacks such as SQL injection, backdoors, and command injection. It has higher accuracy and lower RoC.

Wang et al.<sup>38</sup> suggested graph spatial features with a temporal convolutional neural network-based detection method for false data injection attacks in smart grids. The suggested method has two phases: (i) spatial features extraction, (ii) temporal convolutional network. The temporal convolutional network was utilized to extract the temporal features after the graph convolutional procedure was employed to separate the interactions between buses and extract the spatial aspects of mea surement. The suggested method can find the injected false data injection attacks efectively in smart grids. It attains high RoC and low precision.

Table 1. Comparison of literature review.

<table><tr><td>Author name</td><td>Objective</td><td>Models</td><td>Advantages</td><td>Disadvantages</td></tr><tr><td>Li et al.31</td><td>To develop secure federated learning for detecting FDIA</td><td>Secure Federated Learning (SecFed)</td><td>High accuracy</td><td>low precision</td></tr><tr><td>Pedroso and Santos32</td><td>CONFINIT system to detect FDI attacks in IIoT networks</td><td>Clustering Management Module (CM)</td><td>High precision</td><td>low F1-score</td></tr><tr><td>Takiddin et al.33</td><td>To detect false data injection attacks effectively in smart grids</td><td>Graph Autoencoder, Robust Learning Techniques</td><td>High F1-score</td><td>Low RoC</td></tr><tr><td>Tian et al.34</td><td>data-driven false data injection attack methods</td><td>Robust Linear Regression (RLR)</td><td>High RoC</td><td>Low accuracy</td></tr><tr><td>Bhattacharjee et al.35</td><td>self-supervised DLSC for detecting stealthy false data injection attacks</td><td>Deep Latent Space Clustering (DLSC)</td><td>High F1-score</td><td>Low precision</td></tr><tr><td>Ahmad et al.36</td><td>reliable intrusion detection scheme using a DRNN</td><td>DRNN, PSO</td><td>High RoC</td><td>Low F1-score</td></tr><tr><td>Gaber et al.37</td><td>a novel intrusion detection model</td><td>PSO and Random Forest (RF)</td><td>High accuracy</td><td>Low RoC</td></tr><tr><td>Wang et al.38</td><td>Identification method in smart grids for false data injection attacks</td><td>Temporal convolutional neural networks</td><td>High RoC</td><td>Low precision</td></tr></table>

Table 1 depicts the comparison of the literature review.

Table 1 compares literature reviews aimed at detecting FDIA in diferent systems using various methodologies. Li et $a l . ^ { 3 1 }$ employed Secure Federated Learning (SecFed) to obtain high accuracy, although it had low precision. Pedroso and San-$\mathrm { { t o s ^ { 3 2 } } }$ introduced the CONFINIT system, which uses Clustering Management to achieve great precision, yet with a low F1-score. Takiddin et $a l . ^ { 3 3 }$ used Graph Autoencoders and Robust Learning to detect FDIA in smart grids, resulting in a high F1-score but a low ROC performance. Tian et $a l . ^ { 3 4 }$ used RLR, resulting in a high ROC but reduced accuracy. To address this, the proposed work improves Industrial IoT security by employing Parallel Physics Informed Neural Networks to detect and prevent FDIA. By incorporating domain-specific physical principles into the learning process, the technique improves detection reliability while decreasing vulnerability to adversary manipulation.

![](images/9d52854a11249b2696ef7528324388c0254c4181717cd2bf8b48912ecc9452ba.jpg)  
Fig. 1. Block Diagram of proposed PPINN-FDIA-IIOT method.

## 3. Proposed Methodology

In this work, Robust Industrial IoT Security Leveraging Parallel Physics Informed Neural Networks to Combat False Data Injection is discussed. The block diagram of the PPINN-FDIA-IIOT system is illustrated in Fig. 1. The data are pre-processed and classified using neural network and optimized with optimization techniques for better categorization of the fault data injection attack. This section discusses the techniques used to identify attacks, including collusive, stealthy, and simple FDIA. The complete description of all these steps is detailed in the subsequent sections.

## 3.1. Dataset

Here, the database is obtained from the 2020 US Energy Information Administration (EIA) State Electricity Profiles featuring hourly electricity demand data from smart meters across various US sub-regions. This dataset captures the real-world consumption patterns with 24 h periodicity and reflects the diverse geographical areas and population densities. It is updated hourly and ofers highresolution insights into weekly and daily usage trends, making it possible to assess the proposed FDIA detection scheme in dynamic and realistic circumstances. The dataset’s broad geographic coverage and detailed temporal resolution ensure a robust assessment of the detection method across varied and operational settings.

## 3.2. Pre-processing under distributed set-membership fusion filtering

The DSMFF is pre-processed<sup>39</sup> to remove noise and irrelevant information. DSMFF improves data quality in distributed IIoT systems by combining local and global filtering approaches. This method integrates set-membership constraints locally at each sensor node and globally at a fusion center, ensuring that only relevant and accurate data is retained. DSMFF enhances the robustness of the dataset and reduces the impact of measurement errors, and preserves critical information necessary for accurate anomaly detection by efectively filtering out noise and outliers through local and centralized processes. Each sensor node applies DSMFF to its data. These constraints are based on predefined operational ranges or statistical properties. Data points that fall outside these constraints are considered noise and are filtered using the following equation:

$$
a _ {c + 1, d + 1} ^ {(b)} = e ^ {(1)} (a _ {c, d + 1} ^ {\wedge}) + e ^ {(2)} (a _ {c + 1, d} ^ {\wedge}) + F _ {c, d + 1} ^ {(b, 1)} + F _ {c + 1} ^ {(b, 2)},\tag{1}
$$

where $a _ { c + 1 , d + 1 } ^ { ( b ) }$ denotes local estimation of $e ^ { ( 1 ) }$ on sensor s, $F _ { c , d + 1 } ^ { ( b , 1 ) }$ filter parameters designed. Filtered data from individual sensors are sent to a central fusion center. The fusion center aggregates the data and performs a global set-membership filtering process. This step integrates data from various sensors, considering spatial and temporal correlations, to refine the filtering process, remove irrelevant information

and express in the following equation:

$$
\mu_ {c, d} ^ {(b)} = \Phi J _ {c, d} ^ {(b)} - K _ {c, d} ^ {(b)} a _ {c, d} ^ {(b)}.\tag{2}
$$

By utilizing the Taylor series extension formula, nonlinear functions, here $\mu _ { c , d } ^ { ( b ) } .$ $K _ { c , d } ^ { ( b ) }$ linearized ΦJ denotes filtered data from all nodes is then aggregated at a central fusion center, where global set-membership filtering further refines the data by considering spatial and temporal correlations between diferent sensors, and is expressed in the following equation:

$$
e ^ {(1)} (a _ {c, d}) = e ^ {(1)} (a _ {c, d} ^ {(b)}) + \varphi_ {c, d} ^ {(b, 1)} (a _ {c, d}) + l _ {c, d} ^ {(b, 1)},\tag{3}
$$

where $\varphi _ { c , d } ^ { ( b , 1 ) }$ denotes Jacobian matrices; $e ^ { ( 1 ) } ( a _ { c , d } )$ signifies higher-order Lagrange remainders. This thorough preprocessing pipeline ensures that the data are clean, consistent, and relevant, leading to more accurate and reliable anomaly detection in IIoT systems, which is used to remove noise and irrelevant information, as expressed in the following equation:

$$
\varepsilon_ {c + 1, d + 1} ^ {(b)} = \sum_ {m \notin \mathrm{N}} \beta_ {b m} H _ {c + 1, d} ^ {(b m)} (a _ {c + 1, d} ^ {(e)} - a _ {c + 1} ^ {(b)}),\tag{4}
$$

where $\beta _ { b m }$ is the fused estimate and $a _ { c + 1 , d } ^ { ( e ) }$ is the positive definite matrix $\varepsilon _ { c + 1 , d + 1 } ^ { ( b ) }$ recognized positive definite matrices. By ensuring that the data is clear, consistent, and instructive, this preprocessing technique improves the precision and dependability of anomaly detection in IIoT systems. Finally, DSMFF removes unwanted noises and irrelevant information. Then pre-processed data is transferred into PPINNs for classifying the FDIA.

## 3.3. Fault data injection attack detection utilizing parallel physics-informed neural networks

In this section, Fault Data Injection Attack Detection in IIOT using PPINN<sup>40</sup> is discussed. PPINNs enhance accuracy by integrating physical laws into neural network models, ensuring predictions are consistent with underlying principles. They leverage parallel computing for eficient handling of large-scale datasets and complex computations, making them appropriate for real-time IIoT applications. The consolidation of data-driven and physics-informed training enhances robustness against noise and anomalies, while the integration of domain-specific knowledge improves interpretability.

The FDIA attack is identified in this work. Using the attack model, the DADBN technique is modified to fit requirements, characteristics of IIoT systems. This paradigm allows the hacker to modify and/or fake-inject data from one or more sensors at some moment, provided that the fake data falls inside a reasonable measurement range. The integrity attack on measured data is expressed in Eq. (5):

$$
P (\zeta) = O _ {v} \mathrm{NRT} _ {v} (\zeta ; \{Y _ {v} ^ {j} \} _ {j = 1} ^ {M}) + O _ {G} \mathrm{NRT} (\delta : (Y _ {G} ^ {(j)})),\tag{5}
$$

where $P ( \zeta )$ and $O _ { G } \mathrm { N R T }$ denote weights for data, residual losses. Faulty data previously identified by the PPINN are cleaned using DADBN. The initial data obtained from the sensors are sent into the PPINN during the training phase. The same data are the target values. At this point, the network can use intercorrelation among elements to compress the input vector, decompress it again. PPINN is utilized for false data detection after training phase is over, weights are established. MSE is expressed in the following equation:

$$
\mathrm{NRT} _ {v} (\delta : (Y _ {v} ^ {(j)})) = \frac {1}{M _ {v}} \sum_ {j = 1} ^ {M _ {v}} | v ^ {(j)} - v _ {o} (Y _ {v} ^ {(j)}) | ^ {2}.\tag{6}
$$

MSE is analyzed with predefined threshold that is selected as the mean of validation MSE to identify erroneous data. An attack is declared when the MSE value is over the specified threshold. It’s important to note that validation is required to prevent over-fitting, which occurs when a machine learns the training set so thoroughly that it cannot analyze novel data, as expressed in the following equation:

$$
\mathrm{NRT} _ {G} (\delta : (Y _ {G} ^ {(j)})) = \frac {1}{M _ {g}} \sum_ {j = 1} ^ {M _ {g}} | G _ {\delta} (Y _ {g} ^ {(j)}) | ^ {2},\tag{7}
$$

where $\delta : ( Y _ { v } ^ { ( j ) } )$ represents the mean square error for data mismatch term, imposing initial else border conditions as constraints, and producing a well-posed problem. MSEF is the MSE for PDE residual, with $v _ { o } ( Y _ { v } ^ { ( j ) } )$ ) signifying residual governing PDEs, parameters of NNs Y and $\delta$ denotes calculated by minimizing loss function.

Experiments with synthetic training data are integrated into the loss function. The PDE residual was calculated utilizing automatic diferentiation. In this section, define the dual lately proposed domain decomposition methods in the framework, specifically, PPINN. The computational domain is split into Nsd nonoverlapping regular or irregular subdomains. Independent NNs are deployed in all sub-domains, communicate with one another through a common interface. Then, this step detects the attack of fault data injection as simple FDIA is expressed in the following equation:

$$
V _ {\delta} (H) = \sum_ {k = 1} ^ {M _ {r c}} v _ {\delta K} (H) \cdot 1 \Psi_ {k} (H).\tag{8}
$$

The PPINN approach’s loss function kth in the subdomain is better than the SCCR solution at identifying long-term, covert attack signals and does a good job of identifying stealthy FDIAs on a single sensor. However, from the start of the FDIA, the discrepancy was not immediately apparent. Thus, while identifying covert FDIAs, it’s essential to select an appropriate ETS size or sliding window size, which is expressed in the following equation:

$$
I (\varsigma_ {k}) = O _ {v k} \mathrm{NRT} _ {v k} (Y _ {v k} ^ {(j)}) + O _ {G k} \mathrm{NRT} _ {G k} (Y _ {G _ {k}}),\tag{9}
$$

where $I ( \varsigma _ { k } )$ denotes input vector, $O _ { v k } \mathrm { N R T } _ { v k }$ denotes full forward propagation function, $O _ { G k }$ implies set of biases, weights learned with network through training phase. Then detect the attack of fault data injection as stealthy FDIA is shown in Eq. (10): Moreover, voting algorithm fails to detect FDIAs on more than half of sensors; hence, it makes sense to investigate into detection techniques in collusiontolerant anomaly is expressed in the following equation:

$$
\mathrm{NRT} _ {G k} (Y _ {G k} ^ {M _ {b k}}) ^ {M g k} = \sum_ {j = 1} ^ {M _ {g k}} \left(\frac {1}{M _ {G k}} \sum_ {j = 1} ^ {M i k} | v _ {k} ^ {(j)} - v _ {k} (Y _ {v k} ^ {(j)}) \quad M - G \varsigma_ {k} (Y _ {J k}) \cdot m | ^ {2} \right..\tag{10}
$$

The $Y _ { G k } ^ { M _ { b k } } , \ v _ { k } ( Y _ { v k } ^ { ( j ) } )$ , and $G _ { \mathsf { S } k } ( Y _ { J k } )$ denote data mismatch, interface, residual (normal flux with average solution continuity alongside interface) weights. Finally, PPINN’s ability to uncover intricate association structures concealed within the data allows them to identify a variety of attacks. Therefore, DAE can retrieve the correlation between inputs. The output of DAE is a clean copy of the faulty input when fake data are fed into it. Fault Data Injection Attack Detection is categorized as Simple, Stealthy, and Collusive. This step is expressed in the following equation:

$$
\begin{array}{r} \mathrm{I} (\xi_ {k}) = O _ {v k} \mathrm{NRT} _ {v k} (\varsigma_ {k}): (Y _ {v k}) + O _ {G q} \mathrm{NRT} (\zeta_ {k}) (Y _ {G k} ^ {j}) \\ + O _ {J k} \mathrm{NRT} _ {v a v g} (\zeta_ {k}: (Y _ {J k} ^ {(j)})), \end{array}\tag{11}
$$

The NRT Denotes residual continuity condition on mutual interface, assumed dual various NNs on sub domain K, K+ respectively; superscript $Y _ { G k } ^ { j }$ over $\zeta _ { k } .$ signifies collusive FDIA. The corrupted data are subsequently sent into a DAE upon detection of an assault. Ultimately, PPINN identifies fault data injection as collusive, stealthy, simple, and stealthy FDIA. The PPINN classifier incorporates AI-dependent optimization strategy on account of its practicality and relevance. GPCO is considered to enhance PPINN, also tuning weight, $P ( \zeta )$ and $Y _ { G } ^ { ( j ) }$ biasfactor of PPINN.

## 3.4. Optimization using Giza Pyramid construction optimization algorithm

Weight parameters $P ( \zeta )$ and $Y _ { G } ^ { ( j ) }$ of PPINN using the $\mathrm { G P C O ^ { 4 1 } }$ are discussed in this phase. Weight parameter $P ( \zeta )$ is enhanced to increase the accuracy and $Y _ { G } ^ { ( j ) }$ is enhanced to decrease the computation time. The GPCO algorithm employs a systematic, layer-by-layer approach inspired by the precise and resource-eficient construction methods of the ancient pyramids. This strategy ensures balanced exploration, exploitation of the search space, leading to refined and optimal solutions. The GPCO algorithm eficiently utilizes computational resources, handles large-scale problems, and maintains high precision, making it a powerful tool for diverse optimization challenges across several domains by mimicking resource allocation techniques and progressing gradually.

## Step 1: Initialization.

The laborers include carpenters, masons, coolies, slaves, and metalworkers led by a skilled agent. This Pharaoh’s special agent foreman is an excellent agent. Stone blocks are carried by laborers. It is under the supervision of Pharaoh’s agent. It is possible that multiple people will be in charge of hauling a stone block. Every employee should routinely provide the task report to Pharaoh’s special agent, who does the task. The step-by-step procedure for the Meta–Heuristic Gizza Pyramid Construction Optimization Approach for Image Encryption using Logistic Map and DNA Encoding is expressed in the following equation:

$$
c _ {k} = \vartheta_ {k} f z \cos \tau ,\tag{12}
$$

where z implies the image block mass, f indicates the earth, $\tau$ implies angle that slope creates through horizon, and $c _ { k }$ denotes kinetic friction coeficient.

## Step 2: Random generation.

Input parameters create randomly. The optimum fitness value selection is depending on obvious hyper parameter situation.

## Step 3: Fitness function.

Generate random solution from initialization. It is determined by optimizing parameter by

$$
\mathrm{FitnessFunction} = \mathrm{optimizing} [ P (\xi) \mathrm{and} Y _ {G} ^ {(j)} ],\tag{13}
$$

where $P ( \zeta )$ increases the accuracy and $Y _ { G } ^ { ( j ) }$ decreases the computation time.

## Step 4: Giza pyramid for optimizing $P ( \zeta )$

The initial level of the construction process’s initial image is interrupted as part of the upgrading of the encryption process. The new option is expressed in the following equation:

$$
P (\xi) = - f (\sin \vartheta + \nu_ {q} \cos \vartheta),\tag{14}
$$

where $P ( \zeta )$ denotes current location, f denotes acceleration. sin ϑ denotes worker movement, a cos ϑ signifies random vector.

## Step 5: Minimization of multi-level sets for optimizing $Y _ { G } ^ { ( j ) }$

The basic concept behind the algorithm is to obtain the best dominance, contro over the stone block, and laborers pushing it must move or shake constantly. To better push the stone block, the worker is forced by these shocks to make nonrepetitive movements. The new positioning of the worker pushing the stone block

is attained by

$$
Y _ {G} ^ {(j)} = \frac {u _ {0} ^ {2}}{2 f \sin \vartheta},\tag{15}
$$

where $Y _ { G } ^ { ( j ) }$ denotes current position, $u _ { 0 } ^ { 2 }$ implies displacement value of stone block, f signifies amount of worker movement, sin ϑ implies random vector emulates Normal, Uniform or L´evy distribution $P ( \zeta )$

## Step 6: Termination.

The weight parameter value of generator $P ( \xi )$ and $Y _ { G } ^ { ( j ) }$ from PPINN is enhanced with GPCO; otherwise, step 3 is repeated until it obtains its halting criterion $C _ { k } =$ $C _ { k } + 1$ . The PPINN-FDIA-IIOT assesses the fault data injection by increasing the accuracy and lessening the computation time; the corresponding flow chart is shown in Fig. 2.

## Algorithm 1. Pseudo-code of Giza Pyramids construction algorithm

Step 1:

![](images/033371abb168076a513bd14be3bbec7170598264d08e6d02274b37eb1a033999.jpg)  
Fig. 2. Flowchart of GPCO to optimize PPINN parameter.

```txt
Create initial populace array of stone blocks otherwise workers (populace size);
    Create location, cost of stone block or worker;
Define best worker as Pharaoh's agent;
Step 2: for first iteration to max iteration do
Step 3: for i = 1 to n do (all n stone block or workers)
    Compute stone block dislocation count (Eq.);
Compute worker movement count (Eq.)
Assess new location (Eq.)
examine feasibility of substitute workers
compute new location with cost;
if new_cost < Pharaoh's agent cost then
setnew_cost as Pharaoh's agent cost;
end if
    END Step 3
    Sort solutions for subsequently iteration;
End Step 2
End Step 1
```

```txt
Algorithm 2. Pseudocode of proposed PPINN-FDIA-IIOT method
Input: Real-time IIoT Dataset
Output: FDIA classification (Simple, Stealthy, Stealthy & Collusive)
1. Data collection:
Gather real-time IIoT sensor data.
2. Preprocessing (DSMFF):
For each sensor data point:
Apply DSMFF to remove noise and irrelevant data
Store preprocessed dataset
3. Classification (PPINN):
Initialize PPINN architecture with multiple parallel networks.
Define input layer, hidden layers, and output layer.
Extract spatial-temporal features and classify FDIA
4. Optimization (GPCO):
Optimize PPINN weights using GPCO
5. Fault data injection attack detection:
Classify FDIA types using the optimized PPINN
6. End
```

## 4. Results and Discussions

In this section, Robust Industrial IoT Security Leveraging Parallel Physics Informed Neural Networks to Combat False Data Injection is discussed. The simulations are run in MATLAB on a SAMSUNG laptop that utilizes an Intel 2.40GHz Core i7 processor, Windows 10 Pro operating system, and 8.00 GB RAM. The PPINN technique efectively utilized temporal, spatial correlations in sensor data to detect falsified inputs, outperforming detection accuracy. Corrupted sensor readings can be efectively recovered from clean data using PPINN. The performance of the PPINN-FDIA-IIOT methodology is compared with existing techniques, such as FDIA detection in smart grid: secure federated deep learning method (FDIA-SG-SFDL), dissemination control in dynamic data clustering for dense IIoT against FDIA (DC-IIoT-FDIA), robust graph autoencoder-based FDIA detection against data poisoning in smart grids (RGA-FDIA-SG).

## 4.1. Performance measures

The eficiency of the proposed approach is evaluated under the metrics, like accu racy, mean square error, ROC, computation complexity, F1-score, and computation time.

## 4.1.1. Accuracy

It scales the performance of the classification method. It scales the rate of exact predictions generated by the method over the total count of predictions using the following equation:

$$
\text { Accuracy } = \frac {(\mathrm{TP} + \mathrm{TN})}{(\mathrm{TP} + \mathrm{FP} + \mathrm{TN} + \mathrm{FN})},\tag{16}
$$

where TN denotes true negative, TP implies true positive, FP as false positive, FN as false negative.

## 4.1.2. F1-score

It combines recall, precision into a single scale by computing the harmonic mean of them. F1-Score gives equal weights for precision, recall, which is more significant when imbalanced data is utilized for training. It is computed using the following equation:

$$
F 1 \mathrm{-score} = 2 \times \frac {\mathrm{recall} \times \mathrm{precision}}{\mathrm{recall} + \mathrm{precision}}.\tag{17}
$$

## 4.1.3. RoC

This is a graphical illustration that exemplifies trade-of amongst the rate of true and false positives for a binary classification scheme at diferent thresholds, and is computed by

$$
\mathrm{ROC} = 0. 5 \times \left(\frac {\mathrm{TP}}{\mathrm{TP} + \mathrm{FN}} + \frac {\mathrm{TN}}{\mathrm{TN} + \mathrm{TP}}\right).\tag{18}
$$

## 4.1.4. Mean square error

MSE measures the mean else average of square of variation between real and predicted values using the following equation:

$$
\mathrm{MSE} = \frac {1}{n} \sum_ {i = 1} ^ {n} \left(Y _ {i} - \hat {Y _ {i}}\right) ^ {2},\tag{19}
$$

where MSE signifies mean square error, n signifies number of data points, $Y _ { i }$ means experiential values, $\hat { Y _ { i } }$ means forecast values.

## 4.2. Performance analysis

The simulation results of the PPINN-FDIA-IIOT technique are shown in Figs. 3– 12. The PPINN-FDIA-IIOT approach was then analyzed with current techniques, including FDIA-SG-SFDL, DC-IIoT-FDIA, and RGA-FDIA-SG.

Figure 3 presents the accuracy analysis. Accuracy graphs plot the method’s accuracy over time, epochs, or various conditions. A steadily increasing accuracy

![](images/be441f76611c25a71a60071cd1a37e88e5d9b0647a2b245204ec3de5ffa0b361.jpg)  
Fig. 3. Accuracy analysis.

![](images/946ecdd34285db88fb717130c1a7ac3e658b1fd05e9cdb631f8df3b6f0579611.jpg)  
Fig. 4. F1-score analysis.

![](images/4bb73570d186dc0a1b6a9f0a6dbd88bf9e5871da1d4b18b1a7e8422b433dc2e5.jpg)  
Fig. 5. ROC analysis.

![](images/94db84a955acc6d4a157d6ca5be8ccf88f4bb01c9cfbd9c0aa8c078b4d37ed55.jpg)  
Fig. 6. Computational time analysis.

![](images/210cd2e6af22e2e8b841cf7fa1d57bed5039853f91b1744e1abc9fa6e9cf39e9.jpg)  
Fig. 7. Training with validation losses in training phase.

![](images/094a0bdba2062ac6e790684a49c91f5f652d2a4a2d38344947d07f6cb9b6e68b.jpg)  
Fig. 8. Computational complexity analysis.

![](images/36b2c08c5939614d6ab59ebdc3477b7688ab22916f8fe963bc1a16325b725846.jpg)  
Fig. 9. Result of varying readings per sensor on decision accuracy.

![](images/c671ebaa1feff280239f98a06cf55f6f6c07fca6ae95a109f473652d08ecc691.jpg)  
Fig. 10. Detection percentage and false alarm percentage.

![](images/fb71a2a5c9e82bfbde9defa79451c69d2e0175b192766ca4a98bc658e7f93812.jpg)  
Fig. 11. A visualization of a time series snapshot.

![](images/90d4b82f7ca469215c0b65cfe8d0053a6a5a1fc96f53083846712a2c9b64995c.jpg)  
Fig. 12. Convergence curve analysis.

curve indicates efective learning for adjustments. Here, the proposed PPINN-FDIA-IIOT method attains 27.73%, 25.46%, and 28.55% higher accuracy for Simple FDIA; 26.25%, 24.25%, and 28.45% higher accuracy for Stealthy FDIA; 29.95%, 23.88%, and 28.48% higher accuracy for Stealthy and collusive FDIA when comparing to the existing FDIA-SG-SFDL, DC-IIoT-FDIA, and RGA-FDIA-SG methods, respectively.

Figure 4 presents F1-score analysis. F1-score evaluates a model’s performance by providing a balanced measure of its ability to correctly identify relevant instances. It is particularly useful for datasets with imbalanced class distributions, as it reflects both the accuracy of positive predictions, ability to capture all relevant instances. Here, the proposed PPINN-FDIA-IIOT method attains 18.73%, 17.46%, and 15.55% higher F1-score for Simple FDIA; 19.25%, 20.25%, and 20.45% higher F1-score for Stealthy FDIA; 18.95%, 19.88%, and 20.48% higher F1-score for Stealthy and collusive FDIA when comparing to the existing FDIA-SG-SFDL, DC-IIoT-FDIA, and RGA-FDIA-SG methods, respectively.

Figure 5 portrays ROC analysis. Figure 5 shows the ROC plot for both devices. The relationship between false alarm and detection rate is called ROC. It attains a greater identification rate for the same false alarm rate when two strategies are compared. PPINN-dependent system outperforms ROC as well. Here, the proposed PPINN-FDIA-IIOT method attains 28.87%, 27.98%, and 29.19% higher RoC analyzed with existing methods like FDIA-SG-SFDL, DC-IIoT-FDIA, and RGA-FDIA-SG, respectively.

Figure 6 displays computational time analysis. Computational time analysis evaluates the eficiency of a model or algorithm by measuring the time required to complete its execution or processing tasks. This metric is crucial for assessing quickly whether a model can make predictions or process data, impacting its suitability for real-time applications. Here, PPINN-FDIA-IIOT attains 11.71%, 13.70%, and 15.70% lower computational time analyzed with existing methods like FDIA-SG-SFDL, DC-IIoT-FDIA, and RGA-FDIA-SG, respectively.

Figure 7 portrays training along with validation losses in the training segment analysis. Target values are set to equivalent input values during the training phase, and weights are changed iteratively over epochs to minimize MSE. No goal output is specified during validation or testing; instead, output is derived based on weights modified during training, and MSE is computed. Validation error is utilized for dual purposes. Initially, observed to prevent over-fitting. It determines the threshold that triggers an alarm (attack identified). To define whether input data are attacked, the testing error is evaluated with a threshold (for each input).

Figure 8 displays the Computational Complexity analysis. Computational complexity analysis examines the resources required by an algorithm, focusing on factors such as time and space as the input size grows. It assesses how the algorithm’s performance scales with increasing data, providing insights into its eficiency and feasibility for large-scale problems. By evaluating the complexity, one can determine whether the algorithm will perform adequately under various conditions and make informed decisions about its practicality and optimization needs. Here, PPINN-FDIA-IIOT attains 25.71%, 23.70%, and 28.70% higher computational complexity analyzed with existing methods like FDIA-SG-SFDL, DC-IIoT-FDIA, and RGA-FDIA-SG, respectively.

Figure 9 displays the result of varying readings per sensor on decision accuracy. It defines the percentage of entries that were correctly decided for the whole entries. It is challenging to identify a single malfunctioning (attacked) sensor. Furthermore, it is significantly more dificult to identify this kind of attack.

Figure 10 presents a comparison between two machines in terms of the percentage of false alarms and correct attack detection. The rate of Detection is the proportion of incorrect entries that the machine correctly detected out of all the entries in the figure. The percentage of clean entries that the machine imperfectly determined to be false data relative to all entries is known as the Rate of False

Alarm. It is supported by PPINN’s ability to uncover intricate data correlation structures that are concealed.

Figure 11 provides a snapshot of a piece of test data time series, the choice made by both machines, to improve the visualization of results. The ability of PPINN to learns data structure outcomes in better performance of accuracy. It portrays fewer misdetections with false alarms in PPINN. It is mentioned that PPINN isn’t better than instant. However, PPINN attains better average performance and, greater percentage of detection.

Figure 12 depicts convergence curve analysis. The convergence curves for three optimization algorithms as PSO,<sup>42</sup> Artificial Gorilla Troops Optimizer (AGTO)<sup>43</sup> and the proposed GPCO approach. It displays the objective function value after 100 iterations. The GPCO approach converges the fastest, attaining a near-optimal solution with fewer oscillations, while PSO and AGTO take longer to stabilize. This demonstrates the eficiency of GPCO in optimizing performance, which is used in robust industrial IoT security systems to resist false data injections.

Table 2 compares the proposed PPINN-FDIA-IIOT with state-of-the-art methods depending on performance parameters. The PPINN-FDIA-IIOT method greatly outperforms previous techniques, attains better accuracy of 99.3%, precision of 98.5%, F1-score of 97.51% and RoC of 0.99 while requiring the least computing time. In contrast, previous approaches have poorer accuracy, precision and F1-scores, as well as computational times ranging from 110 s to 254 s. The results show that PPINN-FDIA-IIOT is eficient and robust in detecting defects in industrial IoT systems.

## 4.3. Statistical analysis

Table 3 employs ANOVA to evaluate the performance diferences among various methods by comparing the means of existing methods. The analysis examines differences both between and within the methods to give an understanding of the proposed PPINN-FDIA-IIOT efectiveness. The metrics, such as Degree of Freedom (DF), Mean Square (MS), Sum of Square (SS), F-value, and P-value, are delineated.

Table 2. Comparative study with state-of-the-art models.

<table><tr><td rowspan="2">Authors</td><td colspan="2">Performance metrics</td><td rowspan="2">F1-score (%)</td><td rowspan="2">RoC (%)</td><td rowspan="2">Computational time (s)</td></tr><tr><td>Accuracy (%)</td><td>Precision (%)</td></tr><tr><td>Li et al.31</td><td>80.23</td><td>79.34</td><td>67.18</td><td>0.91</td><td>254</td></tr><tr><td>Pedroso and Santos32</td><td>78.15</td><td>81.34</td><td>72.45</td><td>0.92</td><td>216</td></tr><tr><td>Takiddin et al.33</td><td>82.56</td><td>77.56</td><td>58.17</td><td>0.93</td><td>231</td></tr><tr><td>Tian et al.34</td><td>68.43</td><td>68.2</td><td>78.34</td><td>0.89</td><td>189</td></tr><tr><td>Bhattacharjee et al.35</td><td>74.6</td><td>75.45</td><td>69.15</td><td>0.94</td><td>207</td></tr><tr><td>Ahmad et al.36</td><td>82.76</td><td>71.56</td><td>70.34</td><td>0.95</td><td>110</td></tr><tr><td>Gaber et al.37</td><td>80.47</td><td>80.41</td><td>71.48</td><td>0.96</td><td>124</td></tr><tr><td>Wang et al.38</td><td>79.45</td><td>81.28</td><td>82,67</td><td>0.97</td><td>120</td></tr><tr><td>PPINN-FDIA-IIOT (Proposed)</td><td>99.3</td><td>98.5</td><td>97.51</td><td>0.99</td><td>99</td></tr></table>

Table 3. ANOVA examination.

<table><tr><td>Source of variation</td><td>SS</td><td>DF</td><td>MS</td><td>F-value</td><td>P-value</td></tr><tr><td>Between methods</td><td>150.4</td><td>2</td><td>75.2</td><td>5.48</td><td>0.012</td></tr><tr><td>Within methods</td><td>395.6</td><td>27</td><td>14.65</td><td></td><td></td></tr><tr><td>Total</td><td>546.0</td><td>29</td><td></td><td></td><td></td></tr></table>

The ANOVA results assess the variation in performance between the various approaches utilized in the study. The Between approaches row demonstrates that the variation induced by the various approaches (with a sum of squares of 150.4) is statistically significant, as evidenced by a 5.48 F-value and 0.012 P-value (less than 0.05). This shows that at least one strategy performs significantly diferently from the rest. The Within Methods row displays the variation within the distinct methods, while the Total row depicts the overall variation in the data. The modest P-value confirms that the method has a substantial impact on the results.

## 4.4. Discussion

The study presents a novel approach for Robust Industrial IoT Security Leverag ing Parallel Physics Informed Neural Networks to Combat False Data Injection. This method leverages PPINN to capture temporal and spatial correlations in sensor data, which enhances the detection of subtle anomalies. The integration of denoising PPINN efectively cleans corrupted data, improving detection accuracy. Compared to traditional methods like PPINN, the technique demonstrates superior performance, especially in handling unsupervised data and recovering from attacks. This approach ofers a robust and practical solution for enhancing data integrity and security in dynamic IIoT systems.

## 4.5. Case study

The attack taxonomy intends to help security analysts design secure and resilient IoT systems by revealing the underlying characteristics of IoT attacks, with a particular emphasis on providing robust anomaly detection and response mechanisms. Present a novel approach to recognizing and mitigating attack vectors such as fake data injection, system parameter manipulation, and data infiltration by leveraging PINNs that combine domain-specific physical models with real-time sensor data. These attacks frequently take advantage of old systems, weak network segmentation and insuficient authentication methods.

## Case study 1: Water treatment facility

A municipal water treatment facility uses a variety of IoT-based sensors, SCADA systems and Programmable Logic Controllers (PLCs) to regulate water quality, flow rates, chemical concentrations, and pump operations. These systems communicate via an industrial network and are critical to providing clean water to the public. In recent years, the plant has been attacked by various hacks similar to the 2020 Kemuri Water Company breach, including events including fraudulent data input into the system to manipulate chemical flow rates and pump operations. The attackers gained unauthorized access to the facility’s IoT network and began inserting fraudulent data into the chemical dosing system. This raised the possibility of hazardous chemical levels in the water supply, posing a significant risk to public health. The attackers also modified flow rate data to disrupt the distribution system. Similar to the Kemuri instance, the facility’s legacy systems and weak security practices left it vulnerable to targeted intrusions.

The Parallel PINNs model continuously monitors sensor data for anomalies that could signal FDI attacks, such as aberrant chemical flow rates or valve manipulations, as witnessed in the Kemuri Water Company attack. By including the physical principles regulating water treatment and distribution operations, the model can discern between normal changes in system behavior and those produced by malevolent interference, making it more resistant to misleading data inputs. The neural network architecture’s parallelization enables the system to quickly scale across vast and scattered IIoT networks, ensuring that improved security measures may be applied to even large-scale water treatment and distribution systems. The system detects aberrant patterns in data that break from established physical principles, giving an early warning mechanism for prospective cyberattacks and ensuring that any altered data is identified and repaired in real time.

## Case study 2: Control logic modification attack

In IIoT environments, control logic modification attacks, such as those observed in the Triton, TRISIS, and HatMan incidents, endanger the stability and safety of vital industrial infrastructure. These attacks frequently target PLCs and modify their control logic to disrupt real-time industrial processes, with potentially fatal efects. The attackers were able to remotely deploy malware to reprogram IIoT controllers, modify firmware, and install Remote Access Trojans (RATs), which provided persistent access while avoiding detection. To mitigate these advanced threats, the proposed technique includes a multi-layered security framework that is specifically designed to defend IIoT systems against control logic modification assaults. This framework focuses on adaptive anomaly detection and control logic integrity validation, adding an extra layer of protection against potential exploitation in PLCs and ICS.

The system continuously monitors IIoT devices such as PLCs, sensors and actuators for deviations from predicted behaviors using historical data and physical system models. This dynamic detection technique can detect aberrant control logic behaviors in real time, similar to how the TRITON malware altered PLC firmware and control procedures. ML models based on historical process data are used to detect anomalies that intentionally influence such as unexpected changes in valve operation, chemical flow rates.

## 5. Conclusion

This research proposed a new technique for robust industrial IoT security by leveraging PPINNs to combat false data injection. The detection technique ofers better detection performance when analyzed with PPINN methods. Since PPINN does not need labeled data for training, they are simpler to train. As PPINNs discover hidden, complex correlation structures in data, they are able to identify a variety of attacks. Parallel physics-informed neural network attack detection can identify any attack that may materially alter these correlation structures. Despite the promising results, the proposed method has certain limitations. The reliance on the GPCO introduces additional computational complexity, which may impact real-time applications in highly dynamic environments. The efectiveness of the method was evaluated under a specific dataset, which did not fully represent all possible attack scenarios or diverse industrial environments. In future work, plan to enhance the proposed framework by developing a hybrid security model that combines advanced deep learning techniques for improved anomaly detection. Additionally, incorporate transfer learning to adapt the model across diferent industrial IoT environments, ensuring robustness against evolving cyber threats. Exploring federated learning for decentralized security implementation and optimizing the framework for real-time threat mitigation on resource-constrained IoT devices will also be key directions.

## References

1. J. Tian, C. Shen, B. Wang, X. Xia, M. Zhang, C. Lin and Q. Li, LESSON: Multilabel adversarial false data injection attack for deep learning locational detection, IEEE Transactions on Dependable and Secure Computing 21(5) (2024) 4418–4432.

2. N. Kumar, P. Aryan, G. L. Raja and U. R. Muduli, Robust frequency-shifting based control amid false data injection attacks for interconnected power systems with communication delay, IEEE Transactions on Industry Applications 60(2) (2024) 3710– 3723.

3. S. Hu, X. Ge, X. Chen and D. Yue, Resilient load frequency control of islanded AC microgrids under concurrent false data injection and denial-of-service attacks, IEEE Transactions on Smart Grid 14(1) (2022) 690–700.

4. A. D. Syrmakesis, H. H. Alhelou and N. D. Hatziargyriou, Novel SMO-based detection and isolation of false data injection attacks against frequency control systems, IEEE Transactions on Power Systems 39(1) (2023) 1434–1446.

5. M. Jafari, M. A. Rahman and S. Paudyal, Optimal false data injection attacks against power system frequency stability, IEEE Transactions on Smart Grid 14(2) (2022) 1276–1288.

6. Z. Zhang, J. Hu, J. Lu, J. Cao and F. E. Alsaadi, Preventing false data injection attacks in LFC system via the attack-detection evolutionary game model and KF algorithm, IEEE Transactions on Network Science and Engineering 9(6) (2022) 4349– 4362.

7. X. Chen, S. Hu, Y. Li, D. Yue, C. Dou and L. Ding, Co-estimation of state and FDI attacks and attack compensation control for multi-area load frequency control systems under FDI and DoS attacks, IEEE Transactions on Smart Grid 13(3) (2022) 2357–2368.

8. S. Liu, Q. Li and B. Chen, Game theoretic vulnerability management for secondary frequency control of islanded microgrids against false data injection attacks, IET Cyber-Physical Systems: Theory & Applications 7(1) (2022) 4–15.

9. C. Chen, Y. Chen, J. Zhao, K. Zhang, M. Ni and B. Ren, Data-driven resilient auto matic generation control against false data injection attacks, IEEE Transactions on Industrial Informatics 17(12) (2021) 8092–8101.

10. C. Pei, Y. Xiao, W. Liang and X. Han, A deviation-based detection method against false data injection attacks in smart grid, IEEE Access 9 (2021) 15499–15509.

11. S. Zhao, Q. Yang, P. Cheng, R. Deng and J. Xia, Adaptive resilient control for variablespeed wind turbines against false data injection attacks, IEEE Transactions on Sustainable Energy 13(2) (2022) 971–985.

12. Y. Hu, P. Xun, P. Zhu, Y. Xiong, Y. Zhu, W. Shi and C. Hu, Network-based multidi mensional moving target defense against false data injection attack in power system, Computers & Security 107 (2021) 102283.

13. M. Jorjani, H. Seifi, A. Y. Varjani and H. Delkhosh, An optimization-based approach to recover the detected attacked grid variables after false data injection attack, IEEE Transactions on Smart Grid 12(6) (2021) 5322–5334.

14. M. Shahin, M. Maghanaki, A. Hosseinzadeh and F. F. Chen, Advancing network security in industrial IoT: A deep dive into AI-enabled intrusion detection systems, Advanced Engineering Informatics 62 (2024) 102685.

15. N. N. Tran, H. R. Pota, Q. N. Tran and J. Hu, Designing constraint-based false datainjection attacks against the unbalanced distribution smart grids, IEEE Internet of Things Journal 8(11) (2021) 9422–9435.

16. M. Jafari, M. A. Rahman and S. Paudyal, Optimal false data injection attack against load-frequency control in power systems, IEEE Transactions on Information Forensics and Security 18 (2023) 5200–5212.

17. B. Chen, Q. H. Wu, M. Li and K. Xiahou, Detection of false data injection attacks on power systems using graph edge-conditioned convolutional networks, Protection and Control of Modern Power Systems 8(2) (2023) 1–2.

18. P. Hu, W. Gao, Y. Li, F. Hua, L. Qiao and G. Zhang, Detection of false data injection attacks in smart grid based on joint dynamic and static state estimation, IEEE Access 11 (2023) 45028–45038.

19. Y. Zhang and S. Li, Kinematic control of serial manipulators under false data injection attack, IEEE/CAA Journal of Automatica Sinica 10(4) (2023) 1009–1019.

20. A. S. Musleh, G. Chen, Z. Y. Dong, C. Wang and S. Chen, Spatio-temporal datadriven detection of false data injection attacks in power distribution systems, International Journal of Electrical Power & Energy Systems 145 (2023) 108612.

21. K. D. Lu, Z. G. Wu and T. Huang, Diferential evolution-based three stage dynamic cyber-attack of cyber-physical power systems, IEEE/ASME Transactions on Mechatronics 28(2) (2022) 1137–1148.

22. K. D. Lu and Z. G. Wu, Multi-objective false data injection attacks of cyber–physical power systems, IEEE Transactions on Circuits and Systems II: Express Briefs 69(9) (2022) 3924–3928.

23. P. Hafizunisa, Rai and D. Sinha, False data injection attack detection using machine learning in industrial Internet of Things, in Optimized Computational Intelligence

Driven Decision-Making: Theory, Application and Challenges (Wiley, 2024), pp. 49– 68.

24. H. Nandanwar and R. Katarya, Deep learning enabled intrusion detection system for Industrial IOT environment, Expert Systems with Applications 249 (2024) 123808.

25. W. Choi, S. Pandey and J. Kim, Detecting cybersecurity threats for industrial contro systems using machine learning, IEEE Access 12 (2024) 153550–153563.

26. K. Dhanushkodi and S. Thejas, AI enabled threat detection: Leveraging artificial intelligence for advanced security and cyber threat mitigation, IEEE Access 12 (2024) 173127–173136.

27. F. Mesadieu, D. Torre and A. Chennameneni, Leveraging deep reinforcement learning technique for intrusion detection in SCADA infrastructure, IEEE Access (2024).

28. K. Hassini, S. Khalis, O. Habibi, M. Chemmakha and M. Lazaar, An end-to-end learning approach for enhancing intrusion detection in Industrial-Internet of Things, Knowledge-based Systems 294 (2024) 111785.

29. I. A. Soomro, S. J. Hussain, Z. Ashraf, M. M. Alnfiai and N. N. Alotaibi, Lightweight privacy-preserving federated deep intrusion detection for industrial cyber-physical system, Journal of Communications and Networks 26(6) (2024) 632–649.

30. R. Zhao, H. Song, H. Wen, Z. Chen, W. Hou and X. Feng, Wireless security enhancement framework based on AI and RIS in industrial IoT networks, IEEE Network 39(4) (2025) 29–36.

31. Y. Li, X. Wei, Y. Li, Z. Dong and M. Shahidehpour, Detection of false data injection attacks in smart grid: A secure federated deep learning approach, IEEE Transactions on Smart Grid 13(6) (2022) 4862–4872.

32. C. Pedroso and A. Santos, Dissemination control in dynamic data clustering for dense IIoT against false data injection attack, International Journal of Network Management 32(5) (2022) e2201.

33. A. Takiddin, M. Ismail, R. Atat, K. R. Davis and E. Serpedin, Robust graph autoencoder-based detection of false data injection attacks against data poisoning in smart grids, IEEE Transactions on Artificial Intelligence 5(3) (2023) 1287–1301.

34. J. Tian, B. Wang, J. Li and C. Konstantinou, Data-driven false data injection attacks against cyber-physical power systems, Computers & Security 121 (2022) 102836.

35. A. Bhattacharjee, A. K. Mondal, A. Verma, S. Mishra and T. K. Saha, Deep latent space clustering for detection of stealthy false data injection attacks against AC state estimation in power systems, IEEE Transactions on Smart Grid 14(3) (2022) 2338– 2351.

36. J. Ahmad, S. A. Shah, S. Latif, F. Ahmed, Z. Zou and N. Pitropakis, DRaNN PSO: A deep random neural network with particle swarm optimization for intrusion detection in the industrial internet of things, Journal of King Saud University-Computer and Information Sciences 34(10) (2022) 8112–8121.

37. T. Gaber, J. B. Awotunde, S. O. Folorunso, S. A. Ajagbe and E. Eldesouky, Industrial internet of things intrusion detection method using machine learning and optimization techniques, Wireless Communications and Mobile Computing 2023(1) (2023) 3939895.

38. X. Wang, M. Hu, X. Luo and X. Guan, A detection model for false data injection attacks in smart grids based on graph spatial features using temporal convolutiona neural networks, Electric Power Systems Research 238 (2025) 111126.

39. K. Zhu, Z. Wang, Q. L. Han and G. Wei, Distributed set-membership fusion filtering for nonlinear 2-D systems over sensor networks: An encoding–decoding scheme, IEEE Transactions on Cybernetics 53(1) (2021) 416–427.

40. K. Shukla, A. D. Jagtap and G. E. Karniadakis, Parallel physics-informed neural networks via domain decomposition, Journal of Computational Physics 447 (2021) 110683.

41. S. Harifi, J. Mohammadzadeh, M. Khalilian and S. Ebrahimnejad, Giza Pyramids Construction: An ancient-inspired metaheuristic algorithm for optimization, Evolu tionary Intelligence 14(4) (2021) 1743–1761.

42. F. H. Zhou and Z. Z. Liao, A particle swarm optimization algorithm, Applied Mechanics and Materials 303 (2013) 1369–1372.

43. B. Abdollahzadeh, F. Soleimanian Gharehchopogh and S. Mirjalili, Artificial gorilla troops optimizer: A new nature-inspired metaheuristic algorithm for global optimiza tion problems, International Journal of Intelligent Systems 36(10) (2021) 5887–5958.

44. N., Nagarani, R. Karthick, M.S.C. Sophia and M. B. Binda, Self-attention based progressive generative adversarial network optimized with momentum search optimization algorithm for classification of brain tumor on MRI image, Biomedical Signal Processing and Control 88, (2024)105597.

45. R. Reka, R. Karthick, R. S. Ram and G. Singh, Multi head self-attention gated graph convolutional network based multi-attack intrusion detection in MANET, Computers & Security 136, (2024) 103526.

46. P. Meenalochini, R. Karthick, and E. Sakthivel, An Eficient Control Strategy for an Extended Switched Coupled Inductor Quasi-Z-Source Inverter for 3 θ Grid Connected System, Journal of Circuits, Systems and Computers 32(11), (2023) 2450011.

47. R. Karthick, A. Senthilselvi, P. Meenalochini and S. Senthil Pandi, An optimal partitioning and floor planning for VLSI circuit design based on a hybrid bio-inspired whale optimization and adaptive bird swarm optimization (WO-ABSO) algorithm, Journal of Circuits, Systems and Computers 32(8), (2023) 2350273.

48. J. Jasper Gnana Chandran, R. Karthick, R. Rajagopal and Meenalochini, Dual channel capsule generative adversarial network optimized P., with golden eagle opti mization for pediatric bone age assessment from hand X-ray image, International Journal of Pattern Recognition and Artificial Intelligence 37 (2), (2023) 2354001.

49. R.K.P.M.T.K.R. Rajagopal, Karthick P. Meenalochini and T. Kalaichelvi, Deep Convolutional Spiking R., Neural Network optimized with Arithmetic optimization algorithm for lung disease detection using chest X-ray images, Biomedical Signal Processing and Control 79, (2023) 104197.