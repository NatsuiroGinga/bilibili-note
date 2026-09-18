---
title: "A Note on \"Assessing Generalization of SGD via Disagreement\""
authors: [Andreas Kirsch, Yarin Gal]
year: 2022
date: 2026-08-28
journal: "Transactions on Machine Learning Research (TMLR)，2022 年 10 月，arXiv:2202.01851v2 [cs.LG]，2022 年 11 月 6 日版本，27 页"
source_pdf: "[[raw/papers/methodology/2022-Kirsch-Note-On-Assessing-Generalization-Disagreement.pdf]]"
sha256: "d9fc4dc0d71c5e1b23285def311b4f78c4248c0730c708305f7737a15cb3fce9"
arxiv_id: "2202.01851v2"
tags:
  - 泛化估计
  - 模型分歧
  - 深度集成
  - 校准
  - 分布偏移
  - 反驳性复现
  - 类型/论文
key_finding: "作者用 25 个 WideResNet-28-10 在 CIFAR-10 上训练并分别在 CIFAR-10（分布内）与 CINIC-10（分布偏移）测试集上评估，发现三种校准误差（ECE、CACE、CWCE）都随分歧率增大而单调恶化，分布偏移下恶化更明显（第 9 页，图 1；第 10 页，第 5 节）；由此得出 Jiang et al. (2022) 定理中“校准误差上界”的实际解释力有限（第 10 页，Conclusion 4），且该方法存在循环论证——要验证分布偏移下是否校准，本身就需要有标签数据（第 2 页；第 10 页）。"
method: "先把 Jiang et al. (2022) 基于假设空间（hypothesis space）的定义与证明改写为标准贝叶斯概率记号，证明 GDE 是类聚合校准在期望意义下的直接推论，证明过程比原文更短；再在 CIFAR-10/CINIC-10（及附录中的 ImageNet/PACS）上做拒识曲线（rejection plot）实验，按预测误差（即分歧率）阈值逐步剔除样本，观察 ECE/CACE/CWCE 与真实测试误差的变化趋势。"
baseline: "Jiang et al. (2022) 的原始理论表述（假设空间视角）与其类聚合校准 CACE 上界结论；实证上对照 Nakkiran & Bansal (2020)、Ovadia et al. (2019) 关于分布偏移下校准恶化的既有观察"
aliases:
  - Kirsch2022-GDE反驳笔记
  - A Note on Assessing Generalization of SGD via Disagreement
related:
  - "[[2022-Jiang-以集成分歧估计泛化误差]]"
  - "[[2025-Gorishniy-TabM参数高效集成]]"
---

# 分歧估计泛化在分布偏移下的失效

> Kirsch, Gal，TMLR 2022（10 月）· arXiv:2202.01851v2 · 27 页

## 一句话

作者用标准概率记号重新证明了 Jiang et al. (2022) 的 GDE 定理（证明更短、更直接），但同时用 CIFAR-10→CINIC-10 与 ImageNet/PACS 的分布偏移实验证明，支撑 GDE 的类聚合校准性质会随分歧率增大而系统性恶化，且在分布偏移下恶化更严重，因此"用分歧率估计测试误差"这一方法在最需要它（无标签、可能有分布偏移）的场景下反而最不可靠，并存在"要验证校准就需要标签"的循环论证。

## 题录

- 题名（逐字抄自第 1 页）：A Note on "Assessing Generalization of SGD via Disagreement"
- 发表：Published in Transactions on Machine Learning Research (10/2022)（第 1 页页眉）；OpenReview：<https://openreview.net/forum?id=oRP8urZ8Fx>（第 1 页）
- arXiv：2202.01851v2 [cs.LG]，2022 年 11 月 6 日（第 1 页左侧竖排标记）
- 原件：`raw/papers/methodology/2022-Kirsch-Note-On-Assessing-Generalization-Disagreement.pdf`
- 代码：<https://github.com/BlackHC/2202.01851>（第 1 页，脚注 1）

## 论文原结论

### 理论简化

- 用贝叶斯参数分布 `p(ω)` 替代原文的假设空间/版本空间视角，把深度集成看作对 `p(ω)` 的有限样本经验估计（第 3 页，第 2 节）。
- 重新定义 GDE（第 5 页，定义 3.2）与类别式/类聚合校准（第 5 页，定义 3.3），并给出比原文更简短的证明：类聚合校准可等价改写为置信度水平集上"真实类别概率分布"与"预测概率分布"测度相等（第 6–7 页，引理 4.2 与定理 4.4 的证明），由此"几乎立即"推出 GDE，作者称此为该定理"直白（trivial）"的根源（第 2 页）。
- 修正 CACE 取值范围：原文称 CACE 可落在 `[0,K]`，本文用三角不等式证明 `CACE ≤ 2`（第 7 页，Conclusion 3），与类别数 K 无关。
- 指出 CACE、CWCE 分别等价于 Nixon et al. (2019) 提出的"static calibration error"与"adaptive calibration error"（含实现细节上的差异）（第 2 页；第 8 页，附录 §B 引用处）。

### 核心实证反驳（第三方复现实验）

- 实验设置（第 9–10 页正文，第 22 页附录 E.1）：在 CIFAR-10 上训练 25 个 WideResNet-28-10 模型（350 个 epoch，SGD，学习率 0.1，动量 0.9，在第 150、250 epoch 各衰减 10 倍），分别在 CIFAR-10 测试集（分布内）与 CINIC-10 测试集（CIFAR-10 + 降采样 ImageNet 同类样本，构成分布偏移）上评估。
- 拒识曲线实验（第 9 页，图 1）：按分歧率（=预测误差）阈值从低到高逐步纳入样本，观察 ECE、CACE（class-aggregated）、CWCE（class-wise）、真实测试误差、以及"GDE 差距"`|TestError − PredictedError|` 的变化。结果显示三种校准误差指标随分歧率增大单调恶化，分布内（CIFAR-10）和分布偏移（CINIC-10）两种情形都如此，且分布偏移下整体更差（第 9 页图 1 标题；第 10 页正文）。
- 关键论断（第 10 页，Conclusion 4）：定理 3.6（即原文定理 4.2）给出的校准误差上界"可能没有预想中那么有解释力，因为校准指标本身会随模型对数据变得更'不确定'而恶化"（原文措辞转述）。
- 反例排除（第 10 页，脚注 7）：作者预先排除了"高分歧样本太少导致曲线看起来变平"的解释——对 CINIC-10，最低阈值分桶已含 5 万样本，之后每个分桶再增约 1 万样本，样本量充足。
- 同时观察到一个不完全对立的现象（第 10 页）：尽管校准指标恶化，"GDE 差距"本身趋于平坦，测试误差与预测误差（分歧率）之间仍呈现"近似线性关系（但带偏置，up to a bias）"——即分歧率作为**排序/趋势信号**仍与误差同向变化，只是作为**校准解释下的无偏点估计**站不住脚。
- 额外数据集验证（第 10–11 页正文，第 22 页附录 E.2）：在 ImageNet（分布内）与 PACS（用 photo 域微调、在 art/sketch/cartoon 域评估，构成分布偏移）上重复同样的拒识曲线实验，观察到与 CIFAR-10/CINIC-10 一致的模式（校准指标随分歧率恶化，分布偏移下更差）；PACS 集成由 ResNet-152-D、BEiT-L/16、ConvNext-L、DeiT3-L/16、ViT-B/16 五种预训练架构各取 5 个模型组成 25 模型集成（第 22 页）。
- 循环论证问题（第 2 页正文；脚注 3 说明该论断是"在阅读本文预印本后，Jiang et al. (2022) 才把它作为注意事项加入 camera-ready 版本"）：要用类聚合校准去约束"分歧率-测试误差"差距，本身就要求在待评估的数据分布（可能已发生偏移）上测量校准，而测量校准需要标签——这与"用无标签数据估计测试误差"的初衷矛盾。
- 直接的实用性质疑（第 10 页）："Given that all these calibration metrics require access to the labels, and we cannot assume the model to be calibrated under distribution shift, we might just as well use the labels directly to asses the test error."（原文，第 10 页，第 5 节末段）。
- 全文结论（第 11 页，第 7 节）：概率化证明更简洁，但实证上分布偏移下校准显著恶化，"我们需要警惕循环论证"（原文措辞转述）。

## 本课题可迁移机制

- **拒识曲线（rejection plot）是可直接复用的诊断工具**：按分歧率阈值排序、逐步纳入样本并观察校准误差与真实误差的变化，可直接套用到 TabM 的 k=32 成员分歧上——用 LSPR23（分布内）与 LSPR24（真实时间偏移）分别画拒识曲线，检验分歧率-AP 关系是否也呈现"分布偏移下恶化"的同一模式。
- **区分"分歧作为序数信号"与"分歧作为无偏点估计"的证据强度不同**（第 10 页原文明确讨论）：即使校准恶化，分歧率与测试误差仍可能保持近似线性的排序关系（"up to a bias"）。这为 M-C 采用"分歧率触发复核/加权降权"（序数用途）而非"分歧率直接换算误差数值"（点估计用途）提供了直接的文献支持。
- **CACE ≤ 2 的修正与 CACE/CWCE 同 Nixon 静态/自适应校准误差的等价关系**（第 7–8 页）是通用的校准度量工具，若本课题需要报告 TabM 集成的校准误差，可直接复用该定义与实现，无需重新发明指标。

## 不可直接声称的内容

- 本文的分布偏移实验全部是图像域（CIFAR-10→CINIC-10、ImageNet→PACS 子域），未涉及表格数据、时间序列或网络流量特征，不能把具体数值（如 CACE 恶化幅度）直接套用到 TabM 在 LSPR23→LSPR24 上的表现，只能作为"校准会因分布偏移恶化"这一定性机制的类比证据。
- 本文集成规模为 25 个独立训练的完整模型（第 22 页），与 TabM 的 k=32 单次前向的隐式子网络集成在训练方式和成员间相关性结构上不同，不能假定二者的校准退化幅度相同。
- "GDE 差距趋于平坦、近似线性关系"的观察（第 10 页）仅是本文对自建 CIFAR-10/CINIC-10 实验的描述性发现，作者本人未将其上升为可证明的定理，本课题若要复用该"排序信号仍然有效"的论断，须在自身数据上重新验证，不能直接引用为本文的普适结论。

## 疑问 · 待验证

- 本文未回答"分歧率作为排序信号"在多大的分布偏移幅度下也会失效——PACS 三个子域与 CINIC-10 的偏移幅度是否代表了 LSPR23→LSPR24 的典型偏移量级，本文未给出可比较的偏移度量，需本课题自行标定。
- 本文未测试大规模隐式集成（如 TabM 的 k=32）是否因成员数增多而在偏移下更稳健或反而因参数共享而低估真实的认知不确定性，这是留给本课题的开放问题。

## 可引用的逐字原文（≤15 词，1 处）

- "deep ensemble's calibration can deteriorate as prediction disagreement increases"（第 1 页，摘要）

## 证据记录

- 来源类型：完整论文（27 页，含附录；`pdftotext -layout` 逐页文本核对，`<<<< PAGE N >>>>` 标记与原始页码一致）
- 支持：分布偏移下类聚合校准系统性恶化（图 1，CIFAR-10/CINIC-10，附录 ImageNet/PACS 一致）；GDE 理论表述的概率化简化证明正确
- 限制：图像域实验，未覆盖表格/流量数据；未直接检验大规模隐式集成（如 TabM）
- 论断强度：有支持（分布偏移下类聚合校准恶化、循环论证问题）/ 有支持但需谨慎区分（分歧率排序信号在偏移下部分保留有效性）/ 推论（迁移到 TabM k=32 与加密流量跨年度检测）

## 与 M-C 的差量

**有条件支持，条件是把 M-C 限定为序数/触发信号而非无偏点估计。** 本文与 Jiang et al. (2022) 的 PACS 例外组合共同证明：把 TabM 的 k=32 分歧当作"测试误差的无偏点估计"在真实分布偏移（LSPR23→LSPR24 是货真价实的时间漂移）下缺乏理论保障，且本文进一步指出该方法存在循环论证——若要验证当前是否处于"分歧率可信"的区间，本身就需要目标域标签，这与 M-C 想在无标签或标签稀缺的新一年数据上使用分歧信号的初衷直接冲突。但本文同时观察到，即便校准恶化，分歧率与真实误差仍可能保持近似线性的排序关系（第 10 页），这支持把 M-C 降级为"高分歧样本触发人工复核或降权聚合"的序数用途，而非"用分歧数值直接读出预测置信度或误差率"。因此对 M-C 的裁决是：**证据支持"分歧作为漂移触发器/排序信号"，证据削弱"分歧作为无偏误差点估计"；两种用法在正式实验设计中必须分别验证，不能混用同一套证据。**
