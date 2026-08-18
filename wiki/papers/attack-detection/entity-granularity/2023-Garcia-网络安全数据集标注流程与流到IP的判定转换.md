---
title: "Towards a better labeling process for network security datasets"
authors: [Sebastian Garcia, Veronica Valeros]
year: 2023
date: 2026-08-18
journal: "arXiv:2305.01337v1 [cs.CR]，2023-05-02，预印本，无期刊/会议 journal-ref"
source_pdf: "[[raw/papers/attack-detection/entity-granularity/2023-Garcia-Towards-Better-Labeling-Process-Network-Security-Datasets-arXiv2305.01337.pdf]]"
sha256: "aedb605821222bf8a19493a7857b8027ebf941a6849bcb32c0d4f1dba1a1fce7"
tags:
  - 判定单元
  - 标注本体
  - 告警聚合
  - 评价口径
  - 预印本
  - 类型/论文
key_finding: "在评价视角一节明确指出：多数检测方法只判定流或包，而多数防护手段是按 IP 或域名封禁，因此必须存在「从逐流判定到 IP 判定」的转换；同一攻击产生的多条流告警还需再合成为一条高层告警，这与告警疲劳问题直接相关。同时警告流级指标好不等于 IP 级指标好，反之亦然。"
method: "梳理数据集利益相关方需求 + 提出标签本体 + 提供 Zeek 流标注工具 + 讨论标签生产与消费的差异"
baseline: "无（方法论与本体论文）"
aliases:
  - Garcia2023-LabelingProcess
  - 网络安全数据集标注流程
related:
  - "[[2024-Li-端到端对比学习入侵检测的IP对粒度]]"
  - "[[2012-Dainotti-流量分类的流对象粒度与开放问题]]"
  - "[[../../methodology/soc-alert-operations/2022-Alahmadi-99percent误报SOC分析员访谈]]"
---

# 从逐流判定到 IP 判定的转换，以及两套指标为何不可互推

> Garcia & Valeros, 2023, arXiv 预印本 · CTU Prague（Stratosphere 实验室）

## 一句话

这是本轮调研中**唯一一处直接把「逐流判定」与「实体（IP）判定」的差异写成显式评价问题**的来源：
防护动作以 IP/域名为单位，所以必须做流→IP 的转换；而这个转换会同时改变指标含义。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Towards a better labeling process for network security datasets
- 作者单位：Department of Computer Science, Czech Technical University, Prague（PDF 第 1 页）
- 标识：arXiv:2305.01337v1 [cs.CR]，2023 年 5 月 2 日
- **发表状态：arXiv 预印本，arXiv 页面未登记 journal-ref 或 DOI（除 arXiv DOI 外）。**
- 原件：`raw/papers/attack-detection/entity-granularity/2023-Garcia-Towards-Better-Labeling-Process-Network-Security-Datasets-arXiv2305.01337.pdf`

## 论文原结论（全文核验，§6.1「Flow or IP address」与 §6.2）

1. **判定单元与处置单元不一致**：原文指出多数检测方法把流或包判为恶意，
   但**不决定源 IP 或目的 IP 是否被判定**；由于「多数防护机制是通过封禁 IP 地址或域名来工作的」，
   因此应当有一个从逐流判定到 IP 地址的转换。
2. **这个转换本身是有代价的**：论文说这可以用「良性流与恶意流之比的阈值」解决，
   但需要估计阈值、计算误差等。
3. **同一攻击的多条流告警需要合成为一条**：原文写道，当同一次攻击产生的多条基于流的告警
   需要被转换成**一条供防守方处理的高层告警**时，问题会进一步加剧；论文明确说
   「这与告警疲劳问题相关」，并认为可能需要更多机器学习算法来解决。
4. **两套指标不可互推（本篇最重要的警告）**：§6 提出应分别评估「每 IP 的指标」与「每流的指标」，
   并给出图 2 的算例——恶意主机 A 在检测时刻之前发出 15 条流（5 条恶意、10 条良性），
   检测基于 4 条流做出，其中只有 3 条真正是恶意流，还有 1 条良性流被误当作证据。
   按流层面算得 FPR = 10%、F1 = 66%、准确率 = 80%、TPR = 60%，
   但在 IP 层面主机 A 被正确检出，计为真阳。论文由此得出结论：
   **「流层面表现较差的检测器，在 IP 地址层面仍可能是一个好的检测器」**。
5. §6.2 进一步指出，主机可能攻击、停止、再攻击，因此标签必须有足够精度与时间信息，
   才能同时支持「检出」与「解除检出」的评价。

## 本课题可迁移的机制

- 第 1、3 条是**支持实体级判定**的直接文献依据：处置动作以实体为单位，
  且同一攻击跨多条流会产生重复告警，必须先合成为一条实体级告警。
- 第 4 条是**必须一并写入正文的反向约束**：本课题「同一 4% 假阳工作点上逐流 788,295 条、
  实体级 1,855 个，相差 425 倍」的表述，如果不同时说明聚合规则与两套指标的不可互推，
  就会落入本文警告的陷阱。写作时应明确给出实体化聚合规则（计数阈值或分数聚合方式）
  与两个粒度各自的指标，而不是只报实体级数字。

## 不可直接声称的内容

- **本文是 arXiv 预印本**，未见同行评议出处。按仓库证据等级，只能作为方法论提法来源，
  不得作为「已发表实验证据」支撑效果类论断。
- 图 2 是**构造的说明性算例**，不是实测数据，不得当作实验结果引用。

## 仍需实验验证的假设

- 本课题实体化时使用的具体聚合规则（阈值、时间窗）对实体级指标的敏感性，
  本文只提出需要估计，未给出方法；这一敏感性需本课题自行做消融。
