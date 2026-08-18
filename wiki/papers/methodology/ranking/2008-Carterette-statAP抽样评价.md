---
title: "Evaluation Over Thousands of Queries"
authors: [Ben Carterette, Virgil Pavlu, Evangelos Kanoulas, Javed A. Aslam, James Allan]
year: 2008
date: 2026-08-13
journal: "Proceedings of the 31st Annual International ACM SIGIR Conference，651–658"
source_pdf: "[[raw/papers/methodology/ranking/2008-Carterette-statAP-SIGIR.pdf]]"
sha256: "c5ebe7e09014089e3e11a4f85f35566441d34f7e3ad1fbbdf71722a5d8d20f23"
tags:
  - 信息检索评价
  - 平均精确率
  - 不等概率抽样
  - 类型/论文
key_finding: "statAP 用两阶段分层不等概率抽样与包含概率估计不完整判断下的 AP；Horvitz–Thompson 直接保证的是相关总体总量组成部分，而最终 statAP 是广义比率估计，不能仅凭组成部分无偏就宣称比率本身严格无偏。"
method: "先按排名先验抽层、再在层内无放回抽文档，以包含概率校正相关文档总数和各相关秩的精确率，最后构造 statAP/statMAP。"
baseline: "最小测试集方法、深度池化评价及完整判断集合"
aliases:
  - statAP
  - Carterette2008-statAP
---

# statAP：不完整判断下的抽样平均精确率评价

> Carterette 等，2008，SIGIR · 8 个物理页 · DOI `10.1145/1390334.1390445` · Zotero `W6DEX8GX`

## 论文原结论

- 物理第 2 页第 2.2 节把 AP 看作相关文档集合上“相关秩处精确率”的均值。
- 同页采用两阶段分层抽样：先有放回抽层，再按前一阶段命中数在层内无放回抽文档。
- 物理第 2—3 页用一阶包含概率 `π_d` 构造相关文档总数与 `precision@k` 的 Horvitz–Thompson 估计，再用广义比率构造 statAP；并用一阶、二阶包含概率估计方差。
- 该工作是检索系统**评价**与人工相关性判断预算分配，不是梯度训练算法。

## 与本课题的关系

- **直接近邻**：说明“AP＋不等概率抽样＋包含概率校正”早已存在，不能宽泛声称首次用 Horvitz–Thompson 处理 AP。
- **数学边界**：Horvitz–Thompson 对总体总量线性估计严格无偏；statAP 最终是估计总量的比率。两个组成估计无偏不推出其比率严格无偏，这与把无偏实体矩代入 AP 复合目标的风险相同。
- **关键差异**：本文抽样的是待人工判断文档，用于估计固定系统的 AP；没有可学习 `p`、实体包、模型梯度或实体均匀训练测度。
- **不可直接声称**：首次把逆概率校正用于 AP，或“使用 Horvitz–Thompson 权重即可让整个 AP 目标／梯度无偏”。

## 证据记录

- 全文：作者高校主页 PDF，8 页；关键位置为物理第 2—3 页。
- DOI：<https://doi.org/10.1145/1390334.1390445>
- 证据强度：直接占用 AP 评价中的不等概率抽样；不占用本课题训练算法。

