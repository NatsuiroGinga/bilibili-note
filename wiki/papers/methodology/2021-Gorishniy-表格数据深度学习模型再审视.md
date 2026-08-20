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
