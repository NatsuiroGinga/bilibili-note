---
title: "Curriculum Learning as Transport: Understanding Curricula with Wasserstein Geodesics"
authors:
  - Changho Shin
  - David Alvarez-Melis
year: 2026
date: 2026-10-13
journal: "COLM 2026（Conference on Language Modeling，页眉 `Published as a conference paper at COLM 2026`）；arXiv:2609.09099"
source_pdf: "[[raw/papers/attack-detection/2026-Shin-课程学习作为传输.pdf]]"
tags:
  - 课程学习
  - 最优传输
  - Wasserstein
  - 训练分布路径
  - 节奏
  - 类型/论文
aliases:
  - Curriculum as Transport
  - Shin2026-Wasserstein课程
  - Wasserstein课程路径
key_finding: 把课程学习表示为「难度层上的训练分布轨迹」，用 Wasserstein 测地线做受控解耦，在 12 任务 33 难度轴的合成套件上分离「排序／等曝光／端点平滑度／节奏」四因素——结论是 easy-to-hard 排序在等曝光对照下仍有增益（不只是累积曝光），而节奏与端点平滑度决定增益落在难度谱的哪一段；但在预训练模型的真实数据 SFT 上，这些效应大幅减弱。
method: Wasserstein 课程路径（训练分布 P_k ∈ Δ^{L−1} 的插值 P_t = argmin_Q (1−t)W(Q,P_0)+tW(Q,P_1)）；端点族 (P_1)_l ∝ exp(l/τ)、(P_0)_l=(P_1)_{L−l+1}；遍历节奏 t_k=(k/T)^γ；12 任务 33 难度轴的校准合成套件 + 真实数据 SFT（ARC/MMLU-STEM/StrategyQA，LoRA）
baseline: 静态 i.i.d. 采样、线性插值课程、hard-to-easy（反向）课程、等曝光静态匹配（exposure-matched static）、WARP（学习式自适应几何）
---

# Curriculum Learning as Transport: Understanding Curricula with Wasserstein Geodesics

> Changho Shin（Princeton University）, David Alvarez-Melis（Microsoft Research & Harvard University） · COLM 2026 · 约 9 页正文 + 附录（含 App. B–D）

> 原件状态：本笔记基于 **Zotero 中该条的 PDF 附件**（自 arXiv:2609.09099 自动抓取）全文提取撰写（条目 key `I3L65FTP`）。**`raw/papers/attack-detection/` 下的同名 PDF 副本已于 2026-10-13 由主代理补齐**（1.6 MB，`file` 核验为 `PDF document, version 1.7`），`source_pdf` 链接**现已有效**。原始阻塞记录见 `.Codex/docs/2026-10-13-编辑距离证书文献核查/notes.md`（历史）。引文按节号/式号/表号/图号锚定。

## 一句话

课程学习同时有多个耦合的设计选择（难度怎么定义、easy→hard 还是 hard→easy、每层曝光多少、多快跨层），难以归因；本文把**课程 = 难度层上「训练分布随时间演化的轨迹」**，用 **Wasserstein 测地线插值**做统一受控框架，在合成套件上把「排序／等曝光／端点平滑度／节奏」四项解耦；核心结论：**在等曝光对照下 easy-to-hard 排序仍有增益（说明增益不只来自累积曝光），但节奏与端点平滑度决定了增益落在难度谱的哪一段——且这些效应在预训练模型的真实数据 SFT 上明显减弱。**

## 背景：问题的演进

- 课程学习的经典动机是「先易后难」，但课程是否有效常**归因不清**：增益到底来自①排序本身、②更多地看简单样本（累积曝光）、③层级间更平滑的过渡、还是④固定预算的更好节奏？（§1）
- 既有课程方法（self-paced、teacher-student、bandit、competence-based pacing）**通常一次改动多个设计选择**，无法分离贡献（§1、§2）。近期工作开始直接问「何时排序有帮助」，但未在单一受控参数化下同时分离排序、曝光、端点选择、节奏与几何。
- 本文的定位是**「不设计新课程，而是分离哪一组件驱动观测增益」**的分析框架（§2 末）。

## 方法核心

### 1. Wasserstein–Geodesic 课程（§3.1）

- 对每个任务，把训练数据分成 **L 个有序难度层**。在第 `k` 个训练步，每个 batch 从概率向量 `P_k ∈ Δ^{L−1}` 采样，`P_{lk}` 表示从第 `l` 层抽样的概率。**一个课程 = 难度层上的一串采样分布 `{P_k}`。**
- **Wasserstein 测地线插值**定义这条路径：
  $$P_t = \arg\min_{Q \in \Delta^{L-1}} \big\{(1-t)\,W(Q, P_0) + t\,W(Q, P_1)\big\}$$
  即沿「easy-heavy 起点 `P_0`」到「hard-heavy 终点 `P_1`」之间平滑搬运概率质量（McCann 1997；Peyré & Cuturi 2019；Villani 2008）。与**线性插值**（直接混合两端分布、把质量堆在边界层）不同，Wasserstein 插值**把更多质量放在中间层**（Fig. 1）。
- **端点族与遍历节奏（关键参数）**：
  $$(P_1)_l \propto \exp(l/\tau), \qquad (P_0)_l = (P_1)_{L-l+1}, \qquad t_k = (k/T)^{\gamma}$$
  其中 `l` 为难度层下标、`L` 为层数、`k` 为训练步、`T` 为总步数。
  - **`τ` 控制端点平滑度**：`τ` 越小端点越「尖锐」（质量集中于最易/最难层），`τ` 越大端点越「平滑」。
  - **`γ`（traversal exponent）控制节奏**：训练沿同一路径移动的快慢。
  - **默认**：`τ = 1`、`t_k = k/T`（即 `γ = 1`）。
- 框架支持扩展：学习式节奏（geometry）与**多维/结构化难度空间**（§8，超出单一一维排序）。

### 2. 实验设置（§3.2）

- **校准合成套件**：**12 个任务、33 个难度轴**，用于主研究（可控比较）。
- **训练预算**：不固定单一全局步数，而是按各 benchmark 的**静态 i.i.d. 学习曲线**分别校准 **small / medium / large** 三档（§3.2）。
- **真实数据 SFT 对照**（Appendix D）：ARC、MMLU-STEM、StrategyQA 上做 **LoRA SFT**，基模型为 SmolLM3-3B-Base、OLMo-2-0425-1B、Qwen3-1.7B-Base。

## 主要发现（§1 三条 + §4–§6）

### 发现 1：课程效应高度**依情境而定**（§4.1）

- 合成套件上**没有任何单一课程在所有任务/难度轴/预算上占优**；课程的主要作用是**改变「固定预算花在哪里最有效」**，而非普遍提升。

### 发现 2：**排序的作用超出累积曝光**（§4.2–4.3）

- **easy-to-hard 相对「等曝光静态匹配」基线**，在**困难层**上有更好的表现；而 **hard-to-easy 排序常常有害** ⇒ 「时机」本身重要，不只是累积曝光。
- 量化：**困难桶上，Wasserstein 的「曝光校正准确率」在全部 99 个 task×axis×budget 条件下都高于线性插值**；**最难层上 forward Wasserstein 在 99 个条件中有 92 个优于 reverse Wasserstein**（reverse 多拿的易层收益不足以抵消 Wasserstein 更大的难层收益）。
- 主表（合成套件，三档预算；列 = 平均总准确率 / 平均最难层准确率 / 总胜出数 / 最难层胜出数）：

  | 预算 | 方法 | 平均总(%) | 平均最难(%) | 总胜出 | 最难胜出 |
  | --- | --- | ---: | ---: | ---: | ---: |
  | Small | 静态 i.i.d. | 56.6 | 39.9 | 13 | 6 |
  | Small | 线性 | 55.4 | 46.4 | 7 | 12 |
  | Small | Wasserstein | 56.6 | 46.3 | 13 | 15 |
  | Medium | 静态 i.i.d. | 79.2 | 66.1 | 11 | 5 |
  | Medium | 线性 | 78.8 | 72.6 | 10 | 16 |
  | Medium | Wasserstein | 79.7 | 72.1 | 12 | 12 |
  | Large | 静态 i.i.d. | 92.7 | 86.0 | 6 | 1 |
  | Large | 线性 | 92.9 | 89.6 | 12 | — |

  （读法：**平均总准确率**上课程与静态 i.i.d. 相差很小（≤约 1 点），差距集中在**最难层**；这正是「课程把预算重新分配到难端」的证据。）

### 发现 3：**节奏与端点设计重要**（§5）

- 在**同一** easy-to-hard Wasserstein 路径上只变「端点平滑度 `τ`」与「遍历速度 `γ`」，做 **9×9 网格扫描**：`τ, γ ∈ {0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 5.0, 10.0}`，仅 medium 预算，每条件 3 个种子（共 20 个 task×difficulty-axis 条件）。
- **结果**（Fig. 4c）：**存在一个「宽广的良好区域」而非单一最优点**——**中等节奏 + 较平滑端点**表现好；**端点极尖锐**时，无论节奏**过于激进**还是**过于保守**都会**崩溃**。默认设置 `τ=1, γ=1` 已落在良好区域内。
- 与**学习式自适应几何**（WARP）对照：Wasserstein 56.8/79.8/92.9 vs WARP 57.1/80.6/92.9，增益 +0.2/+0.9/+0.0 ⇒ 学习式节奏**可小幅超过**固定 Wasserstein 路径，但幅度很小。

### 发现 4（重要边界）：**预训练 SFT 上效应大幅减弱**（Appendix D）

- 合成套件之所以用，是因为它能做受控比较；**在真实数据、预训练模型的 SFT 上，课程效应弱得多、更难分辨**。
- 原文明言：预训练 SFT 下**多数课程效应减弱，静态 i.i.d. 反而成为最强的汇总基线，各桶准确率趋平，easy-to-hard 排序不再稳定地分离**；**唯一最清晰的残余差异在「曝光校正的数据效率」**。

## 我的理解

- 本文**没有定理**（全文无 Theorem/Proposition 类结果，检索零命中）——它是一个**受控实证/分析框架**，而非理论论文。所有「排序有效／节奏重要」的结论都来自**校准合成套件**上的实验，不是可移植的证明。
- 「课程 = 分布轨迹」与 OT 视角的价值在于：把「难度」固定成一个**坐标轴**后，排序（沿轴的**方向**）、曝光（质量在轴上的**边际**）、节奏（沿路径的**速度** `γ`）与端点（**边界**形状 `τ`）成了**正交可调旋钮**，因此能回答「哪一旋钮在起作用」。
- 迁移到本课题时最大的警示来自 Appendix D：**在带预训练模型、难度标签更噪的真实数据上，排序增益会明显缩小甚至消失**——本课题的源期训练恰好属于这一类更现实、更「不友好」的设定。

## 与相关工作的关系

- OT × 课程：RL 领域已有用 OT 构造/排序任务的工作；本文的差别是**把 OT 用作「在固定难度轴上分析分布」的框架**，以分离 ordering/exposure/pacing/endpoint（§2）。
- 与本课题内**[[课程式学习-全文|Shi & Liu, AAAI-24]]** 的区别（引文纪律，见该笔记末尾登记）：Shi & Liu 是**对抗训练**的在线视角泛化界，用 Wasserstein 距离界**相邻迭代对抗分布**的漂移；本文是**课程学习/训练分布路径**的运输几何框架。**两者不得混为一谈**——需要「运输几何／课程路径 `{P_t}`／Wasserstein 测地线」表述时须引 **Shin & Alvarez-Melis（本篇）**；需要「在线视角泛化界／相邻迭代漂移」时引 Shi & Liu。
- 本课题内相关：**[[dga/2019-Balaji-逐样本半径对抗训练|Balaji 2019 逐样本半径对抗训练]]**（逐样本 `ε_i` 的调度来源，图像域）。

## 疑问 / 待验证

- 本文的「难度层」是**预先给定的有序轴**，不是本课题的「编辑预算 `q`」。把它当课程时，**难度轴的定义**（每一层如何对应一个 `q`）是迁移前必须先固定的接口。
- §5 的「节奏 `γ`」给的是**连续遍历速率的幂律参数化**，而本课题 D-7 方案是 **epoch 级离散三档（epoch1 弱、epoch2–3 强）**——两者粒度不同。本文的结论（中等节奏 + 平滑端点、避免极端 `γ`/`τ`）是否对本课题这种**极粗粒度（仅 3 个 epoch）**的调度有任何可操作含义，需要评估报告单独判断。
- 本文附录 D 的负面结果（预训练 SFT 上效应减弱）对本课题 D-7 的判据有直接影响——见 `thesis/methods/第三章-编辑距离证书与课程理论评估.md`。

## 原始摘要

> Curriculum learning is governed by several coupled design choices—how difficulty is defined, how examples are ordered, how much exposure each level receives, and how quickly training moves across levels—making it hard to isolate what actually helps. We present Wasserstein curriculum paths, a simple transport-based framework that decouples these factors by representing curricula as trajectories of training distributions over discrete difficulty levels. Across a calibrated synthetic suite with 12 tasks and 33 difficulty axes, we use this framework to isolate the effects of ordering, matched exposure, endpoint smoothness, and pacing under fixed training budgets. We find that curriculum effects are strongly context-dependent: no single strategy dominates across tasks, difficulty axes, and budgets, and curricula mainly change where a fixed budget is spent most effectively. Within this framework, easy-to-hard ordering improves hard-level performance relative to exposure-matched static sampling, showing that the benefit is not explained by cumulative exposure alone. We further show that endpoint smoothness and pacing substantially affect where along the difficulty spectrum a curriculum is effective. Finally, we show that the same transport view naturally supports extensions to learned pacing through geometry and to structured difficulty spaces beyond one-dimensional orderings.

## 文献信息

- arXiv：`2609.09099`；会议：COLM 2026。
- OpenReview：<https://openreview.net/pdf?id=vksN9ocqqh>
- Zotero 条目：key `I3L65FTP`（类型 preprint，含 PDF 附件）。
- 说明：本条为此前仅见于 `.Codex/docs/chatgpt-handoffs/` 的运输几何框架来源，**本次首次完成 `raw/`+`wiki/` 入库**（raw 副本待补，见顶部「原件状态」）。
