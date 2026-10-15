---
schema: paper-note-search/v1
title: "Resetting the Optimizer in Deep RL: An Empirical Study"
title_zh: "在深度强化学习中重置优化器：一项实证研究"
authors: [Kavosh Asadi, Rasool Fakoor, Shoham Sabach]
year: 2023
date: 2026-10-15
journal: "NeurIPS 2023（第 37 届）；arXiv:2306.17833（2023-06-30）"
doi: null
arxiv_id: "2306.17833"
evidence_level: "在线全文已下载"
source_pdf: "raw/papers/methodology/2023-Asadi-Resetting-Optimizer-Deep-RL.pdf"
tags:
  - 优化器状态
  - 动量污染
  - 矩估计
  - 分布非平稳
  - 深度强化学习
  - 类型/论文
key_finding:
  - "**直接支撑提案的核心机制命名**：把值函数逼近表述为「每次迭代损失都变的优化问题序列」，Adam 的一阶/二阶矩估计会携带历史而被**污染（contamination effect）**。"
  - "**重置两个矩效果最好**；只重置二阶矩「quite effective」；**只重置一阶矩（即纯动量）无效**。"
  - "55 个 Atari 游戏、10 seeds、human-normalized：重置 Adam / RAdam 的 Rainbow**明显优于**不重置（mean 与 median 均改善）。"
  - "**边界**：连续控制（MuJoCo + SAC 软目标更新）下帮助不明显，作者称「何时重置不清楚」。"
method: "在 Rainbow（Rainbow Pro）中，每 K 步重置优化器内部参数（K=1000 重置 Adam；K=4000 重置 RAdam；基线 K=8000 不重置）；对比只重置一阶/只重置二阶/两个都重置"
baseline: "Rainbow + Adam（不重置）；Rainbow + Rectified Adam"
metrics: [55 游戏 human-normalized 均值与中位数分数]
related:
  - "[[2024-Ellis-Adam-on-Local-Time|Adam on Local Time：保留动量、只重置时间步（反例）]]"
  - "[[2026-Sahu-Momentum-SGD-Nonstationary|Sahu 2026：动量在非平稳下的可证明次优性]]"
  - "[[INDEX|方法论论文索引]]"
---

# 在深度强化学习中重置优化器：一项实证研究

> **证据等级**：在线全文已下载（`raw/papers/methodology/2023-Asadi-Resetting-Optimizer-Deep-RL.pdf`，arXiv v1）。

## 核心结论

- **问题表述**：深度 RL 的值函数逼近 = **损失函数每次迭代都变的优化问题序列**。
  Adam 维护的一阶/二阶矩估计在迭代间**沿用**，因此历史信息被带入当前迭代，**污染矩估计**。
- **对策**：**在新迭代开始时重置优化器内部参数**。
- **消融（关键）**：
  - **只重置一阶矩 → 无效**；
  - **只重置二阶矩 → quite effective**；
  - **两个都重置 → 最好**。
- **实验**：Rainbow + 55 Atari 游戏 + 10 seeds + human-normalized。重置 Adam / 重置 RAdam 明显优于不重置。
- **边界**：连续控制（MuJoCo + SAC）下效果不明显，作者承认「何时重置不清楚」，留作未来工作。

## 与本提案的关系

- **正面**：为「优化器状态在分布边界携带历史造成危害」提供了**最直接的实证命题与命名**（contamination effect），
  且给出「重置哪一个矩」的操作性结论。
- **关键的、对本提案不利的细节**：**「只重置一阶矩无效」**。本提案的机制是 **SGD momentum（纯一阶动量）**——
  按本文结论，**单独重置动量可能不足以解决问题**。本课题若要立这个机制，必须正面回应这一点：
  Asadi 的结论在 Adam 语境（若二阶矩仍在，自适应缩放会继续吸收历史）；
  纯 SGD 动量下没有二阶矩，结论**不可直接外推**，但也**没有正面证据支持纯动量重置有效**。
- **可用性三问**：
  1. 固定 200 条预算 / 每年度 10 轮协议：**不能直接套用**——原设定是 RL/Atari，非监督分类，无「年度任务序列」概念。
  2. 四层 MLP：**不适用**——骨干是 DQN 的卷积网络；机制本身与架构无关，但实验不提供 MLP 证据。
  3. 公开代码：**未确认**。相关实现可能是同作者前作 Rainbow Pro 的 `github.com/amazon-research/fast-rl-with-slow-updates`，
     **但搜索未找到本论文自身仓库的直接链接**，标为「代码未确认」。
