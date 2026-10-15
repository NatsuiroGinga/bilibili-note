---
schema: paper-note-search/v1
title: "Continual Deep Active Learning for Medical Imaging: Replay-Base Architecture for Context Adaptation"
title_zh: "医学影像的持续深度主动学习：面向上下文适应的回放式架构（RBACA）"
authors: [Rui Daniel, M. Rita Verdelho, Catarina Barata, Carlos Santiago]
year: 2025
date: 2026-10-15
journal: "arXiv 2501.08245v1（2025-01-14，预印本）"
doi: null
arxiv_id: "2501.08245"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2025-Daniel-持续深度主动学习-回放架构医学影像.pdf]]"
tags:
  - 持续学习
  - 主动学习
  - 回放
  - 医学影像
  - 类型/论文
tasks: [医学影像分类, 持续学习, 主动学习]
datasets: [医学影像多上下文数据集]
methods: [回放式 rehearsal + 记忆管理与记忆剪枝策略, 自动上下文漂移识别, AL 信息量选样]
metrics: [未逐项登记（见全文转换件）]
key_finding:
  - "提出 CAL（continual + active learning）组合框架 RBACA：CL rehearsal 方法持续学习多上下文 + AL 组件选最具信息量样本标注（摘要）；支持多种 memory management 与 memory pruning 策略（贡献原文）。"
  - "「标什么」（AL 组件）与「存什么」（记忆管理/剪枝策略）在同一框架内并存且可替换，但论文以框架评测为主线，未把标注预算与存储预算形式化为联合配置问题。"
supports: [CAL 组合（AL+回放式 CL）在 2025 年已是活跃方向的直接证据, 记忆管理策略可作为可替换组件的设计先例]
cannot_support: [双预算联合配置先例, 类不平衡/正例稀缺处理, 恶意软件域读数]
method: "上下文漂移自动识别触发回放更新 + AL 选样标注"
baseline: "CAL 评测协议（论文自设）"
aliases:
  - RBACA
  - Daniel2025-CAL
related:
  - "[[2026-Han-DMAE-双记忆主动集成-类不平衡漂移数据流]]"
---

# Daniel 等：持续深度主动学习（回放式架构，医学影像）

> 页码锚点：按 MinerU 转换件章节引用。证据等级：本地全文。

## 一、协议与预算（与待核任务逐项对照）

- **标注预算**：AL 组件减少标注需求（摘要「reduces the number of required annotations」），但未设固定预算作为约束量参与配置。
- **存储预算**：支持多种 memory management / memory pruning 策略（贡献节原文），即「存什么」有机制空间，但未以固定预算形式联合建模。
- **类不平衡**：非核心轴。
- **协议与域**：医学影像多上下文；非恶意软件、非 LAMDA、非 Domain-IL。

## 二、与目标任务的差量

证明「AL × 回放式 CL + 记忆管理」组合在 2025 年已是活跃研究面（问题 2 证据）；缺双预算联合配置、缺类不平衡、缺恶意软件域。

## 四、入库与 Zotero

- PDF：`raw/papers/attack-detection/lamda-related/2025-Daniel-持续深度主动学习-回放架构医学影像.pdf`
- 全文转换件：`wiki/papers/attack-detection/lamda-related/2025-Daniel-持续深度主动学习-回放架构医学影像-全文.md`
- Zotero：本轮未导入。
