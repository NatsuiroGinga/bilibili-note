---
schema: paper-note-search/v1
title: "Disentangling Label Distribution for Long-Tailed Visual Recognition"
title_zh: "解耦标签分布：面向任意目标先验的长尾识别"
authors: [Youngkyu Hong, Seungju Han, Kwanghee Choi, Seokjun Seo, Beomsu Kim, Buru Chang]
year: 2021
date: 2026-10-20
journal: "IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2021)；doi:10.1109/CVPR46437.2021.00656；arXiv:2012.00321"
doi: "10.1109/CVPR46437.2021.00656"
arxiv_id: "2012.00321"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2021-Hong-LADE-Label-Distribution-Disentangling.pdf"
tags:
  - 长尾识别
  - 标签分布偏移
  - 先验校正
  - PC-Softmax
  - 标签分布解耦
  - Donsker-Varadhan
  - 类型/论文
key_finding:
  - '把长尾识别写成**标签偏移**：\(p_s(x\mid y)=p_t(x\mid y)\) 但 \(p_s(y)\neq p_t(y)\)（§2.2、§3.1，物理第 2–3 页）。'
  - '**PC Softmax** 在推理时把 logit 改为 \(f^{PC}_\theta(x)[y]=f_\theta(x)[y]-\log p_s(y)+\log p_t(y)\)（Eq. 4，第 3 页），可适配任意目标先验 \(p_t(y)\)，且仍是合法的类别概率。'
  - '**LADER** 用正则化 Donsker-Varadhan 表示把 logit 拉向 \(\log[p_u(x\mid y)/p_u(x)]\)（Eq. 8–16，第 3–4 页）；**LADE = 交叉熵（用 \(p_s\)）+ α·LADER**（Eq. 18–20，第 4 页）。'
  - '**Balanced Softmax 是 LADE 在 α=0 时的特例**，但 Balanced Softmax 只覆盖均匀目标先验，LADE 覆盖任意 \(p_t(y)\)（第 4 页末段）。'
  - "CIFAR-100-LT（IR=100）Top-1：Softmax `41.0`、Balanced Softmax `45.1`、PC Softmax `45.3`、LADE `45.4`；Places-LT `31.5`→`38.6`→`38.7`→`38.8`；ImageNet-LT（180 epoch）`48.2`→`52.1`→`52.8`→`53.0`；iNaturalist `65.0`→`69.8`→`69.3`→`70.0`（Table 2–5，第 6 页）。"
  - "Table 6（第 7 页）在 Forward/Backward 多档目标先验下评测；LADE 在每一档都优于 Softmax、Balanced Softmax 与 Causal Norm，且目标分布越偏（Backward IR=50）优势越大（`50.0` 对 PC Softmax `49.0`）。"
method: "PC Softmax（推理时先验补偿）+ LADER（DV 表示正则化 logit）+ LADE（CE + α·LADER）；推理时注入目标先验 p_t(y)"
baseline: "Softmax、Focal、OLTR、CB-Focal、LDAM、LDAM+DRW、Decouple、BBN、Causal Norm、Balanced Softmax"
metrics: [top-1 accuracy, many/medium/few split accuracy, ECE]
related:
  - "[[2020-Ren-平衡元Softmax|Balanced Softmax：均匀目标先验的特例]]"
  - "[[2021-Menon-对数几率调整|Logit Adjustment：Fisher 一致的加性先验偏移]]"
  - "[[2020-Kang-长尾解耦表示与分类器|cRT/NCM：冻结表示后重训分类器]]"
  - "[[2019-Cao-LDAM标签分布感知间隔|LDAM：延迟再平衡]]"
  - "[[INDEX|方法论论文索引]]"
---

# 解耦标签分布：面向任意目标先验的长尾识别

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2021-Hong-LADE-Label-Distribution-Disentangling.pdf`，15 页）。
> 页码为 PDF 物理页。**注意：任务下达时给出的 arXiv:2103.17084 不是本文**（该 ID 是 DA-DETR 目标检测论文）；本文实际为 arXiv:2012.00321，CVPR 2021，DOI `10.1109/CVPR46437.2021.00656`（Crossref 核验）。

## 核心机制

### 1. 问题设定：长尾 = 标签偏移（§2.2、§3.1，第 2–3 页）

作者明确采用标签偏移假设：

\[
p_s(y)\neq p_t(y),\qquad p_s(x\mid y)=p_t(x\mid y).
\]

训练集长尾（source），测试集可以是均匀、长尾或任意先验（target）。模型若用 CE + Softmax 训练，估计的是 \(p_s(y\mid x)\)，与 \(p_t(y\mid x)\) 因 \(p_s(y)\neq p_t(y)\) 而纠缠（Fig. 1–2，第 1–2 页）。

### 2. PC Softmax：推理时先验补偿（Eq. 4，第 3 页）

\[
f_\theta^{PC}(x)[y]=f_\theta(x)[y]-\log p_s(y)+\log p_t(y). \tag{4}
\]

代入 softmax 后得到

\[
p_t(y\mid x;\theta)=
\frac{\frac{p_t(y)}{p_s(y)}e^{f_\theta(x)[y]}}
{\sum_c \frac{p_t(c)}{p_s(c)}e^{f_\theta(x)[c]}}. \tag{5}
\]

- 与简单地把 \(p_t/p_s\) 乘到输出概率上的做法不同，Eq. 5 仍满足 \(\sum_c p_t(y=c\mid x)=1\)（第 3 页）。
- \(p_s(y)\) 用训练集类频；\(p_t(y)\) 是目标先验，**推理时必须已知或估计**。
- 作者强调 PC Softmax 本身就是一个被忽视的强基线：在多个 benchmark 上超过此前 SOTA（第 3 页；Table 2–5）。

### 3. LADER：用 DV 表示解耦源先验（§3.3，第 3–4 页）

目标是把 logit 建模为

\[
f_\theta(x)[y]=\log\frac{p_u(x\mid y)}{p_u(x)}, \tag{8}
\]

其中 \(p_u(y)=1/C\) 是均匀先验。作者用正则化 Donsker-Varadhan 表示的最优形式

\[
\log\frac{d\mathbb{P}}{d\mathbb{Q}}
=\arg\max_T\left(\mathbb{E}_{\mathbb{P}}[T]-\log\mathbb{E}_{\mathbb{Q}}[e^T]
-\lambda(\log\mathbb{E}_{\mathbb{Q}}[e^T])^2\right) \tag{9}
\]

并取 \(\mathbb{P}=p_u(x\mid y),\mathbb{Q}=p_u(x)\)，得到单批次的 LADER（Eq. 15–16，第 4 页）。类权重取 \(\alpha_c=p_s(y=c)\)，即**头部类正则更强、尾部类更弱**（第 4 页）。

### 4. LADE：CE + LADER（Eq. 18–20，第 4 页）

\[
\mathcal{L}_{LADE-CE}(f_\theta(x),y)
=-\log\frac{p_s(y)e^{f_\theta(x)[y]}}
{\sum_c p_s(c)e^{f_\theta(x)[c]}}, \tag{19}
\]
\[
\mathcal{L}_{LADE}=\mathcal{L}_{LADE-CE}+\alpha\cdot\mathcal{L}_{LADER}. \tag{20}
\]

- **Balanced Softmax = LADE 在 \(\alpha=0\)**（第 4 页原文）；但 Balanced Softmax 只对应均匀目标先验，LADE 通过推理时的 Eq. 17 适配任意 \(p_t(y)\)。
- 推理时用

\[
p_t(y\mid x;\theta)=
\frac{p_t(y)e^{f_\theta(x)[y]}}
{\sum_c p_t(c)e^{f_\theta(x)[c]}}, \tag{17}
\]

其前提仍是 \(p_t(x\mid y)=p_u(x\mid y)\)（第 4 页）。

## 实验结果（本地全文核验）

| 数据集 | Softmax | Balanced Softmax | PC Softmax | LADE | 位置 |
|---|---:|---:|---:|---:|---|
| CIFAR-100-LT, IR=100 | `41.0` | `45.1` | `45.3` | `45.4` | Table 2，第 6 页 |
| Places-LT (All) | `31.5` | `38.6` | `38.7` | `38.8` | Table 3，第 6 页 |
| ImageNet-LT, 180 epoch (All) | `48.2` | `52.1` | `52.8` | `53.0` | Table 4，第 6 页 |
| iNaturalist 2018 | `65.0` | `69.8` | `69.3` | `70.0` | Table 5，第 6 页 |

- **PC Softmax 的增益几乎全部来自推理时的一次先验补偿**：在 Places-LT 上 Softmax `31.5`→PC `38.7`，与 Balanced Softmax `38.6` 持平；在 ImageNet-LT 180 epoch 上 `48.2`→`52.8`。这说明“只校正先验”在静态长尾上已经很强。
- **LADE 的额外增益较小但一致**：相对 PC Softmax，LADE 在四个数据集上分别 +0.1、+0.1、+0.2、+0.7（上表）。代价是额外的 DV 正则项与超参 \(\alpha,\lambda\)。
- **偏移目标分布**（Table 6，第 7 页）：在 ImageNet-LT 的 Forward/Backward 多档目标先验下，LADE 每一档都最好；Backward IR=50 时 LADE `50.0`、PC Softmax `49.0`、Balanced Softmax `39.7`、Softmax `27.9`。目标先验越偏离源先验，先验校正的价值越大。
- **校准**：LADE 的 ECE 为 `0.0346`，优于 PC Softmax、Causal Norm、Balanced Softmax（§4.4，第 7–8 页）。

## 与 PAAT M2' 的可迁移点

- **M2' 的“任意目标先验”版本**：PAAT 的正例率先验逐年变化（2024 约 1.64%，2025 约 0.05%）。PC Softmax 的 Eq. 4 正好给出一个**显式的年度先验注入接口**：训练年度用 \(p_s(y)\)，推理年度用 \(p_t(y)\)。如果 \(p_t(y)\) 在评测年度是已知的（例如按年度统计），这是零训练的决策边界校正。
- **比 Balanced Softmax 更灵活**：Balanced Softmax 只能把目标先验设为均匀；PC Softmax/LADE 允许目标先验等于“下一年的自然正例率”。对 PAAT 的自然 F1 评测，这一点比“强行 1:1”更贴近目标。
- **与 cRT 的逐级止损顺序**：PC Softmax（零训练）→ Logit Adjustment（零训练/单超参）→ cRT（冻结表示、重训 10 epoch 的一部分）。LADE 的 DV 正则项实现复杂、收益相对 PC Softmax 很小（+0.1~+0.7），在 PAAT 的小模型与 10 epoch 协议下不应作为首选。
- **M2 的实测背景**：PAAT 全程 1:1 平衡回合在 12 年平均 F1 上为 **−0.27 pp**（`m2` 的 `delta_mean_f1=-0.0027387`，制品 `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/paat-comparison.json`）。LADE/PC Softmax 提供的正是“不改采样、只改先验”的替代路径。

## 不可迁移边界（label shift 前提）

- **核心假设是 \(p_s(x\mid y)=p_t(x\mid y)\)**（§2.2、§3.1；Eq. 17 又要求 \(p_t(x\mid y)=p_u(x\mid y)\)）。本课题若存在年度概念漂移（\(p(x\mid y)\) 改变），则 PC/LADE 的先验补偿是**误设定**：它只能把“类比例”搬过去，不能把“同类样本的特征分布”搬过去。
- **本课题已实测 33.5× 采样噪声**：这会使 \(p_s(y)\) 与 \(p_t(y)\) 的经验估计、以及 \(p(x\mid y)\) 的稳定性都受到挑战。LADE 的 DV 正则化假设 \(p_u(x\mid y)\) 可由源样本重要性采样近似（Eq. 12–14），在极端稀有正类（\(n_+=5\)）下该近似的方差极大。
- **评测口径**：LADE 的主表是**类别平衡**或**人为设计的 shifted target** 测试集；PAAT 是自然年度分布下的 F1（2025 正例率约 0.05%）。LADE 的“目标先验”是数据集级设计量，PAAT 的目标先验需要从训练年/历史年估计，二者不能直接等同。
- **目标先验必须已知**：Eq. 4/17 都需要 \(p_t(y)\)。PAAT 在评测未来年度时并不知道该年的真实正例率；若用训练年先验，则退化为“用旧先验校正新年度”，其有效性取决于先验漂移的可预测性，论文没有提供这种时序外推证据。
- **多类 vs 二分类**：LADE 的 LADER 是逐类正则（Eq. 15 对每个类 c 求和），二分类下可大幅简化；但作者没有给出二分类实验，不能把多类结论逐字迁移。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| 标签偏移假设 \(p_s(y)\neq p_t(y),p_s(x\mid y)=p_t(x\mid y)\) | §2.2、§3.1，物理第 2–3 页 |
| PC 策略 Eq. (4) | §3.2，物理第 3 页 |
| Theorem 1 / Eq. (5)–(7) 目标后验 | §3.2，物理第 3 页 |
| DV 表示 Eq. (9) | §3.3，物理第 4 页 |
| LADER Eq. (15)–(16) | §3.3，物理第 4 页 |
| 目标后验 Eq. (17) 与 \(p_t(x\mid y)=p_u(x\mid y)\) | §3.4，物理第 4 页 |
| LADE Eq. (18)–(20) | §3.4，物理第 4 页 |
| Table 2–5（主结果） | §4.2，物理第 6 页 |
| Table 6（shifted target） | §4.3，物理第 7 页 |
| ECE / 校准 | §4.4，物理第 7–8 页 |
| 训练细节 | 附录，物理第 12 页 |

## 与相关工作的关系

- 与 [[2020-Ren-平衡元Softmax|Balanced Softmax]]：LADE 明确说 Balanced Softmax 是 \(\alpha=0\) 的特例；BSM 只覆盖均匀目标先验，LADE/PC 覆盖任意 \(p_t(y)\)。
- 与 [[2021-Menon-对数几率调整|Logit Adjustment]]：PC Softmax 的 Eq. 4 与 LA 的 Eq. 9 都是加性 log-prior 偏移；LA 给出平衡误差的 Fisher 一致性，LADE 给出任意目标先验的 DV 正则化版本。两者在“只校正先验”的层面同源。
- 与 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]：LADE 把 Decouple-τ-norm/LWS 作为对比基线，并在 Places-LT/ImageNet-LT 上超过；但 LADE 的增益主要来自推理时先验补偿，而不是表示学习。

## 原始摘要要点

> "We formulate long-tailed visual recognition as a label shift problem where the target and source label distributions are different ... we propose LADE loss based on the optimal bound of Donsker-Varadhan representation."
