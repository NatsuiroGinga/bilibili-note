---
title: "通过风险外推实现分布外泛化"
authors: [David Krueger, Ethan Caballero, Joern-Henrik Jacobsen, Amy Zhang, Jonathan Binas, Dinghuai Zhang, Remi Le Priol, Aaron Courville]
year: 2021
date: 2026-08-11
journal: "ICML 2021"
source_pdf: "[[raw/papers/methodology/2021-Krueger-Risk-Extrapolation.pdf]]"
tags: [域泛化, 风险外推, 风险方差, 类型/论文]
key_finding: "MM-REx允许超出源环境凸包的仿射风险组合，V-REx以环境风险方差作为可实现近似；少环境和非线性漂移会削弱其意义。"
---

# 通过风险外推实现分布外泛化

## 全文核验结论

REx 不只优化最坏已见环境，而是尝试在源环境风险的外推集合上优化。PDF 第4至5页给出 MM-REx 与 V-REx；第3至4页讨论少量环境、非线性情形和易环境风险上升的局限。

## 公式族

`R_MM(θ)=sup_{Σ_e λ_e=1, λ_e≥λ_min} Σ_e λ_e R_e(θ)`；工程近似为：

`R_V(θ)=Σ_e R_e(θ)+β Var({R_e(θ)})`。

## 对 LSPR 的映射

V-REx 可直接作用于多个 LSPR23 因果时间环境的 RWKV 分类损失。它与 GroupDRO应作为竞争的 M1 变体，而不是无解释地同时叠加。可观测量为环境风险方差、时间外推验证平均精确率和最差时间块召回率。

## 最小证伪与边界

比较 `β=0`、预注册的单个 `β` 和打乱环境顺序；若风险方差下降而目标平均精确率不升，说明风险相等不是有效代理。不能声称 V-REx 学到了因果特征，也不能把它与 FOIL 的潜在环境推断合并后宣称全新不变学习范式。

## 证据记录

- 全文状态：完成逐项核验。
- Zotero：`8QBD4NUV`。
- 课题角色：M1 的轻量竞争实现；单卡快速筛选优先级高。
