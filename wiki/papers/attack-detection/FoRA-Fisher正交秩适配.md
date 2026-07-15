---
title: "FoRA: Fisher-orthogonal Rank Adaptation for Parameter-Efficient Fine-Tuning"
authors:
  - Juneyoung Park
  - Seongbae Lee
  - Han-Sang Lee
  - Kyuho Lee
  - Minjae Kim
  - Seungheon Hyeon
  - KIDUK KWON
  - Seongwan Kim
  - Jaeho Lee
year: 2026
date: 2026-07-15
journal: arXiv preprint (OptAI + LG Uplus)
source_pdf: "[[2605.29317.pdf]]"
tags:
  - LoRA
  - PEFT
  - Fisher信息
  - Stiefel流形
  - 正交约束
  - 类型/论文
aliases:
  - FoRA
  - Fisher正交秩适配
key_finding: FoRA 回归 PEFT"减参数"初衷——用单次前向 Fisher 分数(<1% 训练成本)选任务相关层（减适配层数而非秩），在选中层对 LoRA 下投影做 Stiefel 流形正交约束；半参数预算下一致优于 LoRA/DoRA，两组件超加性增益。
method: Fisher 对角分数选层 + 选中层 Stiefel 流形上训练下投影（列正交、保有效秩）
baseline: LoRA、DoRA、AdaLoRA（5 个 LLaMA 主干 + 12 主干跨架构 270M-32B）
---

# FoRA: Fisher 正交秩适配

> Park 等 · OptAI/LG Uplus · arXiv:2605.29317 · 2026-05 · 17 页

> 注：改进素材参考文献 [12]，作者/编号核验无误。

## 一句话

PEFT 别只盯着减秩——FoRA 用 Fisher 分数挑少数关键层、只在这些层做 Stiefel 正交 LoRA，半参数预算打赢 LoRA/DoRA。

## 对开题的意义（与 Stiefel-LoRA 同为降级辅助）

1. **同属流形约束 PEFT 家族**：与 [[Stiefel流形LoRA黎曼优化]] 同团队，思路互补——一个减秩正交、一个减层正交。开题若用流形正则，二选一即可，不必都引。
2. **Fisher 选层思路可借鉴**：用 Fisher 分数选"任务相关层"，对开题"哪些层注入物理约束/课程权重"有启发。
3. **降级定位同 [[Stiefel流形LoRA黎曼优化]]**：新方向下仅作 PINN 训练稳定辅助，非核心创新。

## 局限 / 疑问

- 纯 PEFT，与检测/PINN/RL 无关。
- 与新方向核心创新点耦合弱。
- 仅读摘要+引言，实验细节待全读。
