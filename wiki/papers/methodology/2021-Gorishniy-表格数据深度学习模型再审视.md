---
title: "Revisiting Deep Learning Models for Tabular Data"
authors: [Yury Gorishniy, Ivan Rubachev, Valentin Khrulkov, Artem Babenko]
year: 2021
date: 2026-08-20
journal: "Advances in Neural Information Processing Systems 34（NeurIPS 2021），arXiv:2106.11959v5"
source_pdf: "[[raw/papers/methodology/2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data.pdf]]"
sha256: "f2faa32ffd8c15ed8534677f978dc02730fdbe1f94e9c9557ada6aa19163478d"
zotero_item_key: "N4MRAEZF"
bibtex_key: "gorishniy_revisiting_2021"
tags:
  - 表格数据
  - 残差多层感知机
  - FT-Transformer
  - XGBoost
  - 统一基准
  - 类型/论文
key_finding: "作者在 11 个公开表格数据集上以统一数据处理、调参与多种子协议重评深度模型，提出两线性层残差块作为强表格基线；ResNet 平均排名优于普通 MLP，但没有任何深度模型普遍胜过梯度提升树（物理页2至10，公式2、表2至4）。"
method: "在相同数据切分和处理下比较 MLP、表格 ResNet、FT-Transformer、NODE、TabNet 与多种梯度提升树，使用验证集调参、独立测试集评价和15个随机种子，并做架构与效率消融"
baseline: "MLP、ResNet、FT-Transformer、NODE、TabNet、CatBoost、XGBoost、LightGBM"
aliases:
  - Gorishniy2021-TabularDL
  - 表格数据深度学习模型再审视
related:
  - "[[2016-He-深度残差学习]]"
  - "[[2021-Touvron-ResMLP图像前馈网络]]"
  - "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"
---

# 表格数据深度学习模型再审视

> Gorishniy、Rubachev、Khrulkov、Babenko，NeurIPS 2021，arXiv:2106.11959v5，物理页 1 至 25。

## 一句话

这是当前 `resmlp2` 最直接的任务类型近邻：论文把预处理后的表格特征输入两线性层残差块，并证明该结构是值得保留的强深度基线；同时论文明确否定“深度模型普遍胜过梯度提升树”，因此当前实验必须把残差多层感知机视为待证候选，而不是预设优胜方案。

## 题录与原件

- 题名、作者与摘要：物理页 1。
- 会议：NeurIPS 2021，Advances in Neural Information Processing Systems 34。
- arXiv：<https://arxiv.org/abs/2106.11959>。
- 仓库原件：`raw/papers/methodology/2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data.pdf`。
- 原件 SHA256：`f2faa32ffd8c15ed8534677f978dc02730fdbe1f94e9c9557ada6aa19163478d`。
- Zotero 条目键：`N4MRAEZF`；BibTeX 键：`gorishniy_revisiting_2021`。

## 原文问题与方法

- 作者指出既有表格深度学习工作常使用不统一的数据集、切分与调参预算，难以得出可靠排序；目标是建立统一比较并给出简单、可复用的深度基线（物理页 1 至 2）。
- 普通多层感知机由若干 `Dropout(ReLU(Linear(x)))` 层和线性预测头组成（物理页 3，公式 1）。
- 表格 ResNet 的公式（2）为：输入先线性投影；每个残差块执行 `x + Dropout(Linear(Dropout(ReLU(Linear(BatchNorm(x))))))`；最终预测头为 `Linear(ReLU(BatchNorm(x)))`（物理页 3）。
- FT-Transformer 先把每个数值或类别特征变成一个向量标记，再经 Transformer 编码和预测头处理（物理页 3 至 4）。
- 为隔离架构贡献，作者主动排除预训练、额外损失、数据增强、蒸馏、学习率预热与衰减（物理页 5）。

## 评价协议

- 使用 11 个公开数据集、固定的数据切分与相同预处理；只用训练集拟合，验证集选超参数，测试集不参与调参（物理页 5 至 6）。
- 最终报告使用 15 个随机种子；多数深度模型用 AdamW，不使用学习率计划，早停耐心值为 16 个周期（物理页 6）。
- 模型选择采用每个算法 100 次超参数优化；表格 ResNet 的层数搜索范围为 1 至 8，部分数据集扩到 16，另搜索主宽度、隐藏扩张、随机失活、学习率和权重衰减（物理页 18 至 19，表 14）。
- 作者在物理页 13 至 15 给出完整逐数据集结果，并用单侧 Wilcoxon 检验、`p=0.01` 比较模型（物理页 14）。

## FT-Transformer 默认训练协议核查（2026-09-03 补充，逐句带页码）

本节回答"本课题训练 FT-Transformer 用的 AdamW、`lr=1e-4`、`weight_decay=1e-5`、无调度器是否真是原论文默认值"这一具体问题，全部基于 MinerU 逐页核验（禁止 pdftotext）。

### 常数学习率是原论文的主动设计选择，不是遗漏

物理页 5，第 3 节正文（隔离架构贡献的方法论声明）：

> "In our work, we focus on the relative performance of different architectures and do not employ various model-agnostic DL practices, such as pretraining, additional loss functions, data augmentation, distillation, **learning rate warmup, learning rate decay** and many others. While these practices can potentially improve the performance, our goal is to evaluate the impact of inductive biases imposed by the different model architectures."

物理页 6，第 3 节"Neural networks"段：

> "For TabNet and GrowNet, we follow the original implementations and use the Adam optimizer... For all other algorithms, we use the AdamW optimizer... **We do not apply learning rate schedules.** For each dataset, we use a predefined batch size for all algorithms... We continue training until there are patience + 1 consecutive epochs without improvements on the validation set; we set patience = 16 for all algorithms."

即：无学习率预热、无学习率衰减、无调度器，是作者为"公平隔离架构贡献"而**主动排除**的模型无关训练技巧之一，与预训练、数据增强、蒸馏并列，而非配方缺失或论文没讨论。训练时长由早停（patience=16）而非固定轮数决定，对全部被比较算法（含 GBDT 之外的全部深度模型）统一适用。

### 默认优化器数值（Table 12，物理页 18，§E.2）

> "Table 12: Default FT-Transformer used in the main text." ——Layer count 3；Feature embedding size 192；Head count 8；Activation & FFN size factor (ReGLU, 4/3)；Attention dropout 0.2；FFN dropout 0.1；Residual dropout 0.0；Initialization Kaiming；Parameter count 929K（100 个数值特征时的取值）；**Optimizer AdamW；Learning rate 1e-4；Weight decay 1e-5**（对 Feature Tokenizer、LayerNorm 与偏置取 0.0）。

**本课题代码 `thesis/experiments/llm_probe/tools/ch3_ft_transformer_field_token_protocol_a.py` 中 `OPTIMIZER_CANDIDATES` 的 "FT-Transformer-论文默认优化器"（`learning_rate=1e-4`、`weight_decay=1e-5`）与本表逐字相符，核实为真，非臆造。**

正文补注（物理页 18）："the configuration is a result of an 'educated guess' and we did not invest much resources in its tuning"——即该默认配方本身是作者的经验估计，并非经过系统调参得到的最优值。

### 调参空间与"sqrt(1e-5×1e-3)=1e-4"重合的核验

Table 13（物理页 18，§E.2，"FT-Transformer hyperparameter space. Here (A) = {CA, AD, HE, JA, HI} and (B) = {AL, YE, CO, MI}"）：

| 参数 | (A) 数据集组 | (B) 数据集组 |
| --- | --- | --- |
| 学习率 | LogUniform[1e-5, 1e-3] | LogUniform[3e-5, 3e-4] |
| 权重衰减 | LogUniform[1e-6, 1e-3]（两组相同） | 同左 |

组 (A) 含 HI（Higgs Small，对应官方仓库路径 `output/higgs_small/ft_transformer/tuning/0.toml`，与本课题代码 `OFFICIAL_TUNING_SPACE_FILE` 常量指向的文件一致），其学习率调参区间精确为 `[1e-5, 1e-3]`，几何中位 `sqrt(1e-5×1e-3)=1e-4` 恰与 Table 12 默认学习率重合——**本课题代码注释"已知，不是笔误"核实成立**：这是官方调参空间几何中位与官方默认值的真实巧合，非本课题编造。权重衰减调参空间 `[1e-6,1e-3]` 的几何中位 `sqrt(1e-6×1e-3)=3.1622776601683794e-05`，与代码 "FT-Transformer-官方调参空间对数中位优化器" 候选的 `weight_decay` 取值逐位相符。

### 训练轮数与批量

- 无固定 epoch 上限，由早停（patience=16）决定训练时长（物理页 6，见上）。
- 批量大小按数据集预先指定（"predefined batch size for all algorithms"，物理页 6），全文未给出跨数据集统一的单一数值，本核查未进一步定位各数据集具体批量表格（非本次核查重点，如需可另行核实附录 D 数据集统计表）。

### 与后续同谱系工作的横向印证

XTab（2023，`wiki/papers/methodology/2023-Zhu-XTab跨表预训练.md`）与 TabM（2025，`wiki/papers/methodology/2025-Gorishniy-TabM参数高效集成.md`）均延续"AdamW + 无学习率调度器 + patience=16 早停"的协议；前者预训练与微调阶段的 `lr=1e-4`、`wd=1e-5` 逐字沿用本文 Table 12，并在正文明确标注"Following Gorishniy et al. (2021)"（XTab 笔记，物理页 6）。三篇均出自同一 Yandex 研究团队谱系（Gorishniy / Rubachev 系列作者重叠），构成一个内部一致的方法论传统，而非孤例。

## 关键结果

- 表 2 的聚合平均排名中，FT-Transformer 为 `1.8`，ResNet 为 `3.3`，普通 MLP 为 `4.8`；正文据此把 ResNet 定位为可靠的表格深度学习基线（物理页 7）。
- 没有任何被比较方法在全部数据集上稳定超过 ResNet；作者强调在跨数据集比较时没有普遍优胜者（物理页 7）。
- 调优后的 CatBoost、XGBoost 或 LightGBM 在部分数据集上明显领先深度模型；作者的总判断是深度学习与梯度提升树之间不存在通用赢家（物理页 7 至 8，表 4）。
- FT-Transformer 通常比 ResNet 慢；例如 Yahoo 数据集约有 700 个特征，FT-Transformer 的训练时间约为 ResNet 的 `13.8` 倍（物理页 16，表 10）。
- 在人工数据实验中，作者使用 4 个残差块、嵌入宽度 256、随机失活 0.5、约 82 万参数，说明论文并未提供当前“一块、宽度 139、约 9 万参数”的直接配置先例（物理页 23）。

## 对当前 `resmlp2` 的支持

### 原文直接支持

- 当前块的“预归一化后两次线性变换，再加回输入”与公式（2）的表格残差块属于同一结构家族；这篇论文比图像 ResNet 或 Touvron 的图像 ResMLP 更直接。
- 当前实现采用 `LayerNorm → Linear → ReLU → Dropout → Linear → Dropout → 残差相加`。原文采用 `BatchNorm → Linear → ReLU → Dropout → Linear → Dropout → 残差相加`。因此可将当前实现表述为“Gorishniy 表格 ResNet 的预归一化变体”，不能逐字称为原论文实现。
- 论文直接支持把普通 MLP、表格残差网络与调优 XGBoost 放在共同切分和共同选择纪律下比较。

### 本课题推论，仍需实验

- `LayerNorm` 替代 `BatchNorm`、只使用一个残差块、等宽隐藏层、因果前缀融合和可学习实体池化均为本课题实现选择，不由本文验证。
- 当前约 9 万参数的等预算合同是为公平比较制定的本课题约束，不是论文结论。
- 论文的 15 种子与大规模超参搜索属于正式广泛基准；当前源年三折单种子资格门只能用于快速否决，不能据此复刻其统计强度。

### 不能支持的论断

- 不能声称残差多层感知机必然优于 XGBoost；论文恰好强调两类方法没有普遍赢家。
- 不能支持加密流量、跨年度迁移、实体级平均精确率、固定假阳率检出率、CPA 或 ELP 的效果。
- 不能把本文的 FT-Transformer 优势迁移为本课题必须使用 Transformer；高特征数数据上的显著时间成本也需要纳入预算。

## 证据等级

- 原件级别：完整论文与附录，25 个物理页，逐页核验。
- 可支撑：表格两线性层残差块、统一切分和调参纪律、ResNet 是强深度基线、深度模型不普遍胜过梯度提升树。
- 仅可推论：预归一化残差块可能缩小当前普通多层感知机与 XGBoost 的差距。
- 实验待证：`resmlp2` 在 LSPR23 源年三折折外门上的方向、幅度、训练稳定性和资源成本。
