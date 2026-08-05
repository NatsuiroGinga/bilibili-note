---
title: "分布漂移下的自适应共形推断"
authors: [Isaac Gibbs, Emmanuel Candès]
year: 2021
date: 2026-07-30
journal: "arXiv 2106.00170"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2021-Gibbs-Adaptive-Conformal-Shift.pdf]]"
key_finding: "自适应共形推断在任意序列上控制长时间平均错覆盖频率，但不自动给每个时间点、每个协议条件或每个攻击子类的条件覆盖。"
tags: [共形预测, 分布漂移, 在线校准, 类型/论文]
aliases: [Gibbs2021, Adaptive Conformal Inference]
---

# 分布漂移下的自适应共形推断

## 一句话

论文用前一步是否错覆盖来在线更新显著性参数，适合 R3 的按时间顺序校准，但保证是长时间频率而不是逐样本安全证明。

## 方法与证据

- PDF 第 1 至 2 页区分经典交换性下的边际覆盖和分布漂移下的长期覆盖频率。
- PDF 第 6 页给出显著性水平的在线更新及长期频率结论。
- 在额外平滑和缓慢漂移条件下才能得到多数时间点的近似边际覆盖。

## 本课题裁决

R3 若采用在线校准，必须报告总体长期覆盖、各协议/数据源条件覆盖和区间宽度。不能把总体 90% 覆盖写成每个未知攻击场景都有 90% 保证。

## 文献信息

- arXiv: https://arxiv.org/abs/2106.00170
- Zotero: `Z5US9JZD`
