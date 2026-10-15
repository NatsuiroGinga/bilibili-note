---
title: "Learning Dynamic Representations via an Optimally-Weighted Maximum Mean Discrepancy Optimization Framework for Continual Learning（OWMMD：最优加权 MMD 持续学习）"
authors: "KaiHui Huang, RunQing Wu, Fei Ye, Jinhui Shen, Hanyi Zhang, Lingting Ge, Jinyu Guo"
year: 2025
date: 2025-01-21
journal: "Knowledge-Based Systems 337:115419（2025）；arXiv:2501.12121v5"
source_pdf: "raw/papers/attack-detection/lamda-related/2025-Huang-OWMMD最优加权MMD持续学习.pdf"
tags:
  - 持续学习
  - 特征匹配
  - MMD
  - 记忆预算
  - 类型/论文
key_finding: "用「多层特征匹配（度量学习表示变化）+ 自适应正则权重」抑制遗忘，在缓冲仅 200 的 CIFAR-100 上 Class-IL 达 67.74%（优于 DER++ 64.88、ER 44.79、GEM 25.54）；缓冲 500/5120 分别为 75.29/86.33，是固定小缓冲的一档当代对照读数。"
---

# OWMMD: Optimally-Weighted MMD for Continual Learning

## 证据等级
**在线全文已下载并 MinerU 精读**（arXiv 2501.12121v5；期刊版 Knowledge-Based Systems 115419, 2025）。**代码未定位**（检索未找到 GitHub 链接）。

## 方法与设定（原文章节）
- 场景：Class-IL / Task-IL，CIFAR-10/100、Tiny-ImageNet、Cars-196、Cub-200、ImageNet-R；骨干 **ResNet18**；记忆用蓄水池采样。
- 机制：多层特征匹配（MLFMM，不只对齐最终输出，而对齐多层特征表示）+ 自适应正则优化（ARO，按每层重要性自动加权，避免过正则）；额外有 PTM(ViT) 扩展版（OWMMD-PTMs）。
- 缓冲读数（表：`200/500/5120` 列）：OWMMD Class-IL `67.74 ± 1.06 / 75.29 / 86.33`；对比 DER++ `64.88 / 72.70 / 85.24`、DER+++Refresh `65.39 / 73.88 / 85.98`、ER `44.79 / 57.74 / 82.47`、GEM `25.54 / 26.20 / 25.26`、A-GEM `20.04 / 22.67 / 21.99`、GSS `39.07 / 49.73 / 67.27`、iCaRL `49.02 / 47.55 / 55.07`。缓冲 200→5120，OWMMD Class-IL 提升 18.59 点。

## 三问
1. **能否在固定 200 条预算下运行？** **能**。缓冲 200 是原文明确报告的一档（本文同容量）。方法为特征匹配**正则项**，不增加存储。
2. **能否挂 MLP？** **能（机制上）**。MLFMM 是逐层特征距离正则，架构无关；本文为 MLP，可逐层施加。原文用 ResNet18 但未绑定卷积假设（其 PTM 版换 ViT 仍有效，说明与具体骨干解耦）。
3. **有无公开代码？** **未定位**（无确认的 GitHub 仓库）。

## 与本文第三章的关系
- **固定小缓冲（200）的当代正则类对照**：与本文回放机制正交（一个改特征/参数约束，一个改缓冲分配/复用），可作"同样只给 200 条时，非回放路线能到多少"的参照。
- 其缓冲 200 的 Class-IL 表格给出 ER/DER++/GEM/A-GEM/iCaRL/GSS 在同一 200 预算下的读数——**对本文"200 条预算下方法排序"有直接参考价值**（但为 CIFAR-100，非 LAMDA）。

## 不能直接声称
- CIFAR-100 缓冲 200 的 67.74% 不可搬到 LAMDA；数据集与任务类型不同。
- 无代码，实施需自写；其实验为 5 任务/10 任务 Class-IL，非年度 Domain-IL。
