---
title: "Minerva: Reinforcement Learning with Verifiable Rewards for Cyber Threat Intelligence LLMs"
authors:
  - Md Tanvirul Alam
  - Aritran Piplai
  - Ionut Cardei
  - Nidhi Rastogi
  - Peter J Worth Jr
year: 2026
date: 2026-07-15
journal: arXiv preprint (RIT + UTEP + FAU)
source_pdf: "[[2602.00513.pdf]]"
tags:
  - GRPO
  - 可验证奖励
  - RLVR
  - CTI
  - LLM
  - 奖励作弊
  - 类型/论文
aliases:
  - Minerva
  - MinervaRL
  - CTI可验证奖励
key_finding: CTI 输出有规范目标（ATT&CK ID/CWE/CVSS/结构化 schema）可确定性验证——据此用可验证奖励（RLVR）训 LLM，配 MinervaRL 自训练生成已验证轨迹回蒸馏缓解奖励稀疏，4 主干×12 基准均值比基模型高 15.8 个百分点、比 GRPO 高 4.3。
method: 任务特定验证器对结构化输出打分（RLVR）+ MinervaRL 自训练（生成已验证轨迹→蒸馏回模型，解 rollout 奖励稀疏）
baseline: 基模型、SFT、GRPO
---

# Minerva: RLVR for CTI LLMs

> Alam 等 · RIT/UTEP/FAU · arXiv:2602.00513 · 2026-02 · 33 页

> 注：改进素材参考文献 [10]，作者/编号核验无误。

## 一句话

**奖励要"可验证"而不是"可自检"**——CTI 输出有标准 ID/schema，能用确定性验证器打分，这比让模型自己写 `<check>` 说"校验通过"靠谱得多。

## 对开题的意义（解决初版诊断 2 的原理性方案）

这是三篇 GRPO-安全里**对初版改造最关键**的一篇：

1. **可验证奖励（RLVR）= `<check>` 自校验的原理性替代**。初版 3.2 的 `<check>` 纯文本自检易被奖励作弊（模型写句"校验通过"骗分）。Minerva 的思路：用**确定性验证器**打分，模型无法靠话术蒙混。开题可用"物理残差阈值 + 输出 schema 合规"作为可验证奖励——这正是 [[数字孪生约束LLM-CPS异常检测]] 的 JSON schema 约束 + 物理合理性过滤的奖励化。
2. **MinervaRL 解奖励稀疏**：rollout 时多数轨迹无可验证命中→奖励稀疏。MinervaRL 生成额外已验证轨迹蒸馏回模型。开题初版用 Jaccard 软奖励缓解稀疏，MinervaRL 提供了另一条（自训练已验证轨迹）可叠加。
3. **比 GRPO 高 4.3 分**：实证 RLVR + 自训练优于纯 GRPO，为开题"在 GRPO 基础上叠加可验证物理奖励"提供正向证据。

## 局限（gap）

- CTI 任务（ATT&CK/CWE/CVSS 标注），非流量检测。其"可验证"依赖标准 ID——网络流量攻击检测的"可验证目标"需自己定义（如物理残差是否超阈、攻击类型标签）。
- 无课程学习、无物理信息。

## 疑问 / 待验证

- 流量攻击检测的"可验证奖励"如何定义？候选：①物理残差是否超阈（确定性）②输出 schema 合规 ③与 ground-truth 攻击标签的 Jaccard。三者能否组合成统一可验证奖励？
- MinervaRL 的已验证轨迹自训练，能否与开题"在线课程采样"结合——把课程选出的困惑区样本优先做自训练？
- 这是把初版诊断 2（自校验冗余/作弊）落地改造的关键引用，开题"自我验证机制"章应改为"可验证物理奖励"。
