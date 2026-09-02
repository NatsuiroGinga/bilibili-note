---
title: "Checkmate: Breaking the Memory Wall with Optimal Tensor Rematerialization"
authors: [Paras Jain, Ajay Jain, Aniruddha Nrusimha, Amir Gholami, Pieter Abbeel, Kurt Keutzer, Ion Stoica, Joseph E. Gonzalez]
year: 2020
date: 2026-09-02
journal: "Proceedings of Machine Learning and Systems 2020 (MLSys 2020)，arXiv:1910.02653"
source_pdf: "[[raw/papers/methodology/training-efficiency/2020-Jain-Checkmate-Optimal-Tensor-Rematerialization-MLSys.pdf]]"
sha256: "8355cc2ecac072863fde2542585f8da0be30924e6181d9b05a36a63b22a1f694"
tags:
  - 训练效率
  - 激活重计算
  - 张量重物化
  - 整数线性规划
  - 显存优化
  - 类型/论文
key_finding: "把张量重物化问题形式化为 MILP（式9），对任意 DAG、非均匀显存/算力成本给出全局最优的检查点+重算调度；在 U-Net 上比最优基线快 1.2x（V100 显存预算下），MobileNet 上把最大可训练 batch size 提到 checkpoint-all 的 5.1 倍（第 8 页 6.4 节，图 6）；一个多项式时间两阶段 LP 舍入近似算法在全部测试架构上与 MILP 最优解的比值不超过 1.06（第 8 页 Table 2）。"
method: "把每个算子在每个执行阶段是否重算（R）、是否作为检查点保留（S）表示为 0/1 决策变量，配合内存记账变量 U 与释放指示变量 FREE，构造带内存预算约束的整数线性规划（式9），用 Gurobi/COIN-OR 等现成求解器求解；求解太慢时用 LP 松弛+两阶段确定性舍入得到近优解。"
baseline: "Checkpoint all（默认全存不重算）、Griewank & Walther (2000) log n 方案、Chen et al. (2016b) sqrt(n)/greedy 启发式及其对非线性图的自定义推广（AP变体、Linearized变体）"
aliases:
  - Checkmate
  - 张量重物化 MILP
  - Jain2020-Checkmate
related:
  - "[[2021-Kirisame-动态张量重物化]]"
  - "[[2022-Korthikanti-大规模Transformer激活重计算优化]]"
---

# Checkmate：用最优张量重物化打破显存墙

> P. Jain, A. Jain, Nrusimha, Gholami, Abbeel, Keutzer, Stoica, Gonzalez，2020，MLSys 2020 · arXiv:1910.02653 · 15 页（正文 1–7 节 + 附录 A–D）

**本次核验范围**：全文 15/15 页完整核验，含正文第 1–7 节与附录 A（整数性差距分析）、B（基线泛化到非线性图的构造方法）、C（重物化问题的 NP 完全性归约）、D（近似算法与随机/确定性舍入的对比图）。未发现无法定位的章节。

## 一句话

Checkmate 把"训练一次迭代时，哪些中间激活要保留、哪些要在反向传播时重算"这一调度问题精确形式化为一个整数线性规划（式9），支持任意 DAG 结构（不要求线性图）、非均匀的每层显存/算力成本，用现成求解器求全局最优解；在真实网络上，最优重物化调度让 U-Net 在 V100 16GB 预算下比此前最好的启发式快 1.2 倍，MobileNet 可训练的最大 batch size 提升到不做任何重算方案的 5.1 倍（第 7–8 页 6.3、6.4 节）。

## 背景：问题的演进

训练大网络时显存主要被中间激活占用而非参数（第 2 节，图 3）；标准做法是全部保留激活直到反向用完再释放，显存不够时用"检查点+重算"（rematerialization/checkpointing）：前向时主动丢弃部分激活，反向需要时再重算。此前的经典方法（Griewank & Walther 2000 的 Treeverse、Chen et al. 2016b 的 $\sqrt n$/greedy 方案）都假设计算图是**线性图**（每层只依赖前一层）且**每个节点代价相同**（第 3 节 Related Work）。这两个假设在现代网络上都不成立：残差连接、U-Net 式长跳连让图非线性；VGG19 中最大层比最小层贵六个数量级（第 2 节末段）。把非线性图强行按 articulation point 或拓扑序线性化再套用旧算法（本文的 AP/Linearized 泛化，Table 1）是可行的权宜之计，但不是针对真实图结构与真实成本的最优解。

## 方法核心

- 问题定义（第 4.1 节）：计算图 $G=(V,E)$ 是 DAG，节点按拓扑序编号；每个算子输出占用 $M_v$ 显存、计算耗时 $C_v$。目标是找到调度使终止节点 $v_n$ 在显存预算 $M_{\mathrm{budget}}$ 下以最小总计算代价完成。
- 调度表示（第 4.2 节）：把执行展开为 $T=n$ 个阶段，$S_{t,i}\in\{0,1\}$ 表示算子 $i$ 的结果是否从阶段 $t-1$ 保留到阶段 $t$（检查点），$R_{t,i}\in\{0,1\}$ 表示算子 $i$ 是否在阶段 $t$ 被（重）计算。
- 无显存约束的基础目标（式1a–1f）：最小化 $\sum_t\sum_i C_iR_{t,i}$，约束保证依赖关系（式1b/1c）与首末阶段的边界条件（式1d/1e）。
- 显存记账（第 4.4 节，式2–5）：引入内存变量 $U_{t,k}$（阶段 $t$ 算完节点 $k$ 后的显存占用）与释放指示 $\mathrm{FREE}_{t,i,k}$，通过递推（式2、3）刻画显存随执行推进的变化；Theorem 4.1 证明该定义下同一张量不会被重复释放。
- 线性化多项式约束（第 4.5 节，Lemma 4.1、4.2）：式5 中 FREE 的定义本是多个 0/1 变量的乘积（多项式），作者用两条引理把它等价改写为一组线性不等式（式7a–7c），使整个问题保持为 ILP 而非非线性整数规划。
- "frontier-advancing" 分阶段技巧（第 4.6 节）：固定执行顺序为拓扑序，让节点 $i$ 恰好在阶段 $i$ 首次计算，替换掉原始的松散约束（式8a–8c）。作者报告一个 8 层线性网络例子：不分阶段时 Gurobi 需 9.4 小时求解，分阶段后仅需 0.23 秒（第 5 页第 4.6 节末段），并在附录 A 用整数性差距（integrality gap，从 21.56 降到 1.18）解释为何分阶段能极大加速分支定界。
- 完整 MILP（式9，第 5 页 4.7 节）：$O(|V||E|)$ 个变量与约束；4.8 节进一步剔除已知在最优解中恒为 0 的 $|V|^2$ 个 $\mathrm{FREE}_{t,k,k}$ 变量以精简问题规模。
- 生成执行计划（第 4.9 节，Algorithm 1）：对可行解 $(R,S,U,\mathrm{FREE})$ 做行优先扫描，生成一串"计算/释放"语句，可编译为静态计算图执行。
- 近似算法（第 5 节）：直接对 ILP 的 LP 松弛做随机或确定性舍入均不可行——作者报告对 VGG16 在 4 倍缩小的显存预算下，50000 次随机舍入采样**没有找到一个可行解**（第 5.1 节末段）。作者提出两阶段舍入（Algorithm 2）：先确定性舍入检查点矩阵 $S^*$，再用最少的额外重算把违反的依赖约束逐一修正得到可行的 $R^{\mathrm{int}}$；再留 $\epsilon=0.1$ 的显存余量应对舍入带来的预算违反风险（第 5.3 节）。

## 实验结果

- 内存-算力权衡（第 7 页 6.3 节，图 5）：VGG16、MobileNet、U-Net 上，Checkmate 产生的调度在所有测试预算下计算开销均低于 Chen et al. (2016b) 与 Griewank & Walther (2000) 及其非线性图泛化；在 U-Net 上，V100 显存预算下比次优基线（linearized greedy）快 1.2 倍，比 linearized $\sqrt n$ 快 1.38 倍；可以用低于 10% 的额外开销训练 batch size 32 的 U-Net（原本无重算需要 23GB 显存）。
- 最大可训练 batch size（第 8 页 6.4 节，图 6，Table 2 上方正文）：在限制总代价不超过"多做一次前向"的约束下（式10），Checkmate 使 U-Net 在高分辨率下理论最大 batch size 达到 61（相比常规上限 16，提升 3.8x）；MobileNet 上达到 1105，是不做重算方案（checkpoint all）的 5.1 倍，是最好启发式基线（greedy）的 1.73 倍。
- 近似算法质量（第 8 页 6.5 节，Table 2）：以 $\mathrm{COST_{approx}}/\mathrm{COST_{opt}}$（几何平均，跨多个显存预算）衡量，两阶段确定性舍入在 MobileNet/VGG16/VGG19/U-Net/ResNet50 五种架构上的比值分别为 1.06/1.01/1.00/1.03/1.05，均优于三种基线泛化算法（AP $\sqrt n$、AP greedy、Griewank log n，其中 Griewank log n 在 MobileNet 上达到 7.07x）。
- ILP 求解耗时（第 7 页第 5 节）：多数问题在数秒到一小时内求解完成（本文全部 ILP 结果限时 1 小时，≥24 核机器）；相对训练总时长（如 BERT 21 天）求解 ILP 的开销"less than a percent"；但 DenseNet161 这类数百层网络"no feasible solution was found within one day"，说明 ILP 精确求解在层数极多时不可扩展，这是近似算法存在的直接动机。
- 硬件感知的可行性上限（附录 C，NP 完全性归约）：证明无重算开销的重物化决策问题（RP-DEC）是 NP-完全的（归约自 Sethi 1973 的寄存器分配问题），但作者引用 Goodwin & Wilken (1996) 的观察——受限于给定指令调度顺序的 0-1 整数规划在实践中经验复杂度约为 $O(n^{2.5})$，呼应本文"frontier-advancing 分阶段"在实践中的可扩展性。

## 我的理解

Checkmate 的核心贡献不是"重物化"这个想法本身（Chen et al. 2016b 早已提出），而是把它从"手工设计的线性图启发式"升级为"一般 DAG 上可精确求解的组合优化问题"。关键工程技巧是"frontier-advancing 分阶段"：不是让求解器同时搜索执行顺序和检查点选择，而是先固定执行顺序为拓扑序，只让求解器决定"每个阶段保留/重算哪些张量"，这把一个原本因决策变量耦合过深而几乎不可解的 ILP（9.4 小时）压缩到瞬间可解（0.23 秒），代价是牺牲了对执行顺序本身的搜索自由度。这是一个"缩小搜索空间换取可解性，同时用整数性差距分析证明缩小后的问题仍逼近最优"的典型系统论文范式。

## 与本课题（BER 训练效率／第四章候选）的关系

### 论文原结论
- Checkmate 求解的是"给定计算图与显存预算，哪些张量保留、哪些重算"的**全局最优**离线调度（MILP 精确解或近优的 LP 舍入解），依赖已知的、静态的前向/反向计算图与可预测的每层显存/算力成本（第 4.10 节：成本通过对目标硬件做逐层 profile 得到）。
- 这是一个**离线规划**方法：求解 MILP 本身需要提前拿到完整计算图并离线求解（第 7 节报告求解耗时数秒到一小时），不是训练过程中的在线决策。

### 本课题推论（原文未给出，本课题基于原文外推）
- Checkmate 的调度粒度是"算子/张量级别的保留-重算决策"，这与本课题候选四 SAC（选择性激活重计算，保留 k 个微批不重算、其余重算）**不是同一粒度**：Checkmate 在单次前向/反向内部对每个算子做决策，SAC 是在微批粒度上做决策（整微批保留或整微批重算）。若要把 Checkmate 的 MILP 框架直接套用于 SAC 的微批级决策，需要把"微批"当作 Checkmate 中的一个粗粒度节点重新建模，这是本课题需要独立验证的适配工作，原文未涉及微批粒度调度。
- BER 排序头当前用 `torch.utils.checkpoint.checkpoint(use_reentrant=False)` 做的是最朴素的"整段区间重算"（相当于本文 Table 1 中的 Checkpoint all 之外、粒度更粗的手工分段），与 Checkmate 的逐算子最优调度之间存在明显的优化空间差距——这是本课题基于两文对照后的推论，需要用 BER 实际排序头的计算图重新跑一次 Checkmate 式的 MILP 或近似算法才能验证收益，原文未针对 CVaR-pAUC 排序损失做过实验。

### 可迁移机制
- MILP 形式化本身（式1–9）是通用的，只要能拿到计算图结构与逐算子的显存/耗时 profile，理论上可以直接应用于任意 PyTorch 计算图（包括 BER 排序头），这是论文明确声称的通用性（第 1 节贡献列表："a formalization... with a substantially more flexible search space than prior work"）。
- 两阶段 LP 舍入近似算法（Algorithm 2）在 ILP 精确求解不可扩展时（如层数极多）提供了一个有理论近似比保证（本文实测 ≤1.06）的替代方案，这一"精确解不可行时退化为近似但仍可控"的设计模式可迁移到本课题需要频繁重新求解调度的场景。

### 不可直接声称的内容
- 不能声称 Checkmate 的 5.1x batch size 提升或 1.2x 速度提升可直接迁移到 BER 排序头——原文全部实验针对图像分类/分割 CNN（VGG16/19、ResNet50、MobileNet、U-Net、FCN、SegNet），未覆盖 Transformer 或排序损失场景，提升幅度高度依赖具体网络的显存/算力比例结构（如 VGG19 层间代价差六个数量级这一特性）。
- 不能声称该方法是在线/训练时动态调整的方案——它是离线规划工具，训练前求解好调度后生成静态图执行（第 4.9 节），与候选四 SAC 若需要在训练过程中动态调整"保留几个微批"存在方法论上的差异，需要额外的在线化改造。

### 仍需实验验证的假设
- 用 Checkmate 的 MILP 框架对 BER 排序头的实际计算图（含 CVaR-pAUC 损失的自定义算子）重新建模求解，能否获得优于当前手工 `torch.utils.checkpoint` 方案的显存-速度权衡——待验证，且需要先确认 BER 排序头的计算图是否满足 Checkmate 假设的"确定性、可 profile 成本"的前提。

## 与相关工作的关系

本文与 Griewank & Walther (2000)、Chen et al. (2016b) 构成直接对照（前两者是本文改进的对象，Table 1 系统列出各方法在"支持通用图/是否成本感知/是否显存感知"三维上的差异）；[[2021-Kirisame-动态张量重物化]]（DTR）是本文之后的工作，把"离线 MILP 精确解"替换为"在线贪心启发式"，二者在 DTR 论文的图 3 中直接对比（详见该篇笔记）。与 [[2022-Korthikanti-大规模Transformer激活重计算优化]] 的关系是互补而非竞争：Checkmate 解决"哪些张量该重算"的通用调度问题，NVIDIA 论文解决"Transformer 特定结构下如何减少需要重算的激活总量"（序列并行）与"哪类激活最值得选择性重算"（selective activation recomputation），后者可以作为 Checkmate 类调度器的输入侧优化。

## 疑问 / 待验证

- 附录 C 证明的 NP 完全性针对无重算开销的判定版本 RP-DEC，与本文实际求解的最小化重算代价版本之间的复杂度关系，原文未给出精确的复杂度等价证明，只引用了经验复杂度观察（Goodwin & Wilken 1996）。
- 论文承认对 DenseNet161（数百层）ILP 无法在一天内求解出可行解（第 7 页第 5 节），但未报告此时近似算法的具体表现数字，只笼统说明近似算法是为此类场景准备的。

## 原始摘要

> We formalize the problem of trading-off DNN training time and memory requirements as the tensor rematerialization optimization problem, a generalization of prior checkpointing strategies. We introduce Checkmate, a system that solves for optimal rematerialization schedules in reasonable times (under an hour) using off-the-shelf MILP solvers or near-optimal schedules with an approximation algorithm, then uses these schedules to accelerate millions of training iterations. Our method scales to complex, realistic architectures and is hardware-aware through the use of accelerator-specific, profile-based cost models. In addition to reducing training cost, Checkmate enables real-world networks to be trained with up to 5.1× larger input sizes.

## 文献信息

- MLSys 2020；arXiv:1910.02653
- 原件：`raw/papers/methodology/training-efficiency/2020-Jain-Checkmate-Optimal-Tensor-Rematerialization-MLSys.pdf`
- 代码：https://github.com/parasj/checkmate（第 1 页摘要末尾）
