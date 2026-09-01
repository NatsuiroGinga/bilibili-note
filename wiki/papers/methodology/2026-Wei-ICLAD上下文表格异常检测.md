---
title: "ICLAD: In-Context Learning for Unified Tabular Anomaly Detection Across Supervision Regimes"
authors: [Jack Yi Wei, Narges Armanfard]
year: 2026
date: 2026-09-01
journal: "arXiv preprint 2603.19497v1（2026-03-19，McGill/Mila）"
source_pdf: "[[raw/papers/methodology/2026-ICLAD-InContext-Tabular-Anomaly-Detection.pdf]]"
sha256: "ef5adc1912c789cecfe4e66c0570244dea53a5e798ffac980e64ce7cfa5ac827"
arxiv_id: "2603.19497"
tags:
  - 表格异常检测
  - 上下文学习
  - FiLM
  - 条件化
  - 类型/论文
key_finding: "TabPFN 式表格异常检测基础模型；对支持集样本用 FiLM 注入标签条件（物理第 9 页）：x̃ = (1+γ(c))⊙x + β(c)，γ、β 为线性映射，且「Unlabeled samples correspond to c = 0, for which FiLM reduces to the identity transformation」——条件缺失时恒等退化已作为实现约定发表。"
method: "元学习训练的 in-context 异常检测 transformer，统一 one-class/无监督/半监督三种监督制度；标签经查表嵌入后走 FiLM 调制支持样本嵌入"
aliases:
  - ICLAD
  - Wei2026-ICLAD
related:
  - "[[2018-Perez-FiLM通用条件化层]]"
---

# ICLAD：表格异常检测中的 FiLM 条件化与恒等退化

> Wei, Armanfard，arXiv:2603.19497v1。预印本，未见同行评审版；引用时注明。

## 全文证据（物理页码）

- 第 9 页「FiLM Label Conditioning」：`x̃ = (1 + γ(c)) ⊙ x + β(c)`；未标注样本 `c = 0` 时 FiLM 退化为恒等变换（逐字核对）。

## 与本课题的关系

这是 M-E 最近的已发表结构近邻：表格异常检测 + FiLM 条件调制 + 「条件缺失 → 恒等退化」。差异在条件变量（ICLAD 用标签嵌入，M-E 用严格过去实体统计）与挂载点（支持集嵌入 vs 数值分词器）。它证明 M-E 的零门退化命题在近邻文献中只是一条实现约定，不构成理论贡献；同时也证明「FiLM 进表格异常检测」的组合空间已开始被占用（2026-03）。

## 边界

- 预印本证据等级；其实验为跨数据集监督制度泛化，非跨年时间漂移。
