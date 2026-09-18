---
title: "2024-Zhou-ETGuard"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/encrypted/2024-Zhou-ETGuard.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# ETGuard: Malicious Encrypted Trafic Detection in Blockchain-based Power Grid Systems

Peng Zhou<sup>1</sup>, Yongdong Liu<sup>2,⋆</sup>, Lixun Ma<sup>2</sup>, Weiye Zhang<sup>2</sup>, Haohan Tan<sup>2</sup>, Zhenguang Liu<sup>2</sup>, and Butian Huang<sup>2</sup>

<sup>1</sup> State Grid Zhejiang Electric Power Company, LTD. Information and Communication Branch, China

<sup>2</sup> Zhejiang University, Hangzhou, Zhejiang Province, China {malx}@zju.edu.cn

Abstract. The escalating prevalence of encryption protocols has led to a concomitant surge in the number of malicious attacks that hide in encrypted trafic. Power grid systems, as fundamental infrastructure, are becoming prime targets for such attacks. Conventional methods for detecting malicious encrypted packets typically use a static pre-trained model. We observe that these methods are not well-suited for blockchainbased power grid systems. More critically, they fall short in dynamic environments where new types of encrypted attacks continuously emerge.

Motivated by this, in this paper we try to tackle these challenges from two aspects: (1) We present a novel framework that is able to automatically detect malicious encrypted trafic in blockchain-based power grid systems and incrementally learn from new malicious trafic. (2) We mathematically derive incremental learning losses to resist the forgetting of old attack patterns while ensuring the model is capable of handling new encrypted attack patterns. Empirically, our method achieves state-ofthe-art performance on three diferent benchmark datasets. We also constructed the first malicious encrypted trafic dataset for blockchain-based power grid scenario. Our code and dataset are available at https://github. com/PPPmzt/ETGuard, hoping to inspire future research.

Keywords: Blockchain · Network security · Malicious encrypted trafic detection · Incremental learning.

## 1 Introduction

The immutable and decentralized nature of blockchain has led to applications such as Bitcoin, decentralized crowdfunding, and cross-industry finance [31]. While research often focuses on system and software issues like consensus mechanisms [29], smart contracts [18], and virtual machines, cybersecurity challenges, particularly malicious trafic attacks, are often neglected.

In blockchain-based power systems, critical national infrastructure, malicious trafic poses severe risks such as widespread power outages and energy data breaches. Although encryption protocols are widely adopted to secure data, they can be exploited by attackers to hide malicious activities. Detecting malicious encrypted trafic in power systems involves distinguishing attack patterns from benign packets [15]. Research in this area generally follows two approaches: one [12,7,9] uses decryption analysis to reveal clues in encrypted sequences, while another [22,23] examines statistical diferences using deep learning. Current methods face two main issues: poor performance on blockchain-based power grids, leading to a significant drop in F1 scores, and dificulties with novel attack sequences due to reliance on static models.

To address these challenges, we propose a novel approach incorporating incremental learning to adapt to new attacks. Our method involves training a model with self-supervised learning to extract detailed packet features and deriving incremental learning losses to preserve old data while learning new attack patterns. We update the model using replayed samples combined with these losses. Additionally, we introduce the GridET-2024 dataset, which includes real-world trafic data from the State Grid of China, to evaluate detection in blockchainbased power grid scenarios. To evaluate our method, we conducted extensive experiments on three benchmark datasets, as well as ablation studies to assess key components. Our method demonstrates state-of-the-art performance on these datasets. In summary, our contributions are as follows:

• We propose ETGuard, a novel framework for detecting malicious encrypted trafic in blockchain-based power grids. It is the first method to automatically identify these attacks and adapt to new trafic patterns incrementally.

• We derive a loss function for efective incremental learning, supported by rigorous theoretical analysis, to manage new attack patterns while mitigating catastrophic forgetting. Additionally, we introduce a sample bufer for eficient storage and replay of representative trafic samples.

• We have collected real-world data from blockchain-based power grid systems and created the GridET-2024 dataset, the first of its kind for detecting malicious encrypted trafic in this context. Our method achieves state-of-the-art performance on several benchmark datasets.

## 2 Problem Statement

Problem formulation. Given a sequence of encrypted packets $s = \{ p _ { 1 } , p _ { 2 } , . . . , p _ { n } \}$ we are interested in developing a fully automated model to determine whether the packet sequence is malicious. Put diferently, we aim to estimate the label yˆ for each encrypted packet sequence s, where yˆ = 1 represents s is a malicious sequence, and $\hat { y } = 0$ indicates that s is benign.

## 3 Method

Method Overview The detailed architecture of our proposed framework is outlined in Fig. 1. Overall, the framework consists of three key components:

• Data Preprocessing: Raw packets are cleaned and processed, ensuring that the packets from an individual client are sorted into a packet sequence and are separated from the packets of other clients. To extract features from these sequences, we use an unsupervised auto-encoder with stacked bi-GRUs.

• Incremental Learning Module: To adapt to novel attacks while preventing catastrophic forgetting, we introduce an incremental learning module and mathematically derive the incremental learning losses.

• Detection Module: The detection module learns the feature distinctions between benign and malicious sequences to continuously identify potential attacks. The learning process is supervised by the classification loss and incremental learning losses.

In what follows, we will elaborate on the details of these components one by one.

![](images/ad53a70e521f25ae9341755eb3608d31197f98ed6584ee7652d7d91f294d159d.jpg)  
Fig. 1: The framework of ETGuard.

## 3.1 Data Preprocessing

The preprocessing module aims to clean and process raw packet data into distinct sequences for diferent clients. Since packet sequences cannot be directly input into a network, we employ an unsupervised auto-encoder with stacked bi-GRUs to extract features from each client’s packet sequence.

Specifically, raw trafic data consists of packets organized by a five-tuple (i.e., source and destination IP addresses, source and destination ports, and transport layer protocol). We group packets with the same five-tuple into sequences s and sort them chronologically. Irrelevant packet information, such as IP addresses and port numbers, is removed from each sequence.

The resulting sequences, $s _ { i n p u t }$ , are formatted with components $l , \ d ,$ and $t _ { m } ,$ where: $l = \{ b _ { 1 } , b _ { 2 } , \ldots , b _ { n } \}$ denotes the packet length sequence, $d = t _ { n } - t _ { 1 }$ represents the duration of $s _ { i n p u t } , t _ { m }$ is the mean time interval between packets.

The feature extractor uses an auto-encoder with multiple bi-directional Gated Recurrent Units (bi-GRUs) [8], serving as both encoder and decoder. The encoder transforms the input sequence into a feature vector, which the decoder uses to reconstruct the sequence. A multi-layer perceptron in the reconstruction layer restores the original embedded sequence. The encoder learns an accurate representation of encrypted network trafic by minimizing reconstruction loss during training.

Compared to traditional methods [2,3,16] that focus on specific versions of TLS handshake metadata or message types [23], our approach captures the finegrained behavior of network trafic more efectively.

## 3.2 Mathematical Derivation of Incremental Learning Objectives

In this subsection, we introduce the incremental learning module, and provide the key mathematical derivations of incremental learning objectives within this module.

We use the incremental learning method based on empirical replay [24,6,27] with targeted modifications for encrypted trafic scenarios to realize the incremental update of the model when facing new types of trafic attack. Specifically, we maintain a sample bufer to store representative trafic samples. When new malicious encrypted trafic arises, we incrementally update the model through a anti-forgetting loss function to detect new attack patterns. The new trafic samples are updated into the bufer using a reservoir sampling algorithm [28], serving as a representative sample set for subsequent incremental model updates.

Sample Bufer The sample bufer is used to store representative trafic samples to achieve experience replay during incremental learning. When the model learns new trafic patterns, it replays previous samples from the sample bufer to efectively prevent catastrophic forgetting. We implement the update of the sample bufer using the reservoir sampling algorithm. When new trafic samples arrive, the sample bufer is dynamically updated to ensure diversity and representativeness.

Incremental Learning Loss Function The goal of the incremental learning module is to detect the ongoing emergence of new malicious trafic attacks. To enable the model to learn from new datasets, the loss function and optimization objectives are defined as follows:

$$
\min _ {\theta} \mathcal {L} _ {c e} = \mathbb {E} _ {(x, y) \sim D} [ \ell (f _ {\theta} (x), y) ],\tag{1}
$$

where θ denotes the model parameters, $\mathcal { L } _ { c e }$ represents the loss function using cross-entropy, D denotes the dataset, $f _ { \boldsymbol { \theta } } ( \boldsymbol { x } )$ denotes the detection model, and y denotes the true target of the sample.

To mitigate catastrophic forgetting, we introduce a new loss function aimed at balancing the learning between new and old data. We use the past data on the updated model to obtain an output $f _ { \boldsymbol { \theta } } ( \boldsymbol { x } )$ that closely approximates the output of the pre-update model trained on past trafic data, denoted as $f _ { \theta * t }$

$$
\mathcal {L} _ {i l} = \alpha \mathbb {E} _ {(x, z) \sim \mathcal {M}} \left[ D _ {K L} (\operatorname{softmax} (z) | | f _ {\theta} (x)) \right].\tag{2}
$$

In the above equation, z represents the output logits of the model on the past trafic data. In order to reduce the resource consumption, we use z to replace the model output $f _ { \theta * t }$ . The logits z are softmaxed to obtain the probability vector, which is used to calculate the KL scatter with the model output $f _ { \boldsymbol { \theta } } ( \boldsymbol { x } )$

Theorem 1. If two logits output by the model are similar, the KL divergence between them can be approximated as the Euclidean distance.

Proof. Assume logits $z _ { 1 }$ and logits $z _ { 2 }$ are two close vectors, we set the sample space of logits $z , R = \{ 1 , . . . , n \}$ , n is the dimension of logits z, so we can express $z _ { 2 }$ as:

$$
z _ {2} = z _ {1} + \epsilon \Delta z,\tag{3}
$$

for some small $\epsilon > 0$ and perturbation vecto $\varDelta z = [ \varDelta z ( 1 ) \cdot \cdot \cdot \varDelta z ( n ) ] ^ { T }$ . Next, we approximate the KL divergence locally.

$$
D _ {K L} (z _ {1} \| z _ {2}) = \sum_ {i \in R} z _ {1} (i) \log \left(\frac {z _ {1} (i)}{z _ {2} (i)}\right).\tag{4}
$$

Substituting $z _ { 2 } ( i ) = z _ { 1 } ( i ) + \epsilon \Delta z ( i )$ into the KL divergence formula gives:

$$
D _ {K L} (z _ {1} \| z _ {2}) = \sum_ {i \in R} z _ {1} (i) \log \left(\frac {z _ {1} (i)}{z _ {1} (i) + \epsilon \Delta z (i)}\right).\tag{5}
$$

Applying the second-order Taylor approximation to log $\left( \frac { z _ { 1 } ( i ) } { z _ { 1 } ( i ) + \epsilon \varDelta z ( i ) } \right)$

$$
D _ {K L} (z _ {1} \| z _ {2}) = \frac {\epsilon^ {2}}{2} \sum_ {i \in R} \frac {\varDelta z (i) ^ {2}}{z _ {1} (i)} + o (\epsilon^ {2}).\tag{6}
$$

This implicitly assumes $z _ { 1 } ( i ) > 0$ for all $i \in R$ . Introducing the weighted Euclidean norm, the KL divergence becomes:

$$
D _ {K L} (z _ {1} \| z _ {2}) = \frac {\epsilon^ {2}}{2} \| \varDelta z \| _ {z _ {1}} ^ {2} + o (\epsilon^ {2}) = \| z _ {1} - z _ {2} \|.\tag{7}
$$

Thus, under the local approximation, the KL divergence approximates a weighted Euclidean distance.

By Theorem 1, $\mathcal { L } _ { i l }$ can be simplified to:

$$
\mathcal {L} _ {i l} = \alpha \mathbb {E} _ {(x, z) \sim \mathcal {M}} \left[ \| z ^ {\prime} - g (x ^ {\prime}) \| _ {2} ^ {2} \right].\tag{8}
$$

To handle significant changes in new attack patterns and avoid bias towards previous patterns, we introduce a smoothness loss function:

$$
\mathcal {L} _ {l b} = \beta \mathbb {E} _ {(x ^ {\prime \prime}, y ^ {\prime \prime}, z ^ {\prime \prime}) \sim \mathcal {M}} \left[ \ell (y ^ {\prime \prime}, h (x ^ {\prime \prime})) \right].\tag{9}
$$

To balance the contributions of $\mathcal { L } _ { i l }$ and $\mathcal { L } _ { l b } .$ we use a coeficient k:

$$
k = 0. 5 + \mathrm{softmax} (\mathcal {L} _ {i l} \cdot \gamma).\tag{10}
$$

The final loss function is:

$$
\mathcal {L} _ {c e} + \alpha \mathbb {E} _ {(x ^ {\prime}, y ^ {\prime}, z ^ {\prime}) \sim \mathcal {M}} \left[ \| z ^ {\prime} - g (x ^ {\prime}) \| _ {2} ^ {2} \right] + k \alpha \mathbb {E} _ {(x ^ {\prime \prime}, y ^ {\prime \prime}, z ^ {\prime \prime}) \sim \mathcal {M}} \left[ \ell (y ^ {\prime \prime}, h (x ^ {\prime \prime})) \right].\tag{11}
$$

## 3.3 Detection Module

Due to the substantial volume of trafic data and the high trafic rate in the blockchain-based power grid scenario, the real-time performance and resource consumption of the model are critically demanding. The MLP model architecture, being relatively simple, requires lower computing resources and ofers faster training speeds. It is capable of monitoring trafic data in real time, and experiments have demonstrated that the MLP model is suficient to meet the task requirements. Therefore, the MLP model is chosen to detect malicious trafic.

## 4 Evaluations

In this section, we conduct extensive experiments on multiple malicious encrypted trafic detection datasets to evaluate our framework. Next, we introduce the experimental setup, followed by presenting the comprehensive empirical results.

## 4.1 Experimental Setup

Datasets

• CIRA-CIC-DoHBrw-2020 (DoHBrw) [21]: The DoHBrw dataset provides a mix of benign and malicious DNS-over-HTTPS (DoH) trafic, all data is encrypted trafic. The normal trafic is generated by querying benign DNS servers using the DoH protocol. Tunneling tools such as dns2tcp, DNSCat2, and Iodine are used to generate malicious DoH trafic.

• CIC-AndMal2017 (CIC) [14]: CIC collected a rich variety of malicious attacks from several sources. The malicious trafic samples come from 42 unique malware families, which can be classified into four categories: Adware, Ransomware, Scareware, and SMS Malware.

• GridET-2024 (GridET): To better detect the encrypted attacks of realworld blockchain-based power grid scenario, we create the dataset GridET-2024. Benign trafic samples are collected by capturing power grid system interaction trafic data. Malicious trafic data samples are sourced from malware-trafic-analysis.net and USTC-TFC2016 dataset to ensure the diversity of malicious trafic attack patterns.

Implementation Details We implement our detection framework and all baselines by using Python 3.8.5. We run these models on a Linux server with NVIDIA GeForce RTX 3090 GPU. We list all the parameters used by our framework in Table 2. In particular, we set n = 50 and d = 32 to make a better capability of capturing fine-grained behaviors of network trafic. Then, we apply Grid Search to find the appropriate values for α and γ. The values of α and γ are 0.5 and 10, respectively. In particular, bufer size is a hyperparameter manually tuned to best fit the specific scenario. We conduct comprehensive experiments to evaluate the performance of ETGuard with various bufer sizes.

Table 1: Statistics of Datasets

<table><tr><td>Dataset</td><td>Normal</td><td>Malicious</td></tr><tr><td>DoHBrw</td><td>688,489</td><td>6,112</td></tr><tr><td>CIC</td><td>894,367</td><td>62,972</td></tr><tr><td>GridET</td><td>43,611</td><td>27,141</td></tr></table>

Table 2: Parameter Settings of ETGuard

<table><tr><td>Module</td><td colspan="2">Para. Value</td><td>Description</td></tr><tr><td rowspan="4">Feature Extraction</td><td>n</td><td>50</td><td>Number of used head packets</td></tr><tr><td>V</td><td>32</td><td>Embedding size of GRU-AE</td></tr><tr><td>H</td><td>8</td><td>Hidden size of each GRU layer</td></tr><tr><td>B</td><td>2</td><td>Number of GRU layers</td></tr><tr><td rowspan="2">Incremental Learning</td><td> $\alpha$ </td><td>0.5</td><td>Coefficient of loss  $L_{2}$ </td></tr><tr><td> $\gamma$ </td><td>10</td><td>Coefficient to balance loss  $L_{2}$  and loss  $L_{3}$ </td></tr></table>

Evaluation Metrics We use ACC and F1 Score as metrics to evaluate the malicious trafic detection and incremental learning performance of ETGuard.

## 4.2 Performance on Malicious Encrypted Trafic Detection

In this section, we benchmark our method against state-of-the-art malicious encrypted trafic detection methods for two public dataset and one power grad scenario dataset GridET.

In public dataset evaluations, we train and test methods on DoHBrw, and CIC, respectively. Fig. 2 presents public dataset comparison results. From Fig. 2, we observe that our method is capable of consistently outperforming existing methods on all five benchmarks. For example, the F1 score of our method is 0.92 on DoHBrw while the state-of-the-art detection method RAPIER [23] is 0.88. The F1 score of our method is also outperformed FS [17] in all datasets. In addition, we also use the CoinFlip algorithm and PacketLen algorithm, which simulate randomly guess and only utilize packet length, respectively, to detect encrypted trafic.

Table 3: F1 scores of Malicious Encrypted Trafic Detection Methods

<table><tr><td>Dataset</td><td>RAPIER</td><td>FS</td><td>CoinFlip</td><td>PacketLen</td><td>ETGuard (Ours)</td></tr><tr><td>DoHBrw</td><td>0.88</td><td>0.76</td><td>0.28</td><td>0.56</td><td>0.92</td></tr><tr><td>CIC</td><td>0.84</td><td>0.71</td><td>0.27</td><td>0.46</td><td>0.86</td></tr><tr><td>GridET</td><td>0.83</td><td>0.73</td><td>0.31</td><td>0.49</td><td>0.94</td></tr></table>

The blockchain-based power grid scenario malicious trafic detection is more challenging for existed detection methods. To evaluate the detection abilities of the methods on this scenario, we train and test the models on the GridET dataset. Table 3 demonstrate the state-of-the-art malicious encrypted trafic detection methods still sufer from relatively low F1 score on the GridET dataset, which reveals that such methods are fall short to extract the critical features of trafic sample in the blockchain-based power grid scenario.

![](images/c53d3f7d725d105ce50b1a5cb34a2d10de081de34d6706a5303e8fb89e684de7.jpg)  
Fig. 2: Performance on Malicious Encrypted Trafic Detection.

Overall, our method achieves state-of-the-art general scenarios and blockchainbased power grid scenario malicious encrypted trafic detection performance. For general scenarios comparisons, our method improves the F1 score on DoHBrw from 0.88 to 0.92, and on CIC from 0.84 to 0.86. In contrast with general scenarios methods, our method also attains 0.94 F1 score on GridET, outperforming the current state-of-the-art method RAPIER.

## 4.3 Performance on Incremental Learning

To evaluate the performance of our method on incremental learning, we create a new dataset DoHBrw/CIC. Specifically, we combine all benign samples from the DoHBrw dataset with a selection of malicious samples from the CIC dataset. We further divide the datasets into six sub-datasets $\left\{ A _ { 0 } , A _ { 1 } , A _ { 2 } , A _ { 3 } , A _ { 4 } , A _ { 5 } \right\}$ . In each of these sub-datasets, the benign trafic is all of the same type DoHBrw, while the malicious trafic all consists of diferent types of malicious attacks. We use $A _ { 0 }$ for pre-training the model, while the other sub-datasets are used for incremental updates to the model. We established a separate test set for each round, where the test set for round i includes all attack types observed from rounds 0 to i.

We compare ETGuard against five incremental learning methods (ER [25], DER [6], DER++ [6], GSS [1], SI [30]) on DoHBrw/CIC. To assess the eficacy of the incremental learning module within our approach, we extracted this component from ETGuard, resulting in a variant dubbed ETGuard-V. We then evaluated the performance of ETGuard-V to conduct an ablation study. We further provide an upper bound given by training all attack samples (FULL).

Fig. 3 reports performance in terms of average accuracy across all rounds. Experimental evidence ETGuard achieve state-of-the-art performance in almost all settings.

![](images/55108e5a408b2ad134e4d718f2f9ee1814270de06a2bfd7035a3d6624b6f5726.jpg)  
Fig. 3: The Performance of Incremental Learning Methods.

![](images/51c5a4cbf7bbc44bd434e13e5fa6d8b64d7785a64a4a52dda7bba0ab065ca2e8.jpg)  
Fig. 4: The Performance of Incremental Learning Methods in Diferent Round.  
At the same time, we observe that the performance of ETGuard is almost always better than that of ETGuard-V. And as the number of rounds increases, the gap in detection performance between ETGuard-V and ETGuard gradually widens, which further proves the efectiveness of our incremental learning module.

## 5 Related Work

## 5.1 Malicious Encrypted Trafic Detection

Traditional malicious encrypted trafic detection mainly uses signature-based methods [12,7,9] to detect malicious encrypted trafic. However, the method relies heavily on the quality of decryption operations and rules for trafic [13,4]. With the growth of artificial intelligence technology[26,19], machine learning is increasingly being adopted for detecting malicious encrypted trafic. Machine learning enhances detection by extracting statistical features from trafic, ofering faster and more accurate results compared to traditional methods. For example, Fu et al, utilized frequency domain features for real-time detection [11]. Barradas et al, detect attacks by applying random forests [5]. In addition to traditional trafic detection or packet inspection [20,3], Fang et al. [10], on the other hand, detects TLS trafic by collecting features of the trafic communication channel (packets consisting of the same destination IP and destination port) and uses Random Forest (RF) to enhance malware trafic detection performance. All these methods are not efective in detecting attacks on new encrypted trafic.

## 5.2 Incremental Learning

The core challenge of incremental learning is to balance the conflict between remembering information about old tasks and absorbing information about new tasks, the so-called catastrophic forgetting problem. To overcome this problem, existing methods fall into two main categories: replay-based methods and parameter optimization-based methods. Replay-based methods mitigate Catastrophic Forgetting by replaying some samples of old tasks while learning new ones. The replayed samples can be real historical data, i.e., empirical replay. It can also be pseudo-samples generated by generative models (e.g., Generative Adversarial Networks, GAN), i.e., generative replay. iCaRL [24] is a representative of the empirical replay-based approach, which combines knowledge distillation methods to update the model parameters on a representative sample pool. However, iCaRL updates the parameters of old tasks and therefore sufers from overfitting to old data.

## 6 Conclusion

In this paper, we try to tackle the malicious encrypted trafic detection problem from two aspects: (1) We propose a novel framework termed ETGuard, which to our knowledge is the first approach tailored for automatically identifying malicious trafic attacks in blockchain-based power grid systems. (2) We lay the mathematical foundation for establishing an incremental learning model that can efectively adapt to new types of attacks. We utilized real data collected from the State Grid and constructed the malicious encrypted trafic dataset GridET. We extensively evaluated the proposed method on three benchmark datasets. Empirical results show that our method consistently delivers state-of-the-art performance on malicious encrypted trafic detection across general scenarios and the blockchain-based power grid scenario.

Acknowledgments. This work was supported by State Grid Zhejiang Electric Power Company, LTD. Information and Communication Branch, China (Grant number 5211XT 24000D).

## References

1. Aljundi, R., Lin, M., Goujaud, B., Bengio, Y.: Gradient based sample selection for online continual learning. Advances in neural information processing systems 32 (2019)

2. Anderson, B., McGrew, D.: Identifying encrypted malware trafic with contextual flow data. In: Proceedings of the 2016 ACM workshop on artificial intelligence and security. pp. 35–46 (2016)

3. Anderson, B., McGrew, D.: Machine learning for encrypted malware trafic classification: accounting for noisy labels and non-stationarity. In: Proceedings of the 23rd ACM SIGKDD International Conference on knowledge discovery and data mining. pp. 1723–1732 (2017)

4. Azeez, N.A., Bada, T.M., Misra, S., Adewumi, A., Van der Vyver, C., Ahuja, R.: Intrusion detection and prevention systems: an updated review. Data Management, Analytics and Innovation: Proceedings of ICDMAI 2019, Volume 1 pp. 685–696 (2020)

5. Barradas, D., Santos, N., Rodrigues, L., Signorello, S., Ramos, F.M., Madeira, A.: Flowlens: Enabling eficient flow classification for ml-based network security applications. In: NDSS (2021)

6. Buzzega, P., Boschini, M., Porrello, A., Abati, D., Calderara, S.: Dark experience for general continual learning: a strong, simple baseline. Advances in neural information processing systems 33, 15920–15930 (2020)

7. Chiba, Z., Abghour, N., Moussaid, K., Omri, A.E., Rida, M.: Newest collaborative and hybrid network intrusion detection framework based on suricata and isolation forest algorithm. In: Proceedings of the 4th international conference on smart city applications. pp. 1–11 (2019)

8. Chung, J., Gulcehre, C., Cho, K., Bengio, Y.: Empirical evaluation of gated recurrent neural networks on sequence modeling. arXiv preprint arXiv:1412.3555 (2014)

9. Dong, C., Lu, Z., Cui, Z., Liu, B., Chen, K.: Mbtree: Detecting encryption rats communication using malicious behavior tree. IEEE Transactions on Information Forensics and Security 16, 3589–3603 (2021)

10. Fang, Y., Li, K., Zheng, R., Liao, S., Wang, Y.: A communication-channel-based method for detecting deeply camouflaged malicious trafic. Computer Networks 197, 108297 (2021)

11. Fu, C., Li, Q., Shen, M., Xu, K.: Realtime robust malicious trafic detection via frequency domain analysis. In: Proceedings of the 2021 ACM SIGSAC Conference on Computer and Communications Security. pp. 3431–3446 (2021)

12. Gupta, A., Sharma, L.S.: A categorical survey of state-of-the-art intrusion detection system-snort. International Journal of Information and Computer Security 13(3- 4), 337–356 (2020)

13. Khraisat, A., Gondal, I., Vamplew, P., Kamruzzaman, J.: Survey of intrusion detection systems: techniques, datasets and challenges. Cybersecurity 2(1), 1–22 (2019)

14. Lashkari, A.H., Kadir, A.F.A., Taheri, L., Ghorbani, A.A.: Toward developing a systematic approach to generate benchmark android malware datasets and classification. In: 2018 International Carnahan conference on security technology (ICCST). pp. 1–7. IEEE (2018)

15. Li, Y., Guo, H., Hou, J., Zhang, Z., Jiang, T., Liu, Z.: A survey of encrypted malicious trafic detection. In: 2021 International Conference on Communications, Computing, Cybersecurity, and Informatics (CCCI). pp. 1–7. IEEE (2021)

16. Liu, C., Cao, Z., Xiong, G., Gou, G., Yiu, S.M., He, L.: Mampf: Encrypted trafic classification based on multi-attribute markov probability fingerprints. In: 2018 IEEE/ACM 26th International Symposium on Quality of Service (IWQoS). pp. 1–10. IEEE (2018)

17. Liu, C., He, L., Xiong, G., Cao, Z., Li, Z.: Fs-net: A flow sequence network for encrypted trafic classification. In: IEEE INFOCOM 2019-IEEE Conference On Computer Communications. pp. 1171–1179. IEEE (2019)

18. Liu, Z., Qian, P., Yang, J., Liu, L., Xu, X., He, Q., Zhang, X.: Rethinking smart contract fuzzing: Fuzzing with invocation ordering and important branch revisiting. IEEE Transactions on Information Forensics and Security (TIFS) 18, 1237–1251 (2023). https://doi.org/10.1109/TIFS.2023.3237370

19. Liu, Z., Wu, S., Xu, C., Wang, X., Zhu, L., Wu, S., Feng, F.: Copy motion from one to another: Fake motion video generation. In: IJCAI. pp. 1223–1231 (2022). https://doi.org/10.24963/IJCAI.2022/171

20. Mirsky, Y., Doitshman, T., Elovici, Y., Shabtai, A.: Kitsune: an ensemble of autoencoders for online network intrusion detection. arXiv preprint arXiv:1802.09089 (2018)

21. MontazeriShatoori, M., Davidson, L., Kaur, G., Lashkari, A.H.: Detection of doh tunnels using time-series classification of encrypted trafic. In: 2020 IEEE Intl Conf on Dependable, Autonomic and Secure Computing, Intl Conf on Pervasive Intelligence and Computing, Intl Conf on Cloud and Big Data Computing, Intl Conf on Cyber Science and Technology Congress (DASC/PiCom/CBDCom/CyberSciTech). pp. 63–70. IEEE (2020)

22. Ni, J., Chen, W., Tong, J., Wang, H., Wu, L.: High-speed anomaly trafic detection based on staged frequency domain features. Journal of Information Security and Applications 77, 103575 (2023)

23. Qing, Y., Yin, Q., Deng, X., Chen, Y., Liu, Z., Sun, K., Xu, K., Zhang, J., Li, Q.: Low-quality training data only? a robust framework for detecting encrypted malicious network trafic. arXiv preprint arXiv:2309.04798 (2023)

24. Rebufi, S.A., Kolesnikov, A., Sperl, G., Lampert, C.H.: icarl: Incremental classifier and representation learning. In: Proceedings of the IEEE conference on Computer Vision and Pattern Recognition. pp. 2001–2010 (2017)

25. Riemer, M., Cases, I., Ajemian, R., Liu, M., Rish, I., Tu, Y., Tesauro, G.: Learning to learn without forgetting by maximizing transfer and minimizing interference. arXiv preprint arXiv:1810.11910 (2018)

26. Shuai, C., Zhong, J., Wu, S., Lin, F., Wang, Z., Ba, Z., Liu, Z., Cavallaro, L., Ren, K.: Locate and verify: A two-stream network for improved deepfake detection. In: ACM MM. pp. 7131–7142 (2023). https://doi.org/10.1145/3581783.3612386

27. Van de Ven, G.M., Siegelmann, H.T., Tolias, A.S.: Brain-inspired replay for continual learning with artificial neural networks. Nature communications 11(1), 4069 (2020)

28. Vitter, J.S.: Random sampling with a reservoir. ACM Transactions on Mathematical Software (TOMS) 11(1), 37–57 (1985)

29. Yadav, A.K., Singh, K., Amin, A.H., Almutairi, L., Alsenani, T.R., Ahmadian, A.: A comparative study on consensus mechanism with security threats and future scopes: Blockchain. Computer Communications 201, 102–115 (2023)

30. Zenke, F., Poole, B., Ganguli, S.: Continual learning through synaptic intelligence. In: International conference on machine learning. pp. 3987–3995. PMLR (2017)

31. Zheng, Z., Xie, S., Dai, H.N., Chen, X., Wang, H.: Blockchain challenges and opportunities: A survey. International journal of web and grid services 14(4), 352– 375 (2018)