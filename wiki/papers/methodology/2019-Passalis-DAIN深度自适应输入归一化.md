---
title: "Deep Adaptive Input Normalization for Time Series Forecasting"
authors: [Nikolaos Passalis, Anastasios Tefas, Juho Kanniainen, Moncef Gabbouj, Alexandros Iosifidis]
year: 2019
date: 2026-09-01
journal: "IEEE TNNLS（2020 刊出）；本地原件为 arXiv:1902.07892"
source_pdf: "[[raw/papers/methodology/2019-Passalis-DAIN-Deep-Adaptive-Input-Normalization.pdf]]"
sha256: "83338bed88a70332fad68651aacb82b5c4618d196f7d1451c8de21181b14ae21"
arxiv_id: "1902.07892"
tags:
  - 自适应归一化
  - 分布偏移
  - 输入层
  - 类型/论文
key_finding: "DAIN 用三层可学习算子（移位 α(i)=W_a·a(i)、缩放 β(i)、σ 门控 γ(i)）对每个输入实例做自适应归一化（物理第 2–3 页式 1–9），条件量全部来自当前实例自身摘要而非全局统计；明言全局 z-score 是其特例，并在金融时序上验证对非平稳数据的增益。"
method: "实例摘要 a(i)（式 2）→ 线性移位（式 3）→ 更新摘要出缩放 → 非线性门控（式 7–8）；与主网络端到端联合训练（式 9）"
aliases:
  - DAIN
  - Passalis2019-DAIN
related:
  - "[[2022-Kim-RevIN可逆实例归一化]]"
  - "[[2016-Bartos-优化不变表示检测未见恶意软件变种]]"
---

# DAIN：条件量来自实例自身的自适应输入归一化

> Passalis, Tefas, Kanniainen, Gabbouj, Iosifidis，IEEE TNNLS。

## 全文证据（物理页码）

- 第 2–3 页式 (1)–(9)：`x̃_j = (x_j − α(i)) ⊘ β(i)` 后过 σ 门控层；`α(i)=W_a a(i)`，摘要 `a(i)` 与 `c(i)` 均由当前实例计算；全局 z-score 是 `α(i)=α, β(i)=β` 的特例。

## 与本课题的关系

对应 M-E 弱点 (b)「条件变量本身跨域漂移」：DAIN 与 RevIN 同线——**归一化/条件量应来自当前实例（实体/片段）自身，而非训练期冻结的全局常数**。M-E 的 `s_e` 分母 `log(1+C)`、`log(1+D)` 是源年冻结常数，`c` 源年内部均值已漂移 3.8 倍，正落在该文献线反对的构造上。也是候选 B（实体条件不变式归一化）的方法论组件之一。

## 边界

- 金融时序预测域；三层算子对分类任务与 FT 分词器挂载点需重新设计；未涉及实体分组结构。
