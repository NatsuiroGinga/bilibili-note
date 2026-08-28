---
title: "Fine-grained Attention in Hierarchical Transformers for Tabular Time-series"
authors: [Raphael Azorin, Zied Ben Houidi, Massimo Gallo, Alessandro Finamore, Pietro Michiardi]
year: 2024
date: 2026-08-28
journal: "KDD 2024 MiLeTS Workshop"
source_pdf: "[[raw/papers/methodology/ft-mechanisms/2024-Azorin-Fieldy-Fine-Grained-Tabular-Time-Series.pdf]]"
sha256: "f02a6748254446bafd35841ddd0dd70deb6a49844e6dd007e2d4634fc7177ba8"
arxiv_id: "2406.15327"
tags: [序列表格, 跨行注意力, 跨列注意力, 贷款违约, 类型/论文]
key_finding: "Fieldy 同时做行向和列向字段上下文化，再用第二级 Transformer 关联全部字段；它在客户历史贷款违约任务上直接以 AP 评价，进一步压缩了“实体历史注意力”的新颖性空间。"
zotero_status: "未操作：本轮 Zotero 本地 API 未运行"
---

# Fieldy：跨行跨列细粒度注意力

## 题录与源码

- KDD 2024 第十届 MiLeTS Workshop，9 个物理页；arXiv `2406.15327`。
- 官方源码：<https://github.com/raphaaal/fieldy>。

## 全文证据

- 物理第 3–4 页图 2 与方法节：第一级分别进行行向和列向注意力，拼接字段表示；第二级 Transformer 让所有字段再次交互。
- 贷款违约任务按客户标识聚合历史交易；长度 10 的连续交易作为输入，指标为 AP（物理第 4–5 页）。
- 表 3 在等参数条件下比较 FT、Tabbie、行/列 TabBERT 和 Fieldy；贷款 AP 分别约 `0.44/0.39/0.44/0.46/0.48`，但标准差 `0.05–0.07`，差值未显示稳定显著性（物理第 5 页）。
- 表 4 消融两级容量分配、行位置和列位置 embedding（物理第 6 页）。

## 新颖性边界

- 已占用：实体历史表上的跨行、跨列、全字段细粒度注意力；FT 扁平化时序输入对照；实体任务用 AP 评价。
- 未覆盖：严格因果单流检测、当前流查询独立只读记忆、低误报排序训练和 LSPR 跨年度隔离。
- D1 不能以“跨历史字段注意力”为首创，只能以单向因果记忆接口与 FT 结构差量立论。
