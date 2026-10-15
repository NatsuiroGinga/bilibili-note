---
title: "2018-Espeholt-IMPALA-V-trace重要性权重截断"
authors: Espeholt, Lasse; Soyer, Hubert; Munos, Remi; Simonyan, Karen; Mnih, Volodymyr; Ward, Tom; Doron, Yotam; Firoiu, Vlad; Harley, Tim; Dunning, Iain; Legg, Sid; Kavukcuoglu, Koray
year: 2018
date: 2026-10-15
journal: "ICML 2018 / arXiv:1802.01561"
source_pdf: "raw/papers/attack-detection/lamda-related/2018-Espeholt-IMPALA-V-trace重要性权重截断.pdf"
tags:
  - 类型/论文
  - attack-detection
  - 机制/截断方差缩减
  - Method/强化学习
key_finding: "V-trace 式 (1)：ρ_t=min(ρ̄,π/μ)、c_i=min(c̄,π/μ)；§4.1 末段给出截断的理论身份——ρ̄ 决定收敛不动点，c̄ 是方差缩减、不改不动点；截断是方差缩减器，不是不变量恢复器。"
---

# V-trace 截断重要性权重（cap 的理论身份）

## 背景与定位

IMPALA 的解耦架构中 actor 与 learner 间存在策略滞后，V-trace 用截断重要性权重处理离策略偏差/方差权衡。我们的 m_cap 与 c̄ 同型截断。

## 方法核心（原文公式）

- §4.1 式 (1)：`v_s = V(x_s) + Σ γ^{t−s}(Π c_i)δ_t V`，其中 `ρ_t=min(ρ̄, π/μ)`、`c_i=min(c̄, π/μ)`。
- §4.1 末段与图注：**ρ̄ 决定收敛不动点，c̄ 是方差缩减、不改不动点**。
- Remark 2：加 λ 因子后 V-trace 退化为 TD(λ)（on-policy 情形）。

## 与缺陷 A 的关系（本课题推论）

- 判读：m_cap 与 c̄ 同型——**cap 是方差缩减器，不是不变量恢复器**。任务给定事实（cap 后 3.97≈4）与原文定位一致：cap 压住凸放大长尾、消掉 Jensen 缺口的大头，但「m̄ 是 a\* 的不变量」没有被恢复。
- E4 实验设计：odds+cap vs 线性有界映射 `m_r = m_cap·λ_r/λ_cap`，验证「凸性是漂移主因」；若线性版不优于 cap 版，则该机制主张被证伪。
- 处理 (i)：否；处理 (ii)：否（但给出 cap 的理论身份）。

## 不可直接声称的内容

- V-trace 的重要性权重截断处理的是离策略 IS 权重方差，与我们的 λ→m 映射凸性是不同问题；只借「截断=方差缩减」的角色定位，不能声称 V-trace 解决凸映射标定。
- 收敛不动点分析（附录 A）未逐条核验。