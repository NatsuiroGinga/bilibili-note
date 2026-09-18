---
title: "physics-informed-graph-convolutional-recurrent-network-for-cyber-attack-detection-in-chemical-process-networks"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/physics-informed-graph-convolutional-recurrent-network-for-cyber-attack-detection-in-chemical-process-networks.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

pubs.acs.org/IECR

# Physics-Informed Graph Convolutional Recurrent Network for Cyber-Attack Detection in Chemical Process Networks

Guoquan Wu, Haohao Zhang, Wanlu Wu, Yujia Wang, and Zhe Wu\*

![](images/5b54c8342190e80b52136e08ff1d3050e96d670da9c9e4ad4e11ba5cc9da48a0.jpg)

Cite This: Ind. Eng. Chem. Res. 2025, 64, 3370−3382

![](images/dbc58ad47f562c0553702f8f8d6da880a0da764273dc82d6989775c861a6f6ac.jpg)

Read Online

ACCESS

Metrics & More

Article Recommendations

ABSTRACT: Cyber-attacks pose a significant threat to the safety and operational eficiency of industrial chemical processes. Traditional data-driven detection methods often require suficient training data to achieve the desired detection accuracy. However, for complex chemical process networks, such data sets are often unavailable or insuficient, limiting the efectiveness of these approaches. To address this challenge, this work presents a physics-informed graph convolutional recurrent network (PIGCRN) that incorporates both spatial and temporal information on chemical process networks and a priori knowledge of attacking patterns to improve the detection of cyber-attacks while reducing the requirement on extensive training data. A chemical process network consisting of two reactors is simulated in Aspen Plus Dynamics to demonstrate its superior performance in detecting cyber-attacks compared to traditional data-driven methods.

![](images/edfa3c78739cc5c2bdaa627f128102d959eeba63abc21a21bf871ca9485b601d.jpg)

## ■ INTRODUCTION

The rapid advancement of automation and digital technologies in industrial processes has significantly improved operational eficiency in chemical manufacturing industries. However, this increased reliance on automated control systems and networked sensor infrastructures has also increased the vulnerability of these processes to cyber-attacks. In chemical processes, where control ofvariables such as temperature, pressure, and flow rates is important to maintain safe and stable operations, any disruption caused by a cyber-attack can have catastrophic consequences.<sup>1</sup> These could range from minor disruptions that lead to economic losses to serious incidents involving safety hazards, environmental damage, and a potential loss of life. Chemical process networks are challenging to monitor and control due to their nonlinear nature and complex interactions among multiple subsystems that dynamically evolve over time. The existence ofcyber-attacks further increases the dificulties of maintaining stable operations of such complex systems. Specifically, a sensor cyber-attack can modify the feedback measurement sent to the controller, leading to incorrect control actions that drive the system away from its normal operating condition.<sup>2</sup> Therefore, the early detection of such attacks is critical to maintaining the safety and stability ofchemical process networks.

Traditional detection methods for cyber-attacks in industrial control systems often use first-principles models to detect anomalies by comparing real-time process data with predicted behavior generated from the first-principles model.<sup>3,4</sup> However, due to the nonlinear behavior and interactions among process variables in complex process networks, it is dificult to develop accurate first-principles models for prediction. To that end, there has been growing interest in machine learning (ML)-based methods for detecting various types of cyber-attacks.<sup>2,5</sup> For example, a convolutional neural network (CNN)-based model is proposed in ref6 to detect message injection attacks in vehicular networks. However, many existing ML-based approaches require a large amount of labeled data for efective training, which can be a significant limitation for real-world chemical processes where labeled data for systems under cyber-attacks is often scarce.

Motivated by the consideration of data scarcity, physics informed neural networks (PINNs), a synergistic method that integrates physical laws into the training process of neura networks, has emerged as a promising solution to bridge the gap between data-driven methods and domain-specific knowl edge.<sup>7,8</sup> For example, a physics-informed recurrent neural network (PIRNN) model is proposed in ref 9 to capture the dynamic behavior of the batch crystallization process. Addition ally, a mixed-variable scheme of PINNs is presented in ref 10 to simulate steady and transient incompressible viscous laminar flows at low Reynolds numbers, which improves the training capacity and accuracy of the solution. However, existing PINN based detection models are limited in their ability to handle chemical process networks due to the complex interplay between interconnected subsystems. Therefore, it is important to integrate other forms of a priori knowledge (e.g., process topology) to improve the accuracy of the model.

![](images/f5b4744428db2002527b72afbb40d804372cd7896bc6d78191c2dbe5c578712f.jpg)

Graph Neural Networks (GNNs) are a class of neural networks designed to operate on graph-structured data, efectively capturing relationships and interactions between diferent entities represented as nodes and edges.<sup>11</sup> Within GNNs, graph convolutional networks (GCNs) stand out as a powerful variant that uses graph convolution operations to aggregate information from neighbors of a node, enabling the neural network to learn local and global patterns within the graph. GCNs have been widely used in various domains to model complex dependencies,<sup>12</sup> such as social networks,<sup>13</sup> molecular structures,<sup>14</sup> and industrial processes. For example, a novel GCN-based soft sensor was constructed in ref 15 to capture localized spatial-temporal correlations between the process variables ofthe fermentation processes. However, at this stage, the incorporation ofGCNs into cyber-attack detection for distributed nonlinear systems has not been investigated. Furthermore, there is a lack of research on how to integrate process topological knowledge into GCNs, which is critical for understanding the underlying dynamics and identifying abnormal behaviors that evolve over time. For example, attacks on one system may afect the operation of downstream units, which is dificult to detect using sensor measurement of individual processes. Therefore, there is a compelling need for advanced detection systems that can integrate spatial and temporal information from a process network to efectively monitor and protect nonlinear chemical processes.

Motivated by the above considerations, in this work, we develop a physics-informed graph convolutional recurrent network (PIGCRN) to detect cyber-attacks in chemical process networks described by nonlinear distributed systems. Specifi cally, we first introduce a novel approach to incorporate topological knowledge of a chemical process network into a directed graph framework. Subsequently, a data-driven method is designed to assign edge weights in the directed graph. Furthermore, we integrate GCNs with long short-term memory networks (LSTMs) to capture both spatial and temporal dependencies within the process network. The characteristics of cyber-attacks are embedded into a physics-informed loss function to improve the accuracy and reliability of detection in the presence of limiting training data. Finally, we implemented the proposed PIGCRN detector in a chemical process network simulated in Aspen Plus Dynamics. The results demonstrate that the PIGCRN, which combines a priori knowledge of process topology and cyber-attacks, improves the accuracy in detecting cyber-attacks compared to traditional data-driven approaches.

## ■ PRELIMINARIES

Nonlinear Systems. We consider the class of continuoustime nonlinear systems consisting ofn subsystems, where each of the subsystems can be characterized by a state-space form that includes states and sensor measurements.

$$
\dot {x} _ {i} = F _ {i} (x, u _ {i})\tag{1}
$$

$$
\overline {{x}} _ {i} = s _ {i} (x _ {i})\tag{2}
$$

$x _ { i } \in \mathbb { R } ^ { n _ { i } }$ is the state vector, and $u _ { i } \in \mathbb { R } ^ { m _ { i } }$ is the manipulated input for the ith subsystem, $i = 1 , . . . ,$ n. The manipulated input $u _ { i }$ is s u b j e c t t o i n p u t c o n s t r a i n t s $u _ { i } \in U : = \{ u _ { i } ^ { \operatorname* { m i n } } \leq u _ { i } \leq u _ { i } ^ { \operatorname* { m a x } } \} \subset \mathbb { R } ^ { m _ { i } }$ <sup>i</sup>, where $\mathbf { u } _ { i } ^ { \mathrm { { \ m a x } } }$ and ${ \bf { u } } _ { i } ^ { \mathrm { { m i n } } }$ specify the maximum and minimum bounds for the manipulated input $\mathbf { \phi } _ { u _ { i } \cdot \mathbf { \phi } } ^ { \prime } x = \left[ x _ { 1 } ^ { T } . . . \ x _ { i } ^ { T } . . . \ x _ { n } ^ { T } \right] ^ { T }$ is the state vector for the entire system. The dynamics for the ith subsystem is described by the nonlinear function $F _ { i } ( \cdot , \cdot )$ , which is assumed to be Lipschitz continuous, and the sensor measurement function is denoted as $s _ { i } ( \cdot )$ . The sensor measurement of $x _ { i }$ is denoted as $\overline { { x } } _ { i } \in \mathbb { R } ^ { n _ { i } }$ and is vulnerable to sensor cyber-attacks. In the absence of cyber attacks, $s _ { i } ( x _ { i } ) = x _ { i } .$ . As shown in eq 1, the subsystems are coupled with each other since state $x _ { i }$ of the ith subsystem is afected by the entire state vector x.

Intelligent Cyber-Attacks. The landscape of cyber-attacks has evolved significantly, with attackers increasingly employing state-of-the-art techniques to disrupt process operations. Intelligent cyber-attacks, characterized by their complexity and adaptability, have emerged as a major threat to critical infrastructure worldwide. The objectives of intelligent cyberattacks are diverse, such as disrupting the stability and performance of closed-loop systems, causing significant operational failure. Sensor cyber-attacks target physical sensors within critical systems, such as industrial control systems, autonomous vehicles, or smart grids, by manipulating the data fed to the control systems, leading to incorrect decisions based on faulty input. These attacks can cause serious physical damage or disrupt operations by deceiving systems that rely on accurate sensor data. The impact of such attacks often becomes evident only when there are noticeable changes in the dynamic behavior of the closed-loop system, which makes it impractical to rely solely on hardware performance countermeasures for detecting code modifications. Among the various forms of sensor cyber attacks, some of the most prevalent and accessible to attackers include deception attacks (e.g., Geometric, Surge, and Min-Max attacks), replay attacks, and Denial-of-Service (DoS) attacks. In this study, we focus on attacks that target sensor measurements and use geometric attacks as an example to illustrate the development of a physics-informed loss function.

The objective of a geometric cyber-attack is to initially compromise the stability of a closed-loop system at a slow rate, with its impact gradually increasing over time in a geometric manner until it reaches the maximum or minimum allowable values of sensor readings. At the beginning of the attack, a small constant $\beta$ is added to the true measurement output. Subsequently, this ofset is multiplied by a factor of $( 1 + \alpha )$ where α ${ \mathfrak { c } } \in ( 0 , 1 )$ , until x reaches the maximum allowable attack value $\rho _ { a } .$ Therefore, the parameters α and $\mathbf { \nabla } \cdot \beta$ are selected based on the operating region and the duration of the attack. The mathematical representation of the geometric attack can be expressed as follows

$$
\overline {{x}} _ {t _ {k}} = x _ {t _ {k}} + \beta \times (1 + \alpha) ^ {k - k _ {0}}, \forall i \in [ k _ {0}, k _ {0} + L _ {a} ]\tag{3}
$$

where $\overline { { x } } _ { t _ { k } }$ represents the compromised sensor measurement at time step t ; $\beta$ and α define the magnitude and speed of the geometric attack, respectively; $k _ { 0 }$ indicates the initial time at which the attack is launched; and $L _ { a }$ denotes the duration of the attack in terms of sampling periods.

## ■ PHYSICS-INFORMED GCRN DETECTOR

In a chemical process network, interactions between subsystems introduce significant spatial dependencies and dynamic relation ships. While traditional NN-based models have shown success in capturing the dynamics of individual chemical processes, they often fail to fully capture the intricate relationships of the subsystems within an interconnected process network when training data is limited. Therefore, in this section, we develop a physics-informed graph convolutional recurrent network (PIGCRN) to detect cyber-attacks in a chemical process network represented by nonlinear distributed systems while reducing the requirements for training sample size.

Graph Convolutional Network. We first introduce GCN as the foundation of PIGCRN that captures spatial relationships in a chemical process network. GCN can eficiently model the interactions between diferent nodes (i.e., the corresponding measurements of unit operations and streams) in a chemical process network, which is critical for understanding the underlying dynamics and detecting anomalies.

Definition of Graph. A graph is a structured representation that consists of nodes (or vertices) and edges specifically designed to capture the relationships and dependencies between diferent entities within the data. The nodes represent individual objects, while the edges define the connections or relationships between these objects. This structure allows GNNs to perform computations that take into account not only the individual properties of nodes but also the impact of neighboring nodes through the edges. In GNNs, the graph serves as the foundational data structure on which the network operates. The nodes are typically associated with feature vectors that contain the properties of the entities they represent. The edges may also carry information, such as weights or labels, that indicates the strength or type of connection between nodes. By processing this graph, a GNN can learn to propagate information across the network, allowing it to model complex relationships and interactions that are not easily captured by traditional neural networks.

Specifically, a graph G is typically represented as $G = \left( V , E , A \right)$ where V denotes the set of nodes and E represents the set of edges in the graph, and A is the adjacency matrix that encodes the connectivity between nodes. Each node $\nu _ { i } \in V$ corresponds to an individual entity in the data, while the edges $e _ { i j } \in E$ indicate interactions between nodes $\nu _ { i }$ and $\nu _ { j } .$ The adjacency matrix A is a crucial component, typically defined as a square matrix ofsize |V| $\times \mid U \mid$ , where each element $a _ { i j }$ indicates the presence of the connection between the corresponding nodes v and $\nu _ { j } .$ In many cases, $a _ { i j }$ is binary, with $a _ { i j } = 1$ denoting a direct connection and $a _ { i j } = 0$ indicating that there is no connection. However, in applications where the relationships are weighted, the elements ofA can take nonbinary values, reflecting the varying strengths of connections between nodes. This mathematical structure allows graph G to capture spatial relationships between nodes, with the network structure remaining static over time.

Graph Convolutional Neural Network. Graph Convolu tional Networks (GCNs) define graph convolution through a process known as message passing. This approach requires two primary inputs: a general data matrix containing the stacked node features and an additional adjacency matrix that describes the connectivity between nodes within the graph. Specifically, the operation ofa single GCN layer can be expressed as follows

$$
H ^ {(l + 1)} = \sigma (\tilde {D} ^ {- 1 / 2} \tilde {A} \tilde {D} ^ {- 1 / 2} H ^ {(l)} W ^ {(l)})\tag{4}
$$

where $H ^ { l }$ represents the node features at layer $l , \tilde { A } = A + I$ is the adjacency matrix with added self-loops, D<sup>̃</sup> is the diagonal degree matrix of $\mathbf { \widetilde { A } } , \mathbf { W } ^ { ( l ) }$ is the learnable weight matrix at layer l, and σ is an activation function $( \mathrm { e . g . , R e L U } )$ . The key insight behind this formulation is that each node aggregates feature information from its neighboring nodes, efectively integrating the local structure of the graph into the node’s representation. By stacking multiple graph convolution layers, GCNs can propagate node information along the graph’s edges in a predefined manner. This layered propagation enables the GCN to learn and understand the relationships between diferent nodes under the guidance of process knowledge, enhancing its ability to model complex dependencies in the graph.

Knowledge-Guided Topology Graph Construction. The predefined graph is an important component for constructing GCNs. It can provide a structured framework within which knowledge or information about external processes can be integrated. This integration allows GCN to incorporate domain-specific insights to improve its performance in learning the patterns and interactions in the data. In chemical processes, the physical layout of unit operations and the flow of materials through pipelines inherently create a network of relationships that can be naturally represented as a topology, which contains a wealth of knowledge about the relationships between diferent variables within the system. Specifically, unit operations, such as reactors, distillation columns, and heat exchangers, are physically connected through pipelines that transport materials between these units. This physical connectivity reflects not only spatial relationships but also functional dependencies. For example, the output of one unit operation may serve as the input to another or a particular sensor reading may directly afect the behavior of a control valve downstream. Additionally, control loops within these chemical processes further elaborate this topology by linking process variables and manipulated variables with sensors, controllers, and actuators. These control loops are critical for maintaining the desired operating conditions and ensuring process stability, which increases the complexity of the process topology as they introduce signal transmission lines that connect various control elements throughout the plant. Therefore, a priori knowledge of the process topology can be used to construct a graph that accurately represents the underlying process.

In this study, we construct graphs by integrating domain specific knowledge ofchemical process structures. The following steps outline the process of constructing graphs from chemical processes.

Step 1: Identify all unit operations and streams within the chemical process. These include critical components such as reactors, distillation columns, heat exchangers, and pipelines that transport materials or energy between these units. Once the unit operations and streams are identified, the next task is to determine all corresponding measurements associated with them. These measurements typically include process variables such as pressure, temperature, level, and flow rate, which are critical for monitoring and controlling the chemical process.

Step 2: Create nodes for each measurement identified in Step 1. Each node represents a specific process variable $( \mathrm { e . g . } ,$ pressure, temperature, and flow rate) or a manipulated variable (e.g., cooling water flow rate). These nodes form the basic building blocks of the graph, representing the key entities involved in the chemical process.

Step 3: Establish directed edges based on physical pathways. In this study, we focus on directed graphs, where the directionality ofedges is crucial to accurately capture the interactions and dependencies between nodes. The direction of the edges reflects the flow of impact or material from one component to another. Specifically, directed edges can be constructed based on the physical pathways through which materials or energy flow within the process. For example, a pipeline that transports fluid from a reactor to a separator would be represented by a directed edge from the reactor node to the separator node. This directionality models the unidirectional impact commonly observed in chemical processes, where upstream unit operations significantly afect downstream operations, while the reverse impact is generally negligible.

Step 4: Integrate domain knowledge of process variables and manipulated variables into edge construction. In this step, domain-specific knowledge ofthe chemical process structure is integrated into the graph by defining edges that reflect the functional dependencies between nodes. Specifically, based on the control loop, a directed edge is established from the manipulated variables to their corresponding state variables, which represent how control actions afect the process states. For example, changes in the cooling water flow rate might afect the reactor temperature, which in turn afects the reaction rate and the concentration of substances in the reactor. In this case, directed edges would be created from the flow rate node to the temperature node, and from the temperature node to the concentration node, accurately capturing the chain of impact within the graph.

This approach to constructing the digraph ensures that it not only reflects the physical layout of the chemical process but also encapsulates the functional dependencies and control strategies that govern the process. From an information transfer perspective, diferent nodes generate or carry process-related information, while directed edges represent the flow of information passing within the process. Unlike complex firstprinciples models, the digraph focuses on the connections among diferent components of the process, qualitatively indicating the relationships among various variables. By carefully defining nodes and directed edges based on domain knowledge, the resulting digraph becomes a powerful tool for modeling the interactions within the chemical process and for further analysis using GCNs.

Weighted System Digraph. After the topology digraph of the chemical process is constructed, the next step is to assign a weight to each edge to quantify the interactions between nodes, particularly to capture the short-time response of the system. Specifically, the weight assigned to an edge reflects the impact that a particular node has on another node within the process. This impact could be due to various factors such as the flow rate of a material, the sensitivity of a process variable to changes in another, or the responsiveness of a control loop.

When the first-principles models of a system $( \mathrm { i . e . , ~ e q ~ 1 } )$ are known, edge weights can be obtained by calculating response sensitivities,<sup>17</sup> which allows for a precise quantification of the interactions between nodes based on the underlying physical laws governing the system. However, due to the highly coupled and nonlinear nature of a chemical process network, deriving an accurate first-principles model for a complex chemical process network is often challenging. Therefore, in this work, we will calculate the weights for each edge without relying on the firstprinciples models. A data-driven approach that uses historical data from the nominal system will be developed to obtain edge weights by using statistical methods.

Specifically, we employ mutual information to calculate the nonlinear dependencies between the features of nodes in the time-series data. Mutual information is a powerful statistical measure that quantifies the amount of information shared between two random variables. Unlike linear correlation measures, mutual information can capture both linear and nonlinear dependencies and therefore is particularly useful for analyzing complex, interconnected systems such as chemical processes. Given two discrete random variables X and Y, with a joint probability distribution $P ( X , Y )$ and marginal distributions $P ( X )$ and $P ( Y )$ , the mutual information $I ( X ; Y )$ is defined as follows:

$$
I (X; Y) = \sum_ {x \in X} \sum_ {y \in Y} P (x, y) \mathrm{log} \left(\frac {P (x , y)}{P (x) P (y)}\right)\tag{5}
$$

where $P ( x , y )$ represents the joint probability that ${ \mathrm { X } } = x$ and $Y = y$ occur simultaneously, and $P ( x )$ and $P ( \dot { y } )$ are the marginal probabilities that $\mathrm { X } = x$ and $Y = y ,$ respectively. A higher mutual information value indicates a stronger dependency between the two variables, regardless of whether the dependency is linear or nonlinear. By analyzing time-series data, we calculate mutua information between pairs of nodes to understand how changes in one variable afect another. The computed mutual information values are then normalized and assigned as weights to the corresponding edges in the topology digraph. $\mathtt { B y }$ incorporation of these weights, the digraph becomes a more accurate representation of a chemical process network, which could improve learning performance with limited data.

Graph Convolutional Recurrent Networks. In chemical process networks, data often exhibit both spatial and temporal dependencies. Long short-term memory (LSTM) networks are adept at capturing temporal dependencies in sequential data. Traditional RNNs struggle with learning long-range depend encies due to the problem of vanishing or exploding gradients during backpropagation. LSTM addresses this issue by incorporating a memory cell that can maintain information over extended time steps along with a series of gating mechanisms that regulate the flow of information into and out of the cell. Specifically, the LSTM architecture consists of three key gates: the input gate, which controls how much of the new input to store in the cell; the forget gate, which decides how much of the past information to discard; and the output gate, which determines the amount of information from the cell to output at each time step. However, LSTMs fall short when it comes to capturing the spatial relationships inherent in graphstructured data, where the state of one entity is afected not only by its past values but also by the states ofits neighboring entities.

On the other hand, GCNs can capture the structural information on graphs, but they are limited in their ability to handle time-series data. Therefore, in this section, we construct a graph convolutional recurrent network (GCRN) to integrate GCNs and LSTMs into a unified framework, which can simultaneously capture both spatial and temporal dependencies. The resulting GCRNs can be used for distributed systems in which the state of each node in the graph is afected by both its neighbors and its own past states. The formulation of a single layer GCRN cell is presented as follows

$$
H _ {t} = \sigma (\tilde {D} ^ {- 1 / 2} \tilde {A} \tilde {D} ^ {- 1 / 2} X _ {t} W)\tag{6}
$$

$$
f _ {t} = \sigma_ {g} (W _ {f} \cdot [ h _ {t - 1}, H _ {t} ] + b _ {f})\tag{7}
$$

![](images/4bf6677cc652dc5b819fb566f7aeb810d87bff0d763f35cf5c977f7040080328.jpg)  
Figure 1. Schematic of the physics-informed GCRN detector.

$$
i _ {t} = \sigma_ {g} (W _ {i} \cdot [ h _ {t - 1}, H _ {t} ] + b _ {i})\tag{8}
$$

$$
\tilde {C} _ {t} = \tanh \big (W _ {C} \cdot [ h _ {t - 1}, H _ {t} ] + b _ {C} \big)\tag{9}
$$

$$
C _ {t} = f _ {t} ^ {*} C _ {t - 1} + i _ {t} ^ {*} \tilde {C} _ {t}\tag{10}
$$

$$
o _ {t} = \sigma_ {g} (W _ {o} \cdot [ h _ {t - 1}, H _ {t} ] + b _ {o})\tag{11}
$$

$$
h _ {t} = o _ {t} ^ {*} \mathrm{tanh} (C _ {t})\tag{12}
$$

where $X _ { t }$ is the input feature matrix at time step $t , f _ { t }$ represents the forget gate, $i _ { t }$ is the input gate, $\tilde { C } _ { t }$ is the candidate cell state, $C _ { t }$ is the updated cell state, $o _ { t }$ is the output gate, $h _ { t }$ is the hidden state, and \* represents the element-wise multiplication of the vectors. The functions $\sigma _ { g }$ and tanh denote the sigmoid and hyperbolic tangent functions, respectively, which are applied element-wise to ensure the nonlinear transformations required for the model.

The GCRN architecture constructed in this study combines the capabilities of GCNs for spatial feature extraction with the temporal sequence modeling capabilities of LSTMs, which is illustrated in Figure 1. Specifically, at each time step, a GCN layer of eq 6 is first applied to the graph-structured data, where each node’s feature vector is updated based on the features ofits neighboring nodes. The output of this layer captures the spatial dependencies within the graph for each individual time step. Following the GCN layers, the LSTM layers ofeqs 7−12 capture the temporal dependencies by considering the sequence ofnode features over time. It takes the output of the GCN at the current time step and combines it with the hidden state from the previous time step to update the hidden state for the current step. This process allows the GCRN model to retain the memory of previous states, which is essential to understanding how the system evolves over time. After processing the temporal sequence with LSTM, the final hidden state is passed through a fully connected layer (FCL) to produce the output. In the context of classification tasks, this output layer is used to predict the class labels based on the learned spatiotemporal features.

In the context of cyber-attacks, GCRNs can be employed to detect the spread of attacks across a process network. Specifically, when a cyber-attack occurs, it may initially afect only a subset of nodes, while over time the attack can propagate through the network, afecting other nodes. GCRNs are able to detect this behavior as they can track how the attack afects the states ofconnected nodes over time. By integration ofthe spatial structure with the temporal dynamics, GCRNs can provide early detection of attacks, allowing for timely intervention and mitigation. In this work, the GCRN is developed to perform multilabel classification across diferent scenarios: a nominal closed-loop system with no attacks and a closed-loop system where a specific sensor (or multiple sensors) is under a cyberattack. The sensor reading of the state variables $\overline { { x } } _ { t }$ and the manipulated input $\boldsymbol { u } _ { t }$ are utilized as input to the GCRN, as they ofer valuable insight into the dynamic behavior of the closed loop system. The output of the GCRN is a classification result with dimensions corresponding to the number of state sensors. The GCRN output vector not only indicates whether the system is under a cyber-attack but also identifies which specific sensors have been compromised. Each element in the output vector represents the probability of a cyber-attack targeting a particular sensor, providing a view of the system’s security status. A sigmoid layer is applied to map the raw output ofthe GCRN to a probability between 0 and 1, which is then converted to binary predictions based on a predefined threshold. Specifically, if the probability for a sensor exceeds 0.5, then that sensor is considered to be under cyber-attacks. In contrast, if the probabilities for all sensors are below 0.5, then the system is classified as the nominal closed-loop system with no attacks. By identifying compromised sensors, the GCRN model provides critical information that can be used for immediate mitigation actions, improving system stability, and security.

Remark 1 The concept of a graph convolutional recurrent network is not being introduced for the first time in this work. Similar architectures have been explored in previous studies<sup>18</sup> and are sometimes referred to as “spatial-temporal convolution layers”.<sup>19</sup> However, to the best ofour knowledge, this work is the first to incorporate chemical process topology knowledge into the design of a graph layer within a GCRN framework. By embedding this process-specific graph structure into the GCRN architecture, the proposed model is uniquely equipped to handle the complex spatial-temporal dynamics inherent to chemical process networks and, therefore, could outperform the traditional recurrent neural networks in detecting cyber-attacks in a process network. Additionally, this work explicitly presents the mathematical formulation ofa single-layer GCRN cell, as shown in eqs 6−12. This formulation details how graph convolutional layers process spatial relationships within the data and pass the extracted features into the recurrent layers to capture temporal dependencies.

Physics-Informed Loss Function. While the proposed GCRN has great potential to improve detection accuracy by learning both the spatial and temporal behavior of a chemical process network under cyber-attacks, a significant challenge arises from the scarcity of labeled data, particularly for complex and rare attack scenarios in real-world systems. To address this issue, a physics-informed loss function is developed for the GCRN, which combines historical data from both norma operations and attacks with a priori knowledge of cyber-attacks. In this work, we consider geometric attacks, a specific type of sensor cyber-attack of eq 3 designed to subtly and gradually degrade the stability of a closed-loop system, as an example to show the development of physics-informed detectors. The stealthy nature of this attack is that it grows exponentially over time with a small initial impact on the system but quickly escalates as the attack progresses. Therefore, one possible solution is to embed the exponential characteristics ofgeometric attacks as a priori knowledge into the GCRN training process to help distinguish between a nominal system and a system under such an attack.

We begin by constructing a physics-based indicator within the GCRN framework that leverages the exponential characteristics of geometric attacks to assess whether a given state trajectory has been impacted by geometric cyber-attacks. Specifically, the method begins by calculating the diference between two consecutive measurements

$$
\begin{array}{r l} z _ {k} & = \overline {{x}} _ {k + 1} - \overline {{x}} _ {k} = x _ {k + 1} - x _ {k} + \beta \times (1 + \alpha) ^ {k - k _ {0}} \times \alpha , k \\ & = 1, 2, 3, \dots , N _ {T} - 1 \end{array} \tag {1}\tag{13}
$$

where $z _ { k }$ represents the residual obtained by calculating the backward diference in the state trajectory at the kth time step within the GCRN input. Given that the time interval between consecutive measurements is suficiently short and the assumption that the process dynamics follows a Lipschitz continuous function, the deviation between two consecutive state measurements $\left( \mathrm { i . e . , } x _ { k + 1 } - x _ { k } \right)$ remains small and bounded. Therefore, to simplify the calculation, the diference between $x _ { k + 1 }$ and $x _ { k }$ is neglected in eq 13 with a suficiently small sampling time. Subsequently, a natural logarithm transformation is applied to $z _ { k }$

$$
\mathcal {Z} _ {k} = \ln (z _ {k}) = \ln (\beta \times (1 + \alpha) ^ {k - k _ {0}} \times \alpha)\tag{14}
$$

where $\mathcal { Z } _ { k }$ is the logarithmic transformation of $z _ { k } .$ Eq 14 can be further simplified to

$$
\mathcal {Z} _ {k} = \ln (\beta) + (k - k _ {0}) \ln (1 + \alpha) + \ln (\alpha)\tag{15}
$$

The logarithmic transformation converts the exponential form of the geometric attack into a linear form, which is easier to analyze by regression. In this linearized form, $\ln ( \beta ) + \ln ( \alpha )$ is the intercept, and $\ln ( 1 { \mathrm { ~ + ~ } } \alpha )$ represents the slope of the line. However, the purpose of this equation is not to fit α or β during training. Instead, eq 15 suggests that ifthe residuals $z _ { k }$ follow the pattern of a geometric attack, they should exhibit a linear trend when plotted on a logarithmic scale.

Unlike methods that either use specific α and $\beta$ to validate data against eq 15 or estimate α and $\bar { \boldsymbol { \beta } }$ from data, the subsequent linear regression step is applied to the residuals $\mathcal { Z } _ { k }$ to obtain the slope m and the correlation coeficient $R ^ { 2 }$ . The final step involves constructing the physics-based indicator to evaluate the correlation coeficient $R ^ { 2 }$ and the slope value to determine whether the data align with the expected form of the geometric attack. The physics-based indicator D is defined as follows:

$$
D = \left\{ \begin{array}{l l} 1, & \text { if } R ^ {2} \geq \epsilon_ {R} \text { and } m \geq \epsilon_ {m} \\ 0, & \text { otherwise } \end{array} \right.\tag{16}
$$

where $\epsilon _ { R }$ and $\epsilon _ { m }$ are predefined thresholds used to evaluate the likelihood of potential cyber-attacks. A high value of $R ^ { 2 }$ suggests that the data closely follow the exponential pattern, which is characteristic of a geometric attack. Additionally, by setting a threshold $\epsilon _ { m }$ the indicator ensures that only those residuals $\mathcal { Z } _ { k }$ exhibiting a suficiently strong growth pattern are classified as attacks, which helps to distinguish between normal fluctuations due to sensor noise or process disturbances and those consisten with geometric cyber-attacks. If both conditions are satisfied, then the indicator D is assigned a value of 1, indicating that the system is under geometric attack. Otherwise, D is assigned a value of 0, indicating that the system is operating normally or that the detected deviations do not conform to the expected attack pattern. The physics-based indicator D plays a crucial role in the overall detection framework by providing a clear decision criterion based on the underlying physical characteristics of geometric attacks.

Next, the physics-based indicator D is incorporated into the training process of GCRN to guide the model in identifying potential attack patterns. Specifically, a custom physicsinformed loss function is developed as follows:

$$
\mathrm{Loss} = \alpha_ {X} \mathrm{Loss} _ {X} + \alpha_ {G} \mathrm{Loss} _ {G}\tag{17}
$$

where $\alpha _ { X }$ and $\alpha _ { G }$ are hyperparameters that balance the contribution of each loss term to the overall training process. The total loss function of eq 17 is designed to combine two components: a data-driven loss Loss and a physics-informed loss $\operatorname { L o s s } _ { G } .$ The data-driven loss $\operatorname { L o s s } _ { X }$ is the traditional binary cross-entropy loss function for the multilabel classification task, measuring the discrepancy between the true and predicted labels, which is defined as follows:

$$
\operatorname{Loss} _ {X} = - \frac {1}{N _ {X}} \sum_ {i = 1} ^ {N _ {X}} \sum_ {j = 1} ^ {M} [ y _ {i j} \cdot \log (\hat {y} _ {i j}) + (1 - y _ {i j}) \cdot \log (1 - \hat {y} _ {i j}) ]\tag{18}
$$

where $N _ { X }$ is the number oftraining samples and M is the number of classes (i.e., the number of state sensors that might be compromised). Each sensor is treated as a separate binary classification problem, where the model predicts whether a specific sensor is under attack. $y _ { i j }$ is the true label for the jth class of the ith sample, and $\hat { y } _ { i j }$ is the predicted result for the jth class of the ith sample.

The physics-informed loss Loss represents the regularization term designed based on the knowledge of attack patterns, which is defined as follows

$$
\mathrm{Loss} _ {G} = - \frac {1}{N _ {G}} \sum_ {i = 1} ^ {N _ {G}} \sum_ {j = 1} ^ {M} y _ {i j} ^ {G} \cdot \log (\hat {y} _ {i j}) + (1 - y _ {i j} ^ {G}) \cdot \log (1 - \hat {y} _ {i j})\tag{19}
$$

$N _ { G }$ represents the number of samples where the physics-based indicator D classifies the system as under cyber-attack $( { \mathrm { i . e . , } } D =$ 1), while the ML model classifies it as the nominal system. ${ \ y _ { i j } } ^ { G }$ denotes the detection result ofthe indicator D for the ith sample associated with the jth sensor. When there is a discrepancy between the detection result provided by indicator D and the prediction made by the PIGCRN model, the physical laws impose a penalty on the loss function. This ensures that the model not only learns from historical data but also incorporates domain-specific knowledge, leading to a more accurate and reliable detection of cyber-attacks, especially in data-scarce scenarios.

Development and Implementation of Physics-Informed GCRN Detector. The PIGCRN detector is designed to detect cyber-attacks that disrupt the dynamic control of closed-loop systems. A schematic of the PIGCRN is shown in Figure 1. The key novelty of this framework lies in its ability to embed both the topological knowledge of chemical processes and a priori knowledge of cyber-attacks into the GCRN.

Specifically, the PIGCRN detector in Figure 1 is constructed with the following steps: (1) Historical process data are collected under the nominal system and under cyber-attacks, where diferent sensors could be compromised by cyber-attacks. Each variable in historical data is standardized using its mean and standard deviation. Additionally, the chemical process flowchart is incorporated into graph modeling, which helps capture spatial relationships within the process. (2) A directed graph is constructed based on the topological knowledge of the chemical process. (3) To capture the interactions between nodes, mutual information is used to define the edge weights in the directed graph by analyzing the historical data of the nominal system. (4) The process data, along with the constructed weighted topology digraph, are then fed into the GCRN layers. By integrating the predefined process topology into the GCRN framework, the GCRN model can use domain-specific insights to capture the dynamic behavior of the system. The GCRN can then propagate information along these predefined edges, allowing it to capture the complex interactions between diferent components of the process network. Additionally, the LSTM layer within the GCRN further processes the temporal sequences of the node features, capturing the evolution of the system over time. After processing through the LSTM layers, the output is passed through FCL to map the processed data to predefined attack classes. The FCL is responsible for interpreting the complex features extracted by the LSTM and translating them into classification results, indicating whether the system is under attack and which specific sensor is afected. (5) Finally, the PIGCRN is trained using the customized physics-informed loss function of eq 17, which integrates the physics-based indicator D to account for the discrepancies between the model predictions and the expected behavior under known attack patterns.

Real-time detection is essential for preserving the stability and security of control systems, especially in environments where rapid responses to cyber-attacks are necessary to prevent potential disruptions. Therefore, in this work, a sliding detection window is developed using the PIGCRN model. Since the PIGCRN model processes data in fixed-length sequences $N _ { T } ,$ the detection system is triggered at every time step, using a moving-horizon approach to analyze the most recent sequences of state measurements $\overline { { x } } _ { t }$ over the fixed length $N _ { T } .$ continuously accepting the input data with the latest measurements, the PIGCRN model can detect deviations from norma behavior that may indicate an ongoing attack, forming a key component of the cyber-secure framework. Additionally, to minimize false alarms, the system triggers a cyber-attack alert only if the PIGCRN detector consistently identifies an attack across $N _ { a }$ consecutive iterations of the sliding window. $N _ { a }$ and $N _ { T }$ are key parameters to balance the false positive rate and detection eficiency. Specifically, larger values of $N _ { a }$ and $N _ { T }$ result in longer detection times but reduce false positive rates, while smaller values allow for faster detection but increase false alerts.

Remark 2 It should be noted that the proposed PIGCRN model is capable of detecting geometric attacks with diferent parameters (i.e., the cyber-attacks in training data sets and real world systems have diferent parameters). This is because the physics-informed loss function uses the exponential character istics of the geometric attack rather than relying on specific attack parameters (e.g., α and β). The PIGCRN model is trained to learn the general pattern of exponential growth in sensor measurements that characterizes a geometric attack. In fact, as the exponential nature of the attack becomes more pronounced $( \mathrm { i . e . , }$ with larger values ofα and $\beta )$ , the physics-based indicator D becomes increasingly efective in identifying such attacks. As a result, the physics-informed loss function further enhances the model’s ability to detect a class ofattacks with similar patterns by guiding the learning process to identify these characteristic features, irrespective of the specific parameter values. This increases the flexibility and robustness ofthe model in real-world scenarios, where the exact attack parameters may not always be known.

Remark 3 While this work focuses on designing a physicsinformed loss function specifically for geometric attacks, the proposed PIGCRN-based detector is not limited to a single type of cyber-attack. By analyzing past incidents and cybersecurity research, common patterns and mechanisms used by attackers can be identified and incorporated into the loss function. In cases where multiple types of cyber-attacks are anticipated, the loss function of eq 17 can be extended by adding terms tailored to additional attack types, which allows the training process of the PIGCRN model to account for the potential presence of a variety of attack scenarios. Additionally, by embedding general physical characteristics of specific attacks $\left( \mathrm { e . g . } \right)$ , exponential growth patterns for geometric attacks) into the loss function, the PIGCRN model demonstrates superior extrapolation capabil ities. This implies that the model can still detect unforeseen attacks if they exhibit a similar attack pattern to the attack considered in the physics-informed loss function, even ifthey are not included in the training process. For example, the PIRNN detector trained with surge attacks has been shown to successfully detect previously unseen min-max attacks due to the similar characteristics between these two attack types.

## APPLICATION TO A CHEMICAL PROCESS NETWORK IN ASPEN PLUS DYNAMICS

This section illustrates the implementation of the PIGCRN based detector for cyber-attacks using a chemical process network simulated in Aspen Plus Dynamics. First, a dynamic model of the chemical process network is developed using Aspen Plus Dynamics V12. Subsequently, time-series data sets are collected for both the nominal system and various scenarios where diferent sensors are compromised by cyber-attacks. Finally, the PIGCRN model is trained and tested using these data sets, and the detection performance of the PIGCRN-based detector is evaluated and discussed.

Description of the Process Network in Aspen Plus Dynamics. In this work, we consider the production process of ethylbenzene (EB) using ethylene (E) and benzene (B) as raw materials. The primary reaction involved in this process is a second-order exothermic and irreversible reaction, which occurs alongside two other side reactions. The chemical reactions are presented as follows:

$$
\mathrm{C} _ {2} \mathrm{H} _ {4} + \mathrm{C} _ {6} \mathrm{H} _ {6} \rightarrow \mathrm{C} _ {8} \mathrm{H} _ {1 0}\tag{20}
$$

$$
\mathrm{C} _ {2} \mathrm{H} _ {4} + \mathrm{C} _ {8} \mathrm{H} _ {1 0} \rightarrow \mathrm{C} _ {1 0} \mathrm{H} _ {1 4}\tag{21}
$$

$$
\mathrm{C} _ {6} \mathrm{H} _ {6} + \mathrm{C} _ {1 0} \mathrm{H} _ {1 4} \rightarrow 2 \mathrm{C} _ {8} \mathrm{H} _ {1 0}\tag{22}
$$

The chemical reactions take place in two nonisothermal, well mixed continuous stirred tank reactors (CSTRs) in series. Specifically, the process model is first developed in Aspen Plus, where steady-state simulations are performed based on material and energy balances, and the results are thoroughly checked for accuracy. Subsequently, dynamic simulations of the process are performed with Aspen Plus Dynamics to analyze and control the dynamic behavior of the system. The detailed steps involved in building the steady-state and dynamic models can be referenced in ref 20. The dynamics of the chemical process network can be represented by the following ODEs:

$$
\frac {d C _ {\mathrm{E1}}}{d t} = \frac {F _ {\mathrm{I}} C _ {\mathrm{E10}} - F _ {\mathrm{out1}} C _ {\mathrm{E1}}}{V _ {\mathrm{I}}} - r _ {\mathrm{1}} - r _ {\mathrm{2}}\tag{23}
$$

$$
\frac {d C _ {\mathrm{B1}}}{d t} = \frac {F _ {1} C _ {\mathrm{B10}} - F _ {\mathrm{out1}} C _ {\mathrm{B1}}}{V _ {1}} - r _ {1} - r _ {3}\tag{24}
$$

$$
\frac {d C _ {\mathrm{EB1}}}{d t} = \frac {- F _ {\mathrm{out1}} C _ {\mathrm{EB1}}}{V _ {1}} + r _ {1} - r _ {2} + 2 r _ {3}\tag{25}
$$

$$
\frac {d C _ {\mathrm{DEB1}}}{d t} = \frac {- F _ {\mathrm{out1}} C _ {\mathrm{DEB1}}}{V _ {1}} + r _ {2} - r _ {3}\tag{26}
$$

$$
\frac {d T _ {1}}{d t} = \frac {(T _ {1 0} F _ {1} - T _ {1} F _ {\mathrm{out1}})}{V _ {1}} + \sum_ {j = 1} ^ {3} \frac {- \Delta H _ {j}}{\rho_ {1} C _ {p}} r _ {j} + \frac {Q _ {1}}{\rho_ {1} C _ {p} V _ {1}}\tag{27}
$$

$$
\frac {d C _ {\mathrm{E2}}}{d t} = \frac {F _ {2} C _ {\mathrm{E20}} + F _ {\mathrm{out1}} C _ {\mathrm{E1}} - F _ {\mathrm{out2}} C _ {\mathrm{E1}}}{V _ {2}} - r _ {1} - r _ {2}\tag{28}
$$

$$
\frac {d C _ {\mathrm{B2}}}{d t} = \frac {F _ {2} C _ {\mathrm{B20}} + F _ {\mathrm{out1}} C _ {\mathrm{B1}} - F _ {\mathrm{out2}} C _ {\mathrm{B1}}}{V _ {2}} - r _ {1} - r _ {3}\tag{29}
$$

$$
\frac {d C _ {\mathrm{EB2}}}{d t} = \frac {F _ {\mathrm{out1}} C _ {\mathrm{EB1}} - F _ {\mathrm{out2}} C _ {\mathrm{EB2}}}{V _ {2}} + r _ {1} - r _ {2} + 2 r _ {3}\tag{30}
$$

$$
\frac {d C _ {\mathrm{DEB2}}}{d t} = \frac {F _ {\mathrm {out_ {1}}} C _ {\mathrm{DEB1}} - F _ {\mathrm{out2}} C _ {\mathrm{DEB2}}}{V _ {2}} + r _ {2} - r _ {3}\tag{31}
$$

where the reaction rates can be calculated as follows:

$$
r _ {1} = k _ {1} e ^ {- E _ {1} / R T _ {i}} C _ {\mathrm{Ei}} C _ {\mathrm{Bi}}\tag{32}
$$

$$
r _ {2} = k _ {2} e ^ {- E _ {2} / R T _ {i}} C _ {\mathrm{EB} i} C _ {\mathrm{E} i}\tag{33}
$$

$$
r _ {3} = k _ {3} e ^ {- E _ {3} / R T _ {i}} C _ {\mathrm{DEBi}} C _ {\mathrm{Bi}}, i = 1, 2\tag{34}
$$

where $C _ { \mathrm { B } } , C _ { \mathrm { E } } , C _ { \mathrm { E B } } ,$ and $C _ { \mathrm { D E B } }$ represent the concentrations of benzene, ethylene, ethylbenzene, and diethylenebenzene (DEB), respectively, and $\rho _ { i } , T _ { i } ,$ and $V _ { i }$ denote the mass density, temperature, and liquid volume of $\mathrm { C S T R } _ { i } , i = 1 , 2$ , respectively. The mass heat capacity of the liquid mixture, denoted as $C _ { p } ,$ is assumed to remain constant. The specific values of the process parameters are detailed in Table 1, where the subscript ${ } ^ { \omega } 0 ^ { \it { p } }$ indicates the initial state and $" s "$ denotes the steady-state conditions.

Table 1. Process Parameter of the Aspen Plus Model

<table><tr><td> $T_{1s} = 400 \text{ K}$ </td><td> $T_{2s} = 450 \text{ K}$ </td></tr><tr><td> $C_{E1s} = 0.0835 \text{ kmol/kmol}$ </td><td> $C_{E2s} = 0.0164 \text{ kmol/kmol}$ </td></tr><tr><td> $C_{B1s} = 0.2404 \text{ kmol/kmol}$ </td><td> $C_{B2s} = 0.1853 \text{ kmol/kmol}$ </td></tr><tr><td> $C_{EB1s} = 0.5409 \text{ kmol/kmol}$ </td><td> $C_{EB2s} = 0.6527 \text{ kmol/kmol}$ </td></tr><tr><td> $C_{DEB1s} = 5.1318 \times 10^{-4} \text{ kmol/kmol}$ </td><td> $C_{DEB2s} = 0.0011 \text{ kmol/kmol}$ </td></tr><tr><td>heat transfer option</td><td>dynamics</td></tr><tr><td>medium temperature</td><td>298 K</td></tr><tr><td>temperature approach</td><td>77.33 K</td></tr><tr><td>heat capacity of coolant</td><td>4200 J/kg K</td></tr><tr><td>medium holdup</td><td>1000 kg</td></tr><tr><td> $C_p = 2.267 \text{ kJ/kg K}$ </td><td> $\rho_1 = 632.6490 \text{ kg/m}^3$ </td></tr><tr><td> $V_1 = V_2 = 60 \text{ m}^3$ </td><td> $\rho_2 = 594.3740 \text{ kg/m}^3$ </td></tr></table>

The process flowchart for this production setup is illustrated in Figure 2. Specifically, each CSTR is equipped with a cooling jacket to remove or supply heat by adjusting the flow rate of the cooling medium. Additionally, the feed flow rates $F _ { 1 }$ and $F _ { 2 }$ to the reactors are controlled by adjusting the openings of the valves $V _ { 1 }$ and $V _ { 2 } ,$ respectively, which, in turn, regulate the concentration of materials within the reactors. Furthermore, a direct-acting level controller is installed on each reactor to maintain the liquid level at half of the reactor’s capacity, ensuring optimal operation.

The controller is developed to control the concentration of ethylbenzene $C _ { \mathrm { E B } }$ and the temperature T in both CSTRs to their steady-state $( C _ { \mathrm { E B } s } , T _ { s } )$ by adjusting the feed flow rates and the flow rates of the cooling medium. In Aspen Plus Dynamics, a combination of PID and cascade control is employed to achieve this goal, with the PID parameters determined through careful tuning to ensure optimal performance. Therefore, in this case, the state variables are $C _ { \mathrm { E B 1 } } , T _ { 1 } , C _ { \mathrm { E B 2 } }$ , and $T _ { 2 } \left( \mathrm { i . e . , } x = \left[ C _ { \mathrm { E B 1 } } , T _ { 1 } , \right. \right.$ $C _ { \mathrm { E B } 2 } , ~ T _ { 2 } ] )$ , which are the target of potential cyber-attacks. The manipulated inputs are the feed flow rates $F _ { 1 }$ and $F _ { 2 } ,$ and the cooling medium flow rates $C F _ { 1 }$ and CF $( { \mathrm { i . e . , ~ } } u = \left[ F _ { 1 } , F _ { 2 } , C F _ { 1 } , \right.$ $C F _ { 2 } ] )$ , which are adjusted in real-time to maintain the desired steady-state within the reactors.

Data Generation. The geometric attack ofeq 3 is applied in this chemical process network and is considered for training a PIGCRN-based detector. Specifically, for temperature sensor $T ,$ the geometric attack parameters are set to $\beta = 0 . 5$ and $\alpha = 0 . 1 5 ,$ while for concentration sensor $C _ { \mathrm { E B } } ,$ the parameters are $\beta = 0 . 0 0 5$ and $\alpha = 0 . 1$ . The sensor under attack will remain compromised until the end ofthe simulation. In this work, the cyber-attack can target either one sensor or multiple sensors simultaneously. Specifically, we consider scenarios where cyber-attacks could compromise both $T _ { 1 }$ and $T _ { 2 }$ at the same time. The closed-loop simulation of the system under attack is performed using the

![](images/0bb5637065eec1301a1b29dc86f4ae69f9ae3afbeadaa671d4c529a53ee83157.jpg)  
Figure 2. Flowchart of two CSTRs in series in Aspen Plus Dynamics.

Aspen dynamic model, with pseudosensor input signals generated by MATLAB scripts. To facilitate the interaction between Aspen Plus Dynamics and MATLAB, a message passing interface (MPI) is constructed, which enabled the dynamic model to automatically read the input signals generated by MATLAB and implement them within the dynamic simulation. The MATLAB script plays a critical role in this setup by taking the true state values and generating the compromised sensor measurements x according to eq 3. These compromised readings are then fed into the PID controllers within the model, allowing the simulation ofthe impact ofcyber attacks on the process control system.

To develop a PIGCRN-based detector, closed-loop simulations are first performed in Aspen Plus Dynamics to collect training data. Specifically, time-series trajectories of the closedloop states are gathered for both the nominal system and scenarios, where diferent sensors are subjected to geometric attacks. These trajectories are simulated from various initial states $x _ { 0 }$ to capture a wide range of system behaviors. The sampling interval is set to 0.01 h, and each dynamic simulation runs for a duration of 2 h. Additionally, the sliding-window approach with the width of $N _ { T } = 5$ is applied to segment the raw time-series data, allowing the model to be used for real-time monitoring. To ensure accuracy of the PIGCRN model, each output class of attack has the same number of samples. Specifically, 20 samples are collected for each sensor under attack, and 60 samples are collected for the nominal system. Therefore, a total of 160 samples are collected to simulate the real-world scenario where only a limited number of instances under cyber-attacks can be used, reflecting the imbalance in such data sets. Each sample is structured as a two-dimensional matrix of size $n \times N _ { T }$ where $n = 4$ represents the number of state variables, and $N _ { T } = ~ 5$ is the length of the sliding window. Furthermore, all data samples are normalized.

Remark 4 In practice, while cyber-attacks on industrial operations are relatively rare, making it challenging to collect real-world training data for such events, their consequences can be catastrophic when they do occur. This underscores the motivation for developing the physics-informed graph convolutional recurrent network, which aims to improve the detection of cyber-attacks while reducing the dependency on the amounts of training data. In scenarios where companies lack data from actual attacked operations, a common approach is to use simulation-based data. As demonstrated in this work, chemical process networks can be simulated in Aspen Plus Dynamics, and various attack scenarios can be introduced to generate training data sets. This method allows the creation of diverse attack scenarios, providing a robust foundation for training machine learning models, even in the absence ofreal-world data. By using simulated environments, companies can prepare detection systems for potential cyber-attacks in advance, ensuring the safety of industrial operations.

Construction of PIGCRN-Based Detector. As described in the Graph Convolutional Network section, the PIGCRN model requires a system graph as part of its input data structure. Therefore, we begin by translating the chemical process topology in Figure 2 into a directed graph. Following the steps detailed in the Knowledge-Guided Topology Graph Construction section, the directed system graph is constructed in Figure 3. Specifically, changes in the flow rates of the cooling medium $C F _ { 1 }$ and $C F _ { 2 }$ directly impact the reactor temperatures $T _ { 1 }$ and $T _ { 2 } ,$ which in turn change the reaction rates of chemical reactions and ultimately afect $\bar { C } _ { \mathrm { E B 1 } }$ and $C _ { \mathrm { E B } 2 } .$ Given that the two CSTRs are connected in series, the output of the first CSTR becomes the input of the second reactor, implying that fluctuations in $C _ { \mathrm { E B 1 } }$ and $T _ { 1 }$ propagate through the system to afect $C _ { \mathrm { E B } 2 }$ and $T _ { 2 } .$ Additionally, increases in the feed flow rates $F _ { 1 }$ and $F _ { 2 }$ lead to corresponding increases in $C _ { \mathrm { E B 1 } }$ and $C _ { \mathrm { E B } 2 } $ respectively. The edge weights in the directed graph are calculated using the mutual information method and are reported in Table 2.

![](images/cdc4dd0d99a6dec55e63e44d9b7f5a7ed2dbeec4fbe95d49901ae368651fe780.jpg)  
Figure 3. System diagram of the two-CSTR network, where the thickness of arrows represents the strengths of connections between nodes.

Table 2. Edge Weights in the System Digraph of Figure 3

<table><tr><td>source</td><td>target</td><td>edge weight</td></tr><tr><td> $CF_1$ </td><td> $T_1$ </td><td>0.1575</td></tr><tr><td> $T_1$ </td><td> $C_{EB1}$ </td><td>0.1816</td></tr><tr><td> $T_1$ </td><td> $C_{EB2}$ </td><td>0.0844</td></tr><tr><td> $T_1$ </td><td> $T_2$ </td><td>0.1114</td></tr><tr><td> $F_1$ </td><td> $C_{EB1}$ </td><td>0.0799</td></tr><tr><td> $C_{EB1}$ </td><td> $C_{EB2}$ </td><td>0.0640</td></tr><tr><td> $C_{EB1}$ </td><td> $T_2$ </td><td>0.0903</td></tr><tr><td> $CF_2$ </td><td> $T_2$ </td><td>0.2177</td></tr><tr><td> $T_2$ </td><td> $C_{EB2}$ </td><td>0.1189</td></tr><tr><td> $F_2$ </td><td> $C_{EB2}$ </td><td>0.2239</td></tr></table>

The PIGCRN model consists of a GCN layer and an LSTM layer, each containing 64 neurons, and is developed using the open-source machine learning library, PyTorch. To evaluate the performance of the proposed model, a purely data-driven RNN model and a GCRN model with the same hyperparameters and structure as the PIGCRN model are also trained using the same data set, which serve as benchmarks for comparison with the PIGCRN model. The RNN, GCRN, and PIGCRN models are all trained for 500 epochs using the Adam optimizer with an early stopping mechanism to prevent overfitting.

Results and Discussion. To better compare the performance of diferent models, the RNN, GCRN, and PIGCRN models were tested on a larger testing data set of a total of 2,320 samples collected for each class label. The confusion matrices of the RNN, GCRN, and PIGCRN models are shown in Figure 4. To ensure that the proposed model can be easily extended to scenarios where multiple sensors are simultaneously compromised, the detectors are designed to output the status of each sensor independently, making it flexible and robust for various cyber-attack scenarios in industrial processes. Specifically, the detector outputs a vector in the form of $[ x _ { a } , x _ { b } , x _ { c } , x _ { d } ] _ { \ast }$ , where $x _ { \omega }$ $x _ { b } , x _ { c } , x _ { d } = 0 \mathrm { o r } 1$ , indicating that $C _ { \mathrm { E B 1 } } , T _ { 1 }$ , C , and $T _ { 2 }$ are under normal operation or attack, respectively. The performances of the RNN-based detector, the GCRN-based detector, and the PIGCRN-based detector are summarized in Table 3. It is important to note that in this case, a sample is considered correctly detected only if the model accurately predicts the status ofevery sensor within that sample $( \mathrm { i . e . , } C _ { \mathrm { E B 1 } } , \bar { T } _ { 1 } , C _ { \mathrm { E B 2 } } ,$ and $T _ { 2 }$ are all correctly identified). The GCRN model shows a significant improvement over the RNN model, with higher accuracy in most metrics. This demonstrates that by embedding domain knowledge of the process topology, the GCRN is better able to capture complex dynamics and identify the occurrence of attacks in a chemical process network. Specifically, the graph structure enables the GCRN model to understand the spatial dependencies and interactions between diferent process variables and manipulated inputs, which are critical for accurately detecting cyber-attacks. It can be seen from the table that both the RNN and the GCRN models struggle to accurately detect attacks on the temperature sensors $T _ { 1 }$ and $T _ { 2 } .$ The accuracy for detecting attacks on $T _ { 1 }$ is particularly low at 55.21% for the RNN model and 58.85% for the GCRN model.

Similarly, the detection accuracy for attacks on $T _ { 2 }$ is 40.36% for the RNN model and 59.38% for the GCRN model. Specifically, as shown in Figure $^ { 4 , }$ the RNN model and the GCRN model frequently misclassify attacks on $T _ { 2 }$ as normal operations, resulting in a high false negative rate.

To address these challenges, in this work, the physicsinformed loss terms tailored for $T _ { 1 }$ and $T _ { 2 }$ are introduced into the PIGCRN model. The results demonstrate that the PIGCRN model outperforms both the RNN and GCRN models with an overall accuracy of 80.47%. Specifically, by embedding the knowledge about attack patterns, the PIGCRN model significantly improves its accuracy in detecting attacks on $T _ { 1 }$ (75.78%) and $\hat { T } _ { 2 }$ (73.70%). Additionally, when both $T _ { 1 }$ and $T _ { 2 }$ are compromised by cyber-attacks simultaneously, the PIGCRN model also shows further improvement, achieving an accuracy of 74.48%, compared to 56.25% for RNN and 63.02% for GCRN. This demonstrates that the physics-informed loss function can guide the model to better capture the subtle efects of attacks, especially in complex scenarios where changes in sensor readings may be subtle $\left( \mathrm { e . g . } \right)$ , the initial stages of the geometric attack). It can be observed from the table that the GCRN model has a higher accuracy for the nominal system compared with the PIGCRN model. This is because the physics-informed loss function in the PIGCRN model increases its sensitivity to subtle changes in sensor measurements, which may lead to misclassification of normal system behavior as an attack. However, this increased sensitivity significantly improves the detection accuracy for $T _ { 1 } , T _ { 2 } ,$ and ultimately results in a higher overall accuracy for the PIGCRN model.

To further validate the proposed PIGCRN model, a comparison is conducted with a Transformer-based model, which is widely recognized as a state-of-the-art approach in time series modeling and anomaly detection.<sup>21</sup> The Transformer model is known for its self-attention mechanism, which allows it to weigh the importance of diferent parts of the input data, enabling more dynamic and context-aware processing of sequences compared with traditional models that process data step by step. However, the results indicate that the PIGCRN model still achieves a higher overall accuracy compared with the Transformer model, which achieves an overall accuracy of 75.95%. As shown in Table 3, while the Transformer mode performed competitively for simultaneous attacks on $T _ { 1 }$ and $T _ { 2 }$ (75.26%), its performance is poorer for individual sensor attacks. Specifically, the Transformer model achieves accuracies of65.36% for $T _ { 1 }$ and 69.79% for $T _ { 2 } ,$ which are notably inferior to the corresponding accuracies of 75.78 and 73.70% achieved by the PIGCRN model. Overall, the results demonstrate that compared to the RNN, GCRN, and Transformer models, the PIGCRN model improves the accuracy of detecting cyberattacks in chemical process networks by efectively combining topological knowledge of chemical processes with a prior knowledge of cyber-attacks.

Additionally, to quantify the extent to which the PIGCRN model reduces the training data requirement compared to RNN and GCRN models, several experiments are conducted with varying training sample sizes. The results show that the overall accuracy of the RNN model reaches 79.09% when the training sample size is increased to 340. Similarly, the GCRN model achieves an accuracy of 78.62% with 300 training samples. In contrast, the PIGCRN model requires only 160 training samples to reach an overall accuracy of 80.47%, demonstrating that the PIGCRN models can reduce data requirements to achieve a comparable or better detection accuracy. Specifically, when aiming for an accuracy close to 80%, the PIGCRN model reduces the training data requirement by 52.9% compared with the RNN and by 46.6% compared with the GCRN.

![](images/f7805d86960ac1bb2249b93536cb6cb36927619518a59fe1f038563e7e9777d1.jpg)  
(a)

![](images/06836cc7c37d2cd71bb9f2347be19e1cce80a1698206b4d9e3c68e31b0ef281e.jpg)  
(b)

![](images/e55b35280d7775bcd22689ac653fef49788805c22788f8f527dbac27871b4161.jpg)  
(c)  
Figure 4. Confusion matrices ofthe (a) RNN model, (b) GCRN model, and (c) PIGCRN model. Each matrix provides a comparative visualization of the predicted versus true labels. The x label is the detector output, which is a vector in the form o $\cdot \lbrack x _ { a } , x _ { b } , x _ { c } , x _ { d } ] , \bar { \mathrm { w i t h } } x _ { a } , x _ { b } , x _ { c } , x _ { d } = 0 \mathrm { o r } 1 _ { \ r { R } }$ , indicating that $C _ { \mathrm { E B 1 } } ^ { \mathrm { ~ - ~ } } , T _ { 1 } , C _ { \mathrm { E B } 2 } ^ { \mathrm { ~ ~ } }$ and $T _ { 2 }$ are under normal operation or attack, respectively.

Next, the PIGCRN-based detection system is deployed for online implementation to evaluate its real-time detection capabilities. Given that the length of the sliding detection window $N _ { T }$ is set to ${ \mathfrak { H } } ,$ the PIGCRN-based detection system activates at $t = 0 . 0 5$ h, allowing it to collect measurement trajectories over 5 time steps. The alarm threshold $N _ { a }$ is set to 5 to reduce the false alarm rate, ensuring reliable detection. The state profiles of $T _ { 1 }$ and $T _ { 2 }$ for geometric attack under the PIGCRN-based detection system are shown in Figure 5. As

Table 3. Comparison of Detection Accuracy under Diferent Models

<table><tr><td>metric</td><td>RNN (%)</td><td>GCRN (%)</td><td>PIGCRN (%)</td><td>transformer (%)</td></tr><tr><td>accuracy for  $C_{EB1}$  under attack</td><td>82.55</td><td>83.33</td><td>87.50</td><td>79.17</td></tr><tr><td>accuracy for  $T_1$  under attack</td><td>55.21</td><td>58.85</td><td>75.78</td><td>65.36</td></tr><tr><td>accuracy for  $C_{EB2}$  under attack</td><td>84.90</td><td>88.54</td><td>89.84</td><td>85.16</td></tr><tr><td>accuracy for  $T_2$  under attack</td><td>40.36</td><td>59.38</td><td>73.70</td><td>69.79</td></tr><tr><td>accuracy for  $T_1$  and  $T_2$  under attack</td><td>56.25</td><td>63.02</td><td>74.48</td><td>75.26</td></tr><tr><td>accuracy for nominal system</td><td>80.00</td><td>86.25</td><td>81.50</td><td>80.75</td></tr><tr><td>overall accuracy</td><td>66.63</td><td>73.31</td><td>80.47</td><td>75.95</td></tr></table>

![](images/cfeb3e4339c95f5d2da8c9a914413f4c879837aa186bb79d1bc55c539daa3974.jpg)

![](images/8c32e675bb376dac95828ac41428a5650879e1991b279b6f6c17cfe86da86ff3.jpg)  
Figure 5. Closed-loop state profiles under the PIGCRN-based detection system when geometric attacks are simultaneously intro duced at t = 0.21 hrs on the temperature sensors for $T _ { 1 }$ and $T _ { 2 } .$

illustrated in Figure 5, the geometric attack occurs simultaneously in $T _ { 1 }$ and $T _ { 2 }$ at t = 0.21 h, and the PIGCRN-based detection system successfully identifies the cyber-attack after 5 sampling points $( { \mathrm { i . e . , ~ a t ~ } } t = 0 . 2 6 ~ { \mathrm { h } } )$ ). Additionally, it can be observed that without a resilient control system, the PID controller operating with compromised sensor readings drives the closed-loop states away from their steady state, potentially causing significant disruption to the system. This highlights the critical role of the PIGCRN-based detection system in detecting cyber-attacks early and accurately, thereby leaving suficient time for the system to respond appropriately. By efectively distinguishing between normal fluctuations and cyber-attacks, the PIGCRN-based detection system enhances the overall security framework of the chemical process, contributing to its robust and safe operation.

Remark 5 Once cyber-attacks have been detected, resilient control strategies can be implemented to mitigate the impact of cyber-attacks and restore the system to stable operating condition. For example, Chen et al. proposed a combination of closed-loop and open-loop control actions to ensure the stability of the closed-loop system in the presence of cyberattacks over time.<sup>22</sup> Wu et al. proposed a machine learning-based state reconstruction method to estimate process states using 23 compromised sensor measurements upon detection ofattacks. Additionally, Wu et al. developed an extended Kalman filter that incorporated domain knowledge to provide state estimation for postattack resilient control, which allowed the system to continue operating safely and eficiently despite the presence of cyber-attacks.<sup>8</sup>

## ■ CONCLUSIONS

In this work, we developed a PIGCRN-based detector for cyber attack detection and isolation in chemical process networks. Specifically, topological knowledge of chemical process net works was incorporated into a system digraph, and the mutual information method was used to assign weights to each edge in the digraph, efectively capturing the interactions among diferent process variables. A GCRN model was developed to integrate graph-based spatial information with temporal dependencies to model the complex dynamics of chemical process networks. Additionally, a priori knowledge of attack patterns was embedded in the loss function of PIGCRN as a regularization term to improve its learning performance. Finally, the proposed PIGCRN-based detector system was implemented in a chemical process network simulated by Aspen Plus Dynamics. The simulation results demonstrated that the PIGCRN-based detector significantly outperformed traditional RNN and GCRN models in terms of accuracy while reducing the requirements for training data.

## ■ AUTHOR INFORMATION

## Corresponding Author

Zhe Wu − Department of Chemical and Biomolecular Engineering, National University of Singapore, 117585, Singapore; orcid.org/0000-0002-2923-149X; Email: wuzhe@nus.edu.sg

## Authors

Guoquan Wu − Department of Chemical and Biomolecular Engineering, National University of Singapore, 117585, Singapore

Haohao Zhang − Department of Chemical and Biomolecular Engineering, National University of Singapore, 117585, Singapore; School of Chemical Engineering, University of Chinese Academy of Sciences, Beijing 100049, China; Key Laboratory of Green Process and Engineering, Institute of Process Engineering, Chinese Academy of Sciences, Beijing 100190, China

Wanlu Wu − Department of Chemical and Biomolecular Engineering, National University of Singapore, 117585, Singapore

Yujia Wang − Department of Chemical and Biomolecular Engineering, National University of Singapore, 117585, Singapore

Complete contact information is available at: https://pubs.acs.org/10.1021/acs.iecr.4c03601

## Notes

The authors declare no competing financial interest.

## ACKNOWLEDGMENTS

Financial support from NUS Start-up Grant (A-0009486-03-00) and MOE AcRF Tier 1 (22-5367-A0001) is gratefully acknowledged.

## ■ REFERENCES

(1) Parker, S.; Wu, Z.; Christofides, P. D. Cybersecurity in process control, operations, and supply chain. Comput. Chem. Eng. 2023, 171, No. 108169.

(2) Chen, S.; Wu, Z.; Christofides, P. D. Cyber-security ofcentralized, decentralized, and distributed control-detector architectures for nonlinear processes. Chem. Eng. Res. Des. 2021, 165, 25−39.

(3) Oyama, H.; Durand, H. Integrated cyberattack detection and resilient control strategies using Lyapunov-based economic model predictive control. AlChE J. 2020, 66, No. e17084.

(4) Narasimhan, S.; El-Farra, N. H.; Ellis, M. J. Detectability-based controller design screening for processes under multiplicative cyberattacks. AlChE J. 2022, 68, No. e17430.

(5) Wu, Z.; Albalawi, F.; Zhang, J.; Zhang, Z.; Durand, H.; Christofides, P. D. Detecting and handling cyber-attacks in model predictive control of chemical processes. Mathematics 2018, 6, 173.

(6) Song, H. M.; Woo, J.; Kim, H. K. In-vehicle network intrusion detection using deep convolutional neural network. Veh. Commun. 2020, 21, No. 100198.

(7) Zheng, Y.; Hu, C.; Wang, X.; Wu, Z. Physics-informed recurrent neural network modeling for predictive control of nonlinear processes. J. Process Control 2023, 128, No. 103005.

(8) Wu, G.; Wang, Y.; Wu, Z. Physics-informed machine learning in cyber-attack detection and resilient control of chemical processes. Chem. Eng. Res. Des. 2024, 204, 544−555.

(9) Wu, G.; Yion, W. T. G.; Dang, K. L. N. Q.; Wu, Z. Physicsinformed machine learning for MPC: Application to a batch crystallization process. Chem. Eng. Res. Des. 2023, 192, 556−569.

(10) Rao, C.; Sun, H.; Liu, Y. Physics-informed deep learning for incompressible laminar flows. Theor. Appl. Mech. Lett. 2020, 10, 207− 212.

(11) Scarselli, F.; Gori, M.; Tsoi, A. C.; Hagenbuchner, M.; Monfardini, G. The graph neural network model. IEEE Trans. Neural Networks 2009, 20, 61−80.

(12) Zhang, S.; Tong, H.; Xu, J.; Maciejewski, R. Graph convolutional networks: a comprehensive review. Comput. Soc. Networks 2019, 6, No. 11.

(13) Yu,J.; Yin, H.; Li,J.; Gao, M.; Huang, Z.; Cui, L. Enhancing social recommendation with adversarial graph convolutional networks. IEEE Trans. Knowl. Data Eng. 2022, 34, 3727−3739.

(14) Kojima, R.; Ishida, S.; Ohta, M.; Iwata, H.; Honma, T.; Okuno, Y. kGCN: a graph-based deep learning framework for chemical structures. J. Cheminf. 2020, 12, 1−10.

(15) Jia, M.; Xu, D.; Yang, T.; Liu, Y.; Yao, Y. Graph convolutional network soft sensor for process quality prediction. J. Process Control 2023, 123, 12−25.

(16) Wu, D.; Zhao, J. Process topology convolutional network model for chemical process fault diagnosis. Process Saf. Environ. Prot. 2021, 150, 93−109.

(17) Tang, W.; Daoutidis, P. Network decomposition for distributed control through community detection in input-output bipartite graphs. J. Process Control 2018, 64, 7−14.

(18) Cui, Z.; Henrickson, K.; Ke, R.; Wang, Y. Traffic graph convolutional recurrent neural network: A deep learning framework for network-scale traffic learning and forecasting. IEEE Trans. Intell. Transp. Syst. 2020, 21, 4883−4894.

(19) Zhao, L.; Song, Y.; Zhang, C.; Liu, Y.; Wang, P.; Lin, T.; Deng, M.; Li, H. T-GCN: A temporal graph convolutional network for traffic prediction. IEEE Trans. Intell. Transp. Syst. 2020, 21, 3848−3858.

(20) Alhajeri, M. S.; Luo, J.; Wu, Z.; Albalawi, F.; Christofides, P. D. Process structure-based recurrent neural network modeling for predictive control: A comparative study. Chem. Eng. Res. Des. 2022, 179, 77−89.

(21) Wu, H.; Triebe, M. J.; Sutherland, J. W. A transformer-based approach for novel fault detection and fault classification/diagnosis in manufacturing: A rotary system application. J. Manuf. Syst. 2023, 67, 439−452.

(22) Chen, S.; Wu, Z.; Christofides, P. D. Cyber-attack detection and resilient operation of nonlinear processes under economic model predictive control. Comput. Chem. Eng. 2020, 136, No. 106806.

(23) Wu, Z.; Chen, S.; Rincon, D.; Christofides, P. D. Post cyberattack state reconstruction for nonlinear processes using machine learning. Chem. Eng. Res. Des. 2020, 159, 248−261.

![](images/01678dab5eb48a25a9a6d8b96ae870c8ed36135f7dd55c72d63d4b0c5fe94f68.jpg)

CAS BIOFINDER DISCOVERY PLATFORMTM

# CAS BIOFINDER HELPS YOU FIND YOUR NEXT BREAKTHROUGH FASTER

Navigate pathways, targets, and diseases with precision

Explore CAS BioFinder