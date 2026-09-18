---
schema: paper-note-search/v1
title: "LLMs for Domain Generation Algorithm Detection"
title_zh: "用于域生成算法检测的大语言模型"
authors: [Reynier Leyva La O, Carlos A. Catania, Tatiana S. Parlanti]
year: 2024
date: 2026-09-07
journal: "arXiv preprint"
doi: null
arxiv_id: "2411.03307"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2024-Lopez-LLM-DGA-Detection.pdf]]"
tags: [DGA检测, Llama3, 指令微调, 未见家族, 类型/论文]
aliases: [LLM DGA, Lopez2024]
tasks: [DGA二分类, 已见和未见家族评价]
datasets: [54个训练家族, 14个测试独有家族, 新良性域]
methods: [Llama3-8B ICL, Llama3-8B SFT, LA Bin07]
metrics: [Accuracy, Precision, Recall, F1, FPR, 处理时间]
key_finding:
  - "已见54家族上SFT Llama3 F1 0.92、FPR 0.04，LA Bin07 F1 0.88、FPR 0.09；推理3.50秒对0.03秒（PDF物理第18至23页，表8）。"
  - "14个未见家族上Llama3 F1降至0.67，低于LA Bin07的0.80；部分家族F1接近0，说明容量不等于开放集泛化（PDF物理第21至24页，表7至9）。"
supports: ["大模型不是DGA未见家族的默认强基线", "未见家族必须逐家族报告"]
cannot_support: ["跨年泛化", "实时网关部署", "Llama3优于轻量模型"]
related: ["[[2024-Cebere-DGA检测九项假设审计]]", "[[2026-Lee-DRIFT-DGA-Temporal-Drift]]"]
---

# LLM DGA 检测

> 页码锚点：本地PDF共34页；数据和协议见 PDF 物理第11至16页，已见/未见家族结果见 PDF 物理第18至24页。

## 一句话

Llama3微调在已见家族改善总体指标，却在14个未见家族上落后轻量LSTM注意力模型，并慢约两个数量级。

## 论文可以支持

- 模型容量不是未见家族稳健性的替代证据。

## 论文不能支持

- 不能用其4%至5% FPR证明低误报部署，更不能证明时间漂移稳健。

## 实验结果与负证据

- 已见家族：Llama3/LA Bin07 F1 `0.92/0.88`。
- 未见家族：Llama3/LA Bin07 F1 `0.67/0.80`；Llama3耗时 `3.50s`，轻量模型 `0.03s`。

## 与本课题的关系

不把Llama3设为C00；只作为“更大模型仍不能解决未见家族”的外部参照。

## 文献信息

- <https://arxiv.org/abs/2411.03307>
