---
title: "Improving LLM Reasoning for Vulnerability Detection via Group Relative Policy Optimization"
authors:
  - Marco Simoni
  - Aleksandar Fontana
  - Giulio Rossolini
  - Andrea Saracino
year: 2025
date: 2026-07-15
journal: arXiv preprint (CNR Italy + Scuola Superiore Sant'Anna)
source_pdf: "[[2507.03051.pdf]]"
tags:
  - GRPO
  - 漏洞检测
  - LLM推理
  - 强化学习
  - 奖励设计
  - 类型/论文
aliases:
  - GRPO-漏洞检测
  - Simoni2025-GRPO漏洞
key_finding: 用 GRPO + 结构化规则奖励微调 LLM 做软件漏洞检测，重新定义优势函数与奖励信号以适配 BigVul/DiverseVul/CleanVul 标注，系统研究 GRPO 对泛化与推理的影响，缓解 LLM 对某类漏洞过预测、漏检其他类的问题。
method: GRPO 策略梯度 + 基于数据集标注的规则化奖励 + 重定义优势函数；三研究问题（零样本能力/自推理训练/泛化）
baseline: SFT、指令微调小模型、基线 GRPO
---

# GRPO for Vulnerability Detection

> Simoni 等 · 意大利 CNR/Sant'Anna · arXiv:2507.03051 · 2025-07 · 16 页

> 注：本论文是改进素材参考文献 [9]。原素材作者写成 "Zhang Y, Wang H, Liu Y"、出处写成 "2026 IEEE SANER pp 312-319" 均错——真实作者是 Simoni/Fontana/Rossolini/Saracino，目前为 arXiv 预印本，SANER 2026 收录未证实。

## 一句话

漏洞检测里 LLM 爱"偏科"（某类漏洞过检、其他漏检）——用 GRPO 配规则化奖励逼它均衡推理，并重定义优势函数让 GRPO 适配检测任务的离散标注。

## 对开题的意义（创新点 2 的奖励设计先例）

1. **规则化奖励适配检测任务**：把数据集标注重定义为 GRPO 的奖励信号——与开题初版的 Jaccard 软奖励思路同源，都是把检测的离散标签做成连续/结构化奖励。可作为开题奖励函数设计的直接参考。
2. **缓解奖励稀疏/不平衡**：针对"某类过预测、其他漏检"的不平衡，开题在攻击类型不均衡场景下面临同样问题，可借鉴其优势函数重定义。
3. **研究问题框架可借鉴**：用 RQ1/RQ2/RQ3（零样本/自推理/泛化）组织实验，开题的课程式 GRPO 实验可类比设计。

## 局限（gap）

- 漏洞检测（代码级），非流量攻击检测。
- 规则奖励仍基于数据集标签，非物理可验证——未解决奖励作弊（见 [[Minerva-CTI可验证奖励]] 的 RLVR 思路）。
- 无课程学习、无物理信息。

## 疑问 / 待验证

- 其优势函数重定义的具体公式（第 3 节）能否迁移到流量攻击检测的 GRPO？
- 规则奖励与开题 Jaccard 软奖励如何融合？是否用规则奖励做主信号、Jaccard 做平滑项？
