---
title: "Riemannian Optimization for LoRA on the Stiefel Manifold"
authors:
  - Juneyoung Park
  - Minjae Kang
  - Seongbae Lee
  - Haegang Lee
  - Seongwan Kim
  - Jaeho Lee
year: 2025
date: 2026-07-15
journal: arXiv preprint (Opt-AI Inc.)
source_pdf: "[[2508.17901.pdf]]"
tags:
  - LoRA
  - Stiefel流形
  - 黎曼优化
  - PEFT
  - 正交约束
  - 类型/论文
aliases:
  - Stiefel-LoRA
  - Park2025-Stiefel流形LoRA
key_finding: 把 LoRA 的 B 矩阵约束在 Stiefel 流形上做黎曼优化，施加显式正交约束实现近乎完美的正交性与满有效秩，显著提升参数效率与表示能力，在 LoRA/DoRA 上一致超越 AdamW。
method: Stiefel 流形上的黎曼优化器优化 LoRA B 矩阵（正交约束）+ 近满有效秩
baseline: AdamW 优化的 LoRA / DoRA
---

# Stiefel 流形上的 LoRA 黎曼优化

> Park 等 · Opt-AI Inc. · arXiv:2508.17901 · 2025-08 · 15 页

> 注：初版开题报告参考文献 [12]，改进素材 [11]，作者/编号核验无误。

## 一句话

AdamW 训 LoRA 会让 B 矩阵基冗余——把它约束在 Stiefel 流形上做黎曼优化，正交性近乎完美、有效秩满，参数效率大幅提升。

## 对开题的意义（已降级为训练稳定正则项）

新方向（PINN+课程 RL）下，Stiefel 流形约束从"核心创新点"降级为 **PINN 训练稳定正则项**：

1. **正交约束稳定深层训练**：初版 H-ORL 用它解决"特征腐蚀"，新方向里它可用于稳定 PINN 深层 Transformer 训练——与 [[mHC-流形约束超连接]] 一脉相承。
2. **降级定位要写清**：开题应说明流形约束是"数值优化辅助"，不是物理创新，避免重蹈初版"流形=PINN"的概念混淆。
3. **黎曼优化器可复用**：若开题保留流形正则，可直接用本文的 Stiefel 黎曼优化器实现。

## 局限 / 疑问

- 纯 PEFT 方法论文，与攻击检测、PINN、RL 无关。
- 与新方向两个核心创新点（PINN+课程 RL）耦合弱，仅作训练稳定辅助。
- 仅读摘要+引言，实验细节待全读。
- 同主题另见 [[FoRA-Fisher正交秩适配]]（同团队，减层数而非减秩）。
