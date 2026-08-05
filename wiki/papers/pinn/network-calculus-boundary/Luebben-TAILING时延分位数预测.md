---
title: "TAILING：面向分组时延尾部的分位数预测"
authors: [Ralf Lübben, Amr Rizk]
year: 2023
date: 2026-07-30
journal: "IEEE ICC 2023"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2023-Luebben-TAILING-Delay-Quantiles.pdf]]"
key_finding: "历史分组时延可用于预测未来分组的条件时延分位数，但方法要求可观测到达与离开时间或往返时延，只给逐分组点式分位数，不提供样本路径网络演算保证。"
tags: [网络测量, 分位数回归, 时延预测, 类型/论文]
aliases: [Luebben2023TAILING, TAILING]
---

# TAILING：面向分组时延尾部的分位数预测

## 一句话

论文说明未知到达和服务分布下仍可经验预测时延尾部，但其输入是历史分组时延，而不是 GeNIS 或 TQH-C2 当前共享视图中的流级聚合统计。

## 方法与证据

- PDF 第 2 页式（1）至式（2）用到达时间与离开时间之差定义分组时延，并预测给定历史时延后未来第 `k` 个分组的条件分位数。
- PDF 第 2 至 3 页以分位数损失训练前馈网络或长短期记忆网络；未来到达间隔可见时预测更紧。
- PDF 第 6 页明确把结论限定为逐分组点式预测，样本路径联合边界仍属未来工作。

## 本课题裁决

R3 可把分位数回归作为到达超额或时延代理的弱对照，但不能把它写成共形覆盖或网络演算保证。公开数据若没有同一观测点的到达－离开对或往返时延，就不得训练服务或时延分位数头；此时只能保留到达包络。

## 文献信息

- DOI: https://doi.org/10.1109/ICC45041.2023.10279762
- 作者原件: https://ralfluebben.de/publication/luebben-tailing/paper_submitted.pdf
- Zotero: `73IP37N5`
