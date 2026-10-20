---
schema: paper-note-search/v1
title: "Long-tail learning via logit adjustment"
title_zh: "对数几率调整：长尾学习的 Fisher 一致先验校正"
authors: [Aditya Krishna Menon, Sadeep Jayasumana, Ankit Singh Rawat, Himanshu Jain, Andreas Veit, Sanjiv Kumar]
year: 2021
date: 2026-10-20
journal: "International Conference on Learning Representations (ICLR 2021)；arXiv:2007.07314"
arxiv_id: "2007.07314"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2021-Menon-Logit-Adjustment.pdf"
tags:
  - 长尾识别
  - 对数几率调整
  - 先验校正
  - Fisher一致性
  - 平衡误差
  - 分类器再平衡
  - 类型/论文
key_finding:
  - '平衡误差的 Bayes 最优评分器为 \(\arg\max_y \mathbb{P}^{\mathrm{bal}}(y\mid x)=\arg\max_y \mathbb{P}(x\mid y)\)；在固定类条件 \(\mathbb{P}(x\mid y)\)、只变先验 \(\mathbb{P}(y)\) 时，可化为 \(\arg\max_y f_y(x)-\ln\mathbb{P}(y)\)（Eq. 7–8，物理第 5 页）。'
  - '**Post-hoc logit adjustment**：\(\arg\max_y f_y(x)-\tau\log\pi_y\)（Eq. 9，第 5 页）；**Logit-adjusted loss**：\(-\log\frac{e^{f_y+\tau\log\pi_y}}{\sum_{y^{\prime\prime}}e^{f_{y^{\prime\prime}}+\tau\log\pi_{y^{\prime\prime}}}}\)（Eq. 10，第 6 页）。'
  - '该损失对**平衡误差**是 Fisher 一致的（Theorem 1，第 7 页）；权重归一化（含 cRT 的 \(\tau\)-normalization）不是一致的，且其“权重范数随类频变化”的前提在 Adam 下不成立（§2、Fig. 1，第 3–4 页）。'
  - 'CIFAR-10-LT 平衡误差：ERM `27.16` → post-hoc（\(\tau^*\)）`19.08` → loss `22.33`；CIFAR-100-LT `61.64`→`57.90`/`56.11`；ImageNet-LT `53.11`→`49.56`/`48.89`；iNaturalist `38.66`→`33.80`/`33.64`（Table 3，第 9 页）。'
  - '**前提边界**：所有推导都建立在“类条件 \(\mathbb{P}(x\mid y)\) 固定、只有 \(\mathbb{P}(y)\) 变化”的标签偏移假设上；论文没有处理 \(p(x\mid y)\) 漂移。'
method: '按训练先验 \(\pi_y\) 对 logit 做加性偏移；可 post-hoc（推理时）或写入训练损失；\(\tau\) 由校准/验证选择'
baseline: "ERM、weight normalisation（cRT/τ-normalization）、LDAM/adaptive margin、equalised loss"
metrics: [balanced error, per-class error]
related:
  - "[[2020-Ren-平衡元Softmax|Balanced Softmax：乘性/分母形式的先验校正]]"
  - "[[2021-Hong-LADE标签分布解耦|LADE：任意目标先验的 PC Softmax]]"
  - "[[2020-Kang-长尾解耦表示与分类器|cRT/NCM：冻结表示后重训分类器]]"
  - "[[2019-Cao-LDAM标签分布感知间隔|LDAM：延迟再平衡]]"
  - "[[INDEX|方法论论文索引]]"
---

# 对数几率调整：长尾学习的 Fisher 一致先验校正

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2021-Menon-Logit-Adjustment.pdf`，27 页）。
> 页码为 PDF 物理页。arXiv:2007.07314 与题名、作者、ICLR 2021 一致（arXiv 元数据 `arxiv:comment` 明示）。

## 核心机制

### 1. 目标：最小化平衡误差（§2，第 2 页）

\[
\mathrm{BER}(f)=\frac{1}{L}\sum_{y\in[L]}\mathbb{P}_{x\mid y}
\left(y\notin\arg\max_{y'} f_{y'}(x)\right). \tag{2}
\]

平衡误差等价于使用平衡类概率 \(\mathbb{P}^{\mathrm{bal}}(y\mid x)\propto \frac{1}{L}\mathbb{P}(x\mid y)\)。Bayes 最优评分器满足

\[
\arg\max_y f_y^*(x)=\arg\max_y \mathbb{P}^{\mathrm{bal}}(y\mid x)
=\arg\max_y \mathbb{P}(x\mid y). \tag{7}
\]

**关键观察**：固定类条件 \(\mathbb{P}(x\mid y)\) 后，先验 \(\mathbb{P}(y)\) 怎么变都不影响最优评分器。把 \(\mathbb{P}(y\mid x)\propto e^{s_y^*(x)}\) 代入，得到

\[
\arg\max_y \exp(s_y^*(x))/\mathbb{P}(y)
=\arg\max_y s_y^*(x)-\ln\mathbb{P}(y). \tag{8}
\]

这就是全部方法论的来源：**先验只以加性 logit 偏移进入决策**。

### 2. Post-hoc logit adjustment（Eq. 9，第 5 页）

\[
\arg\max_{y\in[L]} \exp(w_y^\top\Phi(x))/\pi_y^\tau
=\arg\max_{y\in[L]} f_y(x)-\tau\log\pi_y. \tag{9}
\]

- \(\pi_y\) 是训练集经验类频（或先验估计）。
- \(\tau=1\) 对应 Bayes 校正；\(\tau\neq1\) 对应温度缩放后的估计，用于处理神经网络校准不良（第 5 页）。
- 与权重归一化的关键差别：Eq. 9 是**加性**偏移，权重归一化 \(f_y/\nu_y^\tau\) 是**乘性**缩放；两者对标签排序不同，乘性更新不是平衡误差的一致方法（§4.2，第 6 页）。

### 3. Logit-adjusted loss（Eq. 10，第 6 页）

\[
\ell(y,f(x))
=-\log\frac{e^{f_y(x)+\tau\log\pi_y}}
{\sum_{y'}e^{f_{y'}(x)+\tau\log\pi_{y'}}}
=\log\left[1+\sum_{y'\neq y}\left(\frac{\pi_{y'}}{\pi_y}\right)^\tau
e^{f_{y'}(x)-f_y(x)}\right]. \tag{10}
\]

它等价于学习一个标准评分器 \(g_y=f_y+\tau\log\pi_y\)，再在推理时做 post-hoc 调整；凸目标下两者解相同，非凸网络下局部极小可能不同（第 6 页）。对 \(\tau=1\)，它是 pairwise margin loss（Eq. 11）在 \(\alpha_y=1,\Delta_{yy'}=\log(\pi_{y'}/\pi_y)\) 的特例：**在稀有正类与主导负类之间强制更大间隔**。

### 4. Fisher 一致性（Theorem 1，第 7 页）

对任意 \(\delta\in\mathbb{R}_+^L\)， pairwise loss（Eq. 11）在

\[
\alpha_y=\delta_y/\pi_y,\qquad \Delta_{yy'}=\log(\delta_{y'}/\delta_y)
\]

时对平衡误差 Fisher 一致。取 \(\delta_y=\pi_y\) 即得 logit-adjusted loss 的一致性；取 \(\delta_y=1\) 则回到经典 balanced loss 的一致性。二分类下 Lemma 2（附录 B.1，第 18 页）给出充要条件。

## 实验结果（本地全文核验）

Table 3（第 9 页，5 次运行平均，balanced error，越低越好）：

| 方法 | CIFAR-10-LT | CIFAR-100-LT | ImageNet-LT | iNaturalist |
|---|---:|---:|---:|---:|
| ERM | `27.16` | `61.64` | `53.11` | `38.66` |
| Weight norm. (\(\tau=1\)) | `24.02` | `58.89` | `52.00` | `48.05` |
| Weight norm. (\(\tau=\tau^*\)) | `21.50` | `58.76` | `49.37` | `34.10` |
| Adaptive margin (LDAM) | `26.65` | `60.40` | `52.15` | `35.42` |
| Equalised loss | `26.02` | `57.26` | `54.02` | `38.37` |
| **Post-hoc LA (\(\tau=1\))** | `22.60` | `58.24` | `49.66` | `33.98` |
| **Post-hoc LA (\(\tau=\tau^*\))** | `19.08` | `57.90` | `49.56` | `33.80` |
| **LA loss (\(\tau=1\))** | `22.33` | `56.11` | `48.89` | `33.64` |

- **后处理就足够强**：在 CIFAR-10-LT 上，仅加性偏移把平衡误差从 `27.16` 降到 `19.08`（相对降低约 30%）；在 ImageNet-LT 上 `53.11`→`49.56`。
- **loss 版本通常略好于 post-hoc**，但两者差距不大；作者明确说 post-hoc 的强表现支持“表示与分类器解耦”的可行性（第 9 页末）。
- **学习率/优化器会影响权重归一化**：Fig. 1（第 4 页）显示 SGD 动量下 \(\|w_y\|_2\) 与类频正相关，Adam 下则反相关或无关；因此 cRT 的 \(\tau\)-normalization 前提依赖优化器。PAAT 使用 SGD，动量 0.9，前提相对更接近论文设定，但仍需以本课题权重范数实测确认。

## 与 PAAT M2' 的可迁移点

- **M2' 的最低成本基线（post-hoc）**：在训练年度结束后，直接对输出 logit 做

  \[
  z \leftarrow z - \tau\log\pi_+ \quad(\text{二分类，等价于阈值平移})
  \]

  不需要重训、不需要冻结/解冻、不需要额外 epoch。对 PAAT 的 10 epoch 年度协议，这是唯一几乎零成本、可逐年施加的再平衡。
- **与 cRT 的分工**：LA 的 post-hoc 只动决策边界；cRT 会重新初始化并重训分类器（见 [[2020-Kang-长尾解耦表示与分类器|Kang et al.]] 的 10 epoch 协议）。若 PAAT 的表示已足够好，先测 LA（零训练）再测 cRT（10 epoch 的一部分）是合理的逐级止损顺序。
- **与 Balanced Softmax 的关系**：两者在二分类下都退化为先验 logit 偏移；LA 的优势是有 Fisher 一致性证明，并且 \(\tau\) 可校准。若 M2' 需要一个可解释的默认值，\(\tau=1\) 是理论起点，但必须用训练区内验证选择，不能接触最终测试年标签。
- **M2 的实测背景**：PAAT 的全程 1:1 平衡回合在 12 年平均 F1 上为 **−0.27 pp**（`m2` 的 `delta_mean_f1=-0.0027387`，制品 `thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/paat-comparison.json`）。这说明“改采样”本身不是有效方向；M2' 应优先测“只动决策边界”的 LA/post-hoc 路径。

## 不可迁移边界（label shift 前提）

- **全部推导假设 \(\mathbb{P}(x\mid y)\) 固定**（Eq. 7–8 的前提；第 5 页原文：“for fixed class-conditionals \(\mathbb{P}(x\mid y)\), varying the class priors \(\mathbb{P}(y)\) arbitrarily will not affect the optimal scorers”）。若年度漂移改变 \(p(x\mid y)\)，则 Bayes 最优评分器本身改变，单靠 \(-\tau\log\pi_y\) 不能恢复；此时 LA 是**误设定校正**，不是一致方法。
- **本课题已实测 \(p(x\mid y)\) 跨年漂移为 33.5× 采样噪声**（`thesis/experiments/llm_probe/runs/diagnostics/ch4-prior-shift-diagnostic/prior_shift_diag.json`：`per_label["0"].ratio=33.5316`；最相似的一对年度仍为 5.6×；`.Codex/docs/LAMDA/LAMDA路线总控.md` 第 521 行据此把“先验／标签转移校正”列为已否决方向）。这会使 \(\pi_y\) 的经验估计和类条件分布都不稳定。LA 只能校正“类比例”，不能校正“同类样本的特征分布变了”；因此标为 **“可迁移为 post-hoc 基线/诊断，不可迁移为机制主张”**。
- **平衡误差 ≠ 自然 F1**：LA 的理论目标是 balanced error（各类等权）。PAAT 评测自然年度分布下的 F1（2024 正例率约 1.64%，2025 约 0.05%），两者目标函数不同；把先验推向 1:1 会改变 0.5 阈值下的正例率，未必提升 F1。
- **\(\tau\) 的选择**：论文用验证集/校准准则选 \(\tau\)；PAAT 末期年度正例极少，若用末期年度选 \(\tau\) 会接触目标标签，必须在前一年度或训练区内冻结。
- **多类 vs 二分类**：二分类下 Eq. 10 可化为单 logit 的 BCE + 常数偏移；但“平衡误差”与“固定 0.5 阈值的 F1”之间的对应需要重新推导，不能直接把多类结论逐字搬过来。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| 平衡误差 Eq. (2) | §2，物理第 2 页 |
| 权重归一化 Eq. (3) 与其优化器依赖 Fig. 1 | §2，物理第 3–4 页 |
| Bayes 最优与先验偏移 Eq. (7)–(8) | §3，物理第 5 页 |
| Post-hoc logit adjustment Eq. (9) | §4.1，物理第 5 页 |
| 加性 vs 乘性更新（Eq. 9 后） | §4.2，物理第 6 页 |
| Logit-adjusted loss Eq. (10) | §5.1，物理第 6 页 |
| Pairwise margin loss Eq. (11) | §5.1，物理第 7 页 |
| Theorem 1（Fisher 一致性） | §5.2，物理第 7 页 |
| Table 3（主结果） | §6.2，物理第 9 页 |
| Table 4（更大骨干） | §6.2，物理第 10 页 |
| 训练细节（CIFAR 200 epoch、160/180 衰减） | 附录 D，物理第 23 页 |

## 与相关工作的关系

- 与 [[2020-Ren-平衡元Softmax|Balanced Softmax]]：BSM 把 \(n_j\) 放进 softmax 分子/分母，LA 把 \(\log\pi_j\) 加进 logit；两者在二分类下等价为同一阈值平移，但 LA 明确给出平衡误差的 Fisher 一致性，并指出权重归一化（cRT 的 τ-norm）不是一致的。
- 与 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]：LA 的 Table 1 把 cRT 的 weight normalisation 列为“不一致”，把 logit adjustment 列为“一致”；这为 M2' 选择“加性先验偏移”而非“权重缩放”提供了理论依据。
- 与 [[2019-Cao-LDAM标签分布感知间隔|LDAM]]：LDAM 的间隔 \(\delta_y\propto\pi_y^{-1/4}\) 只考虑正类；LA 的 \(\Delta_{yy'}=\log(\pi_{y'}/\pi_y)\) 同时考虑正负类，因此在稀有正类 vs 主导负类上更强。LA 附录还提到可以把二者组合（第 11 页）。

## 原始摘要要点

> "We present two simple modifications of standard softmax cross-entropy training ... based on the label frequencies, either applied post-hoc to a trained model, or enforced in the loss during training. Such adjustment encourages a large relative margin between logits of rare versus dominant labels."
