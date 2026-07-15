---
title: "Stability Analysis and Impulsive Control of Bifurcation and Chaos in Fluid Flow Model for TCP/AQM Networks"
authors:
  - Feng Liu
  - Zhi-Hong Guan
  - Guangxi Zhu
  - Tao Li
  - Hua O. Wang
year: 2010
date: 2026-07-15
journal: 2010 8th World Congress on Intelligent Control and Automation (WCICA), IEEE, 5760-5765
source_pdf: "[[Stability_analysis_and_impulsive_control_of_bifurcation_and_chaos_in_fluid_flow_model_for_TCP_AQM_networks.pdf]]"
tags:
  - TCP/AQM
  - 流体模型
  - 分岔混沌
  - 脉冲控制
  - 控制理论
  - 物理信息
  - 类型/论文
aliases:
  - TCP-AQM分岔混沌控制
  - Liu2010-TCP流体分岔
key_finding: 分析 TCP/AQM 流体模型（窗口 W、队列 q 耦合时滞 ODE）的分岔与混沌行为——这些行为会导致平均队列长度剧烈振荡、网络失稳；提出脉冲控制法抑制分岔与混沌。
method: 经典流体流模型(Misra 型) Ẇ, q̇ 耦合 ODE → 平衡点线性化 + Hopf 分岔分析 → 脉冲控制器抑制混沌
baseline: 无控制的原系统
---

# TCP/AQM 流体模型的分岔混沌与脉冲控制

> Liu Feng 等 · 华科/波士顿大学 · WCICA 2010 · 5 页 · DOI 10.1109/wcica.2010.5554932

> 注：改进素材参考文献 [17]，作者/出处核验无误。

## 一句话

TCP/AQM 流体模型在某些参数下会分岔、走向混沌——队列剧烈振荡——本文用脉冲控制把它拉回稳定。**纯控制理论，与攻击检测无关。**

## 模型（与 [[TCP-AQM二维流体模型]] 同源）

经典 Misra 型流体流模型（[4] 的二维模型是其推广）：

$$\dot W(t) = \frac{1}{R(t)} - \frac{W(t)W(t-R(t))}{2R(t-R(t))}p(t-R(t)), \quad \dot q(t) = N(t)\frac{W(t)}{R(t)} - C$$

- $W$=TCP 窗口、$q$=队列、$R$=RTT、$N$=会话数、$C$=链路容量、$p$=标记概率。
- 平衡点 $W^*=RC/N$，$q^*=2N^2/(R^2C^2K)$。
- 参数变化（如时延增大）触发 Hopf 分岔→混沌，队列振荡。

## 对开题的意义（与 [4] 一致，作方案 A 的背景文献）

1. **同一模型族**：本篇与 [[TCP-AQM二维流体模型]]([4]) 共用 TCP 流体方程，是方案 A（TCP 流体作 PINN 物理）的原始动力学来源。
2. **同样不是检测论文**：目标是设计 AQM 控制器抑制振荡，无攻击检测实验。
3. **提供"动力学失稳"视角**：攻击流量可能使系统偏离平衡点、触发分岔——这是方案 A "攻击打破动力学方程"的一种论证角度，但仍需补"残差→攻击"的实证链。

## 局限（与方案 A 的固有硬伤一致）

- 状态量 W/q/R 在 IDS2018 不可观测；非 TCP 攻击不服从该方程。
- 纯控制理论，迁移到检测需自补大量论证。
- 与方案 B（守恒不变量）相比，方案 A 数据可行性更差。详见 [[TCP-AQM二维流体模型]] 的分析。

## 疑问 / 待验证

- "分岔/混沌"视角能否作为方案 A 的补充论据？价值有限，因数据不可算。
- 若开题最终选方案 B，本篇与 [4] 仅作"TCP 流体动力学背景"引用，不作核心方法依据。
