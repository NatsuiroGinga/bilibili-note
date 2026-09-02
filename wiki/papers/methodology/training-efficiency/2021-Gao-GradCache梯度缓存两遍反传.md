---
title: "Scaling Deep Contrastive Learning Batch Size under Memory Limited Setup"
authors: [Luyu Gao, Yunyi Zhang, Jiawei Han, Jamie Callan]
year: 2021
date: 2026-09-02
journal: "Proceedings of the 6th Workshop on Representation Learning for NLP (RepL4NLP 2021, ACL-IJCNLP); arXiv:2101.06983"
source_pdf: "[[raw/papers/methodology/training-efficiency/2021-Gao-GradCache-Scaling-Deep-Contrastive-Learning-Batch.pdf]]"
sha256: "83bb9569305ff9b9c0884cb1c535da764255c7e5d3cade3c0611d8f02511e6bf"
tags:
  - 梯度缓存
  - 对比学习
  - 显存优化
  - 两遍反传
  - 类型/论文
key_finding: "GradCache 把对比损失反传拆成两步：第一步无图前向算出全部表示并对损失反传得到表示梯度缓存，第二步逐子批重建计算图并用缓存梯度做种子反传；论文在 §3.3 用两重求和合并（式 8/9）论证其为大批量梯度的精确算术等价，声称产生 “exact same gradient update”，但全文未出现 bitwise/precision/round 等词，没有任何浮点逐位一致性的讨论；实测代价为约 20% 运行时间增加，且论文自身实测梯度检查点路线只能撑到批量 64、耗时是梯度累积的两倍。"
method: "两遍反传（graph-less forward 缓存表示 → 对表示求梯度存入 Representation Gradient Cache → 逐子批重建图并用缓存梯度做 backward 种子累积）"
baseline: "Sequential（单卡最大批量）、Accumulation（梯度累积）、梯度检查点（作者自评，未进入正式对比表）"
aliases:
  - GradCache
  - Gao2021-GradCache
  - 梯度缓存
---

# GradCache：梯度缓存与两遍反传

> Gao, Zhang, Han, Callan，2021，RepL4NLP 2021（arXiv:2101.06983）· PDF 共 6 页

**本次核验范围**：第 1 页至第 6 页（全文，含 §1–§6、致谢与参考文献），使用 `pdf-converter`（`mineru-open-api flash-extract`，`--language en`，单次转换覆盖全部 6 页，未分页）。页码未逐页核对物理页面渲染，下文位置以论文自身的章节编号（§）为准，辅以推断的大致页序；数值、公式与关键论断均标注章节号。

## 一句话

GradCache 通过“先无图前向缓存全部表示、再分子批重建计算图并用预先算好的表示梯度做种子反传”的两遍反传，把对比损失的显存开销从随批量线性增长压到近似常数，论证依据是对全批量梯度求和公式的代数拆分-合并（并非浮点数值层面的证明），实测额外运行时间约 20%。

## 背景：问题的演进（§1，第 1 页）

- 对比学习（in-batch negative）下，每个样本的损失依赖整个批次的其余样本，要求把整批数据的编码器前向激活同时放进显存；批量越大负样本越多，效果越好，但显存随批量线性增长。
- 梯度累积（gradient accumulation）能把大批量拆成多个小批量分别反传再求和更新，但对比损失的负样本数会被局部批量大小卡死——切分后每个子批只能看到子批内的负样本，无法保留全批量的负样本规模（§1 明确指出这一点，并在 §3.1 式 7 用 `ε_j` 的分段定义解释了为何梯度累积在这里不成立）。
- GradCache 的动机是把“损失到表示”和“表示到编码器参数”两段反传解耦，让编码器侧的反传可以逐子批独立进行。

## 方法核心

### 数学设定（§3.1，式 1）

对比损失定义为批内负样本的 softmax 交叉熵（式 1，温度设为 1）：每个 `s_i∈S` 的损失依赖整个目标集合 `T`，因此每个求和项都需要把全部 `T` 放进显存。

### 关键的两条“观察”（§3.2，紧接式 5–7 之后，原文逐字核验）

论文在给出偏导公式（式 2–7）后，明确写下两条观察（这是全文等价性论证的立论基础，须逐字核对，不可转述走样）：

1. **观察一**：`∂f(s_i)/∂Θ` 只依赖 `s_i` 和 `Θ`，而 `∂g(t_j)/∂Λ` 只依赖 `t_j` 和 `Λ`——即编码器参数梯度对单个样本的雅可比是"局部"的，不依赖批内其他样本。
2. **观察二**：计算 `∂L/∂f(s_i)` 和 `∂L/∂g(t_j)`（即损失对"表示"的梯度）只需要编码后的表示数值，不需要 `Θ` 或 `Λ`。

论文由此推出：只要已知 `∂L/∂s_i` 的数值，`f(s_i)` 的反传就可以用它自己独立的计算图和激活单独运行；而算出 `∂L/∂s_i` 本身，只需要两组表示向量 `F` 和 `G` 的数值（不需要编码器参数）。这是整个方法能拆成"先求表示梯度、再分批重建图反传"的数学基础。

### 四步算法（§3.3）

1. **Step1 无图前向**：对每个批实例多跑一次编码器前向，不建计算图，只收集表示。
2. **Step2 表示梯度计算与缓存**：用 Step1 的表示（有梯度追踪）构建对比损失的计算图并反传，得到每个表示的梯度 `u_i = ∂L/∂f(s_i)`、`v_i = ∂L/∂g(t_i)`，存入 Representation Gradient Cache；注意编码器本身不参与这一步的图构建。
3. **Step3 子批梯度累积**：逐子批重跑编码器前向（这次建图），取出对应的缓存梯度作为种子反传，跨子批累积编码器参数梯度（式 8、式 9）。
4. **Step4 优化**：所有子批处理完后统一 `optimizer.step()`，等效于整批一次前向反传后再更新。

### 等价性论证的层次（本次调研核心问题之一）

- 式 8、式 9 把全批量梯度 `∂L/∂Θ`（原式 2）重写为"外层遍历子批、内层遍历子批内样本"的双重求和，紧跟着的一句原文论证是：合并两重求和即可看出与直接大批量更新等价（"we can see the equivalence with direct large batch update by combining the two summations"，§3.3，式 9 之后）。
- **这是一个纯代数/集合划分恒等式**：把批次划分成互不相交的子批集合 `𝕊`，`Σ_{Ŝⱼ∈𝕊} Σ_{sᵢ∈Ŝⱼ} (·)` 与对整批 `Σ_{sᵢ∈S} (·)` 在实数算术下严格相等，这与浮点数值实现无关，属于"精确算术下的求和恒等式"，不是逐位数值证明。
- **检索结果（本次调研的核心证据）**：对全文用 `rg -a -in 'bitwise|precision|\bround|\bfloat\b|floating|\bexact'` 检索，命中情况为：
  - `bitwise`：**0 次命中**。
  - `precision`：**0 次命中**。
  - `round`（词首）：**0 次命中**。
  - `float`（独立词）：**0 次命中**；`floating`：**1 次命中**，出现在 §3.3 末尾"we only need to store `(|S|d+|T|d)` floating points in the cache"，这里"floating point(s)"是"浮点数"作为存储单位的名词，与数值精度或逐位一致性无关。
  - `exact`：**2 次命中**，均是"exact same gradient update"这一措辞，分别出现在 §1 引言末段（第 1 页）和 §6 结论首句（第 6 页），两处都是自然语言层面的断言，论文正文没有任何一处围绕浮点舍入误差、累加顺序、混合精度或 `torch.equal` 展开数值分析。
- **结论**：GradCache 的"exact same gradient update"是在**精确实数算术**下、基于集合划分求和恒等式成立的数学等价性主张；论文完全没有讨论浮点逐位一致性（无 `bitwise`/`precision`/`round` 相关论述）。这与本课题 ASR-重打包变体"预期数学相等但逐位不等"的判断一致；但**不能**把 GradCache 的"exact"引用为支持 ASR-保形变体"`torch.equal` 逐位相等"目标的文献依据——论文从未做过这个层次的论证。

### 显存与代价量化

- **额外前向的运行时代价**：摘要与 §1 明确报告约 20% 运行时间增加（"with about 20% increase in runtime"）；§4.2 训练速度实验复述为"uses 20% more time for representation pre-computation"，与批量从 64 到 4096 的扫描一致（Figure 1，未提供逐点数值表，只有趋势图）。
- **显存复杂度**：§3.3 明确给出缓存的额外显存开销是 `(|S|d + |T|d)` 个浮点数，与表示维度和批量线性相关，"比百万级模型参数小几个数量级"（作者原话的转述）。
- **对梯度检查点路线的实测评价**（§4.1 与 §4.2，任务要求重点核验的一条）：
  - §4.1 Implementations 段：作者尝试用梯度检查点复现 DPR 设置，"found it cannot scale to standard DPR batch size on our hardware"——即在其硬件上梯度检查点无法撑到 DPR 标准批量，因此**没有进入正式的 Table 1 对比表**。
  - §4.2 Training Speed 段：另有一句独立的量化评价——"we also find gradient checkpoint only runs up to batch of 64 and consumes twice the amount of time than accumulation"，即梯度检查点最多只能跑到批量 64，且耗时是梯度累积（Accumulation）的两倍。
  - 两处都是 GradCache 作者自己的附带实验观察（脚注 3 标注的补充说明），不是论文的主实验对比对象，需注意其硬件是单张 RTX 2080Ti，与本课题的显存规模不可直接类比。
- **端到端训练时间**：原始 DPR 论文报告 8×V100 训练约 1 天；GradCache 在单张 RTX 2080Ti 上"in practice, with improved data loading"实际训练 31 小时（§4.2）。

## 实验结果（§4，Table 1）

| 方法 | Top-5 | Top-20 | Top-100 |
| --- | --- | --- | --- |
| DPR（原论文，8 卡） | — | 78.4 | 85.4 |
| Sequential（单卡最大批量=8） | 59.3 | 71.9 | 80.9 |
| Accumulation（累积到 128，负样本仍受限于子批） | 64.3 | 77.2 | 84.9 |
| Cache（GradCache，批量=128，子批 16/8） | 68.6 | 79.3 | 86.0 |
| Cache（批量=512） | 68.3 | 79.9 | 86.6 |

GradCache 用单卡复现（甚至略超）DPR 8 卡的检索精度，Sequential 和 Accumulation 因负样本不足而明显掉点，验证了"负样本数量而非硬件规模"决定效果这一前提假设（§4.1 结果段）。

### 多 GPU 与深度距离函数的扩展（§3.4、§5）

- §3.4：多卡训练时需要一次额外的 all-gather 通信，把各卡表示同步后再各自算局部梯度、Step3 无需通信、Step4 按标准数据并行做梯度规约。
- §5：把简单点积相似度推广为可参数化的深度距离函数 `Φ`，引入额外的 Distance Gradient Cache，链式法则下可以"链接两个缓存"，覆盖早期交互（early interaction，`f(s)=s, g(t)=t`）作为特例。这部分对本课题的排序损失（`S_e` 是实体分数而非简单点积）具有直接的形式化参考价值。

## 与本课题的关系

- **可迁移机制**：Step1（无图前向缓存分数）→ Step2（对分数反传得到 `∂L/∂S_e`）→ Step3（逐子批重建图、用缓存梯度做种子反传）这一三段式结构，与第四章候选二 ASR 的 Pass 1/Pass 2 设计在形式上一一对应；§3.2 的两条观察（编码器逐样本独立、损失对表示的梯度只需表示数值）是判断 ASR-保形/ASR-重打包在数学上是否站得住脚的直接依据，应作为设计文档的正式引用点。
- **本课题推论（重要，论文未讨论，需独立标注）**：GradCache 的等价性证明只在**精确实数算术**下成立；浮点加法不满足结合律，"整批一次求和"与"分子批求和后再累加"在浮点实现下即便数学期望相同，也**不保证**产生逐位相同的结果——这是本课题读者需要自行推导/实验验证的推论，论文本身完全没有涉及（检索 `bitwise`/`precision`/`round` 均为 0 命中）。据此，ASR-保形若要求 `torch.equal` 严格逐位相等，其依据只能是"批未被重新打包、子批划分与直接反传路径的加法顺序恰好一致"这类实现细节，而不能引用 GradCache 的数学等价性证明本身。
- **不可直接声称**：不得引用本文支持"逐位相同（bitwise identical）"这一表述；本文的"exact"仅指精确算术下的梯度求和恒等式。也不得引用本文的 20% 运行时开销数字直接套用到本课题的排序损失场景——GradCache 的额外开销主要来自"编码器重复前向"，而本课题排序阶段的候选实现（ASR）是否需要重复完整的编码器前向、还是只需重跑轻量打分头，取决于具体实现，本文未覆盖这一差异。
- **仍需实验验证的假设**：(1) 本课题排序批（约 6403 序列）下，两遍反传的实际运行时增幅是否接近论文报告的 20%，需要用真实数据实测；(2) ASR-保形变体是否真能达到 `torch.equal` 逐位相等，需要用本课题的具体聚合算子和累加顺序做最小可证伪实验，不能以本文的数学证明代替。

## 疑问 / 待验证

- 论文的显存复杂度分析假设表示维度 `d` 和批量 `|S|+|T|` 已知且固定；本课题实体分数张量的形状（`6403` 序列 × 每序列多少实体）与论文的双塔检索场景（query/passage 各一个表示向量）结构不同，缓存开销的量级需要重新估算，不能照搬 `(|S|d+|T|d)` 公式。
- §4.2 的"20% 运行时增加"和"梯度检查点两倍耗时"均来自单张 RTX 2080Ti 上的 DPR 复现实验，硬件与任务都与本课题（排序损失、单步显存 30.97 GiB 级别）差异很大，只能作为量级参照，不能作为本课题的性能预期。

## 原始摘要

> Contrastive learning has been applied successfully to learn vector representations of text. [...] This paper introduces a gradient caching technique that decouples backpropagation between contrastive loss and the encoder, removing encoder backward pass data dependency along the batch dimension. As a result, gradients can be computed for one subset of the batch at a time, leading to almost constant memory usage.

## 文献信息

- arXiv: <https://arxiv.org/abs/2101.06983>
- 会议：Proceedings of the 6th Workshop on Representation Learning for NLP (RepL4NLP 2021)
- 代码：脚注提到 DPR 相关实现，正文未给出独立仓库链接（未核验代码仓库）
