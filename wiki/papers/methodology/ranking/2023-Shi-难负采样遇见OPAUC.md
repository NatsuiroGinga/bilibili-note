---
title: "On the Theories Behind Hard Negative Sampling for Recommendation"
authors: [Wentao Shi, Jiawei Chen, Junkang Wu, Chongming Gao, Fuli Feng, Jizhi Zhang, Xiangnan He]
year: 2023
date: 2026-09-02
journal: "Proceedings of the ACM Web Conference 2023（WWW '23），Austin, TX, USA，2023年5月1–5日；DOI 10.1145/3543507.3583223"
source_pdf: "[[raw/papers/methodology/ranking/2023-Shi-HNS-OPAUC-arXiv2302.03472.pdf]]"
sha256: "1a3a1e8b4f842bb4689cc360baeda531bf23d4019ad50b6ab96cbde72e6e7b4b"
tags:
  - 单向偏AUC
  - 难负采样
  - 分布鲁棒优化
  - 推荐系统
  - 类型/论文
key_finding: "证明 BPR 损失配合动态负采样（DNS）等价于优化单向偏 AUC（OPAUC）的精确估计量，配合 softmax 负采样等价于优化其光滑估计量；证明依据直接引用 Zhu et al. 2022（本文参考文献[41]）的 Theorem 1（CVaR-DRO 与 OPAUC 精确等价），是该定理在推荐系统场景下的一次独立复用，而非新的效率或系统层面贡献；全文未讨论训练时间、显存或反向传播工程。"
method: "把 BPR 的负采样过程改写为 DRO 目标（CVaR 散度对应 DNS，KL 散度对应 softmax 采样），套用 Zhu et al. 2022 的等价性定理证明其分别是 OPAUC(β) 的精确/近似估计量；进一步用理论分析和蒙特卡洛模拟证明 OPAUC(β) 与 Top-K 指标（Recall@K、Precision@K）的相关性强于全量 AUC，据此提出可控采样硬度的 DNS(M,N) 与 Softmax-v(ρ,N) 两个算法变体。"
baseline: "BPR、AOBPR、WARP、IRGAN、DNS、Kernel、PRIS(U)/PRIS(P)、AdaSIR(U)/AdaSIR(P)"
aliases:
  - HNS-OPAUC
  - Shi2023-HNS
  - DNS-OPAUC等价性
---

# 难负采样遇见 OPAUC：BPR + DNS 的理论刻画

> Shi, Chen, Wu, Gao, Feng, Zhang, He，2023，WWW '23（The Web Conference）· PDF 共 11 物理页（letter 尺寸，612×792 pts）

**本次核验范围**：使用 `pdf-converter`（`mineru-open-api extract`，精度模式、公式识别，全文一次转换）逐段精读第 1–8 页（摘要、第 1 节引言、第 2 节背景 2.1–2.4、第 3 节"难负采样遇见 OPAUC"、第 4 节"OPAUC 遇见 Top-K 指标"、第 5 节"HNS 的深层理解"、第 6 节实验 6.1–6.4、第 7 节相关工作、第 8 节结论）；第 8–11 页（附录 A 定理 2 证明、附录 B 定理 3 证明、附录 C 指标定义、附录 D 更宽 K 范围实验、附录 E LightGCN 补充实验、附录 F 讨论）**未逐段精读，仅确认其存在与标题**，不作为本笔记论断依据。页码位置已用 `pdftotext -f <页> -l <页> -layout` 逐页核对物理页面（本文为 letter 尺寸单栏排版但正文双栏，页眉含 "WWW '23, May 1–5, 2023, Austin, TX, USA" 字样，用于确认真实会议信息，见文献信息节）。

**任务要求的题录核验（先于内容核验完成）**：原任务简报给出的文件描述"单向 pAUC 相关工作（arXiv 2302.03472）"不含真实题名和作者。经 `pdfinfo` 与首页页脚版权声明核对，本文真实题名为 *On the Theories Behind Hard Negative Sampling for Recommendation*，作者为中国科学技术大学、浙江大学团队（Wentao Shi, Jiawei Chen*, Junkang Wu, Chongming Gao, Fuli Feng, Jizhi Zhang, Xiangnan He*，`*`为通讯作者），发表于 **WWW '23**（The Web Conference 2023，非默认推测的推荐系统专门会议），DOI `10.1145/3543507.3583223`，ACM ISBN `978-1-4503-9416-1/23/04`；代码仓库 `github.com/swt-user/WWW_2023_code`（第 6.2 节，正文给出，本次未核验仓库内容）。这不是一篇纯粹的"效率"论文，而是把推荐系统中广泛使用的难负采样（Hard Negative Sampling, HNS）工程实践，用偏 AUC 的 DRO 等价性理论化的论文。

## 一句话

本文证明贝叶斯个性化排序（BPR）损失配合动态负采样（DNS）严格等价于优化单向偏 AUC（OPAUC(β)）的精确（CVaR-DRO）估计量，配合 softmax 负采样近似等价于优化其光滑（KL-DRO）估计量，且这个等价性证明直接建立在 Zhu et al. (2022) 的 Theorem 1 之上（本文 Lemma 1 明确标注"Theorem 1 of [41]"）；在此基础上进一步证明 OPAUC(β) 与 Top-K 推荐评价指标（Recall@K、Precision@K）的相关性强于标准 AUC，从而首次给出难负采样为何有效的理论解释，并提出两个可调采样硬度的算法变体。

## 背景：问题的演进（第 1 页，引言）

- BPR（Rendle et al. 2009）是隐反馈推荐的经典损失，随机均匀采样负样本，近似优化 AUC 指标。均匀采样的负样本信息量不足、对梯度和收敛贡献小（第 1 页，引用 [28,40]）。
- 已有难负采样方法（DNS、softmax-based sampling）经验上显著优于均匀采样，通常被归因于"加速收敛"（第 1 页）。
- 本文第 1 页 Figure 1 的实证分析发现：与"计算全体负样本梯度"的 Non-Sampling 强基线（Rendle & Freudenthaler 2014）相比，两种 HNS 策略反而**显著更优**——这与"HNS 只是加速收敛到同一最优解"的通常解释矛盾，说明 HNS 的优势另有理论根源，这正是本文要回答的问题。

## 方法核心

### 3. HNS 与 OPAUC 的等价性（第 2–4 页）

- OPAUC(β) 定义（第 2 页，式 7–9）：把标准 AUC（式 6，对所有 FPR 区间积分）限制到 `[0,β]` 区间，非参数估计量（式 8）同样需要对负样本取 top-`(n_-·β)` 名。
- **DRO 框架**（第 2–3 页，2.4 节，式 12–13）：本文遵循 [41]（即 Zhu et al. 2022）定义 DRO 目标（式 13）：`min_θ (1/|C|)Σ_c (1/n_+)Σ_{i∈I_c^+} max_Q E_Q[L(c,i,j)] s.t. D_φ(Q||P_0)≤ρ`。
- **Lemma 1（第 3 页，原文明确标注"Theorem 1 of [41]"）**：取 CVaR 散度并设 `β=e^{-ρ}`，DRO 目标（式 13）等价于 OPAUC(β) 目标（式 9）。这是**直接引用**（非重新证明）Zhu et al. 2022 的核心定理，本文在此基础上继续推进到"负采样"这一层。
- **Theorem 1（第 3–4 页）**：取 `P_ns = P_ns^DNS`（DNS 采样概率，式 2）、`M = n_-·β`，则 DNS 采样下的 BPR 目标（式 1）等价于 OPAUC(β) 目标（式 9）。证明路径（第 3–4 页逐段核验）：先用强对偶性把 DRO 目标（式 13）化为式 15 的 `min_θ min_{η≥0} …`形式，指出最优 `η_i` 是损失 `L(c,i,j)` 的 `e^{-ρ}`-分位数（式 16），代入并令 `e^{-ρ}=M/n_-` 即得等价性。第 3 页 Remark：DNS 目标是 OPAUC(β) 的"精确但非光滑"（exact but non-smooth）估计量，与 Zhu et al. 2022 对 CVaR-based OPAUC 估计量的定性完全一致。
- **Theorem 2（第 4 页）**：取 `P_ns = P_ns^Softmax`、`τ = sqrt(Var_j(L(c,i,j))/(-2 log β))`，softmax 采样下的 BPR 目标是 OPAUC(β) 目标的**软（surrogate/soft）**估计量。证明思路与 Theorem 1 类似（把 CVaR 散度换成 KL 散度），但 `τ` 与 `β` 的精确关系"复杂且难以计算"，本文用泰勒展开给出近似式 17，完整推导见附录 A（本笔记未核验附录细节）。第 4 页 Remark：softmax 采样是 OPAUC(β) 的"光滑但不精确"（smooth but inexact）估计量。

### 4. OPAUC 与 Top-K 指标的关系（第 4–5 页）

- **Theorem 3（第 4 页）**：给定 `K`，Precision@K 与 Recall@K 被 `OPAUC(β)`（`β=K/N_-`）的函数上下界夹住（式 19–20，含开方与取整）。这是本文的第二个理论贡献，与 HNS-OPAUC 等价性（第 3 节）相互独立，共同支撑"HNS 之所以有效，是因为它隐式优化了与 Top-K 指标强相关的 OPAUC(β)"这一论证链条。
- 蒙特卡洛模拟（第 4–5 页，Figure 6，`N_+=200, N_-=800`，抽样 100000 次排列）验证：多数 Top-K 指标与特定 `OPAUC_norm(β)`（`β=K/N_-`）的相关系数超过 0.8，显著高于与全量 AUC（`β=1`）的相关系数（低于 0.4）。

### 5. 两个可控算法：DNS(M,N) 与 Softmax-v(ρ,N)（第 5 页，Algorithm 1/2，完整核验）

原文完整伪代码（第 5 页）：

```
Algorithm 1 DNS(M,N)
1: Initialize θ
2: for t=1,...,T do
3:   Sample a mini-batch B∈D
4:   for (c,i)∈B do
5:     Uniformly sample a mini-batch B'_c⊂I_c^-, |B'_c|=N
6:     Let p_cij = 1/M if j∈S_{B'_c}↓[1,M] else 0
7:   end for
8:   Compute gradient estimator ∇_t = (1/|B|)Σ_{(c,i)∈B}Σ_{j∈I_c^-} p_cij ∇_θ L(c,i,j)
9:   Update θ_{t+1} = θ_t − η∇_t
10: end for

Algorithm 2 Softmax-v(ρ,N)
（结构同上，第 6 步改为软权重 p_cij = e^{ℓ(r_ci−r_cj)/τ} / Σ_{k∈B'_c} e^{ℓ(r_ci−r_ck)/τ}，
 τ = sqrt(Var_j(L(c,i,j))/(2ρ))）
```

- DNS(M,N) 是原始 DNS（`M=1` 特例）的推广：先在采样池 `N` 内均匀取样，再从中挑 top-`M` 名赋均匀权重；`M` 越小、`N` 越大，负样本越"硬"（第 5 页原文归纳的三条经验规律）。
- Softmax-v(ρ,N) 用自适应温度 `τ`（式 17 的近似关系）代替固定温度，使得训练过程中 `β` 保持稳定，而非随模型置信度漂移。
- 两个算法都引入"采样池大小 `N`"这一工程超参数，用**索引采样**（第 5 节末段，"we uniformly sample a mini-batch"）实现，未讨论计算图裁剪或显存优化——这是本文与效率/系统类论文的关键差异（见下节）。

## 实验结果（第 5–7 页，Table 1–2）

- 数据集：Gowalla（822,358 训练交互）、Yelp（1,684,846）、Amazon（1,934,404），稀疏度均超 99.9%（Table 1）。
- 主结果（Table 2，NDCG@50 / Recall@50）：DNS(M,N) 与 Softmax-v(ρ,N) 显著优于全部基线（含 AdaSIR 等 2022 年方法），标注 `**` 表示 `p<0.05` 显著；原文称 DNS(M,N) 相对原始 DNS 平均提升约 40%（第 6.3 节）。
- 消融（Figure 8–10，第 6.4 节 RQ2）：`M`、`N`、`ρ` 三个超参数在不同数据集与不同 Top-K 指标下的最优取值随 K 减小而向"更硬"方向移动，与理论预测（Theorem 3 + 相关性模拟）一致。
- 实现细节（第 6.2 节）：PyTorch 实现，Matrix Factorization 骨干，batch\_size=4096；由于"效率限制"（efficiency limit，原文措辞，未展开定量数字）采样池大小固定为 200/200/500（Gowalla/Yelp/Amazon）——这是本文唯一涉及"效率"字样的位置，且仅为工程配置说明，不含任何实测运行时间或显存数字。

## 与本课题的关系

**本课题背景**：第三章机制 BER 是"多预算 CVaR-pAUC 实体排序损失"，方法学直接来源于 [[wiki/papers/methodology/ranking/2022-Zhu-SOPA偏AUC分布鲁棒优化|Zhu et al. 2022（SOPA/pAUC-DRO）]]。

- **论文原结论**：本文是 Zhu et al. 2022 Theorem 1（CVaR-DRO ↔ OPAUC 精确等价）在**推荐系统负采样**场景下的一次独立复用与扩展（叠加 Top-K 指标相关性这一新论证），不是对 Zhu 2022 方法本身的效率改进、系统实现或训练开销分析。
- **可迁移机制**：本文进一步确认了"CVaR-DRO ↔ 偏AUC 精确等价"这一定理在**跨领域**（图像/分子分类 → 推荐排序）场景下依然成立，构成对 Zhu 2022 核心定理正确性与通用性的独立交叉验证——可以作为本课题引用 Zhu 2022 Theorem 1 时的补充旁证，但不能替代对 Zhu 2022 原文证明的直接核验。
- **不可直接声称**：不得引用本文支持"CVaR-pAUC 训练高效"或"CVaR-pAUC 已有系统级实现优化"——本文全文未讨论训练时间、显存占用或反向传播工程细节，"efficiency limit" 一词仅用于说明采样池大小的工程取值理由，没有任何定量测量。也不得把本文的 DNS(M,N)/Softmax-v(ρ,N) 算法结构，与本课题 BER 的"袋内候选流展开"结构混为一谈——本文的负采样池 `N` 是从**原子候选集**（`I_c^-`，未展开的负样本编号）中采样，而本课题的实体袋展开是**复合样本**（一个实体需要跑袋大小那么多次前向）；两者在采样对象的原子性上存在根本差异，与 Zhu 2022 笔记中记录的同一差异（"原论文的样本是原子的，本课题 BER 的样本是复合的"）一致，本文没有涉及这一差异，不能作为反例或补充证据。
- **仍需实验验证的假设**：本文 Theorem 3（OPAUC 与 Top-K 指标的关系）是否对本课题"实体级排序"场景（而非"用户-物品"推荐场景）同样成立，需要独立推导——本课题的正负样本定义（正常/恶意流量）、评价指标（AUROC/pAUC 而非 Recall@K/NDCG@K）与推荐场景不同，Theorem 3 的具体不等式形式未经改写不能直接套用。

## 我的理解

这篇论文的价值在于把一个长期被当作"工程技巧"的难负采样，用偏 AUC 的 DRO 框架给出了严格的理论刻画，其证明链条的第一环（DNS ↔ OPAUC 精确等价）完全奠基在 Zhu et al. 2022 的核心定理之上——这从侧面印证了 Zhu 2022 该定理的通用性（不同任务、不同损失形式下都能套用同一套 DRO-偏AUC 等价性论证）。但也正因为如此，本文对本课题 BER 机制的方法学贡献有限：它没有引入任何新的优化算法、收敛性结果或效率改进，核心创新在于"发现 HNS 与 OPAUC 的联系"这一认识论层面，而非"如何更快/更省显存地优化 OPAUC"这一工程层面。

## 与相关工作的关系

- 本文 Lemma 1/Theorem 1 直接引用 [[wiki/papers/methodology/ranking/2022-Zhu-SOPA偏AUC分布鲁棒优化|Zhu et al. 2022（SOPA/pAUC-DRO）]]的 Theorem 1 作为证明基础，第 7.2 节相关工作段落原文明确写："[41] proposes new formulations of Partial AUC surrogate objectives using distributionally robust optimization (DRO). This work motivates our proof of the connection between OPAUC and HNS."——即本文作者自己承认这是"受 [41] 启发的证明"，而非独立提出的等价性结论。
- 本文与 [[wiki/papers/methodology/ranking/2021-Qi-SOAP直接优化AUPRC|SOAP]]、[[wiki/papers/methodology/ranking/2022-Wang-FCCO与SOX|FCCO/SOX]]所在的排序优化方法学谱系相邻但应用领域不同（推荐系统 vs 图像/分子/网络流量分类），本文未引用这两篇论文。

## 疑问 / 待验证

- 附录 A（定理 2 证明）、附录 B（定理 3 证明）本次未核验，若需要引用具体的泰勒展开近似误差或 Precision@K/Recall@K 上下界的紧致性，需回原文核实。
- 本文 Theorem 2（softmax 采样 ↔ KL-DRO ↔ OPAUC 光滑估计量）的 `τ` 与 `ρ` 关系式（式 17）是本文自行推导，还是同样直接套用 Zhu 2022 的 KL-DRO 结果，第 4 页正文表述为"proof process is similar to Theorem 1"，具体差异需要回附录 A 核实。

## 原始摘要

> Negative sampling has been heavily used to train recommender models on large-scale data, wherein sampling hard examples usually not only accelerates the convergence but also improves the model accuracy. Nevertheless, the reasons for the effectiveness of Hard Negative Sampling (HNS) have not been revealed yet. In this work, we fill the research gap by conducting thorough theoretical analyses on HNS. Firstly, we prove that employing HNS on the Bayesian Personalized Ranking (BPR) learner is equivalent to optimizing One-way Partial AUC (OPAUC). Concretely, the BPR equipped with Dynamic Negative Sampling (DNS) is an exact estimator, while with softmax-based sampling is a soft estimator. Secondly, we prove that OPAUC has a stronger connection with Top-K evaluation metrics than AUC and verify it with simulation experiments. These analyses establish the theoretical foundation of HNS in optimizing Top-K recommendation performance for the first time. On these bases, we offer two insightful guidelines for effective usage of HNS: 1) the sampling hardness should be controllable, e.g., via pre-defined hyper-parameters, to adapt to different Top-K metrics and datasets; 2) the smaller the K we emphasize in Top-K evaluation metrics, the harder the negative samples we should draw. Extensive experiments on three real-world benchmarks verify the two guidelines.

## 文献信息

- arXiv：<https://arxiv.org/abs/2302.03472>（v2，2023-02-19）
- DOI：10.1145/3543507.3583223
- 会议：The Web Conference 2023（WWW '23），Austin, TX, USA，2023-05-01 至 2023-05-05
- 代码：<https://github.com/swt-user/WWW_2023_code>（正文给出，本次未核验代码仓库内容）
