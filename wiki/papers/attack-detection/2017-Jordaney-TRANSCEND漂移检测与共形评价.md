---
title: "Transcend: Detecting Concept Drift in Malware Classification Models"
authors:
  - Roberto Jordaney
  - Kumar Sharad
  - Santanu K. Dash
  - Zhi Wang
  - Davide Papini
  - Ilia Nouretdinov
  - Lorenzo Cavallaro
year: 2017
date: 2026-08-19
journal: "Proceedings of the 26th USENIX Security Symposium (USENIX Security 17), August 16-18, 2017, Vancouver, BC, Canada, pp. 625-642"
source_pdf: "[[raw/papers/attack-detection/drift/2017-Jordaney-TRANSCEND-Concept-Drift-USENIXSec.pdf]]"
tags:
  - 概念漂移
  - 漂移检测
  - 共形预测
  - 拒识
  - 恶意软件分类
  - 类型/论文
key_finding: "提出共形评价器（conformal evaluator），在模型性能开始下降之前用统计 p 值评估每一次判定的质量，从而识别老化模型；论文自述这是相对「周期性重训」的显著转变（PDF p.2，印刷 p.625），但其产出仍是「该不该信这次判定」，不改变模型本身的判别能力。"
aliases:
  - Transcend
  - TRANSCEND
  - Jordaney2017-Transcend
related:
  - "[[2021-Yang-CADE漂移样本检测与解释]]"
  - "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"
---

# TRANSCEND：恶意软件分类模型中的概念漂移检测

## 一句话

TRANSCEND 把「评估一次判定值不值得相信」形式化为统计问题，用共形预测的非一致性度量算出 p 值与可信度，在模型性能塌下去之前就报出老化信号。

## 题录与原件（全文核验）

- 原件：`raw/papers/attack-detection/drift/2017-Jordaney-TRANSCEND-Concept-Drift-USENIXSec.pdf`，
  20 页 PDF，第 1 页为 USENIX 封面页。
- 印刷页码实测：PDF p.2 页脚 `625`，PDF p.20 页脚 `642` → **pp. 625-642**。
- 载体：首页印 `Proceedings of the 26th USENIX Security Symposium, August 16-18, 2017,
  Vancouver, BC, Canada, ISBN 978-1-931971-40-9`。**同行评议正式发表。**
- 获取：https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-jordaney.pdf ，2026-08-19 下载。

## 论文原结论（页级证据）

- 摘要与引言（印刷 p.625）：本方法在模型性能开始退化**之前**识别老化的分类模型，
  论文自述这是 `a significant departure from conventional approaches that retrain` 的做法。
- 引言对既有做法的批评（印刷 p.625）：既有方案「周期性重训模型」，但重训过密开销高、
  重训过疏会留下检测能力低下的时段，且 `the retraining process requires manual labeling of all the` 新样本。
- 方法定位（印刷 p.625-626）：概率式评估（如 SVM 的到超平面距离、拟合概率）不评估判定本身；
  本文改用统计式评估——把每次判定放在此前判定的语境中考察。
  核心是从 Conformal Predictor 提取统计基础，构造共形评价器（conformal evaluator, CE）。
- 论文自述贡献：这是**第一个用判定评估技术识别不可信预测**的工作；
  并把判定评估问题转写为约束优化问题，使阈值可按运维目标自动求解。
- 图 1（印刷 p.628 附近）：对比 p 值与概率两种阈值下、阈值上下元素的性能，
  显示 p 值筛出的保留集性能更高。

## 本课题推论（非论文原结论）

- TRANSCEND 的输出是「保留 / 拒识」的二分，落在决策后处理层；
  它假设被拒识的样本会转交人工或触发重训。在本课题跨年度零样本设置下，
  次年样本既无标签也不允许回流训练，拒识只能减少错误告警，不能恢复检出率。

## 不可直接声称的内容

- 不得写成 TRANSCEND 提升了跨时间的检测性能。它改善的是**保留子集**上的性能，
  代价是放弃对被拒识样本的判定。

## 与本课题的关系

- 落 1.2.2 段二。承担角色：漂移**检测与拒识**一侧的规范出处，是 CADE 的前作。
- 短板证据：印刷 p.625「重训需要人工标注全部新样本」，与 CADE 印刷 p.2327 同向，
  两条独立出处共同支撑段末「这一族的对策都以取得目标期标签为前提」。
