---
title: "端到端统计有效服务曲线"
authors: [Almut Burchard, Jörg Liebeherr, Stephen D. Patek]
year: 2002
date: 2026-07-30
journal: "University of Virginia Technical Report CS-2001-19"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2002-Burchard-Statistical-Service-Guarantees.pdf]]"
key_finding: "有效服务曲线把服务保证改写为带违约概率的非随机下界，并可在附加假设或修订定义下串联，但并不提供从部分观测学习服务曲线的方法。"
tags: [PINN, 网络演算, 随机服务曲线, 类型/论文]
aliases: [Burchard2002, Statistical Service Guarantees]
---

# 端到端统计有效服务曲线

## 一句话

论文建立统计网络演算的有效服务曲线及端到端串联规则，适合为 R3 的“带覆盖率边界”提供语义基础，不适合证明 GeNIS 或 TQH-C2 能恢复服务状态。

## 方法与证据

- PDF 第 1 页说明目标是把确定性网络演算扩展到统计服务保证。
- PDF 第 5 页给出有效服务曲线定义：它是服务量的概率下界，而不是随机函数本身。
- 第 3 至 4 节说明多节点串联需要附加流量假设或修改有效服务曲线定义。

## 本课题裁决

R3 可以把 ns-3 中学习到的服务下界定义为具有目标违约率的有效服务曲线，但必须在独立校准集报告经验覆盖率。公共数据缺少成对服务真值时，只能输出“不确定或退化”，不能由该定理反推服务可辨识。

## 文献信息

- arXiv: https://arxiv.org/abs/cs/0205001
- Zotero: `BFTIK7EG`
