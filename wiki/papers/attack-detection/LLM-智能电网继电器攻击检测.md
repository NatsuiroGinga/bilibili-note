---
title: "Large Language Models for Detecting Cyberattacks on Smart Grid Protective Relays"
authors:
  - Ahmad Mohammad Saber
  - Saeed Jafari
  - Zhengmao Ouyang
  - Paul Budnarain
  - Amr Youssef
  - Deepa Kundur
year: 2026
date: 2026-07-15
journal: arXiv preprint
source_pdf: "[[2601.04443.pdf]]"
tags:
  - LLM
  - 智能电网
  - 攻击检测
  - 继电器
  - 微调
  - 类型/论文
aliases:
  - LLM智能电网继电器
  - Saber2026-电网继电器LLM
key_finding: 把变压器差动继电器(TCDR)的多相电流时序测量"文本化"成结构化自然语言提示，微调紧凑 LLM(DistilBERT/GPT-2/DistilBERT+LoRA)区分网络攻击与真实故障，DistilBERT 检测 97.62% 攻击且故障检测完美。
method: 多变量电流时序→结构化 NL prompt → 微调紧凑 LLM（DistilBERT / GPT-2 / DistilBERT+LoRA）分类
baseline: SOTA ML/DL 基线（标称、复杂攻击、含噪场景）
---

# LLM 检测智能电网保护继电器攻击

> Saber 等 · arXiv:2601.04443 · 2026-01 · 9 页

> 注：改进素材参考文献 [15]，作者/编号核验无误。

## 一句话

把电网继电器的电流时序数据"翻译"成自然语言提示喂给小 LLM，微调后区分攻击和真实故障——**LLM 用于攻击检测的应用先例**。

## 对开题的意义

1. **"大模型"在攻击检测中的角色参照**：本篇 LLM 做端到端分类（文本化时序→分类），是 LLM-攻击检测的应用先例。开题的"大模型"定位不同——做语义精判 + 物理可验证奖励，但可参考其"时序数据文本化"的 prompt 设计。
2. **紧凑可本地部署 LLM**：用 DistilBERT/GPT-2 而非巨型模型，呼应开题"受限算力"约束。
3. **攻击 vs 真实故障的区分**：电网里要区分"网络攻击"与"真实故障扰动"——这与开题"攻击 vs 正常"的二分更难，可借鉴其场景设计。
4. **含噪鲁棒性评估**：在测量噪声下评估，开题也应做。

## 局限 / 疑问

- 纯 LLM 端到端，无 PINN/物理约束、无 RL。
- 电网继电器场景，非通用网络流量。
- "文本化时序"对高维网络流量是否可行？特征规模差异大。
- 仅读摘要+引言，实验细节待全读。
