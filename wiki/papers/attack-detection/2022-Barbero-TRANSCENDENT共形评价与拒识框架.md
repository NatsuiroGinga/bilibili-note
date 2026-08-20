---
title: "Transcending TRANSCEND: Revisiting Malware Classification in the Presence of Concept Drift"
authors:
  - Federico Barbero
  - Feargus Pendlebury
  - Fabio Pierazzi
  - Lorenzo Cavallaro
year: 2022
date: 2026-08-19
journal: "本机原件为 arXiv:2010.03856v6 [cs.CR]，2024-01-08，首页未印出版载体；据 arXiv 摘要页与作者机构库著录为 2022 IEEE Symposium on Security and Privacy (S&P)，**正式卷期页码待联网回 IEEE Xplore 核定**"
source_pdf: "[[raw/papers/attack-detection/drift/2022-Barbero-TRANSCENDENT-Conformal-Evaluation-IEEESP.pdf]]"
tags:
  - 概念漂移
  - 拒识
  - 共形预测
  - 恶意软件分类
  - 类型/论文
key_finding: "把 TRANSCEND 的共形评价理论形式化并给出两个开销更低的共形评价器；但论文 §V-C「Rejection Cost」（PDF p.8）明写被拒识的样本「可能由专家人工检查并标注」，拒识本身有代价，必须与性能收益权衡。拒识路线降低的是错误判定，不是恢复检出。"
aliases:
  - TRANSCENDENT
  - Barbero2022-Transcendent
related:
  - "[[2017-Jordaney-TRANSCEND漂移检测与共形评价]]"
  - "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"
  - "[[2021-Yang-CADE漂移样本检测与解释]]"
---

# TRANSCENDENT：共形评价的重构与带拒识的恶意软件分类

## 一句话

TRANSCEND 的正式扩展：把共形评价的统计基础补严，换成两个计算开销低得多的评价器，并在去除实验偏置的五年数据集上重评。

## 题录与原件（全文核验）

- 原件：`raw/papers/attack-detection/drift/2022-Barbero-TRANSCENDENT-Conformal-Evaluation-IEEESP.pdf`，19 页。
- **首页只印 `arXiv:2010.03856v6 [cs.CR] 8 Jan 2024`，未印出版载体行。**
  全文 `rg -i 'Symposium on Security and Privacy'` 的两处命中都在参考文献列表中引用他人工作，
  不是本文自身的载体标注。
- 因此：**本机版本按预印本处理；`2022 IEEE S&P` 的正式著录与页码须回 IEEE Xplore 核定后才能写入参考文献。**
- 获取：https://arxiv.org/pdf/2010.03856 ，2026-08-19 下载。
- 作者机构（首页）：King's College London、Royal Holloway、The Alan Turing Institute、
  University of Cambridge、University College London。

## 论文原结论（页级证据）

- PDF p.1 摘要：机器学习恶意软件分类的真实部署会因概念漂移而性能退化；
  一条有希望的应对是**带拒识的分类**——可能被误分的样本先隔离，直到专家能够分析它们。
  TRANSCENDENT 是建立在 Transcend 之上的拒识框架，
  给出共形评价理论的形式化处理，并开发两个额外的共形评价器，
  性能持平或超过原版而显著降低计算开销。
- PDF p.2 §II-C：Transcend 是安全任务中带拒识分类的代表框架；
  低置信预测被隔离并单独处理。
- **PDF p.8 §V-C「Rejection Cost」（本条是本课题最关心的部分）**：
  「被拒识的点会发生什么取决于检测流水线的其余部分。在简单设置下，
  被拒识的点可能**由专家人工检查并标注**；也可能继续下游进入进一步的自动分析或其他机器学习系统。
  无论哪种情况，拒识预测都会有一定代价。选择拒识阈值时，
  必须把这个代价与潜在的性能收益一并权衡。」
  同段援引 TESSERACT 的三个调参与评价指标。

## 本课题推论（非论文原结论）

- 拒识路线与本课题第三章的两个机制不冲突也不重叠：它作用在判定输出之后，
  假定存在一个下游承接被拒识样本的通道（人工或另一套系统）。
- 本课题的跨年度零样本设置没有这个通道：次年测试期不允许引入人工标注。
  因此拒识只能压低误报，不能提高次年的检出率——这与 §V-C 的代价论述一致。

## 不可直接声称的内容

- **不得写「Barbero 等 2022，IEEE S&P」并附页码**，除非先回 IEEE Xplore 核出卷期页码。
  本机原件不支持该著录。
- 不得写成 TRANSCENDENT 提升了跨年度检出率。它提升的是保留子集上的稳健性。

## 与本课题的关系

- 落 1.2.2 段二。承担角色：拒识族的最新形式化工作，与 TRANSCEND、CADE 同段。
- 短板证据：PDF p.8 §V-C 的「拒识有代价，需与性能收益权衡」是段末共同短板的第三条独立出处。
