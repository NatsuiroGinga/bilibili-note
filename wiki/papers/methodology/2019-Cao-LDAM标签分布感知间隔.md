---
schema: paper-note-search/v1
title: "Learning Imbalanced Datasets with Label-Distribution-Aware Margin Loss"
title_zh: "标签分布感知间隔损失与延迟再平衡"
authors: [Kaidi Cao, Colin Wei, Adrien Gaidon, Nikos Arechiga, Tengyu Ma]
year: 2019
date: 2026-10-20
journal: "Advances in Neural Information Processing Systems 32 (NeurIPS 2019)；arXiv:1906.07413"
arxiv_id: "1906.07413"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2019-Cao-LDAM-Label-Distribution-Aware-Margin.pdf"
tags:
  - 类不平衡
  - 长尾识别
  - 间隔损失
  - 延迟再平衡
  - 重采样
  - 类型/论文
key_finding:
  - '从平衡测试分布的分母类误差界出发，得到每类最优间隔 \(\gamma_j\propto n_j^{-1/4}\)（慢速率界；Eq. 8–9，物理第 4–5 页）。'
  - 'LDAM 损失把类相关间隔 \(\Delta_j=C/n_j^{1/4}\) 写入 softmax：\(\mathcal{L}_{\mathrm{LDAM}}=-\log\frac{e^{z_y-\Delta_y}}{e^{z_y-\Delta_y}+\sum_{j\ne y}e^{z_j}}\)（Eq. 12–13，第 5 页）。'
  - "提出**延迟再平衡（DRW）**：先用普通 ERM 训练到学习率退火，再用重加权/重采样做第二阶段（Algorithm 1，第 6 页）。"
  - "重加权/重采样在退火前会损害特征质量；ERM 第一阶段学到的特征更好（§3.3，第 6 页；附录 Fig. 6）。"
  - "CIFAR-10 长尾（不平衡 100）错误率：ERM `29.64`、LDAM `26.65`、LDAM-DRW `22.97`；iNaturalist 2018：ERM `42.86`、LDAM `35.42`、LDAM-DRW `32.00`（Table 2/3，第 8–9 页）。"
method: "LDAM 间隔损失（归一化 logits + 类相关间隔）+ 延迟再平衡训练计划（ERM 预热后重加权）"
baseline: "ERM、RW、RS、CB-RW、CB-Focal、Focal、M-DRW、LDAM 单独"
metrics: [top-1 error, per-class error, balanced test error]
related:
  - "[[2019-Cui-有效样本数类平衡损失|Class-Balanced：有效样本数重加权]]"
  - "[[2020-Kang-长尾解耦表示与分类器|Decoupling：采样策略与分类器再平衡]]"
  - "[[INDEX|方法论论文索引]]"
---

# 标签分布感知间隔损失与延迟再平衡

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2019-Cao-LDAM-Label-Distribution-Aware-Margin.pdf`）。
> 页码为 PDF 物理页。

## 核心机制

1. **问题设定**：训练分布不平衡，但测试准则要求**平衡测试分布**（先均匀采样类别，再采样本）下的误差。
   对每类 \(j\)，定义类间隔 \(\gamma_j=\min_{i\in S_j}(f(x_i)_{y_i}-\max_{\ell\ne y_i}f(x_i)_\ell)\)（Eq. 1–2，第 4 页）。
2. **理论动机**：在可分假设下，类 \(j\) 的误差界为
   \[
   L_j[f]\lesssim \frac{1}{\gamma_j}\sqrt{\frac{\mathbf{C}(\mathcal{F})}{n_j}}+\frac{\log n}{\sqrt{n_j}}
   \]
   （Theorem 1 / Eq. 4，第 4 页）。平衡测试误差是各类误差的平均（Eq. 5）。
   在二分类下最小化该界，得到最优间隔
   \[
   \gamma_1=\frac{C}{n_1^{1/4}},\qquad \gamma_2=\frac{C}{n_2^{1/4}}
   \]
   （Eq. 8，第 5 页）。作者也指出：若采用「快速率」界，指数会变为 \(n^{-1/3}\)（第 5 页），
   因此 \(1/4\) 是慢速率界下的选择，不是普适定律。
3. **LDAM 损失**（§3.2，第 5 页）：对 logits 与最后一层权重做 \(L_2\) 归一化后，
   \[
   \mathcal{L}_{\mathrm{LDAM}}=-\log\frac{e^{z_y-\Delta_y}}{e^{z_y-\Delta_y}+\sum_{j\ne y}e^{z_j}},
   \quad \Delta_j=\frac{C}{n_j^{1/4}}.
   \]
   与标准间隔 softmax 的区别是**间隔依赖标签分布**，稀有类获得更大间隔。
   作者强调：二分类下它看起来像重加权，但多分类下梯度影响不只是标量缩放（第 5 页 Remark）。
4. **延迟再平衡 DRW**（§3.3，Algorithm 1，第 6 页）：第一阶段（\(t\le T_0\)）用普通 ERM + LDAM；
   第二阶段（\(t>T_0\)，通常在学习率退火后）再用 \(n_y^{-1}\) 重加权或重采样。
   作者观察到：退火前使用重加权/重采样，学到的特征比 ERM 差；ERM 第一阶段为第二阶段提供了更好的初始化。

## 实验结果（本地全文核验）

| 数据集/设置 | 方法 | Top-1 error | 位置 |
|---|---|---:|---|
| IMDB（移除 90% 负例） | ERM / RS / RW / LDAM-DRW | `36.82` / `26.50` / `23.66` / `17.84` | Table 1，第 7 页 |
| CIFAR-10 长尾，不平衡 100 | ERM / LDAM / LDAM-DRW | `29.64` / `26.65` / `22.97` | Table 2，第 8 页 |
| CIFAR-100 长尾，不平衡 100 | ERM / LDAM / LDAM-DRW | `61.68` / `60.40` / `57.96` | Table 2，第 8 页 |
| iNaturalist 2018 | ERM / CB Focal / ERM-DRW / LDAM / LDAM-DRW | `42.86` / `38.88` / `36.27` / `35.42` / `32.00` | Table 3，第 9 页 |

- LDAM 单独就优于 ERM 与 CB-Focal；DRW 单独（ERM-DRW）也有效；二者组合最好。
- 在 iNaturalist 上，LDAM-DRW 相对 ERM 的 top-1 error 降低 `10.86` 个百分点，相对此前最好方法降低 `6.88`（§4.3，第 9 页）。
- 重采样（RS）在极端不平衡下容易对少数类过拟合；重加权（RW）在极端不平衡下优化困难（§2，第 2 页）。

## 与 PAAT M2（正例稀缺的平衡回合训练）的可迁移点

- **M2 的精确类比**：PAAT M2 在每个回合做正负 1:1 采样（等价于二分类的 class-balanced sampling，\(q=0\)），
  从训练一开始就改变采样分布。LDAM 的 DRW 给出一个**直接可检验的替代方案**：
  先用自然分布（ERM）训练到学习率退火，再启用 M2 或损失重加权。
  这应作为 PAAT 的一个独立实验臂，而不是默认实现。
- **间隔作为重采样的替代**：LDAM 不改变采样，只把正类的 logit 减去更大的间隔 \(\Delta_+=C/n_+^{1/4}\)。
  对 PAAT 的 BCE，可写成对正类 logit 加间隔的 sigmoid 形式；它保留了原始负例分布，工程改动小于平衡回合。
- **按 PAAT 数据推算的间隔尺度**（**本文推算，非论文实验**）：
  \(n_+=159\) 时 \(n_+^{1/4}=3.55\)；\(n_+=5\) 时 \(n_+^{1/4}=1.50\)。
  若取同一常数 \(C\)，2025 年正类的间隔约为 2024 年的 **2.4 倍**；
  负类（约 \(n_-\approx9{,}500\)）的 \(n_-^{1/4}\approx9.9\) 基本不变。
  这恰好实现「正例越少、决策边界越向负类方向偏移」的目标，但其绝对尺度依赖 \(C\)，必须在训练区内冻结。
- **特征质量警告**：DRW 的核心证据是「早期平衡会损害表示」。PAAT 若从第一个 epoch 就做平衡回合，
  可能重蹈其覆辙。应先跑「自然批次 vs 全程平衡 vs 延迟平衡」三臂，再决定 M2 的启用时点。
- **稀有类过拟合**：LDAM 明确指出重采样少数类容易过拟合；PAAT 的正例有放回重复（2024 年约 3.2 次/回合）
  正是这种风险，应设置重复上限并监控训练/验证差距。

## 不可迁移边界

- **多类 vs 二分类**：LDAM 的间隔是在 \(k\) 类 softmax 上定义的；二分类下可化为 logit 差，
  但「间隔」与「BCE 阈值 0.5」的对应需要重新推导。PAAT 的评测使用固定 0.5 阈值，间隔移动会直接改变正例率与 F1 的平衡点。
- **平衡测试分布假设**：LDAM 的理论界针对平衡测试分布（每类等权）。PAAT 评测的是**自然年度分布**下的 F1，
  2025 年正例率仅 0.05%；两者的目标函数不同，不能把 LDAM 的「平衡误差」结论直接当作 F1 提升。
- **可分与线性分类器假设**：理论推导假设训练集可分、分类器线性；PAAT 使用非线性编码器 + BCE，且年度间不可分。
- **\(n_j\) 的口径**：LDAM 用当前训练集的类样本数；PAAT 若使用回放缓冲，\(n_j\) 应取当前年度还是当前+回放没有定义。
  回放缓冲中的历史正例可能已经不代表当前概念，简单计入 \(n_+\) 会低估稀有程度。
- **指数选择的边界**：\(1/4\) 来自慢速率界，\(1/3\) 来自快速率界；论文没有给出在深度网络中选择哪一个的判据。
  不能把 \(1/4\) 当作固定物理常数。
- **数据集与骨干**：视觉长尾（CIFAR/iNaturalist/ImageNet-LT）与 ResNet；PAAT 是恶意软件行为特征上的小模型，迁移需实测。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| 类间隔定义 Eq. (1)–(2) | §3.1，物理第 4 页 |
| 每类误差界 Theorem 1 / Eq. (4)–(5) | §3.1，物理第 4 页 |
| 二分类最优间隔 Eq. (8) | §3.1，物理第 5 页 |
| 快速率下的 \(n^{-1/3}\) 说明 | §3.1，物理第 5 页 |
| LDAM hinge 形式 Eq. (10)–(11) | §3.2，物理第 5 页 |
| LDAM softmax 形式 Eq. (12)–(13) | §3.2，物理第 5 页 |
| Remark：与重加权的区别 | §3.2，物理第 5 页 |
| 延迟再平衡 Algorithm 1 | §3.3，物理第 6 页 |
| CIFAR 结果 Table 2 | §4.2，物理第 8 页 |
| iNaturalist 结果 Table 3 | §4.3，物理第 9 页 |

## 与相关工作的关系

- 与 Class-Balanced：CB 用有效样本数改**损失权重**，LDAM 用类分布改**决策间隔**；LDAM 论文把 CB 作为主要基线，
  并指出 CB 需要复杂的学习率策略来缓解优化困难（§1、§3.3）。
- 与 Decoupling：Decoupling 把 LDAM+DRW 作为 iNaturalist 上的强基线，并主张「自然采样学表示、再平衡分类器」
  可以达到相近或更好效果；两者在「早期是否应平衡」上一致，见 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]。

## 原始摘要要点

> "We propose a theoretically-principled label-distribution-aware margin (LDAM) loss ... and a simple, yet effective,
> training schedule that defers re-weighting until after the initial stage, allowing the model to learn an initial representation."
