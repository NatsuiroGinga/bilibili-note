---
title: "2021-Gibbs-自适应保形推断-分布漂移在线标定"
authors: Gibbs, Isaac; Candès, Emmanuel
year: 2021
date: 2026-10-15
journal: "Annals of Applied Statistics / arXiv:2106.00170"
source_pdf: "raw/papers/attack-detection/lamda-related/2021-Gibbs-自适应保形推断-分布漂移在线标定.pdf"
tags:
  - 类型/论文
  - attack-detection
  - 机制/在线闭环标定
  - Method/统计学
key_finding: "ACI 式 (2)：α_{t+1}=α_t+γ(α−err_t)；式 (3) 指数加权变体；Proposition 4.1 无分布假设下给出长期经验覆盖率保证；附录 A：ACI 更新等价于 pinball loss 的在线梯度下降。"
---

# ACI：分布漂移下的标定量在线闭环（与本缺陷最同构）

## 背景与定位

保形预测的分位数标定在分布漂移下失效；ACI 把一次性分位数标定换成每步在线更新，按覆盖误差反馈调 α_t。与我们缺陷 A 的同构度最高：标定量（α_t ↔ a\*）、实测量（err_t ↔ λ̄_r）、目标（α ↔ m\*=4）一一对应。

## 方法核心（原文公式）

- §2 式 (2)：`α_{t+1} = α_t + γ(α − err_t)`。
- 式 (3) 指数加权变体：`α_{t+1} = α_t + γ(α − Σ w_s·err_s)`，w_s∝0.95^{t−s}。
- Proposition 4.1：无分布假设下的长期经验覆盖率保证（初始化后最坏行为也有界）。
- 附录 A：ACI 更新等价于 pinball loss 的在线梯度下降。

## 与缺陷 A 的关系（本课题推论）

- 移植式：`a_{r+1} = clip_[a_min,a_max](a_r + γ(λ̄_r − λ*))`，λ\*=0.8。
- ACI 修复成分 (i)；其「标定量→误差」映射单调无凸放大，不处理成分 (ii)——凸放大残差由 cap 与 E4 线性化映射处理，**ACI 与 V-trace 互补而非替代**。
- E5（唯一真训练实验）即按 ACI 式移植设计：1 年滚动 × 2 臂。

## 不可直接声称的内容

- ACI 的保证是「长期经验覆盖率」，不是「每步覆盖正确」；移植后同样只能主张长期平均复用倍数接近目标，不能主张每轮 m_r 精确等于 4。
- Proposition 4.1 的证明细节未逐条核验（本地全文在手，未精读证明）。