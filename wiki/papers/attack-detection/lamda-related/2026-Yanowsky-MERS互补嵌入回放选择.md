---
title: "Leveraging Complementary Embeddings for Replay Selection in Continual Learning with Small Buffers（MERS：小缓冲下互补嵌入的回放选择）"
authors: "Danit Yanowsky, Daphna Weinshall"
year: 2026
date: 2026-04-09
journal: "arXiv preprint（arXiv:2604.08336v2，希伯来大学）"
source_pdf: "raw/papers/attack-detection/lamda-related/2026-Yanowsky-MERS互补嵌入回放选择.pdf"
tags:
  - 持续学习
  - 回放选择
  - 小缓冲
  - 覆盖最大化
  - 类型/论文
key_finding: "把小缓冲回放选样从单嵌入覆盖推广到「监督嵌入 + 自监督嵌入」的多嵌入加权 k-覆盖（贪心保留 (1−1/e) 近似保证），作为即插即用模块替换 ER/ER-ACE/MIR 的缓冲更新规则，在低内存区间显著优于单嵌入选样，且不增加可训练参数。"
---

# MERS: Multiple Embedding Replay Selection

## 证据等级
**在线全文已下载并 MinerU 精读**（arXiv 2604.08336v2，本地 PDF 已入 `raw/`）。**代码未公开**：原文称接收集合后于 GitHub 释放（检索未定位到仓库链接）。

## 方法与设定（原文章节）
- 场景：**类增量（Class-IL）**，Split CIFAR-100 与 Split TinyImageNet；算法载体为 ER / ER-ACE / MIR（§1、§3）。
- 机制：联合**监督嵌入（分类器倒数第二层）**与**自监督嵌入（SimCLR）**，用 k-NN 非参密度估计自动对齐各嵌入尺度并加权，构成"加权最大 k-覆盖"问题，贪心求解（§3、§4 理论）。
- 定位：**drop-in 模块**——无架构改动、不增加可训练参数、不增加回放量，只替换 buffer update rule（§1 摘要段）。
- 结果：在低缓冲区间一致优于 SOTA 选样（Split CIFAR-100 / TinyImageNet），增益在低内存区间最明显。

## 三问
1. **能否在固定 200 条预算下运行？** **能（机制上）**。目标是固定内存预算下的选样，原文强调"低内存区间增益最大"。
2. **能否挂 MLP？** **受限**。虽为架构无关的 drop-in 模块，但**依赖一个自监督嵌入（SimCLR）**。在 4,561 维稀疏二值表格特征上，SimCLR 需要设计正负样本增强（图像增强不可迁移），这是未解决的问题；若只用监督嵌入则退化为普通覆盖选样。
3. **有无公开代码？** **暂无**（原文称接收集合后释放；检索未找到链接）。

## 与本文第三章的关系
- 属"缓冲选样（存什么）"家族的最新形态（覆盖/多样性派），与本文的"年度配额 + 类内分层"同属**选样/分配**轴，是当代对照的合适候选。
- 但作为**可跑基线**的可实施性低于 Seo 2025 / CSReL：无代码 + SSL 嵌入依赖。

## 不能直接声称
- 不能声称其增益来自"多嵌入"而可直接移植到表格数据；表格上 SSL 嵌入是否可得未验证。
- 原文实验全为图像 Class-IL，非 LAMDA / 非 Domain-IL。
