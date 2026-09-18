---
schema: paper-note-search/v1
title: "CITADEL: A Semi-Supervised Active Learning Framework for Malware Detection Under Continuous Distribution Drift"
title_zh: "CITADEL：连续分布漂移下的半监督主动恶意软件检测"
authors: [Md Ahsanul Haque, Md Mahmuduzzaman Kamol, Suresh Kumar Amalapuram, Vladik Kreinovich, Mohammad Saidur Rahman]
year: 2025
date: 2026-09-08
journal: "arXiv 2511.11979v3（2026-02-14，预印本）"
doi: null
arxiv_id: "2511.11979"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/drift/2025-Haque-CITADEL-Semi-Supervised-Active-Learning-Drift.pdf]]"
tags:
  - Android恶意软件
  - 半监督学习
  - 主动学习
  - 概念漂移
  - 课程学习
  - 类型/论文
tasks: [Android恶意软件二分类, 半监督学习, 主动学习, 概念漂移适应]
datasets: [APIGraph, Chen-AZ, MaMaDroid, LAMDA]
methods: [FixMatch, Bernoulli位翻转, 特征掩码, 监督对比学习, 多准则主动采样]
metrics: [F1, FNR, FPR, 标签比例, 训练时间]
key_finding:
  - "CITADEL 在 LAMDA 上以半监督一致性、恶意软件二值特征增强和多准则主动采样获得 77.7% F1。"
  - "该读数依赖持续主动标注，课程学习附录只在 APIGraph 上验证，不能外推为 LAMDA 的课程机制证据。"
supports: [CITADEL是LAMDA的直接半监督主动学习近邻, 恶意软件特征增强需要任务化设计]
cannot_support: [课程学习已在LAMDA获证, 完全无标签适应, 位翻转总能保持APK语义]
method: "FixMatch 式半监督学习、Bernoulli 位翻转/特征掩码、监督对比损失、多准则主动采样"
baseline: "Chen-AL、CADE、TRANSCENDENT、FixMatch、FlexMatch、MORSE"
aliases:
  - CITADEL
  - Haque2025-CITADEL
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
  - "[[2023-Chen-Android恶意软件持续学习]]"
---

# CITADEL：半监督主动学习应对长期漂移

> 页码锚点：标题和摘要位于 PDF 物理第 1 页；本轮按第 5–6 节、表 6、表 9、表 12 核验，精确物理页待 MinerU 修复后补。

## 证据与题录

- arXiv `2511.11979v3`，2026-02-14；当前仅核为预印本，不把它写成 ICLR 2026 已接收论文。
- 本地 PDF SHA-256 `ca2cf8f6cba43c34f8f1c1dcd0002bcff864ee87c497d9a86c8b330b0243341c`。
- MinerU 因文件超过快速接口 10 MB、标准接口提前退出而未产出；本笔记基于 arXiv 官方 HTML 全文与原件表号，页码待视觉复核。
- Zotero：`P86CK65V`，题录已导入，未自动附加 PDF。

## 方法与结果

- 用 Bernoulli 位翻转和特征掩码替代图像增强，在高维二值恶意软件特征上做一致性正则；再加入监督对比损失与由边界、距离、低置信度组成的主动采样。
- 评估 APIGraph、Chen-AZ、MaMaDroid、LAMDA。完整主动学习设置下 F1 分别为 93.5%、82.7%、44.9%、77.7%；论文称对相应强基线的增益为 +1.1、+4.3、+8.9、+13.2 个百分点（摘要、第 5 节）。
- 在 LAMDA 上，只有半监督增强、不主动更新时 F1 为 30.9%；加入多准则主动学习与联合损失后为 `77.7±0.1`、FNR `24.0±0.1`、FPR `2.3±0.4`（第 6 节表 6）。
- 表 4 的月标注预算 50 时，LAMDA F1/FNR/FPR 为 `70.9±1.2/33.6±1.6/2.0±0.1`；预算 400 才达到 `77.7±0.1/24.0±0.1/2.3±0.4`。标签成本必须与效果同时报告。
- 标注比例 40% 的平台期只在 APIGraph 调参表 9 建立，不能自动转成 LAMDA 的冻结标注比例。

## 课程学习证据边界

- 附录 E 只在 APIGraph 2012 训练子集上按实例难度从易到难排序，并额外每月标注 400 个困难样本。
- 表 12：无课程 F1 `71.2±0.6`；课程+每月 400 标签为 `83.0±0.5`；CITADEL 主动学习为 `93.5±0.3`。
- 该实验混合了课程顺序与新增困难样本标签，且没有在 LAMDA 重复。因此它只说明课程是可比较基线，不证明 LAMDA 上存在稳定、源期可观测的难度顺序。

## 风险

- 随机位翻转可能生成语义不可实现的 APK 特征组合；作者用低概率减少破坏，但没有证明每个增强样本满足 Android 依赖约束。
- 主动学习结果需要标签预算，不是无标签时间外推。
- 如果继续使用 LAMDA 发布的全时期词表，CITADEL 仍继承未来协变量预处理风险；论文未替代来源专属预处理门。

## 论文可以支持

- LAMDA 上半监督主动学习是必须对照的直接近邻；任务化二值增强优于直接套用图像增强。

## 论文不能支持

- 不能支持纯课程学习在 LAMDA 上有效，也不能支持无标签最终测试自适应。

## 实验结果与负证据

- LAMDA F1 `77.7±0.1` 依赖主动标注；仅增强、不主动更新时为 30.9%。

## 与本课题的关系

- 适合作为延迟标签维护强基线；不适合作为零标签静态域泛化对照。

## Evidence Record

Evidence ID: `CITADEL-E1`
Source: arXiv `2511.11979v3`
Source type: preprint | full paper
Supports: 半监督主动更新是 LAMDA 上的直接强近邻；课程应作为受限基线
Contradicts: “课程学习已在 LAMDA 上独立获证”
Method / dataset / metric: LAMDA、APIGraph 等；F1、FNR、FPR、标注预算
Limitation: 预印本；课程实验只在 APIGraph；依赖未来标签
Project relevance: 静态漂移下的强方法对照
Claim strength: supported

## 文献信息

- arXiv：https://arxiv.org/abs/2511.11979
- 代码：https://github.com/IQSeC-Lab/CITADEL
