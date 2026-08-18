---
title: "Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progress"
authors: [Renjie Wu, Eamonn J. Keogh]
year: 2021
date: 2026-08-13
journal: "原件为 9 页手稿版，PDF 中未印期刊名与卷期（元数据仅含题名与作者）；后续文献引用为 IEEE TKDE"
source_pdf: "[[raw/papers/methodology/2021-Wu-Keogh-Current-TSAD-Benchmarks-Flawed.pdf]]"
sha256: "5d60584e5880cc81b1415dda7e8d46124ad1573e1e9d46c72625660b197535cf"
tags:
  - 负面结果
  - 基准缺陷
  - 时序异常检测
  - 评价方法论
  - 类型/论文
key_finding: "Yahoo 基准 367 条时间序列中 316 条（86.1%）可被一行 MATLAB 表达式解决，其中 193 条只需一个阈值常数（表 1，第 4 页）。"
method: "提出四类基准缺陷（triviality、unrealistic anomaly density、mislabeled ground truth、run-to-failure bias），用暴力搜索的“一行代码”检测器量化 triviality，并发布 UCR 异常检测档案"
baseline: "一行 MATLAB 表达式（diff/movmean/movstd 组合）、Discord、Telemanom"
aliases:
  - WuKeogh2021-基准缺陷
  - TSAD Benchmarks are Flawed
related:
  - "[[2019-Dacrema-神经推荐进步幻觉]]"
  - "[[2022-Audibert-深度网络是否有助于多变量时序异常检测]]"
  - "[[2022-Kim-时序异常检测的严谨评价]]"
---

# 时序异常检测基准的四类缺陷

> Wu, Keogh, 2021 · 9 页手稿

## 一句话

Yahoo、Numenta、NASA、OMNI 四大时序异常检测基准的多数样例存在四类缺陷，其中最致命的是“平凡性”——86.1% 的 Yahoo 序列可用一行标准库表达式解决，因此这些基准上的算法排名和“近年进步”都不可信。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progress
- 作者单位：University of California, Riverside（第 1 页脚注）
- DOI / arXiv：未在原件中定位（PDF 正文与元数据均无 DOI、arXiv 号或期刊卷期；支持页链接见文末）
- 原件：`raw/papers/methodology/2021-Wu-Keogh-Current-TSAD-Benchmarks-Flawed.pdf`

## 核心方法

- 四类缺陷分类（第 1 页摘要与第 2–6 节）：triviality（平凡性）、unrealistic anomaly density（异常密度不现实）、mislabeled ground truth（标注错误）、run-to-failure bias（跑到失效偏置）。
- 平凡性的可检验定义（定义 1，第 2 页）：只能使用 `mean`、`max`、`std`、`diff` 等基础向量化原语组成一行 MATLAB 代码，禁止调用 `kmeans`、`ClassificationKNN` 等高层函数。
- 通用一行式（第 3 页公式 (1)–(6)）：以 `diff(TS)` 或 `abs(diff(TS))` 与 `movmean`、`movstd` 的加权阈值比较，参数为窗口 k、系数 c、偏置 b；对 367 条序列做暴力搜索求解 k、c、b。
- 新基准构造原则（第 3 节，第 6–7 页）：每条测试序列只放一个异常；异常要么由并行记录的其他模态（out-of-band）确认，要么以高度合理的方式人工植入。

## 关键数字（含页码/表号）

- 平凡性（表 1，第 4 页）：Yahoo 基准 A1 44/67（65.7%）、A2 97/100（97.0%）、A3 98/100（98.0%）、A4 77/100（77.0%），合计 316/367（86.1%）可被一行式解决。
- 更强的结论（第 4 页正文）：367 条中有 193 条（超过一半）只需公式 (3) 或 (5) 中的单个“magic number” b 即可解决；A3 中 14 条使用公式 (6) 的序列共享 k=5、c=0。
- 与已发表结果对比（第 4 页正文）：作者称 86.1% 这个数字“与多数在该数据集上做过实验的论文相当”。
- 异常密度（第 4 页，2.3 节）：NASA 的 D-2、M-1、M-2 中超过一半测试样本是连续异常区；SDM 的 machine-2-5 在很短区间内标了 21 处独立异常。作者主张单条测试序列的理想异常数为 1（第 4 页）。
- 标注错误（第 5 页，2.4 节）：Numenta NY Taxi 原标注 5 处异常，作者认为至少还有 7 处事件同样值得标为异常（含独立日、劳动节、马丁·路德·金日等）；被标注的“NYC 马拉松”异常实际由同日夏令时调整引起。
- 跑到失效偏置（图 10，第 6 页）：Yahoo A1 各序列最右侧异常标签的位置明显非均匀分布，集中在序列末端；作者指出“朴素地把最后一个点标为异常”就有很大概率命中。
- 鲁棒性对比（图 13，第 8 页）：同一条心电图上 Telemanom 与 Discord 都能定位异常；加入显著高斯噪声后 Discord 仍峰值在正确位置，Telemanom 峰值移到错误位置。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 直接支持“简单规则可能胜过复杂序列模型”这一类证据：一行式在 86.1% 的 Yahoo 序列上达到与深度模型相当的表现（表 1，第 4 页），可作为本课题中 XGBoost/前缀均值优于完整 RWKV-7 状态递归的先例参照。
- 支持“先检验任务是否平凡”的实验设计：在为 LSPR24 声称序列建模收益之前，应先给出等价的一行式或单特征阈值基线，如果它已经接近上限，则复杂状态递归的增益无法归因于序列建模。
- 支持“标注与切分本身是误差源”的论证：NY Taxi 与 NASA G-1 的标注争议（第 5–6 页）说明评价结论可能被标签噪声反转；本课题的实体级标签聚合同样需要说明标签口径。
- 需要注意的反向证据：本文的“一行式”都是单变量、点式判据，不涉及跨年度分布漂移，不能用来主张“加密流量任务也一定是平凡的”。

## 局限（不可直接声称的内容）

- 作者明确承认（第 3 页）一行式的存在不等于原论文没有贡献，也承认这些一行式含人工挑选的参数与人的创造性介入。
- 结论限于单变量或取单一维度的公开时序基准，没有网络流量、加密载荷、类别极不平衡与跨年度漂移的实验。
- 新建的 UCR 档案自陈仍有小部分样例可被一行式解决（第 6 页），且征集数据集的社会化呼吁未获得任何投稿（第 6 页）。
- 本文只提供“负面证据”（基准不适合区分算法），没有正面比较深度方法与传统方法的整体性能；这一点由 Audibert 等人后续补足。

## 可引用的逐字原文（≤15 词）

- “much of the apparent progress in recent years may be illusionary”（第 1 页摘要）
- “The community should abandon the Yahoo, Numenta, NASA and OMNI benchmark datasets”（第 7 页，4.1 节，已删去文中引用编号）

## 证据记录

- 来源类型：完整论文（9 页全文，`pdftotext -layout` 抽取并逐页核对）
- 支持：基准平凡性、标注错误与位置偏置会制造虚假进步；简单基线必须先行报告
- 限制：无多变量安全流量证据、无分布漂移实验、无正面性能比较
- 论断强度：有支持（基准诊断）/ 推论（迁移到加密流量任务）

## 文献信息

- 支持页（第 8 页参考文献 [18]）：<https://wu.renjie.im/research/anomaly-benchmarks-are-flawed/>
- UCR 异常检测档案（第 9 页参考文献 [23]）：<https://www.cs.ucr.edu/~eamonn/time_series_data_2018/UCR_TimeSeriesAnomalyDatasets2021.zip>
- DOI：未在原件中定位
