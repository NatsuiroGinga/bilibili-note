---
title: "LibAUC: A Deep Learning Library for X-Risk Optimization"
authors: [Zhuoning Yuan, Dixian Zhu, Zi-Hao Qiu, Gang Li, Xuanhui Wang, Tianbao Yang]
year: 2023
date: 2026-09-02
journal: "Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining（KDD '23），Long Beach, CA, USA，2023年8月6–10日；DOI 10.1145/3580305.3599861"
source_pdf: "[[raw/papers/methodology/training-efficiency/2023-Yuan-LibAUC-X-Risk-Optimization-KDD.pdf]]"
sha256: "aa7c6a35de950a13090740b913eff9577f8d46ea22120a748ac1818691af848a"
tags:
  - X风险优化
  - 深度学习库
  - 受控数据采样器
  - 动态小批损失
  - 类型/论文
key_finding: "LibAUC 的效率手段是工程流水线层面的两项设计——受控数据采样器（DualSampler/TriSampler，用索引采样避免拼接/追加的计算开销，控制正负样本比例）与动态小批损失（用 PyTorch/TensorFlow 自动微分实现 FCCO 类算法，对移动平均估计器派生的标量调用 .detach() 阻断多余反传路径）；全文唯一的实测效率数字是学习排序任务与 TF-Ranking 的每轮训练秒数对比（Figure 6 右），未报告分类/对比学习任务的显存或墙钟数字；全文未出现任何对反向计算图本身的结构性裁剪（无重计算/检查点/图剪枝机制），.detach() 是标准自动微分正确性技巧而非显存优化手段。"
method: "提出 X-risk（对比型复合风险函数族）统一优化框架，形式化为有限和耦合复合优化（FCCO）等三类抽象问题；库设计的两项核心工程创新是受控数据采样器（DualSampler/TriSampler，控制小批内正负样本比例并用索引法加速采样）与动态小批损失（把移动平均估计器派生的中间量定义为可求梯度的动态变量，用 .detach() 阻断不需要的反传路径，使 loss.backward() 直接产出正确的随机梯度估计）。"
baseline: "TFCO（AUPRC/AP 优化对比）、TF-Ranking（NDCG/ListMLE 优化与训练时间对比）、标准 CE/Focal Loss（CID 任务）"
aliases:
  - LibAUC
  - X-Risk优化
  - DXO
  - Yuan2023-LibAUC
---

# LibAUC：面向 X 风险优化的深度学习库

> Yuan, Zhu, Qiu, Li, Wang, Yang，2023，KDD '23 · PDF 共 13 物理页（letter 尺寸，612×792 pts，双栏排版）

**本次核验范围**：使用 `pdf-converter`（`mineru-open-api extract`，精度模式、公式识别，全文一次转换）逐段精读第 1–9 页（摘要、第 1 节引言、第 2 节 X 风险优化框架 2.1–2.4、第 3 节流水线设计 3.1–3.4、第 4 节实验 4.1–4.2 前半段含 Figure 6 训练时间对比）；第 9–13 页（4.3 对比学习实验、4.4 消融研究、第 5 节结论、参考文献）**未逐段精读，仅通过关键词检索确认其中不含额外的效率/显存论述**（检索结果见下节），不作为本笔记的实验数字来源。页码位置已用 `pdftotext -f <页> -l <页> -layout` 逐页核对物理页面，并用页眉 "KDD '23, August 6–10, 2023, Long Beach, CA, USA" 确认真实会议信息。

## 一句话

LibAUC 是围绕"X-risk"（每个样本的损失需要与大量其他样本对比才能定义的复合风险函数族，涵盖 AUROC/AUPRC/偏AUC/NDCG/对比损失等）设计的深度学习库，其效率论述集中在**工程流水线**层面——受控数据采样器（按超参数控制小批内正负样本比例、用索引法避免拼接/追加开销）与动态小批损失（用 `.detach()` 阻断移动平均估计器的多余反传路径以配合标准自动微分）——而非对反向计算图本身的结构性裁剪；全文唯一的实测效率对比是学习排序任务与 TF-Ranking 的训练时间比较，分类与对比学习任务只报告精度指标，不含显存或墙钟数字。

## 背景：问题的演进（第 1 页，引言）

- 已有深度学习平台（TensorFlow、PyTorch）与专用库（TF-Ranking、VISSL、DGL 等）基于标准经验风险最小化（ERM）与标准小批量训练范式，但 X-risk 类目标（AUROC、AUPRC、偏 AUC、NDCG、对比损失等）需要样本间相互比较，标准小批量近似会带来两个问题：**要么不收敛，要么需要非常大的小批量才能取得好效果**（第 1 页原文："existing libraries may not converge or require very large mini-batch sizes in order to attain good performance"）。
- 本文将这一现象归因于两点：(i) ERM 框架不为不可分解目标提供好的抽象；(ii) 所有已有库都基于"小批损失近似整体目标"的标准范式，而 X-risk 的每个样本损失本质上依赖对比集合，不能简单用小批近似。
- LibAUC 的定位是为"深度 X 风险优化"（Deep X-risk Optimization, DXO，Yang et al. 综述框架 [60]）提供统一 API 与工程实现，本文重点不是提出新的优化理论（第 2 节明确"We refer readers to [60] for more discussions about theoretical guarantees"），而是**库的设计原则与工程实现**。

## 方法核心

### 2. X-risk 优化框架（第 2 页，Definition 1，式 1–2）

- X-risk 抽象定义（第 2 页，Definition 1，引用 [60]）：`min_w F(w) = (1/|S|) Σ_{z_i∈S} f_i(g(w;z_i,S_i))`，其中 `g` 是内层复合函数（常见形式为对参照集合 `S_i` 的均值，式 2）。
- 绝大多数 X-risk（AUROC、AUPRC/AP、偏 AUC、NDCG、top-K NDCG、listwise CE、全局对比损失 GCL）可表述为**有限和耦合复合优化**（FCCO，式 2，第 2 页）——这是 Wang & Yang (2022, [[wiki/papers/methodology/ranking/2022-Wang-FCCO与SOX|FCCO/SOX]]) 框架的直接沿用。
- 偏 AUC（pAUC）的具体形式（第 3 页，"Partial Area Under ROC Curve"段）：FPR≤β 限制下的 pAUC 优化问题（式，第 3 页）`min_w (1/n_+)(1/k) Σ_{x_i∈S_+} Σ_{x_j∈S_-↓[1,k]} ℓ(h_w(x_j)−h_w(x_i))`，`k=⌊n_-β⌋`；为处理 top-k 选择，采用 FCCO 形式（式 3，第 3 页，明确标注"following [65]"，即 Zhu et al. 2022）：`min_w (1/n_+) Σ_{x_i∈S_+} λ log E_{x_j∈S_-} exp(ℓ(h_w(x_j)−h_w(x_i))/λ)`。**LibAUC 中偏 AUC 优化算法直接复用 Zhu et al. 2022 的 SOPAs（单向）与 SOTAs（双向）**（第 3 页原文："we have implemented SOPAs for optimizing the above objective of one-way pAUC with FPR≤β and SOTAs for optimizing a similarly formed surrogate loss of two-way pAUC … as proposed in [65]"）。

### 3. 流水线设计：两项工程创新（第 4–6 页）

流水线由五模块组成（第 4 页，Figure 2）：Dataset、Data Sampler、Model、Mini-batch Loss、Optimizer；与已有库的关键差异集中在后两个模块。

#### 3.1 动态小批损失（第 4–5 页，Algorithm 1/2）

以偏 AUC 的 SOPAs 算法为例，原文给出数学算法（Algorithm 1）与对应的 PyTorch 高层伪代码（Algorithm 2，第 5 页，逐字核验）：

```
Algorithm 1: SOPAs for solving pAUCLoss.
1  for t = 0,...,T do
2      Draw two subsets B1_t ⊂ S_+ and B2_t ⊂ S_-
3      for i ∈ B1_t do
4          u_i^{t+1} = (1-γ) u_i^t + γ g_i(w_t; x_i, B2_t)
5          p_i^t = ∇f(u_i^{t+1}) = λ/u_i^{t+1}
      ...

Algorithm 2: High-level pseudocode for SOPAs.
1 def pAUCLoss(**kwargs):  # dynamic mini-batch loss
2     sur_loss = surrogate_loss(neg_logits - pos_logits)
3     exp_loss = torch.exp(sur_loss/Lambda)
4     u[index] = (1 - gamma)*u[index] + gamma*(exp_loss.mean(1))
5     p = (exp_loss/u[index]).detach()
6     loss = torch.mean(p * sur_loss)
7     return loss
```

- 核心设计动机（第 5 页正文）：直接调用 `loss.backward()` 若不处理，会因为 `p_i` 依赖 `u_i^{t+1}`（而 `u_i^{t+1}` 又依赖 `w_t`）导致**额外的、不需要的**对 `p_i` 关于 `w_t` 的求导（"may cause extra differentiation of `p_i` in term of `w_t`"）。解决办法是对 `p`（即 `p = (exp_loss/u[index]).detach()`）调用 `.detach()`，把它从计算图中断开，返回一个不需要梯度的新张量。
- **对该实现细节的定性（回应任务第 3 点"是否包含对反向计算图本身的工程裁剪"）**：`.detach()` 是 PyTorch 自动微分的**标准正确性工具**，作用是"阻止对某条特定路径求导"，以保证动态变量 `p_i`（本质上是移动平均估计器 `u_i` 的函数，理论上应被当作"常数系数"处理，只对配对损失 `sur_loss` 求导）不会引入错误的额外梯度项——这与 Zhu et al. 2022 原论文（SOPA-s/SOTA-s 的 `p_ij` 定义）在数学上完全一致，`.detach()` 只是把该数学要求（"`p_ij` 视为已知常数，不对其求导"）在 PyTorch 自动微分层面显式实现出来。**这不是对反向计算图的结构性裁剪**（不涉及重计算/检查点式的显存-时间权衡，也不涉及图剪枝或算子融合），而是保证随机梯度估计正确性的必要操作，本身既不减少显存也不减少计算量（`exp_loss`、`sur_loss` 等中间张量仍完整保留在计算图中参与反传）。

#### 3.2 受控数据采样器（第 5–6 页，3.2 节）

- 动机（第 5 页）：DXO 需要同时估计外层均值（正样本）和内层均值（负样本），标准随机采样器不保证小批内正负样本比例可控，而理论分析（引用 [50]，FCCO 相关工作）显示平衡内外层小批量大小有利于加速收敛。
- **DualSampler**（面向 CID 分类任务）：超参数 `batch_size`、`sampling_rate`，按 `#positives = batch_size × sampling_rate` 构造小批（第 5 页代码示例）。
- **TriSampler**（面向 LTR 排序任务）：超参数 `sampled_tasks`（每步采样的查询数）、`batch_size_per_task`、`sampling_rate_per_task`，支持多标签场景下的标签采样。
- **索引法加速采样**（第 5 页原文，任务第 3 点直接相关）："To improve the sampling speed, we have implemented an **index-based approach** that eliminates the need for computationally intensive operations such as **concatenation and append**."——即用维护正/负样本索引列表 + shuffle 的方式构造小批（第 5 页 Figure 4 图示），避免了逐样本拼接（concat）/追加（append）张量这类计算密集操作。这是一项**数据加载层面**的工程优化，与反向传播/计算图无关。
- Table 1（第 6 页）汇总了库中每种损失对应的采样器与优化器：`pAUCLoss('1w')` 配 `DualSampler` + `SOPAs`；`pAUCLoss('2w')` 配 `DualSampler` + `SOTAs`（均引用 [65]，即 Zhu et al. 2022）；`NDCGLoss`/`ListwiseCELoss` 配 `TriSampler` + `SONG`（引用 [41]）；`GCLoss` 配 `RandomSampler` + `SogCLR`（引用 [63]）。

#### 3.3/3.4 优化器与其他模块（第 6 页）

- 优化器模块（3.3 节）沿用（动量）SGD 或 Adam 风格更新（第 6 页），未引入新的优化器设计，直接复用各算法原论文（[41,50,63–65,67]）给出的更新规则。
- 3.4 节给出 `Dataset.__getitem__` 返回索引（`index`）以支持移动平均估计器（`u[index]`）跨迭代持久更新的代码范式（第 6 页代码片段），与 SOPA/SOPA-s（Zhu 2022）中 `s_i`/`u_i` 跨迭代持久、仅更新当前采样分量的设计完全一致——库层面把"用索引取回上一轮状态、更新后写回"这一操作模式标准化为通用接口。

## 效率论述的性质核验（对应任务第 3 点，全文检索结果）

对提取全文（13 页、609 行 Markdown）执行大小写不敏感检索：

- `checkpoint`、`gradient checkpoint`、`backward graph`、`computation graph`、`retain_graph`、`no_grad`、`compile`、`kernel fusion`、`fused`、`sparse`、`pruning`、`recomputation`、`activation`：**全部零命中**。全文没有任何针对反向计算图本身的重计算、检查点、算子融合或图裁剪机制的讨论。
- `detach`：命中 3 处，均对应上文 Algorithm 2 及其两处代码示例中的 `p.detach()` / `(neg_logits/u).detach()`，作用是阻断移动平均估计器对模型参数的多余反传路径（见上文分析），不是显存优化手段。
- `memory`、`GPU memory`：**零命中**——全文不含任何显存占用的讨论或测量。
- `wall clock`、`wall-clock`、`throughput`、`speedup`：**零命中**。
- `training time`：命中 1 处，即第 8 页 Figure 6 图题"Comparison of training time for LibAUC and TF-Ranking"。
- `seconds`：命中 1 处（第 8 页正文）："The runtime comparison, where we report the **average runtime in seconds per epoch**, is shown in Figure 6 (right). The results show that our implementation of LibAUC on TensorFlow is even faster than three methods in TF-Ranking. It is interesting to note that LibAUC for optimizing ListwiseCE loss is **1.6× faster** than TF-Ranking for optimizing GumbelLoss yet has better performance."

**结论**：LibAUC 论文中唯一的、可引用的实测效率数字，是**学习排序（LTR）任务**下 LibAUC（TensorFlow 实现）与 TF-Ranking 库的**每轮训练秒数**对比（Figure 6 右，未给出具体秒数表格，只有柱状图与"1.6× 更快"这一相对倍数），且这一对比针对的是 SONG/K-SONG（NDCG 优化）算法而非 SOPAs/SOTAs（偏 AUC 优化）——**没有为偏 AUC 优化本身报告任何墙钟时间或显存数字**，分类任务（4.1 节，CID）与对比学习任务（4.3 节，未精读）的实验结果表格（Table 2 等）只含 AUROC/AP/pAUC 等精度指标，不含耗时或显存列。

## 实验结果（第 6–8 页，Table 2、Figure 5–6，仅记录用于交叉核对）

- CID 任务（第 6–7 页，Table 2）：CIFAR10（imratio=1%）、CheXpert（imratio 均值 24.54%）、OGB-HIV（imratio=1.76%）三个数据集上，PESG（AUCMLoss）、SOAP（APLoss）、SOPAs（pAUCLoss）均显著优于 CE/Focal 基线；例如 CheXpert 上 SOPAs 取得 AUROC `0.894±0.003`，优于 CE 的 `0.853±0.006`。
- 与 TFCO 库对比（第 7 页，Figure 5）：LibAUC（SOAP）在 CIFAR10（imratio=1%/2%）上训练/测试曲线一致优于 TFCO。
- LTR 任务（第 7–8 页，Table 未编号 + Figure 6）：MovieLens20M/25M 上，LibAUC 的 NDCGLoss 取得 NDCG@5 `0.3476±0.0001`（20M），优于 TF-Ranking 的 GumbelNDCG `0.3179±0.0003`；同时训练时间更短（1.6× 加速）——这是本文唯一"精度更好且更快"同时成立的对比。

## 与本课题的关系

**本课题背景**：第三章机制 BER 是"多预算 CVaR-pAUC 实体排序损失"，其损失公式在数学结构上与本文 3.1 节引用的 Zhu et al. 2022 偏AUC-FCCO 表述（第 3 页式 3）同源。

- **论文原结论**：LibAUC 把偏 AUC 优化（SOPAs/SOTAs，来自 [[wiki/papers/methodology/ranking/2022-Zhu-SOPA偏AUC分布鲁棒优化|Zhu et al. 2022]]）封装进标准 PyTorch/TensorFlow 训练流水线，核心工程贡献是"受控数据采样器"（控制正负比例、索引化避免拼接开销）与"动态小批损失"（`.detach()` 保证自动微分正确性），**不涉及对反向计算图的结构性裁剪**（无重计算/检查点/图剪枝/算子融合）。
- **可迁移机制**：`.detach()` 阻断移动平均估计器对模型参数的多余反传路径这一实现模式，与本课题 BER 损失中"`ξ` 作为叶张量参与同一次 `backward()` 后按其梯度更新"的实现方式属于**同一数学要求的两种不同工程实现**——LibAUC 用 `.detach()` 显式阻断（`ξ` 类变量完全不参与自动微分，由外部规则单独更新），本课题背景描述的做法是让 `ξ` 作为叶张量参与同一次反传（依赖 PyTorch 对叶张量梯度的正确计算，而非阻断）。**这两种实现是否数学等价，需要独立核实**，本笔记不作断言（该差异同时记录在 [[wiki/papers/methodology/ranking/2022-Zhu-SOPA偏AUC分布鲁棒优化|Zhu 2022 笔记]]的"仍需实验验证的假设"一节）。
- **不可直接声称**：不得引用本文支持"LibAUC 已解决大规模偏AUC训练的显存/时间问题"——本文对偏AUC优化（SOPAs/SOTAs）本身完全没有报告任何墙钟时间或显存数字，唯一的实测效率对比是 LTR 任务（NDCG 优化，非偏AUC）与 TF-Ranking 的训练时间比较。也不得把"受控数据采样器"的索引化技巧，等同于对本课题"实体袋展开成多条序列"这一显存开销结构性来源的解决方案——本文的采样器只优化"如何从原子样本池中挑出小批"的数据加载效率，不涉及"单个复合样本（袋）展开后前向/反传代价"这一维度，与 Zhu 2022 笔记中记录的"BER 样本是复合的，原论文样本是原子的"这一结构性差异同样适用于本文。
- **仍需实验验证的假设**：本课题若要复用 LibAUC 的 `DualSampler`/`SOPAs`/`SOTAs` 实现（而非自行复现 Zhu 2022 的算法），需要先核实该库对"实体袋"这种复合样本结构的支持程度——本文的采样器设计假设每个样本对应一次独立的 `Dataset.__getitem__` 调用与一次前向，未讨论"一个样本内部还需要多次前向（袋内多条流）"这种两级结构，直接套用可能需要额外适配层，这是待验证的工程问题而非已有证据。

## 我的理解

LibAUC 论文的核心信息，对本课题而言主要是**排除性**的：它明确告诉我们，Zhu et al. 2022 的 SOPA/SOPA-s/SOTA-s 系列算法在工程实现层面已经存在（这篇 KDD 论文就是其官方库文档），但该库解决的效率问题是"如何用标准自动微分正确实现移动平均估计器的随机梯度"和"如何高效采样构造正负均衡的小批"，这两个问题都发生在**样本是原子的**假设下。本课题 BER 遇到的问题——袋展开成多条序列导致单步激活 30.97 GiB、首步 OOM——属于**复合样本**带来的开销，LibAUC 论文完全没有涉及这一维度，因此不能指望通过"直接调用 LibAUC 的实现"来解决本课题的显存问题；如果需要工程层面的显存优化思路，应转向 `wiki/papers/methodology/training-efficiency/` 目录下专门处理梯度检查点、张量重计算、梯度缓存的论文（如 [[wiki/papers/methodology/training-efficiency/2021-Gao-GradCache梯度缓存两遍反传|GradCache]]），而非本文或 Zhu 2022。

## 与相关工作的关系

- 本文 3.1 节明确引用 [[wiki/papers/methodology/ranking/2022-Zhu-SOPA偏AUC分布鲁棒优化|Zhu et al. 2022]]（文中 [65]）作为偏 AUC 优化算法（SOPAs/SOTAs）的直接来源，是该论文方法的**官方工程实现**，而非独立的方法学贡献。
- 本文 2.1 节"简史"段落把 Qi et al. 2021（[[wiki/papers/methodology/ranking/2021-Qi-SOAP直接优化AUPRC|SOAP]]）列为 FCCO 框架最早应用于 AUPRC/AP 优化的工作，Wang & Yang 2022（[[wiki/papers/methodology/ranking/2022-Wang-FCCO与SOX|FCCO/SOX]]）列为"改进了算法设计与分析"的后续工作，Zhu et al. 2022（偏 AUC）与另一篇 NDCG/listwise 优化工作（[41]，SONG）列为"FCCO 技术的后续应用"，本文（X-risk 框架）是对这一整条谱系的统一封装。
- 本文与 [[wiki/papers/methodology/ranking/2023-Shi-难负采样遇见OPAUC|Shi et al. 2023（HNS-OPAUC）]]没有直接引用关系（两篇论文发表时间接近，方向不同：一个是系统/库论文，一个是推荐系统理论论文），但都建立在 Zhu et al. 2022 的偏 AUC-DRO 框架之上，构成该框架的两条独立应用/验证支线。

## 疑问 / 待验证

- 4.3 节（对比学习实验，第 9 页起）与 4.4 节（消融研究）本次未精读，若需要引用 SogCLR 相关的效率或消融数据需回原文核实。
- Figure 6 右侧的训练时间对比图本身（柱状图）本次仅读取了图题与紧邻正文段落，未核实图中具体数值（该图为图片格式，MinerU 提取文本未还原柱状图内的精确秒数），若需要精确数字需回原始 PDF 图像核验。
- 本文 3.2 节提到"根据我们的理论分析 [50]，平衡内外层小批量大小有利于加速收敛"——[50] 具体是哪篇论文（参考文献列表本次未逐条核对到 [50]），其理论分析是否量化了"加速"的具体幅度，未核实。

## 原始摘要

> This paper introduces the award-winning deep learning (DL) library called LibAUC for implementing state-of-the-art algorithms towards optimizing a family of risk functions named X-risks. X-risks refer to a family of compositional functions in which the loss function of each data point is defined in a way that contrasts the data point with a large number of others. They have broad applications in AI for solving classical and emerging problems, including but not limited to classification for imbalanced data (CID), learning to rank (LTR), and contrastive learning of representations (CLR). The motivation of developing LibAUC is to address the convergence issues of existing libraries for solving these problems. In particular, existing libraries may not converge or require very large mini-batch sizes in order to attain good performance for these problems, due to the usage of the standard mini-batch technique in the empirical risk minimization (ERM) framework. Our library is for deep X-risk optimization (DXO) that has achieved great success in solving a variety of tasks for CID, LTR and CLR. The contributions of this paper include: (1) It introduces a new mini-batch based pipeline for implementing DXO algorithms, which differs from existing DL pipeline in the design of controlled data samplers and dynamic mini-batch losses; (2) It provides extensive benchmarking experiments for ablation studies and comparison with existing libraries. The LibAUC library features scalable performance for millions of items to be contrasted, faster and better convergence than existing libraries for optimizing X-risks, seamless PyTorch deployment and versatile APIs for various loss optimization. Our library is available to the open source community at https://github.com/Optimization-AI/LibAUC, to facilitate further academic research and industrial applications.

## 文献信息

- DOI：10.1145/3580305.3599861
- 会议：29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining（KDD '23），Long Beach, CA, USA，2023-08-06 至 2023-08-10
- 开源库：<https://github.com/Optimization-AI/LibAUC>（正文给出，本次未核验代码仓库内容）
- 官网：<https://www.libauc.org>
