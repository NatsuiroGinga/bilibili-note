---
title: "表格深度学习中 MLP 的优化器基准（15 种优化器 × 17 数据集）"
authors: [Yury Gorishniy, Ivan Rubachev, Dmitrii Feoktistov, Artem Babenko]
year: 2026
date: 2026-10-15
journal: "arXiv 2604.15297（Yandex / HSE）"
source_pdf: "[[raw/papers/methodology/2026-Gorishniy-表格深度学习中MLP优化器基准.pdf]]"
tags: [优化器, 表格深度学习, MLP, AdamW, SGD, 消融基准, 类型/论文]
key_finding: "统一协议下 15 种优化器 × 17 个表格数据集 × MLP 家族：AdamW 是强基线，SGD+动量在多数数据集上劣于 AdamW；Muon 一致最好，AdamW+EMA 与 Schedule-Free AdamW 是简单有效替代。表格优化器选择此前从未被系统检验。"
---

# 表格深度学习中 MLP 的优化器基准

## 全文核验结论

- 动机：表格 DL 的架构被大量研究，但**优化器选择从未被系统检验**，AdamW 是事实默认（Abstract，物理第 1 页）。
- 协议：17 个数据集（含 TabReD 工业集，**时间切分**）、15 种优化器、MLP / MLP† / TabM 家族；每个优化器**独立调参**（Optuna TPE，同调参预算），**10 个随机种子**重训；分类用交叉熵，10 个种子取均值；用 Welch t 检验（α=0.05）判定 win/tie/loss（§3.1，第 2 页）。
- 主结论（Figure 1，Table 1）：**Muon 一致最好**；**Schedule-Free AdamW 与 AdamW+EMA** 一致优于 AdamW；多数其余方法（NAdamW/RAdam/ADOPT/Adan/AdaBelief/Cautious/AdEMAMix/Lion/Signum/SOAP）与 AdamW 无可靠差异。
- **SGD 基线实测（Table 10，第 8–11 页，逐数据集）**：MLP[SGD] 在多数数据集劣于 MLP[AdamW]，例如 Diamond `0.1590` vs `0.1380`（↓差）、Churn `0.8530` vs `0.8591`、Higgs `0.7137` vs `0.7218`、Weather `1.5505` vs `1.5242`；仅 Microsoft 一项 SGD 略优（`0.7501` vs `0.7473`）。
- 表格数据常含二值特征（Table 4 的 `#Bin` 列，如 Homesite `23`、Sberbank `17`；最多 `#Num` 984），但**不含 4561 维极端稀疏二值输入**。
- 明确限制：纯经验，未解释 Muon 为何有效；不含基础模型（§4 Limitations，第 3 页）。

## 对本课题的合法映射

- 这是「**换优化器是否能在表格 MLP 上可靠带来增益**」这一问题的**直接、高预算实测**：结论是 AdamW 类自适应方法在表格 MLP 上普遍优于 SGD+动量（R1 的调用对象），而更强的替代（Muon/EMA）需要额外训练开销。
- 与本课题协议兼容性最好的一篇：可挂四层 MLP（其调参空间为 `#layers ∈ [1,6]`），代码公开。

## 原创边界与不能直接声称

- 不含极端稀疏二值（0/1、绝大多数位为 0）输入，也未覆盖年度顺序到达的持续学习；不能据本文声称其结论在 4561 维稀疏二值 + 年度漂移下同样成立。
- 未报告任何「损失停在 ln2」类现象，也不解释首年不收敛机制。

## 证据记录

- 全文状态：已下载并核验（Abstract、§3、Table 1/2/4/10）。
- 稳定标识：arXiv `2604.15297`；代码 `https://github.com/yandex-research/tabular-dl-optimizers`。
- 课题角色：Q1「稀疏/表格输入下 SGD vs 自适应优化器」的关键判别证据；Q4「表格优化器实践」证据。
