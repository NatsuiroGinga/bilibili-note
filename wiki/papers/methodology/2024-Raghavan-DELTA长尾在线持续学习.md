---
schema: paper-note-search/v1
title: "DELTA: Decoupling Long-Tailed Online Continual Learning"
title_zh: "DELTA：长尾在线持续学习中的表示与分类器解耦"
authors: [Siddeshwar Raghavan, Jiangpeng He, Fengqing Zhu]
year: 2024
date: 2026-10-20
journal: "IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW 2024)；doi:10.1109/CVPRW63382.2024.00409；arXiv:2404.04476"
doi: "10.1109/CVPRW63382.2024.00409"
arxiv_id: "2404.04476"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2024-Raghavan-DELTA-Long-Tailed-Online-Continual.pdf"
tags:
  - 长尾识别
  - 在线持续学习
  - 表示解耦
  - 监督对比学习
  - Equalization Loss
  - 分类器再平衡
  - 类型/论文
key_finding:
  - '定义 **Long-Tailed Online Continual Learning (LTOCL)**：数据以类别不平衡的流形式到达，每个样本只训练一次，训练/测试都不提供任务标识（Abstract、§3，物理第 1、4 页）。'
  - '**两阶段解耦**：Stage 1 用监督对比损失学表示（Eq. 1，第 4 页）；Stage 2 **冻结除分类层以外的所有层**，用 **Equalization Loss** 训练分类器（§4.2，第 4–5 页）。'
  - 'Equalization Loss 受 Balanced Softmax 启发，但不需要全局类分布：用**任务内临时分布向量 \(P(k^t)\)** 作为先验校正（§4.2，第 5 页）。'
  - "Split CIFAR-100-LT（20 task，M=2K）：DELTA `19.93` 对 OnPRO `18.01`、SCR `15.88`、CBRS `8.91`；10 task：`22.47` 对 `18.85`；VFN-LT（15 task）：`13.84` 对 `13.50`（Table 1，第 7 页）。"
  - "消融：对比学习 + CE `16.62`（CIFAR）/`9.91`（VFN）→ 对比学习 + Equalization Loss `19.93`/`13.84`（Table 3，第 7 页）。"
method: "双阶段：监督对比学习学表示 → 冻结编码器，仅用 Equalization Loss 训练分类层；分类器阶段使用任务内类分布先验"
baseline: "OnPRO、SCR、ASER、PRS、CBRS、GSS、LT-CIL(offline)"
metrics: [average accuracy, forgetting]
related:
  - "[[2020-Kang-长尾解耦表示与分类器|cRT/NCM：静态长尾的解耦]]"
  - "[[2022-Liu-长尾类增量学习|LT-CIL：类增量下的两阶段 LWS]]"
  - "[[2020-Ren-平衡元Softmax|Balanced Softmax：Equalization Loss 的来源]]"
  - "[[2023-Baby-在线标签移位|Online Label Shift：显式先验漂移方法]]"
  - "[[INDEX|方法论论文索引]]"
---

# DELTA：长尾在线持续学习中的表示与分类器解耦

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2024-Raghavan-DELTA-Long-Tailed-Online-Continual.pdf`，11 页）。
> 页码为 PDF 物理页。CVPRW 2024（archival track）；arXiv:2404.04476。

## 核心机制

### 1. 问题设定：LTOCL（§3，第 4 页）

- 数据以任务流 \(t=1,2,\ldots\) 到达，每个任务内部类别分布长尾；
- **每个样本只被模型看一次**（online）；
- 训练和测试都不提供任务标识；
- 测试集是**类别平衡**的、只包含已见类。

这与 PAAT 的年度循环有两点相似：数据按时间到达、类比例变化；但 DELTA 的任务是**新增类**，不是同一标签空间的概念漂移。

### 2. Stage 1：监督对比学习（§4.1，第 4 页）

用 SimCLR 风格的对比损失：

\[
L_{\text{contrastive}}(Z_T)=\sum_{j\in T}\frac{-1}{|P(j)|}
\sum_{p\in P(j)}
\frac{\exp(v_j\cdot v_p/\tau)}
{\sum_{k\in A(j)}\exp(v_j\cdot v_k/\tau)}. \tag{1}
\]

其中 \(P(j)\) 是同标签正样本集合，\(A(j)\) 是 batch 内其他样本；温度 \(\tau=0.09\)（§5.2，第 6 页）。动机是：长尾类样本少，但头部类的负样本多样性可以帮助学习判别特征。

### 3. Stage 2：冻结编码器 + Equalization Loss（§4.2，第 4–5 页）

- **冻结除分类层外的所有层**；
- 用任务内临时类分布 \(P(k^t)\) 作为先验向量，调整分类 logits/梯度；
- 作者明确说 Equalization Loss 受 **Balanced Softmax** 启发，但 Balanced Softmax 需要整个数据集的类分布，而 LTOCL 只能看到流式数据，因此用 \(P(k^t)\) 的在线估计替代全局 \(n_j\)。

这一步与 cRT 的结构最接近：**表示冻结、只重训分类器**；差别是 DELTA 在每个任务后都做一次，且分类器损失是先验校正版 CE，而不是单纯的类平衡采样 CE。

## 实验结果（本地全文核验）

Table 1（第 7 页，average accuracy，越高越好）：

| 设置 | DELTA | 最强基线 | 位置 |
|---|---:|---:|---|
| Split CIFAR-100-LT, 20 task, M=2K | `19.93` | OnPRO `18.01` | Table 1，第 7 页 |
| Split CIFAR-100-LT, 20 task, M=0.5K | `16.53` | OnPRO `14.02` | Table 1，第 7 页 |
| Split CIFAR-100-LT, 10 task, M=2K | `22.47` | OnPRO `18.85` | Table 1，第 7 页 |
| VFN-LT, 15 task, M=2K | `13.84` | OnPRO `13.50` | Table 1，第 7 页 |
| VFN-LT, 7 task, M=2K | `12.84` | OnPRO `11.84` | Table 1，第 7 页 |

- **不平衡越严重，增益越大**（Table 2，第 7 页）：\(\rho=0.005\) 时 DELTA `18.02`、CBRS `7.60`、SCR `3.59`；\(\rho=1.0\)（平衡）时 DELTA `33.23`、CBRS `15.79`。
- **Equalization Loss 的独立贡献**（Table 3，第 7 页）：对比学习 + CE 为 `16.62`（CIFAR）/`9.91`（VFN）；对比学习 + EQ 为 `19.93`/`13.84`。这说明“只在分类阶段做先验校正”本身就有实质增益。
- **表示阶段不做过平衡**：DELTA 的 stage 1 用自然流 + 对比学习，stage 2 才平衡；这与 Kang et al. 的“自然采样学表示、分类器再平衡”一致。

## 与 PAAT M2' 的可迁移点

- **最接近的“长尾 + 时序流”证据**：DELTA 是本次检索中唯一同时满足“表示/分类器解耦 + 长尾 + 在线流”的全文论文。它说明在流式设定下，**冻结表示后只做分类器再平衡**是可行的，且比端到端平衡训练更稳。
- **年度先验的在线估计**：PAAT 的每个年度内可以估计 \(P(k^t)\)（正/负类比例），然后只在分类头做一次先验校正；这与 DELTA 的 stage 2 结构同型。相比 cRT，它不需要重训整个分类器，成本更低。
- **与 M2 的对照**：PAAT 的 M2 在**表示学习阶段**就做 1:1 平衡采样，实测 12 年平均 F1 为 **−0.27 pp**（`m2` 的 `delta_mean_f1=-0.0027387`，制品 `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/paat-comparison.json`）。DELTA 的证据方向相反：**表示阶段用自然流，分类阶段再平衡**。这为 M2' 提供了直接的结构依据。

## 不可迁移边界

- **任务定义不同**：DELTA 是 class-incremental（新类不断到来），PAAT 是同一正/负标签空间的年度概念漂移。DELTA 的“长尾”是任务内类频不平衡，不是 \(p(x\mid y)\) 的漂移。
- **没有显式 label shift 假设**：DELTA 的 \(P(k^t)\) 是任务内类比例，用于梯度校正；它没有证明 \(p(x\mid y)\) 不变，也没有处理 \(p(x\mid y)\) 漂移。因此它**不能作为“漂移 + 长尾”联合证据**，只能作为“流式长尾下的解耦”证据。
- **每个样本只看一次**：PAAT 每年训练 10 epoch、有 200 条回放；DELTA 的 online 单遍设定使它的结论不能直接外推到多 epoch 年度训练。
- **图像骨干与对比学习成本**：ResNet-32/18 + 128 维投影头；PAAT 是行为特征上的小模型，且 M2' 的目标是低成本基线，DELTA 的对比学习阶段成本较高。
- **任务标识**：DELTA 训练/测试都不提供任务 ID，但仍按任务顺序组织数据；PAAT 的年度边界是天然已知的，这一点更简单。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| LTOCL 定义 | §3，物理第 4 页 |
| Stage 1 / Stage 2 结构 | §4，物理第 4 页 |
| 对比损失 Eq. (1) | §4.1，物理第 4 页 |
| Equalization Loss 与 \(P(k^t)\) | §4.2，物理第 4–5 页 |
| 训练细节（ResNet-32/18、τ=0.09、单遍） | §5.2，物理第 6 页 |
| Table 1（主结果） | §5.3，物理第 7 页 |
| Table 2（不平衡率消融） | §5.5，物理第 7 页 |
| Table 3（CE vs EQ） | §5.5，物理第 7 页 |

## 与相关工作的关系

- 与 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]：DELTA 把 cRT 的“冻结表示 + 重训分类器”搬到 online CL；差别是分类器损失用 Equalization Loss，且每个任务后都做一次。
- 与 [[2022-Liu-长尾类增量学习|LT-CIL]]：LT-CIL 用 LWS + 冻结旧头处理离线类增量；DELTA 用 EQ loss + 冻结编码器处理在线类增量。两者都支持“分类阶段再平衡”，但实现不同。
- 与 [[2020-Ren-平衡元Softmax|Balanced Softmax]]：DELTA 明确说 EQ loss 受 Balanced Softmax 启发；但 BSM 需要全局类频，DELTA 用任务内在线估计，适合流式设定。
- 与 [[2023-Baby-在线标签移位|Online Label Shift]]：OLS 显式假设 \(Q_t(x\mid y)\) 不变，DELTA 不处理这个假设；两者是“流式长尾”与“流式标签偏移”的平行工作。

## 原始摘要要点

> "We study the under-explored problem of Long-Tailed Online Continual Learning (LTOCL) ... We present DELTA, a decoupled learning approach ... adapting supervised contrastive learning ... and Equalization Loss."
