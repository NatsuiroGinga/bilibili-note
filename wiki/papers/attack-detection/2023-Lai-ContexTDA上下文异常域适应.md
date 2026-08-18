---
title: "Context-aware Domain Adaptation for Time Series Anomaly Detection"
authors: [Kwei-Herng Lai, Lan Wang, Huiyuan Chen, Kaixiong Zhou, Fei Wang, Hao Yang, Xia Hu]
year: 2023
date: 2026-08-12
journal: "SDM 2023"
source_pdf: "[[raw/papers/attack-detection/2023-Lai-Context-Aware-Domain-Adaptation-Time-Series-Anomaly.pdf]]"
zotero_key: EU4B756L
zotero_key: EU4B756L
tags: [异常检测, 时间序列, 域适应, 强化学习, 负迁移, 类型/论文]
key_finding: "ContexTDA 通过 DQN 选择源/目标上下文窗口以缓解异常少数分布负迁移，但依赖连续时序语义、完整目标序列和多损失奖励。"
method: "LSTM 自编码器、MMD/域对抗、DQN 上下文窗口策略"
baseline: "AE、RDC、VRADA、SASA 与随机上下文策略"
aliases: [ContexTDA, Lai2023-ContexTDA]
---

# ContexTDA：上下文异常域适应

## 论文原结论

第 3.1 节把源/目标 LSTM 表示拼为状态，动作为下一时间点两域窗口长度；公式（3.5）的奖励是源加权分类、源/目标重构、对齐和负号域判别损失的组合倒数。异常分数为源分类置信与目标重构误差乘积。表 3 对四种奖励项做消融。

## 可迁移机制

论文明确指出普通 MMD/对抗联合在上下文不匹配时会对异常少数分布负迁移；这支持把异常保护和时序合法性列为门禁，而非支持完整方法迁入。

## 本课题推论

候选 B 的时间机制已改变输出但恶化目标排序，且树模型显著领先序列模型，因此上下文窗口、时间衰减或强化学习采样不进入前三候选。

## 不可直接声称

论文评价为宏平均 F1 与 ROC-AUC，数据异常率 4.1%—15%，并用完整目标序列联合训练；若 LSPR 行不是连续同实体序列，窗口动作没有因果语义。

## 待验证

只在未来证明存在合法连续实体序列且树锚残差有正信号后，才重开上下文机制；当前暂缓。

## 文献信息

- DOI：10.1137/1.9781611977653.ch76
- arXiv：2304.07453
