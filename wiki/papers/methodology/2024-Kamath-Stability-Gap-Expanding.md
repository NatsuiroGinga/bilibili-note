---
schema: paper-note-search/v1
title: "The Expanding Scope of the Stability Gap: Unveiling its Presence in Joint Incremental Learning of Homogeneous Tasks"
title_zh: "稳定性缺口的扩大范围：揭示其在同质任务联合增量学习中的存在"
authors: [Sandesh Kamath, Albin Soutif-Cormerais, Joost van de Weijer, Bogdan Raducanu]
year: 2024
date: 2026-10-15
journal: "IEEE/CVF CVPR 2024 Workshops (CLVision)，pp. 4182–4186，doi:10.1109/cvprw63382.2024.00421；arXiv:2406.05114"
doi: "10.1109/cvprw63382.2024.00421"
arxiv_id: "2406.05114"
evidence_level: "在线全文已下载"
source_pdf: "raw/papers/methodology/2024-Kamath-Stability-Gap-Expanding-Scope.pdf"
tags:
  - 稳定性缺口
  - 任务边界
  - 优化动力学
  - 联合增量学习
  - 类型/论文
key_finding:
  - "**稳定性缺口（stability gap）**：切换到新任务时旧任务性能的**暂时性下跌**，最坏情况在**任务边界**，后果严重。"
  - "它**也发生在同质任务的联合增量训练中**——即**继续训练同一分布的数据、且可访问全部旧任务数据**时仍然发生。"
  - "该场景下**存在通向新极小点的低损失线性路径，但 SGD 优化不走这条路**。"
  - "**含义**：稳定性缺口的根源是**优化动力学**，不是记忆不足或表征漂移。"
method: "联合增量训练（access to all data）下测量任务边界的稳定性缺口；做逐批次（batch-wise）细化分析定位 SGD 的路径选择"
baseline: "朴素联合增量训练（joint incremental training）"
metrics: [任务边界处旧任务准确率的时间曲线（稳定性缺口）]
related:
  - "[[2023-Asadi-Resetting-Optimizer-Deep-RL|Asadi：重置优化器]]"
  - "[[2024-Ellis-Adam-on-Local-Time|Adam on Local Time]]"
  - "[[2026-Sahu-Momentum-SGD-Nonstationary|Sahu 2026：动量在非平稳下的可证明次优性]]"
  - "[[INDEX|方法论论文索引]]"
---

# 稳定性缺口的扩大范围

> **证据等级**：在线全文已下载（`raw/papers/methodology/2024-Kamath-Stability-Gap-Expanding-Scope.pdf`，4 页 workshop 论文）。

## 核心结论

- **稳定性缺口**：转向新任务时，**旧任务性能短暂下跌**；最坏性能出现在**任务边界**，且会拖低算法最终性能。
- **关键发现**：缺口**在同质任务的联合增量训练**中也出现——
  **数据分布相同、且可访问全部旧任务数据**时依然发生。
- 该场景下**存在低损失的线性路径**通向新极小点，但 **SGD 不选择这条路径**。
- **推论**：稳定性缺口来自**优化动力学**，而不是记忆容量或表征漂移。

## 与本提案的关系

- **支撑**：为「任务边界的性能损失源自优化过程」提供了干净证据，
  且**排除了「数据不足/遗忘」这一混淆解释**——这正是本提案要论证的前提。
- **对本提案的隐含约束**：它同时说明**即使不做任何回放、全量数据在手**也会发生该现象，
  所以「年度边界性能下降」**不能只归因到小回放预算**；本课题若要把损失归到动量，
  必须做「重置动量 vs 不重置」的对照，而不是拿「是否回放」来论证。
- **另一支线**：有后续工作（NORADRENERGIC-INSPIRED GAIN MODULATION，OpenReview `eecCPK8upD`）引用本文，
  称**动量项会让更新偏离真实梯度方向、在任务边界过冲**。该解读**来自引用方而非本文**，引用时须注明出处。
- **可用性三问**：
  1. 固定 200 条预算 / 每年度 10 轮：**可适配**——它是分类任务序列，但原文用「全量数据联合训练」，与固定小预算对照相反。
  2. 四层 MLP：**可适配**——无架构限制（原文用图像分类骨干），概念与架构无关。
  3. 公开代码：**未确认**（本次检索未取到仓库链接，标为「代码未确认」）。
