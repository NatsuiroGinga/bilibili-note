---
schema: paper-note-search/v1
title: "Continuous Learning for Android Malware Detection"
title_zh: "面向Android恶意软件检测的持续学习"
authors: [Yizheng Chen, Zhoujie Ding, David Wagner]
year: 2023
date: 2026-09-08
journal: "32nd USENIX Security Symposium（USENIX Security 2023），1127–1144"
doi: null
arxiv_id: "2302.04332"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/drift/2023-Chen-Continuous-Learning-Android-Malware.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 主动学习
  - 对比学习
  - 类型/论文
tasks: [Android恶意软件二分类, 主动学习, 持续学习]
datasets: [API Graph, Chen-AndroZoo]
methods: [层次对比学习, 伪损失不确定度, 月度主动采样, 暖启动]
metrics: [F1, FPR, FNR, 标签预算]
key_finding:
  - "按月请求分析员标签并重训的层次对比主动学习，把七年评估中的平均漏报率从强基线 14% 降至 9%，误报率从 0.86% 降至 0.48%。"
  - "方法优势依赖每月新标签，不是免标注漂移适应。"
supports: [标签预算下主动学习可减缓Android恶意软件时间退化, 家族层次可服务样本选择]
cannot_support: [无标签部署适应, LAMDA上的直接效果, 任意时间跨度保证]
method: "层次对比学习、伪损失不确定度、按月主动采样、暖启动持续重训"
baseline: "固定模型、置信度/熵/TRANSCENDENT 等主动学习选择、CADE"
aliases:
  - Chen-AL
  - Chen2023-ContinuousLearning
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
---

# Chen 等：Android 恶意软件持续学习

> 页码锚点：PDF 物理第 2 页摘要与图 1 给出主要 FNR/FPR；方法和数据协议见物理第 3 页起。

## 证据与题录

- USENIX 官方全文 19 页，本地 SHA-256 `f15541d85dd4626b86fcb64f2034f68aeb1ccd80034e9c0e62525fd4f74259d4`；MinerU 快速提取成功。
- 正式题录：USENIX Security 2023，1127–1144；arXiv `2302.04332`。
- Zotero：`FJADHX96`，本地题录已导入，未自动附加 PDF。

## 方法和协议

- 数据：API Graph 2012–2018；另建 2019–2021 AndroZoo 集合。
- 初始模型用 2012 年，之后每月从新样本中选定预算交分析员标注，将已标样本加入训练集并重训，下一月再评估（PDF 第 2–3 页）。
- 核心方法把 malware family 纳入层次对比结构，并用“伪损失”度量单样本对比表示的不确定度。
- 每月标注 200 个样本时，平均 FNR 从最佳基线 14% 降至 9%，FPR 从 0.86% 降至 0.48%；在 AndroZoo 上相对最佳方法的 F1 增益为 8.99%–16.50%（PDF 第 2 页）。

## 与 LAMDA 的关系

- LAMDA 第 2 节和参考文献 [17] 明确引用本论文，把它作为 Android 漂移下主动学习与对比学习的主要直接近邻。
- LAMDA 的 MLP/持续学习设置也引用 Chen-AL；CITADEL 则直接把 Chen-AL 作为强主动学习基线。
- 该方法回答“有稳定月度标注预算时如何更新”，不回答“未来标签不可立即获得时如何免监督适应”。

## 边界

- 需要持续人工标注和重训；标注延迟、分析员一致性、真实低误报预算与长期算力成本必须单独核验。
- 与 LAMDA 对比时必须重建来源专属特征空间，不能让未来年份共同决定词表。

## 论文可以支持

- 有固定月度标签预算时，层次对比主动学习可优于已有样本选择方法。

## 论文不能支持

- 不能支持无标签或标签延迟未知的最终未来测试适应。

## 实验结果与负证据

- 每月 200 标签时 FNR `14%→9%`、FPR `0.86%→0.48%`；固定分类器六个月 F1 `0.99→0.76`。

## 与本课题的关系

- 是 LAMDA 上主动学习的直接强基线，但需共享标签、计算和时间协议。

## Evidence Record

Evidence ID: `CHENAL-E1`
Source: USENIX Security 2023 官方全文
Source type: full paper
Supports: 主动学习可在固定标签预算下减缓 Android 恶意软件时间退化
Contradicts: “主动学习方法无需未来标签或运维更新”
Method / dataset / metric: APIGraph、AndroZoo；F1、FPR、FNR、标签预算
Limitation: 标签可用和月度重训假设
Project relevance: LAMDA 主动学习强基线
Claim strength: strong

## 文献信息

- 官方页：https://www.usenix.org/conference/usenixsecurity23/presentation/chen-yizheng
- arXiv：https://arxiv.org/abs/2302.04332
- 代码：https://github.com/wagner-group/active-learning
