---
title: "Theoretical Performance Guarantees for Partial Domain Adaptation via Partial Optimal Transport"
authors: [Jayadev Naram, Fredrik Hellström, Ziming Wang, Rebecka Jörnsten, Giuseppe Durisi]
year: 2025
date: 2026-08-12
journal: "ICML 2025，PMLR 267"
source_pdf: "[[raw/papers/methodology/2025-Naram-WARMPOT-Partial-Domain-Adaptation.pdf]]"
zotero_key: 3NCT6JX8
zotero_key: 3NCT6JX8
tags: [部分域适应, 部分最优传输, 风险界, 样本加权, 类型/论文]
key_finding: "WARMPOT 给出含构造性源权重和部分 Wasserstein 项的目标风险界，但仍含不可计算任务难度项，且无稀有恶意质量下限。"
method: "非对称部分传输、传输边缘源权重、目标风险上界"
baseline: "部分域适应与不同源权重基线"
aliases: [WARMPOT, Naram2025-WARMPOT]
related: ["[[JayD2106-WARMPOT官方源码]]", "[[2023-Yang-原型部分最优传输]]"]
---

# WARMPOT：部分域适应的风险界与源权重

## 论文原结论

定义 3.1、公式（3）—（4）定义固定质量 `α` 的部分 Wasserstein 距离。定理 3.2 的公式（5）包含构造性加权源经验损失、部分 Wasserstein、目标边缘总变差和不可计算任务难度项；定理 3.3 将成本扩为特征距离与源标签—目标预测损失。公式（19）给出训练目标，`α` 与 `β` 分别控制目标和源参与质量。

## 可迁移机制

传输计划的源边缘可形成样本或环境权重，`α、β` 可表达源/目标非对称支持参与。论文风险界可约束理论叙述：小传输距离不是目标风险保证。

## 本课题推论

无约束最低成本计划很可能优先搬运占绝大多数的良性质量。第一候选需额外加入源恶意传输质量下限和可松弛支持拒绝，而不是照搬论文参数。

## 不可直接声称

论文的目标标签空间为源标签空间子集，实验为图像；风险界依赖有界度量损失、分类头 Lipschitz 性及不可计算项。不能把风险界说成 LSPR 性能保证。

## 待验证

恶意质量下限是否优于普通 `α、β` 搜索；若普通 WARMPOT 达到同等目标增益，任务特定质量保护未获独立支持。

## 文献信息

- PMLR：https://proceedings.mlr.press/v267/naram25a.html
- arXiv：2506.02712
