---
title: "独立验证集约束泛化与双数据集训练"
date: 2026-09-09
tags: [约束泛化, 独立验证, FPR约束, LAMDA近邻]
source_pdf: "raw/papers/attack-detection/lamda-related/2019-Cotter-Training-Well-Generalizing-Classifiers-PMLR.pdf"
---

# 独立验证集约束泛化与双数据集训练

题录：Andrew Cotter 等，ICML 2019，PMLR 97:1397--1405，arXiv:1807.00028。

原件 SHA-256：1d08a44c7cf1ca67f8b91c49c62f0d4bfeceb751a996014d5871966e869c10dd。

关键公式：Eq.（1）为最小化目标并满足数据依赖约束；Eq.（2）给出拉格朗日形式。论文把模型训练和独立验证约束拆成两个玩家，以改善约束泛化。

LAMDA 映射：当前训练只使用时间上合法到达的标签，约束玩家使用不参与模型更新的时间一致良性 gate。项目开发层不能被写成未知未来年份 FPR 保证。

官方页面：https://proceedings.mlr.press/v97/cotter19b.html

证据等级：E2；公开原件已下载并由 MinerU 解析，尚无 LAMDA 本地实验支持。
