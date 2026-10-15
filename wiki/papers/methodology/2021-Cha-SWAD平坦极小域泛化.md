---
title: "SWAD：以追求平坦极小实现域泛化"
authors: [Junbum Cha, Sanghyuk Chun, Kyungjae Lee, Han-Cheol Cho, Seunghyun Park, Yunsung Lee, Sungrae Park]
year: 2021
date: 2026-10-15
journal: "NeurIPS 2021（arXiv 2102.08604）"
source_pdf: "[[raw/papers/methodology/2021-Cha-SWAD-Seeking-Flat-Minima.pdf]]"
tags: [域泛化, 平坦极小, 权重平均, ERM强基线, 类型/论文]
key_finding: "把「求平坦极小」引入域泛化：理论证明平坦极小对应更小的泛化间隙；提出密集且过拟合感知的随机权重平均（SWAD），在五个基准上比 ERM 基线平均高 +3.6 个百分点、比此前最好方法高 +1.6 个百分点。"
---

# SWAD：以追求平坦极小实现域泛化

## 全文核验结论

- 明确以 Gulrajani & Lopez-Paz 的 DomainBed 结论为出发点：ERM 在公平协议下可与众多域泛化方法相比或更优（Introduction，物理第 1–2 页）。
- 论点：单纯最小化经验损失易落到**尖锐极小**，泛化次优；因此把最小化重构为**鲁棒风险最小化（RRM）**——在参数邻域内最小化最坏情况经验风险，理论证明该解给出域泛化间隙上界（§2，第 2 页）。
- 方法 **SWAD**：密集的、过拟合感知的随机权重平均；用验证损失轨迹选定权重平均的起止迭代（超参：optimum-patient、overfitting-patient、tolerance rate），比 vanilla SWA 找到更平坦的极小（第 1–2 页）。
- Table 1（第 2 页）实测平均 OOD 准确率：
  - ERM `63.3`；
  - 最好的 SOTA 竞争者 `65.3`；
  - **SWAD `66.9`**；
  - 此前 SOTA + SWAD `67.3`。
  - 正文结论（第 2 页）：相对 ERM 基线 **+3.6pp**，相对既有最好方法 **+1.6pp**。
- 消融：Mixup/CutMix 等仅在域内有效，对 OOD 无效；SWAD 与 SAM 同时在域内与 OOD 有效（第 2 页）。

## 对本课题的合法映射

- SWAD 属于「**不改变组结构、只改进 ERM 优化几何**」的路线：它把「ERM 打不过」的部分归因于优化而非目标函数。
- 对本课题的方法论含义：第四章若主张按年份分组的 group 目标是增益来源，**必须与「ERM + 平坦/权重平均等优化侧强基线」对照**，否则无法区分增益来自「组目标」还是「更好的优化/正则」。这是共同预算基线设计的一条硬约束来源。

## 原创边界与不能直接声称

- SWAD 的平坦性与域泛化间隙的界是**在 i.i.d. 邻域**下推的（第 2 页），其到**非平稳年度序列**的推广并未在本文证明；不能据本文声称「平坦极小一定缓解年度漂移」。
- 本文域为视觉基准，无恶意软件/时间序实验。

## 证据记录

- 全文状态：已下载并逐页核验（摘要、§1–2、Table 1）。
- 稳定标识：arXiv `2102.08604`；NeurIPS 2021。
- 课题角色：ERM 优化侧强基线的代表；第四章消融设计（组目标 vs 优化几何）的对照来源。
