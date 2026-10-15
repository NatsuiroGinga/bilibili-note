---
title: "大规模预训练是良好域泛化的秘密吗？"
authors: [Piotr Teterwak, Kuniaki Saito, Theodoros Tsiligkaridis, Bryan A. Plummer, Kate Saenko]
year: 2025
date: 2026-10-15
journal: "ICLR 2025（arXiv 2412.02856）"
source_pdf: "[[raw/papers/methodology/2025-Teterwak-Large-Scale-Pretraining-DG.pdf]]"
tags: [域泛化, 预训练, 基准协议, DomainBed-OOP, 类型/论文]
key_finding: "近年域泛化基准分数提升主要来自更强预训练而非新算法：提出 Alignment Hypothesis（最终 DG 表现取决于图像与类标签文本嵌入的对齐度），并给出 DomainBed-OOP（域外预训练）与 DomainBed-IP（域内预训练）两个新划分，多数 DG 方法在 OOP 上失效。"
---

# 大规模预训练是良好域泛化的秘密吗？

## 全文核验结论

- 问题：近年 DG 方法把「强预训练骨干 + 少量源域微调」的分数提高，**不清楚是 DG 方法真的进步，还是更强预训练的结果**（摘要，物理第 1 页）。
- 提出 **Alignment Hypothesis**：最终 DG 表现高，当且仅当图像与类标签文本嵌入的对齐度高；实验证实该假设，并以其为分析工具（摘要，第 1 页）。
- 新划分（摘要、正文）：
  - **DomainBed-IP**（In-Pretraining）：目标域出现在预训练数据中；
  - **DomainBed-OOP**（Out-Of-Pretraining）：目标域不在预训练数据中。
  - 结论：所有被评 DG 方法在 **DomainBed-OOP** 上吃力，而较新方法在 **DomainBed-IP** 上出色；因此基准分数提升可能只是「目标域落在预训练数据内 + 正则化更强」所致（第 1 页）。
- 释放 `DomainBed-OOP` 数据集（huggingface `PTeterwak/DomainBed_OOP`，第 1 页）。

## 对本课题的合法映射

- 是对 Gulrajani 结论的**第三类后续**：新协议变体——把「预训练数据是否包含目标域」显式分离。
- 对本课题的直接警示：若骨干用了大规模预训练，且目标年份的样本特征与预训练分布重叠程度不同，则「方法增益」可能被预训练对齐度混淆。第四章须控制这一点（例如固定骨干、显式报告目标域是否落入预训练分布）。
- 与年度序列的类比：时间上「越接近训练期的年份」越像 IP、「越远的未来年份」越像 OOP；本文提示应按时间外推难度分层报告，而非只报平均。

## 原创边界与不能直接声称

- 本文域为视觉多源 DG（图像-文本对齐），**不涉及**表格特征、安全域或年度序列；Alignment Hypothesis 依赖图文嵌入，**不能直接搬到**数值特征恶意软件检测。只能借其「协议分层」的思想，不能借其结论数值。

## 证据记录

- 全文状态：已下载并逐页核验（摘要、Introduction、OOP/IP 定义）。
- 稳定标识：arXiv `2412.02856`；ICLR 2025。
- 课题角色：DG 协议演进线索（Gulrajani → 本文 OOP/IP 分层）；第四章「增益 vs 预训练对齐」混淆控制的依据。
