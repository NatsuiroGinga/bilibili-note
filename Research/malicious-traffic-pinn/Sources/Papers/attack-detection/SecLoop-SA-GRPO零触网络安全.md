---
title: "Advancing LLM-Based Security Automation with Customized Group Relative Policy Optimization for Zero-Touch Networks"
authors:
  - Xinye Cao
  - Yihan Lin
  - Guoshun Nan
  - Qinchuan Zhou
  - 等
year: 2025
date: 2026-07-15
journal: arXiv preprint (北邮 + 新加坡科技设计大学)
source_pdf: "[[2512.09485.pdf]]"
tags:
  - GRPO
  - 网络安全
  - 零触网络
  - LLM
  - 强化学习
  - 类型/论文
aliases:
  - SecLoop
  - SA-GRPO
  - 零触网络安全GRPO
key_finding: 提出 SecLoop（首个覆盖安全策略生成→编排→响应→反馈全生命周期的自动化框架）与 SA-GRPO（面向 6G 零触网络安全定制的 GRPO），解决动态对抗环境下安全策略的自动生成与持续适配。
method: SecLoop 全生命周期闭环 + SA-GRPO 定制化策略优化（针对安全策略生成/编排/响应/反馈各环节改造 GRPO）
baseline: 通用 GRPO、SFT 安全大模型
---

# SecLoop + SA-GRPO: 零触网络安全自动化

> Cao 等 · 北邮/新加坡科技设计大学(Quek 团队) · arXiv:2512.09485 · 2025-12 · 18 页

> 注：改进素材参考文献 [8]，作者/编号核验无误。

## 一句话

把 GRPO 定制成"安全专用"，套进一个从策略生成到响应反馈的全自动闭环里，给 6G 零触网络做自适应防御——**"GRPO 用于网络安全"的最直接先例**。

## 对开题的意义（创新点 2 的 RL 侧先例）

1. **GRPO 可安全化定制**：SA-GRPO 证明通用 GRPO 能针对安全任务改造（策略生成/编排/响应/反馈各环节）。开题的"课程式 GRPO"是同思路的另一改造方向（课程采样维度）。
2. **全生命周期闭环**：SecLoop 的"生成→编排→响应→反馈"闭环，与开题原型的"物理初筛→语义精判→审计报告"流水线可对照——反馈环节可借鉴。
3. **动态对抗环境适配**：强调策略要随威胁演化，这正是开题"在线课程"想解决的（按模型实时能力动态采样）。

## 局限（gap）

- 面向 6G 零触网络的策略生成，偏高层安全策略，非底层流量攻击检测。
- 未结合物理信息/守恒约束——纯 LLM + RL，无 PINN 协同。
- 课程维度未涉及物理残差。

## 疑问 / 待验证

- SA-GRPO 对 GRPO 的具体改造点（奖励/优势函数/采样）需读全文第 3 节，看能否复用到检测任务的课程采样。
- SecLoop 的反馈机制能否作为开题"物理自校验"的外部闭环？
