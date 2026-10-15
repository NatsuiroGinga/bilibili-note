---
schema: paper-note-search/v1
title: "Local-Time AdamW for Stability-Gap Reduction in Continual Learning"
title_zh: "局部时间 AdamW：降低持续学习中的稳定性缺口"
authors: [未核（Analemma Research 论文页未列出完整作者）]
year: 2026
date: 2026-10-15
journal: "Analemma Research 论文页（非 arXiv／非会议；来源可信度待核）"
doi: null
arxiv_id: null
evidence_level: "仅摘要"
source_pdf: null
tags:
  - 优化器状态
  - 偏差校正
  - 任务边界
  - 稳定性缺口
  - 持续学习
  - 待核来源
  - 类型/论文
key_finding:
  - "**与本提案最接近的监督式持续学习候选**：指出 AdamW 的**偏差校正**为冷启动设计，在任务边界「矩估计是热的但与新任务梯度错位」时**反成负担**。"
  - "对策 **LT-AdamW**：**只重置偏差校正时间步**，**保留矩缓冲**，产生更新阻尼（切换后早期有效学习率约降 3×）。"
  - "报告效果：Split CIFAR-100 稳定性缺口 **−31%**、切换后最低准确率 **+24%**；Rotated MNIST 稳定性缺口 **−17%**；一行代码改动。"
  - "**证据等级警告**：仅取到论文页摘要，**未取到全文**，且来源非 arXiv／非会议，**不得据此支撑正文论断**。"
method: "LT-AdamW：在任务边界重置 Adam 的偏差校正时间步 t（局部时间），保留一阶/二阶矩缓冲"
baseline: "标准 AdamW（不重置）"
metrics: [稳定性缺口, 切换后最低准确率]
related:
  - "[[2024-Ellis-Adam-on-Local-Time|Adam on Local Time（RL 版，同一思想）]]"
  - "[[2023-Asadi-Resetting-Optimizer-Deep-RL|Asadi：重置优化器]]"
  - "[[INDEX|方法论论文索引]]"
---

# 局部时间 AdamW：降低持续学习中的稳定性缺口

> **证据等级：仅摘要。** 本笔记由 Analemma Research 论文页
> （https://analemma.ai/papers/786c7661-d46b-4395-ad43-8b8b3908fc4f/ ）的摘要片段整理，
> **未取到全文，未找到 arXiv 或会议版本**。**不得用于支撑正文论断**；若需引用，先取得正式全文。

## 为什么仍然登记

- 它是本次检索中**唯一**把「**优化器状态 × 监督式持续学习的任务边界**」作为主题的候选，
  与本提案的设定（监督分类任务序列、非 RL）**最接近**。
- 其结论与本提案**部分一致、部分冲突**：
  - **一致**：任务边界确实需要处置优化器状态。
  - **冲突**：它**保留矩缓冲**、只重置偏差校正时间步——即主张**不应完全丢弃动量**（与 Adam-Rel 同向，与「重置动量」的原始提案反向）。
- 因此它是本提案「**部分重置 vs 完全重置**」对比中的关键一员，**必须补齐全文**再决定是否作为对照臂。

## 待办

- [ ] 检索 arXiv / OpenReview 是否有正式版本（本次 WebSearch 未命中 arXiv 号）
- [ ] 若确认无正式版本，按 `raw/AGENTS.md` 的付费墙／来源不可信条款，仅登记为候选，不升级为全文证据
- [ ] 核验其 Split CIFAR-100 与 Rotated MNIST 的具体协议是否兼容「固定 200 条预算」设定
