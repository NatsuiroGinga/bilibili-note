---
title: "CADE: Detecting and Explaining Concept Drift Samples for Security Applications"
authors:
  - Limin Yang
  - Wenbo Guo
  - Qingying Hao
  - Arridhana Ciptadi
  - Ali Ahmadzadeh
  - Xinyu Xing
  - Gang Wang
year: 2021
date: 2026-08-19
journal: "Proceedings of the 30th USENIX Security Symposium (USENIX Security 21), August 11-13, 2021, pp. 2327-2344"
source_pdf: "[[raw/papers/attack-detection/drift/2021-Yang-CADE-Concept-Drift-USENIXSec.pdf]]"
tags:
  - 概念漂移
  - 漂移检测
  - 对比学习
  - 可解释性
  - 恶意软件分类
  - 入侵检测
  - 类型/论文
key_finding: "把漂移处理拆成「检测单个漂移样本 + 解释漂移原因」两步，用对比自编码器学出低维距离函数并以 MAD 判离群，检测 F1 达 0.96 以上（印刷 p.2327 摘要）；但论文自身明写既有做法「需要周期性重训，而重训往往要标注大量新样本」（印刷 p.2327），CADE 本身只做检测与解释，不改变模型对未见年份的判别能力。"
aliases:
  - CADE
  - Yang2021-CADE
related:
  - "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"
  - "[[2017-Jordaney-TRANSCEND漂移检测与共形评价]]"
  - "[[2021-Andresini-INSOMNIA网络入侵检测漂移鲁棒]]"
---

# CADE：安全应用中的概念漂移样本检测与解释

## 一句话

CADE 不试图让分类器在漂移下仍然判对，而是在分类器之外并联一个模块，逐个识别「不属于任何已知训练类」的漂移样本并给出可读解释，把人工标注预算集中到这些样本上。

## 题录与原件（全文核验）

- 原件：`raw/papers/attack-detection/drift/2021-Yang-CADE-Concept-Drift-USENIXSec.pdf`，19 页 PDF，
  第 1 页为 USENIX 封面页。
- 印刷页码实测：PDF p.2 页脚为 `2327`，PDF p.19 为末页，故 **pp. 2327-2344**。
- 载体：USENIX 官方 proceedings 版式，首页印 `This paper is included in the Proceedings of the
  30th USENIX Security Symposium. August 11-13, 2021`。**同行评议正式发表。**
- 获取：https://www.usenix.org/system/files/sec21-yang-limin.pdf ，2026-08-19 下载。

## 论文原结论（页级证据）

- 摘要（印刷 p.2327）：目标是 1) 检出偏离已有类的漂移样本、2) 解释漂移；与「需要大量新标签才能统计地判定漂移」的传统做法不同，本文逐个识别到达的漂移样本。
- 印刷 p.2327 引言：`most learning-based models require periodical re-training`，
  而 `retraining often needs labeling a large number of new samples (expensive)`，
  且难以确定何时该重训；延迟重训会留下检测空窗。
- 方法（印刷 p.2327-2328）：CADE = Contrastive Autoencoder for Drifting detection and Explanation。
  用对比学习从既有训练数据学出低维空间的距离函数，拉大异类样本距离、压缩同类样本距离；
  再用基于距离的离群判据识别漂移样本。
- 解释方法：找出把该样本与其最近类区分开的少量重要特征，基于「距离」而非基于分类边界作解释。
- 结果（印刷 p.2327 摘要）：检测漂移样本的平均 F1 达 0.96 或更高，优于对照方法；
  在 10 个家族训练、其余家族测试的设置下 F1 为 0.95。
- 与 Transcend 的关系（印刷 p.2328）：论文把 Transcend 归为用非一致性度量与可信度 p 值做拟合度评估的一类，
  指出这类方法在封闭世界假设下对「不属于任何已知类」的样本会失效。

## 本课题推论（非论文原结论）

- CADE 与本课题第三章任务不同层：它假设可以在部署期持续取样并交由人工标注，
  而本课题的跨年度零样本评价明确不允许使用次年样本或标签。
- CADE 的贡献在「把标注预算花在哪里」，不在「不重训也能判对」。
  因此它可以作为 1.2.2 中漂移方法族的代表，但**不能**被写成解决了跨年度外推问题。

## 不可直接声称的内容

- 不得写成 CADE 提升了跨年度检测性能。论文报告的 F1 是**漂移样本检测任务**的 F1，
  不是恶意流量检测任务的 F1，两者判定对象不同。
- 论文实验域为 Android 恶意软件与网络入侵数据集，非 Locked Shields 演习流量。

## 与本课题的关系

- 落 1.2.2 段二（面向漂移的适应与校正方法）。
- 承担角色：漂移**检测**一侧的代表工作，与 TRANSCEND 同族。
- 短板证据：印刷 p.2327「重训需要标注大量新样本」一句是段末共同短板的直接出处。
