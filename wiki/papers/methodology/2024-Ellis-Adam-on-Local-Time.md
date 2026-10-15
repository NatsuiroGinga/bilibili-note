---
schema: paper-note-search/v1
title: "Adam on Local Time: Addressing Nonstationarity in RL with Relative Adam Timesteps"
title_zh: "局部时间上的 Adam：用相对 Adam 时间步处理 RL 的非平稳性"
authors: [Benjamin Ellis, Matthew T. Jackson, Andrei Lupu, Alexander D. Goldie, Mattie Fellows, Shimon Whiteson, Jakob N. Foerster]
year: 2024
date: 2026-10-15
journal: "NeurIPS 2024（第 38 届，poster 94469）；arXiv:2412.17113（2024-12-22）"
doi: null
arxiv_id: "2412.17113"
evidence_level: "在线全文已下载"
source_pdf: "raw/papers/methodology/2024-Ellis-Adam-on-Local-Time.pdf"
tags:
  - 优化器状态
  - 时间步重置
  - 动量保留
  - 非平稳
  - 深度强化学习
  - 反证
  - 类型/论文
key_finding:
  - "**对本提案的反证**：完全重置优化器（Adam-MR，类比 Asadi 的做法）在 DQN Atari-10 上 `23.5%`，**低于**不重置的 Adam `28.8%`；而**保留动量、只重置时间步**的 Adam-Rel 达 `65.7%`。"
  - "结论：**阻止一切梯度信息跨越目标变化是「过度矫正（excessive correction）」甚至有害**；应保留动量估计。"
  - "机制：非平稳梯度幅度突变（如目标网络更新）会使 Adam 更新量过大；把时间步重置到 0 可避免大更新，且在没有梯度突变时退化为学习率退火。"
method: "Adam-Rel：Adam 更新中用 epoch 内的**局部时间步**替代全局时间步 t（目标变化后把 t 归零），**保留一阶/二阶矩缓冲**；对照 Adam-MR（完全重置）与 Adam"
baseline: "Adam（不重置）、Adam-MR（完全重置，即 Asadi 式重置）"
metrics: [Atari-10 DQN human-normalized 分数, Craftax PPO 分数, Atari-57 IQM]
related:
  - "[[2023-Asadi-Resetting-Optimizer-Deep-RL|Asadi：重置优化器（被本文质疑）]]"
  - "[[2026-Sahu-Momentum-SGD-Nonstationary|Sahu 2026：动量在非平稳下的可证明次优性]]"
  - "[[INDEX|方法论论文索引]]"
---

# 局部时间上的 Adam

> **证据等级**：在线全文已下载（`raw/papers/methodology/2024-Ellis-Adam-on-Local-Time.pdf`）。
> 页码待补（arXiv v1 第 1 页已核；数值来自检索到的正文/表）。

## 核心结论

- **问题**：RL 是非平稳的（目标网络更新、策略更新），但 Adam 的时间步 `t` 假设平稳。
  梯度幅度突变会导致 **Adam 更新量过大且持续**，损害性能。
- **对策 Adam-Rel**：用 epoch 内**局部时间步**（目标变化后归零），**保留矩缓冲**。
  无梯度突增时**退化为学习率退火**。
- **与 Asadi 的直接对立（关键数值）**：
  - DQN Atari-10：**Adam-Rel `65.7%` > Adam `28.8%` > Adam-MR `23.5%`**（Adam-MR ≈ Asadi 式完全重置）。
  - PPO Craftax：Adam-Rel 全面更优，**Adam-MR 急剧更差**。
  - PPO Atari-57：Adam-Rel 在 55 个游戏中 33 个优于 Adam，且 IQM 更优。
- **作者立场**：完全重置（Adam-MR）是**过度矫正**，会丢弃有用梯度信息。

## 与本提案的关系

- **最强反证**：本提案想在年度边界**重置/衰减动量**；本文在同一类非平稳设定下给出
  「**完全重置有害、保留动量更好**」的对照数字。
- **但两者不矛盾到不可调和**：Adam-Rel 的胜出靠的是**只重置时间步**（一种**部分重置**），
  且其未来工作**明确把「持续学习」列为 Adam-Rel 的待验证应用场景**——即作者认为该路线**尚未在持续学习上验证过**。
- **可用性三问**：
  1. 固定 200 条预算 / 每年度 10 轮：**不能直接套用**——RL 设定，非监督分类任务序列。
  2. 四层 MLP：**不适用**——Atari 用 CNN。机制与架构无关，但无 MLP 证据。
  3. 公开代码：**未确认**（本次检索未取到该文仓库链接，标为「代码未确认」）。
