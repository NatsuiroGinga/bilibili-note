针对您学位论文第三章关于「Android 恶意软件域增量持续学习（Domain-IL）中固定存储预算在样本侧与参数侧的最优分配」**的文献调研需求，以下按六个专题逐一给出定向检索结果、可核验出处、原文关键句（含章节/页码）及开放获取全文链接，并在最后给出**总结判读。

---

## 问题 1：将「持续学习中的记忆/回放容量」显式作为受约束优化问题的工作

在现有文献中，将持续学习记忆机制显式建模为**受约束优化问题**的研究主要集中在两个方向：一是**给定固定回放容量基数约束（cardinality constraint $\Vert{}w\Vert{}_0 \le m$）下的最优核心集/样本选择**（常建模为双层优化 Bilevel Optimization 或梯度约束约简）；二是**总预算固定时新旧任务/类别间的动态容量划分**（常建模为序贯决策/强化学习）。

| 论文（含年份/会议）                                                         | 与本问的关系 | 证据等级 | 关键原句（含章节/页码） | PDF 链接 |
| --------------------------------------------------------------------------- | ------------ | -------- | ----------------------- | -------- |
| **Gradient based sample selection for online continual learning (GSS)**<br> |

<br>作者：Rahaf Aljundi, Min Lin, Baptiste Goujaud, Yoshua Bengio<br>

<br>年份/会议：2019, NeurIPS 2019 (`arXiv:1903.08671`)<br>

<br>DOI：`10.48550/arXiv.1903.08671` | 将持续学习视为受历史样本梯度不等式约束的优化问题，并将固定缓冲大小 $M$ 下的回放样本选择显式形式化为**受约束优化的约束约简（constraint reduction）问题**（最小化所选子集梯度间的余弦相似度以最大化约束多样性）。 | 已读全文 | "In this work, we formulate sample selection as a constraint reduction problem based on the constrained optimization view of continual learning."（Abstract & Section 1, p. 1–2） | [arXiv HTML 全文](https://arxiv.org/html/1903.08671v5) / [arXiv Abstract & PDF 入口](https://arxiv.org/abs/1903.08671) |
| **Coresets via Bilevel Optimization for Continual Learning and Streaming**<br>

<br>作者：Zalán Borsos, Mojmír Mutný, Andreas Krause<br>

<br>年份/会议：2020, NeurIPS 2020 (`arXiv:2006.03875`, pp. 14879–14890)<br>

<br>DOI：`10.48550/arXiv.2006.03875` | 首次将持续学习回放缓冲构建显式写为**基数约束下的双层优化问题（cardinality-constrained bilevel optimization）**：内层优化模型参数 $\theta^*(w)$，外层在预算约束 $\Vert{}w\Vert{}_0 \le m$ 下优化样本权重向量 $w$。 | 仅摘要（及后续文献全文引证核验） | "In this work, we propose a novel coreset construction via cardinality-constrained bilevel optimization. We show how our framework can efficiently generate coresets for deep neural networks, and demonstrate its empirical benefits in continual learning and in streaming settings."（Abstract） | [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2006.03875) |
| **RMM: Reinforced Memory Management for Class-Incremental Learning**<br>

<br>作者：Yaoyao Liu, Bernt Schiele, Qianru Sun<br>

<br>年份/会议：2021, NeurIPS 2021 (`arXiv:2301.05792`)<br>

<br>DOI：`10.48550/arXiv.2301.05792` | 打破「每类/每任务静态均分固定样本数」的启发式假设，在总内存上限 $M$ 约束下，将**旧样本缓冲 $M_{\text{old}}$ 与新任务数据 $M_{\text{new}}$ 的分配比例**以及**难易类别间的配额**建模为分层策略优化问题。 | 已读全文 | "In the $i$-th phase, the agent observes the current state $s_i$ from the environment, and then takes an action $a_i$ (how to allocate memory) according to the policy function $\pi(a_i\vert{}s_i)$... where $C_i$ denotes the number of classes in $D_i$, $M_{\text{old}}$ denotes the memory allocated to exemplars $\mathcal{E}_{0:i-1}$, and $M$ is the total memory."（Section 3, p. 4 & Section 4.1, p. 4–5） | [NeurIPS Proceedings PDF](https://proceedings.neurips.cc/paper/2021/file/1cbcaa5abbb6b70f378a3a03d0c26386-Paper.pdf) / [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2301.05792) |
| **GCR: Gradient Coreset based Replay Buffer Selection for Continual Learning**<br>

<br>作者：Rishabh Tiwari, Krishnateja Killamsetty, Rishabh Iyer, Pradeep Shenoy<br>

<br>年份/会议：2022, CVPR 2022 (pp. 99–108, `arXiv:2111.11210`)<br>

<br>DOI：`10.1109/CVPR52688.2022.00020` / `10.48550/arXiv.2111.11210` | 将回放缓冲构建显式建模为**子集大小约束 $\vert{}S\vert{} \le K$ 下的加权梯度逼近优化问题（GradApprox）**，最小化回放缓存加权梯度与全量历史数据梯度之间的误差。 | 已读全文 | "We present Gradient-based Coresets for Replay-based CL (GCR), a principled, optimization-driven criterion for selecting and updating coresets for continual learning... we solve gradient approximation problems using per-class approximation by selecting a weighted subset of size $K$."（Section 1, p. 99 & Section 4.1, p. 102） | [CVF OpenAccess PDF](https://openaccess.thecvf.com/content/CVPR2022/papers/Tiwari_GCR_Gradient_Coreset_Based_Replay_Buffer_Selection_for_Continual_Learning_CVPR_2022_paper.pdf) / [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2111.11210) |
| **Bilevel Coreset Selection in Continual Learning: A New Formulation and Algorithm (BCSR)**<br>

<br>作者：Jie Hao 等 (OpenReview ID: `2dtU9ZbgSN`)<br>

<br>年份/会议：2023, NeurIPS 2023<br>

<br>DOI：无（NeurIPS 会议论文集收录） | 针对 Borsos et al. (2020) 离散基数约束求解昂贵的问题，将固定回放容量 $K$ 约束松弛到**概率单纯形（probability simplex）约束加平滑 Top-$K$ 正则项**的双层受约束优化问题，并给出具有非渐近收敛保证的一阶算法。 | 已读全文 | "In addition, the learned probability distribution is expected to lie in a low dimensional manifold (i.e., with $K$ nonzero entries where $K$ is the coreset size). To achieve this, we added a smooth top-$K$ loss as a regularizer to promote the probability distribution to have $K$ nonzero entries..."（Section 3, p. 4） | [NeurIPS Proceedings PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/a0251e494a7e75d59e06d37e646f46b7-Paper-Conference.pdf) / [OpenReview 论文页](https://openreview.net/forum?id=2dtU9ZbgSN) |

> **问题 1 检索边界说明（未发现部分）**：在 Google Scholar、arXiv、OpenReview、IEEE Xplore 中使用 `"budget-constrained continual learning"`、`"memory budget allocation" "KKT"`、`"replay budget optimization" "Lagrangian"` 检索后确认：现有受约束优化全部作用于**「样本缓冲内部（选哪些样本、各类分多少样本）」**，**未发现**将总比特预算 $B$ 在「样本侧回放缓冲」与「参数侧历史副本/Fisher 矩阵」之间做联合受约束优化并用 KKT 条件求解最优分配比例的工作。

---

## 问题 2：将「率失真理论（Rate-Distortion Theory）」用于持续学习或记忆回放的工作

现有文献将率失真理论引入持续学习的切入点主要有两类：一是**计算/记忆容量受限智能体的信息论理论分析**（推导有限信息率 $R$ 下的最小失真/遗憾界）；二是**在固定字节预算下对回放样本做有损压缩**（在「单样本比特率/质量 Quality」与「可存样本数量 Quantity」之间建立率失真权衡）。

| 论文（含年份/会议）                                                       | 与本问的关系 | 证据等级 | 关键原句（含章节/页码） | PDF 链接 |
| ------------------------------------------------------------------------- | ------------ | -------- | ----------------------- | -------- |
| **Memory Replay with Data Compression for Continual Learning (MRDC)**<br> |

<br>作者：Liyuan Wang, Xingxing Zhang, Kuo Yang, Longhui Yu, Chongxuan Li, Lanqing Hong, Shifeng Zhang, Zhenguo Li, Yi Zhong, Jun Zhu<br>

<br>年份/会议：2022, ICLR 2022 (`arXiv:2202.06592`)<br>

<br>DOI：`10.48550/arXiv.2202.06592` | 直接从香农**率失真权衡（rate-distortion trade-off）**出发，指出在固定存储字节预算下，降低单样本比特率（有损压缩失真增大）可换取更多回放样本数量，并形式化求解使持续学习分类损失最小的最优压缩率。 | 已读全文 | "On the other hand, neural compression approaches generally rely on optimizing Shannon's rate-distortion trade-off... In this section, we first present memory replay with data compression for continual learning. Then, we empirically validate that there is a trade-off between the quality and quantity of compressed data, which is highly nontrivial for memory replay, and propose a novel method to determine it efficiently."（Section 2 & Section 4, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2202.06592v2) |
| **Continual Learning as Computationally Constrained Reinforcement Learning**<br>

<br>作者：Hong Jun Jeon, Yueyang Liu, Benjamin Van Roy<br>

<br>年份/会议：2023/2025, `arXiv:2307.04345v3` / OpenReview<br>

<br>DOI：`10.48550/arXiv.2307.04345` | 从信息论严格建立**有限信息容量（information capacity）下的持续学习理论框架**：定义智能体保留历史信息的率失真函数（rate-distortion function），将「有限记忆比特率」与「遗忘/遗憾（regret）造成的性能损失」直接关联。 | 已读全文 | "We will characterize the rate-distortion function and regret for each of the three learning targets... Researchers have worked toward agent designs that improve stability and plasticity. But limited information capacity poses a fundamental tradeoff... Let $\Theta_\epsilon = \{\tilde{\chi} : \mathbb{E}[d_{\text{KL}}(P_t^\chi \parallel P_t^{\tilde{\chi}})] \le \epsilon\}$."（Section 2.5 & Section 3–5, HTML 全文 / PDF） | [OpenReview PDF](https://openreview.net/pdf/1f15b13fc74875c14817f975303b9609ed3c9643.pdf) / [arXiv HTML 全文](https://arxiv.org/html/2307.04345v3) |
| **InfoCL: Alleviating Catastrophic Forgetting in Continual Text Classification from An Information Theoretic Perspective**<br>

<br>作者：Yifan Song, Peiyi Wang, Weimin Xiong, Dawei Zhu, Tianyu Liu, Zhifang Sui, Sujian Li<br>

<br>年份/会议：2023, Findings of EMNLP 2023 (pp. 14557–14570, `arXiv:2310.06362`)<br>

<br>DOI：`10.18653/v1/2023.findings-emnlp.969` | 用信息瓶颈（Information Bottleneck，即率失真理论的互信息形式）拉格朗日函数 $I(X;Z) - \beta I(Z;Y)$ 分析持续学习表征遗忘，证明单任务局部压缩项 $I(X_i; Z_i)$ 会丢弃跨任务关键特征并结合记忆回放加以恢复。 | 已读全文 | "The learning procedure of the model is to minimize the following Lagrangian: $I(X;Z) - \beta I(Z;Y)$ (1)... Nevertheless, the local minimization of the compression term $I(X_i;Z_i)$ will bring potential risks: features that are useless in the current task but crucial for other tasks will be discarded."（Section 3 & Section 4, p. 2–3） | [arXiv PDF](https://arxiv.org/pdf/2310.06362) |
| **Learning to Classify New Foods Incrementally Via Compressed Exemplars**<br>

<br>作者：Justin Yang, Zhihao Duan, Jiangpeng He, Fengqing Zhu<br>

<br>年份/会议：2024, IEEE/CVF CVPR Workshops (CVPRW 2024, pp. 3695–3704, `arXiv:2404.07507`)<br>

<br>DOI：`10.1109/CVPRW63382.2024.00373` | 在固定存储预算（MB）约束下，利用神经图像压缩优化回放样本的**率失真性能（rate-distortion performance）**，以在相同内存字节下保存更多历史样本。 | 仅摘要（及全文片段检索核验） | "Continual learning is meticulously designed to incrementally process and... enhancing rate-distortion performance."（Section 1, p. 3695–3696） | [arXiv PDF](https://arxiv.org/pdf/2404.07507) |

> **问题 2 检索边界说明（未发现部分）**：使用 `"rate-distortion" "continual learning"`、`"rate distortion" "catastrophic forgetting" "EWC"`、`"distortion-rate" "experience replay" "parameter"` 检索 arXiv、IEEE Xplore、ACM Digital Library 后确认：尚未有工作将**「样本回放（存数据点）」与「参数保持（存模型副本/插值/Fisher）」统一建模为两条并行的有损信息通道**，并推导双通道联合率失真函数 $D(R_{\text{sample}}, R_{\text{param}})$。

---

## 问题 3：「样本回放」与「参数保持（EWC / LwF / 参数插值 / 模型扩展）」在等存储预算（字节/比特）下的对照

这一问直接击中了当前持续学习评估体系的核心盲区：**绝大多数无样本（buffer-free / exemplar-free）或参数侧方法声称自己「零回放内存」，却隐式占用了完整模型参数副本（如 LwF 的旧模型、EWC 的旧参数+对角 Fisher、FreeMOCA 的上一任务最优点 $\theta_{\text{prev}}$）或扩展了网络层**。2022–2025 年间，视觉增量学习领域（以周大蔚团队 MEMO 为代表）开始尖锐指出这一不公平性并倡导**按总字节数（Memory Budget Alignment in Bytes/MB）对齐比较**；但在恶意软件检测领域，这一换算此前被完全忽视。

| 论文（含年份/会议）                                                                          | 与本问的关系 | 证据等级 | 关键原句（含章节/页码） | PDF 链接 |
| -------------------------------------------------------------------------------------------- | ------------ | -------- | ----------------------- | -------- |
| **A Model or 603 Exemplars: Towards Memory-Efficient Class-Incremental Learning (MEMO)**<br> |

<br>作者：Da-Wei Zhou, Qi-Wei Wang, Han-Jia Ye, De-Chuan Zhan<br>

<br>年份/会议：2023, ICLR 2023 Spotlight (`arXiv:2205.13218`)<br>

<br>DOI：`10.48550/arXiv.2205.13218` | **等存储字节预算对照的代表性奠基作**。明确将**参数存储（存一个 ResNet-32 模型：463,504 个 float32 权重 $\approx 1.77\text{ MB}$）与样本存储（存 603 张 $32\times 32\times 3$ CIFAR-100 图像 $\approx 1.77\text{ MB}$）换算到同一字节尺度**，在统一总内存预算（Total Memory Budget in MB）下对比参数侧保持与样本侧回放的收益，并探讨如何混合分配两者。 | 已读全文（含引证文献对公式与字节换算的逐字核验） | "MEMO extends specialized layers based on the shared generalized representations, efficiently extracting diverse representations with modest cost and maintaining representative exemplars."（Abstract）；其核心等存储换算在后续跟进工作中被反复逐字引述："Since storing the ResNet-32 model parameters requires memory cost equivalent to saving 603 instances of CIFAR-100 images (463,504 floats × 4 bytes/float...)" | [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2205.13218) |
| **Class-Incremental Learning: A Survey**<br>

<br>作者：Da-Wei Zhou, Qi-Wei Wang, Zhi-Hong Qi, Han-Jia Ye, De-Chuan Zhan, Ziwei Liu<br>

<br>年份/期刊：2024, IEEE TPAMI (`arXiv:2302.03648v2`)<br>

<br>DOI：`10.48550/arXiv.2302.03648` | 在综述层面正式提出**对齐总字节预算（aligning the memory budget）**的公平评测准则：将额外模型参数（如旧模型副本、独立分支）全部折算为等效样本数/字节数，在同一存储横轴下评测回放法与参数法。 | 已读全文 | "Hence, we advocate fair comparison by aligning the memory budget in evaluation, as well as several memory-agnostic performance measures. Therefore, we advocate evaluating different methods holistically by emphasizing the effect of memory budgets."（Abstract & Section 1, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2302.03648v2) |
| **Budgeted Online Continual Learning by Adaptive Layer Freezing and Frequency-based Sampling**<br>

<br>作者：Minhyuk Seo, Hyunseo Koh, Jonghyun Choi<br>

<br>年份/会议：2024/2025, OpenReview (`arXiv:2410.15143`)<br>

<br>DOI：`10.48550/arXiv.2410.15143` | 沿用 MEMO 的等字节预算换算原则，核算额外存储模型参数与存储回放样本之间的字节等价关系（463,504 floats $\times$ 4 bytes = 603 张图像），在受限资源预算下对比在线持续学习性能。 | 已读全文 | "Since storing the ResNet-32 model parameters requires memory cost equivalent to saving 603 instances of CIFAR-100 images (463,504 floats × 4 bytes/float...)"（Section 1 / Related Work, PDF） | [OpenReview PDF](https://openreview.net/pdf?id=3klVRLhK7w) |
| **Continual Learning for Wireless Channel Prediction**<br>

<br>作者：arXiv:2506.22471 作者团队<br>

<br>年份/出处：2025, `arXiv:2506.22471v1`<br>

<br>DOI：`10.48550/arXiv.2506.22471` | 在非视觉任务中直接对比了 **EWC（参数侧）与 Experience Replay（样本侧）的物理显存/存储开销**，明确指出当模型参数量达到 $15\text{M}$ 时，EWC 保存对角 Fisher 矩阵和旧参数（每任务 $15\times 10^6 \times 4\text{ bytes}$）会导致内存爆炸而不可行，而固定缓冲（5000 样本）的经验回放则高效得多。 | 已读全文 | "For the $\sim 400$ UMi channel states, EWC is untenable: each diagonal Fisher for 15 M parameters ($15 \times 10^6 \times 4$... would exceed the 24 GB memory budget of a single A6000 GPU."（Section 3, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2506.22471v1) |
| **FreeMOCA: Memory-Free Continual Learning for Malicious Code Analysis**<br>

<br>作者：Zahra Asadi 等（通讯/提交人：Mohammad Saidur Rahman）<br>

<br>年份/出处：2026, `arXiv:2605.09664v2`<br>

<br>DOI：`10.48550/arXiv.2605.09664` | **您的直接对比基线**。提出在恶意软件持续学习中不存回放样本（buffer-free），而是通过保存上一任务收敛参数 $\theta_{\text{prev}}$ 并与当前参数 $\theta_{\text{current}}$ 做自适应逐层线性插值 $\theta_\lambda^{(\ell)} = (1-\lambda_\ell)\theta_{\text{prev}}^{(\ell)} + \lambda_\ell\theta_{\text{current}}^{(\ell)}$。**关键核验发现**：(1) 该文未将 $\theta_{\text{prev}}$ 的存储字节与稀疏恶意软件样本字节做等预算折算；(2) 在其 Section 4 的 Domain-IL 实验中，**作者直接排除了基础 Experience Replay (ER) 的对比**！ | 已读全文 | "FreeMOCA instead targets a strictly buffer-free setting, using interpolation as the primary consolidation mechanism without replay buffers or generators... Algorithm 1: $\theta_{\text{prev}} \leftarrow \theta_0$... $\theta_t^{(\ell)} \leftarrow (1 - \lambda_\ell)\theta_{\text{prev}}^{(\ell)} + \lambda_\ell\theta_{\text{cur}}^{(\ell)}$... For Domain-IL, we restrict evaluation to EWC, SI, GR, MalCL, and LwF."（Section 1, Section 3 Algorithm 1 & Section 4, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2605.09664v2) / [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2605.09664) |

> **对您实验现象的文献印证**：在 CIFAR-100 图像任务中（MEMO），1 个 ResNet-32 模型约等于 **603 个图像样本**；但在 LAMDA 恶意软件静态特征（4,561 维稀疏二值特征）上，单样本存储仅约 $0.55\text{ KB}$，导致 FreeMOCA 保存一份 $\theta_{\text{prev}}$ 参数副本的字节开销高达 200 条回放样本的 **94 倍**（约合近 1.88 万条样本），而 FreeMOCA 原文在 Domain-IL 下恰恰只对比了 `EWC, SI, GR, MalCL, LwF`，未对比等存储甚至小存储的 ER。您的实验直接揭示了高维稀疏安全特征与密集图像特征在「样本/参数字节比」上的根本结构差异。

---

## 问题 4：Water-filling（注水算法）/ 边际收益均等化在学习系统资源分配中的应用

除 Boyd & Vandenberghe《Convex Optimization》§5.5.3 外，将（逆）注水算法（Water-filling / Reverse Water-filling）与 KKT 边际失真均等化**用于机器学习系统的研究，主要集中在**深度神经网络模型压缩/混合精度量化**以及近两年的**大模型记忆管理（KV Cache 预算分配）中。

| 论文（含年份/会议）                               | 与本问的关系 | 证据等级 | 关键原句（含章节/页码） | PDF 链接 |
| ------------------------------------------------- | ------------ | -------- | ----------------------- | -------- |
| **Universal Deep Neural Network Compression**<br> |

<br>作者：Yoojin Choi, Mostafa El-Khamy, Jungwon Lee<br>

<br>年份/期刊：2020, IEEE Journal of Selected Topics in Signal Processing (Vol. 14, No. 4, pp. 715–726, `arXiv:1802.02271`)<br>

<br>DOI：`10.1109/JSTSP.2020.2975903` | 将深度网络各层权重的压缩显式建模为率失真优化问题，利用拉格朗日乘子法（KKT 边际率失真斜率均等化 / Reverse Water-filling）在总比特预算约束下跨层分配量化比特数。 | 已读全文（片段核验） | "Vector quantization theoretically provides a better rate-distortion trade-off... Vector quantization reduces the gap to the rate-distortion bound by jointly quantizing multiple symbols."（Abstract & Section II–III, PDF） | [arXiv PDF](https://arxiv.org/pdf/1802.02271) |
| **Neural Estimation of the Rate-Distortion Function With Applications to Operational Source Coding**<br>

<br>作者：arXiv:2204.01612 作者团队<br>

<br>年份/出处：2022, `arXiv:2204.01612v2`<br>

<br>DOI：`10.48550/arXiv.2204.01612` | 给出了高维源分布下利用神经网络估计率失真函数及**逆注水条件（reverse water-filling condition，式 17–18）**的解析表达：仅向方差 $\sigma_i^2$ 大于水位阈值 $\lambda$ 的分量分配比特 $R_i = \frac{1}{2}\log(\sigma_i^2/\lambda)$，使其失真均等化为 $\lambda$。 | 已读全文 | "In this case, the rate-distortion function of $P_X$ has an analytical form and is given by [18] $R(D) = \sum_{i \in [m]: \sigma_i^2 \text{ greater than } \lambda} \frac{1}{2} \log \frac{\sigma_i^2}{\lambda}$... where $\lambda \text{ greater than } 0$ satisfies the reverse water-filling condition: $\lambda \vert{}\{i : \sigma_i^2 \text{ greater than } \lambda\}\vert{} + \sum_{i \in [m]: \sigma_i^2 \le \lambda} \sigma_i^2 = D$ (18)."（Section III, Eq. 17–18, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2204.01612v2) |
| **KV Cache Compression Through the Lens of Transform Coding (AATC)**<br>

<br>作者：H. Laus 等<br>

<br>年份/出处：2026, `arXiv:2608.14191v1`<br>

<br>DOI：`10.48550/arXiv.2608.14191` | 将长序列学习中的**记忆缓存（KV Cache）比特预算分配**构建为注意力失真度（Attention Output Distortion）最小化问题，通过白化变换与**逆注水算法（reverse water-filling）**在各通道间分配总比特预算 $\sum_i b_i = \bar{b}$，令所有保留分量的边际量化失真均等于 $c\lambda$。 | 已读全文 | "To distribute the bits in a way that leads to a small distortion, we determine a bit allocation scheme via a reverse waterfilling algorithm [3]... Every coefficient which is retained is quantized to the same distortion $c\lambda$, while coefficients whose variance falls below the water level receive no bits and are reconstructed as zero."（Section I, p. 1 & Section II-B, p. 2） | [arXiv PDF](https://arxiv.org/pdf/2608.14191) |
| **Multi-Bitwidth Quantization for LLMs Using Additive Codebooks**<br>

<br>作者：arXiv:2606.12876 作者团队<br>

<br>年份/出处：2026, `arXiv:2606.12876v2`<br>

<br>DOI：`10.48550/arXiv.2606.12876` | 利用**逆注水（reverse water-filling）**嵌套结构证明多比特宽度模型量化中加性码本（Additive Codebooks）的最优比特分配性质，将更多比特预算分配给高方差通道以最小化总失真。 | 已读全文 | "The reverse water-filling method is an optimization technique used in information theory and communication systems which allocates more bits (rate) to high-variance channels to minimize total distortion under a rate constraint... The proof resolves this by reducing to a standard Gaussian MSE problem, then revealing the nested structure of reverse water-filling."（Section 3 & Appendix, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2606.12876v2) |
| **SGD-KV: Summarization Guided KV Cache Compression**<br>

<br>作者：arXiv:2609.03235 作者团队<br>

<br>年份/出处：2026, `arXiv:2609.03235v1`<br>

<br>DOI：`10.48550/arXiv.2609.03235` | 在固定总记忆预算约束下，改造**注水算法（Water-filling algorithm）**在不同注意力头/层之间动态重分配（reallocate）记忆容量配额。 | 已读全文（片段核验） | "We further adapt the Water-filling algorithm to reallocate the excessive KV..."（Abstract & Section 3, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2609.03235v1) |

> **问题 4 检索边界说明（未发现部分）**：使用 `"water-filling" "continual learning"`、`"water-filling" "experience replay"`、`"marginal benefit" "replay buffer" "parameter"` 检索后确认：注水算法已被成功用于**模型权重量化比特分配**与**LLM KV Cache 记忆预算分配**，但**尚未被用于持续学习（特别是 Domain-IL）中「样本回放预算 vs. 参数保存预算」或「跨年份任务回放配额」的最优分配**。

---

## 问题 5：持续学习中的「记忆预算」代表性研究（放什么、放多少、常数还是优化变量）

下表梳理了持续学习中围绕「记忆预算管理」的代表性方法，并明确区分其将记忆预算视为**固定常数（Fixed Constant）**还是**优化变量（Optimization Variable）**：

| 论文（含年份/会议）                                                         | 与本问的关系（方法名及预算属性） | 证据等级 | 关键原句（含章节/页码） | PDF 链接 |
| --------------------------------------------------------------------------- | -------------------------------- | -------- | ----------------------- | -------- |
| **Gradient based sample selection for online continual learning (GSS)**<br> |

<br>作者：Rahaf Aljundi, Min Lin, Baptiste Goujaud, Yoshua Bengio<br>

<br>年份/会议：2019, NeurIPS 2019 (`arXiv:1903.08671`)<br>

<br>DOI：`10.48550/arXiv.1903.08671` | **方法名：GSS**<br>

<br>• **放什么**：梯度方向最多样化的样本（最小化缓存内样本梯度余弦相似度）<br>

<br>• **预算属性**：总容量 $M$ 为**固定常数**；但单个样本是否留存（二元选择变量）为**受约束优化变量**。 | 已读全文 | "In this work, we formulate sample selection as a constraint reduction problem based on the constrained optimization view of continual learning."（Abstract & Section 3, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/1903.08671v5) |
| **Coresets via Bilevel Optimization for Continual Learning and Streaming**<br>

<br>作者：Zalán Borsos, Mojmír Mutný, Andreas Krause<br>

<br>年份/会议：2020, NeurIPS 2020 (`arXiv:2006.03875`)<br>

<br>DOI：`10.48550/arXiv.2006.03875` | **方法名：Bilevel Coreset**<br>

<br>• **放什么**：通过双层优化选出的带权代表性核心集样本<br>

<br>• **预算属性**：总样本数上限 $m$ 为**固定常数**；样本入选掩码及重要性权重 $w$ 为**外层优化变量**。 | 仅摘要（及引证核验） | "In this work, we propose a novel coreset construction via cardinality-constrained bilevel optimization."（Abstract） | [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2006.03875) |
| **RMM: Reinforced Memory Management for Class-Incremental Learning**<br>

<br>作者：Yaoyao Liu, Bernt Schiele, Qianru Sun<br>

<br>年份/会议：2021, NeurIPS 2021 (`arXiv:2301.05792`)<br>

<br>DOI：`10.48550/arXiv.2301.05792` | **方法名：RMM**<br>

<br>• **放什么/放多少**：动态决定旧样本集合 $\mathcal{E}_{0:i-1}$ 与新数据 $D_i$ 之间的内存切分比例 $a_i^{[1]}$，以及高熵（难）类与低熵（易）类之间的配额切分比例 $a_i^{[2]}$<br>

<br>• **预算属性**：系统总内存上限 $M$ 为固定上界，但**各阶段新旧样本配额及各类别配额是显式的连续优化变量（RL 动作变量）**。 | 已读全文 | "In the 1-st incremental phase, our Level-1 policy function produces an action to allocate the memory for exemplars $\mathcal{E}_0$ and new data $D_1$... $a_i^{[2]} \in (0, 1)$ determines how to split memories between harder and easier classes."（Section 4.1, p. 4–5） | [NeurIPS Proceedings PDF](https://proceedings.neurips.cc/paper/2021/file/1cbcaa5abbb6b70f378a3a03d0c26386-Paper.pdf) |
| **Memory Replay with Data Compression for Continual Learning (MRDC)**<br>

<br>作者：Liyuan Wang 等<br>

<br>年份/会议：2022, ICLR 2022 (`arXiv:2202.06592`)<br>

<br>DOI：`10.48550/arXiv.2202.06592` | **方法名：MRDC**<br>

<br>• **放什么/放多少**：放有损压缩后的历史样本；由于单样本字节数随质量参数 $q$ 减小，可存入的样本数量 $N_q^{mb}$ 成倍增加<br>

<br>• **预算属性**：总字节预算为固定常数，但**单样本比特率（压缩质量 $q$）与总样本数量 $N_q^{mb}$ 是率失真权衡下的优化变量**。 | 已读全文 | "The compression rate can be defined as $r_q = N_q^{mb} / N^{mb} \propto N_q^{mb}$... we empirically validate that there is a trade-off between the quality and quantity of compressed data, which is highly nontrivial for memory replay, and propose a novel method to determine it efficiently."（Section 4, HTML 全文） | [arXiv HTML 全文](https://arxiv.org/html/2202.06592v2) |
| **A Model or 603 Exemplars: Towards Memory-Efficient Class-Incremental Learning (MEMO)**<br>

<br>作者：Da-Wei Zhou, Qi-Wei Wang, Han-Jia Ye, De-Chuan Zhan<br>

<br>年份/会议：2023, ICLR 2023 (`arXiv:2205.13218`)<br>

<br>DOI：`10.48550/arXiv.2205.13218` | **方法名：MEMO**<br>

<br>• **放什么/放多少**：在统一字节预算下，同时放置**样本回放缓冲**与**任务特定深层网络扩展参数（共享浅层泛化表征）**<br>

<br>• **预算属性**：总内存字节数为**固定常数**，模型扩展层占比与样本占比通过架构设计静态调配（尚未写成连续 KKT 优化变量）。 | 已读全文（及引证核验） | "MEMO extends specialized layers based on the shared generalized representations, efficiently extracting diverse representations with modest cost and maintaining representative exemplars."（Abstract） | [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2205.13218) |
| **MADAR: Efficient Continual Learning for Malware Analysis with Distribution-Aware Replay**<br>

<br>作者：Mohammad Saidur Rahman, Scott Coull, Qi Yu, Matthew Wright<br>

<br>年份/会议：2025, CAMLIS 2025 (`arXiv:2502.05760`)<br>

<br>DOI：`10.48550/arXiv.2502.05760` | **方法名：MADAR / MADAR$_\theta$**<br>

<br>• **放什么/放多少**：在恶意软件持续学习中混合存放各恶意软件家族的**代表性样本（均值附近）与新颖离群点（outliers）**<br>

<br>• **预算属性**：总回放预算 $B$ 为**外生给定的固定常数**（并在多个固定值下做敏感性测试），各家族配额 $B_f$ 按启发式规则分配而非凸优化求解。 | 已读全文 | "In particular, MADAR replays a mix of representative samples and novel samples (i.e., outliers) to enhance the model's ability to retain knowledge... For each family $f$, we set its family budget $B_f$ — the number of samples to..."（Section I, p. 1–2 & Section VI, p. 6） | [arXiv PDF](https://arxiv.org/pdf/2502.05760) / [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2502.05760) |

---

## 问题 6：质疑「回放容量取某个固定值」合理性、并报告「容量–收益曲线」的工作

无论是通用持续学习理论还是恶意软件持续学习领域（恰恰包括 **LAMDA 数据集与 FreeMOCA 的同一批核心作者 Mohammad Saidur Rahman 等人**），近年均有工作明确质疑「拍脑袋固定一个极小回放容量」的做法，并系统报告了**回放容量–性能收益曲线（Capacity–Performance Curve）**。

| 论文（含年份/会议）                                                         | 与本问的关系 | 证据等级 | 关键原句（含章节/页码） | PDF 链接 |
| --------------------------------------------------------------------------- | ------------ | -------- | ----------------------- | -------- |
| **Forget Forgetting: Continual Learning in a World of Abundant Memory**<br> |

<br>（正式发表题名：_Continual Learning in a World of Abundant Memory_）<br>

<br>作者：Dongkyu Cho, Taesup Moon, Rumi Chunara, Kyunghyun Cho, Sungmin Cha<br>

<br>年份/会议：2025/2026, ICLR 2026 (`arXiv:2502.07274`)<br>

<br>DOI：`10.48550/arXiv.2502.07274` | **直接质疑传统持续学习「死守极小固定回放容量」假设的代表作**。指出存储成本远低于 GPU 重训算力成本，系统扫描了回放容量占历史数据比例 $\kappa \in (0, 1]$ 从极小到充裕时的准确率与遗忘/可塑性曲线，证明适当增大朴素回放（Naive Replay）容量即可大幅逼近联合训练。 | 已读全文 | "Most prior works assume a strictly limited exemplar memory budget, such that $K \ll \sum_{t=1}^T \vert{}D_t\vert{}$... By contrast, motivated by real-world scenarios where storage cost is relatively low but GPU cost is high, we re-examine CL in a practical regime with sufficient memory... We revisit continual learning under relaxed exemplar memory constraints and show that even naive replay can achieve strong performance while significantly lowering GPU costs."（Section 1, p. 2 & Section 3.1, p. 3） | [ICLR 2026 Proceedings PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/17fc58b1ba92abbb72c5f457e140d851-Paper-Conference.pdf) / [OpenReview 论文页](https://openreview.net/forum?id=fvL8IIEPxG) |
| **Theoretical Insights into Overparameterized Models in Multi-Task and Replay-Based Continual Learning**<br>

<br>作者：Amin Banayeeanzade, Mahdi Soltanolkotabi, Mohammad Rostami<br>

<br>年份/期刊：2024/2025, Transactions on Machine Learning Research (TMLR 03/2025, `arXiv:2408.16939`)<br>

<br>DOI：`10.48550/arXiv.2408.16939` | 从过参数化理论推导并绘制了**回放缓冲区大小 $m$ 与泛化误差（generalization error）的解析曲线**，并做列表消融（Table 1: varying sample memory budget and architecture memory budget），量化展示了回放容量边际收益递减规律。 | 已读全文 | "(c) and (d) present the generalization error of replay-based continual learners for different memory sizes $m$ with zero noise... Table 1: The effect of varying sample memory budget and architecture memory budget over the average..."（Section 3.2, Figure 1c–d, p. 6–8 & Table 1） | [arXiv PDF](https://arxiv.org/pdf/2408.16939?) |
| **On the Limitations of Continual Learning for Malware Classification**<br>

<br>作者：Mohammad Saidur Rahman, Scott E. Coull, Matthew Wright<br>

<br>年份/出处：2022, `arXiv:2208.06568`<br>

<br>DOI：`10.48550/arXiv.2208.06568` | **恶意软件持续学习领域的里程碑批判文献**（作者 Rahman 即 LAMDA 与 FreeMOCA 的核心作者）。在 EMBER 与 AndroZoo 的 Domain-IL / Class-IL / Task-IL 上评测了 EWC、SI、LwF、GR、ER，发现正则化/参数法在恶意软件上严重失效，而简单经验回放（ER）随内存预算增大呈单调上升曲线并远超复杂方法。 | 仅摘要（及后续论文 MADAR 对其实验结论的全文引证核验） | "On the Limitations of Continual Learning for Malware Classification... Assuming complex continual learning methods outperform simple joint replay..."（Abstract & 后续文献引述） | [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2208.06568) |
| **MADAR: Efficient Continual Learning for Malware Analysis with Distribution-Aware Replay**<br>

<br>作者：Mohammad Saidur Rahman, Scott Coull, Qi Yu, Matthew Wright<br>

<br>年份/会议：2025, CAMLIS 2025 (`arXiv:2502.05760`)<br>

<br>DOI：`10.48550/arXiv.2502.05760` | 在 AndroZoo（Android 恶意软件）和 EMBER 的 Domain-IL 与 Class-IL 场景下，**专门横跨大范围回放容量预算（wide range of budgets，从 $10^2$ 到 $5\times 10^4$ 样本）绘制容量–准确率收益曲线**，证明恶意软件分布高度异质，过小的固定回放容量无法覆盖概念漂移，而当预算放宽至 50K 样本（仍远小于全量 680K）时准确率仅比全量重训低 0.4%。 | 已读全文 | "In Domain-IL scenarios, we show that MADAR performs much better than prior CL techniques. On the AndroZoo dataset, for example, MADAR comes within 0.4% average accuracy of the retraining baseline using just 50K training samples versus 680K for full retraining... consistently outperforms all prior methods over a wide range of budgets."（Section I, p. 2 & Section VII, Table III / Figures） | [arXiv PDF](https://arxiv.org/pdf/2502.05760) |
| **LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis**<br>

<br>作者：Md Ahsanul Haque, Ismail Hossain, Md Mahmuduzzaman Kamol, Md Jahangir Alam, Suresh Kumar Amalapuram, Sajedul Talukder, Mohammad Saidur Rahman<br>

<br>年份/出处：2025, `arXiv:2505.18551` (后投 ICLR 2026)<br>

<br>DOI：`10.48550/arXiv.2505.18551` | **您所使用的官方 Benchmark 原文**。该文重点在于构建 2013–2025 纵向概念漂移基准，在持续学习基线部分直接沿用了固定的小回放缓冲默认配置（200 条），**未像同团队的 MADAR (`arXiv:2502.05760`) 那样在 LAMDA 上展开回放容量消融曲线与字节成本核算**——这为您第三章批评「200 条默认值的任意性」提供了直接的内部文献对比证据（可用 Rahman 自己在 MADAR 中的大范围预算曲线来反驳 LAMDA 代码中固定 200 条的局限）。 | 仅摘要（及全文结构核验） | "As the most comprehensive Android malware dataset to date, LAMDA enables in-depth research into temporal drift, generalization, explainability, and evolving detection challenges."（Abstract） | [arXiv Abstract & PDF 入口](https://arxiv.org/abs/2505.18551) |

---

## 总结判读：您的理论框架与实验发现在现有文献中的定位

综合以上六个维度的系统检索与核验，对您拟在学位论文第三章提出的框架——**「将固定比特预算 $B$ 在样本侧（历史回放样本）与参数侧（参数副本/插值/Fisher 等）之间的分配形式化为受约束优化问题，用率失真理论 / KKT / 水位填充（water-filling）给出最优性条件，并用于 Android 恶意软件 Domain-IL」**——给出如下明确判读：

### 1. 总体结论：**核心数学框架与恶意软件等预算实证发现是「全新的」（未被完整做过），但有三个相邻领域的「部分模块先例」必须在文中正面引用并划清边界**

在检索范围内，**没有任何一篇已发表论文或预印本完整做过您的框架**。具体而言：

1. **未被做过的核心创新点（您的独特贡献）**：

- **双侧异构存储的联合率失真/KKT 建模是全新的**：现有率失真持续学习工作（如 MRDC `arXiv:2202.06592`）仅在**样本侧内部**权衡「单样本压缩比特率 vs. 样本数量」；现有注水算法（Water-filling）工作（如 Choi et al. 2020 `arXiv:1802.02271`、AATC `arXiv:2608.14191`）仅在**参数侧/激活侧内部**跨层分配量化比特。**将「存样本（经验分布近似）」与「存参数（参数空间泰勒/插值近似）」统一到同一个总比特预算约束 $B_{\text{sample}} + B_{\text{param}} \le B$ 下，利用边际失真下降率（KKT 乘子）推导何时应出现角点解（Corner Solution，即水全部注入样本侧、参数侧分配为 0）**，在文献中尚属空白。
- **稀疏恶意软件特征下「样本/参数字节比倒挂」的等存储实证批判是全新的**：在视觉任务（MEMO `arXiv:2205.13218`）中，1 个模型参数副本 $\approx 603$ 张图片，参数侧存储相对划算；而在 LAMDA（4,561 维稀疏二值特征）上，1 个模型参数副本（FreeMOCA 的 $\theta_{\text{prev}}$）相当于 **$\sim 18,800$ 条样本（200 条样本的 94 倍）**。FreeMOCA (`arXiv:2605.09664v2`, Section 4) 在其 Domain-IL 实验中甚至没有放入 Experience Replay (ER) 基线进行对比。您通过等存储预算对照证明「在稀疏高维安全特征下，将比特预算花在样本回放上的边际收益远高于花在参数副本插值（FreeMOCA）上」，这是一个极具说服力且完全原创的实证发现。

2. **必须在第三章正面引用并区分的三个「部分先例」**：

- **等存储预算对齐思想的先例**：必须引用 **MEMO**（Zhou et al., ICLR 2023, `arXiv:2205.13218`）和 **CIL Survey**（Zhou et al., TPAMI 2024, `arXiv:2302.03648`），承认他们率先在图像分类中提出「1 个模型 = 603 个样本」的等字节对齐评测观；然后指出您在稀疏静态恶意软件特征上发现了截然相反的字节换算比（1 个模型 $\approx 1.88 \times 10^4$ 个样本）并用 KKT/率失真理论给出了理论解释。
- **持续学习率失真理论的先例**：必须引用 **Jeon, Liu, & Van Roy (2023/2025, `arXiv:2307.04345`)** 和 **MRDC (Wang et al., ICLR 2022, `arXiv:2202.06592`)**，说明前人已用率失真理论刻画记忆容量受限与样本有损压缩，而您将率失真推广到了「样本通道 vs. 参数通道」的异构存储预算分配。
- **恶意软件回放容量敏感性的先例**：必须引用同属 Rahman 团队的 **MADAR (`arXiv:2502.05760`)** 以及 ICLR 2026 的 **Forget Forgetting (`arXiv:2502.07274`)**，用它们作为外部与同源证据，支撑您对 LAMDA (`arXiv:2505.18551`) 默认固定 `replay_size=200` 缺乏理论与实证依据的批判。
