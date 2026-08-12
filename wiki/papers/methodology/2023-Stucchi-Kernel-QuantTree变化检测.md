---
title: "Kernel QuantTree：核化非参数变化检测"
authors: [Diego Stucchi, Paolo Rizzo, Nicolò Folloni, Giacomo Boracchi]
year: 2023
date: 2026-08-11
journal: "ICML 2023"
source_pdf: "[[raw/papers/methodology/2023-Stucchi-Kernel-QuantTree.pdf]]"
tags: [变化点检测, 核方法, 非参数检验, 类型/论文]
key_finding: "在核诱导几何中构造QuantTree分区，提高复杂多变量变化的检测能力，同时保留稳定期统计量的分布无关校准性质。"
---

# Kernel QuantTree：核化非参数变化检测

## 全文核验结论

KQT 用核相似度替代原始空间的轴对齐分区，以表达非线性多变量结构，并延续 QuantTree 对稳定期误报校准的设计。证据位于 PDF 第1至7页的方法与理论。

## LSPR 角色

它比普通 QuantTree 更适合高维 RWKV 状态监控，但核矩阵成本和窗口大小需要单卡预算审计。可观测量为变化统计量、告警前缀、检测延迟、平均运行长度和状态核计算开销。

## 最小证伪与边界

与原始分数上的 QuantTree 共同预算比较；若核化只增加成本、没有更早发现与性能相关的变化，则排除。不能把检测到分布变化写成检测到攻击概念漂移。

## 证据记录

- 全文状态：完成逐项核验。
- Zotero：`ZB25DPNA`。
- 课题角色：变化检测强诊断；受 C12 原创空间限制。
