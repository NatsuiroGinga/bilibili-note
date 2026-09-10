---
title: "Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs（提出 RLOO）"
authors: [Arash Ahmadian, Chris Cremer, Matthias Gallé, Marzieh Fadaee, Julia Kreutzer, Olivier Pietquin, Ahmet Üstün, Sara Hooker]
year: 2024
date: 2026-09-10
journal: "arXiv:2402.14740v2（2024-02-22 首版，v2 修订，28 页）"
source_pdf: "[[raw/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE-Style.pdf]]"
tags:
  - REINFORCE
  - RLOO
  - 去评论家
  - 强化学习
  - RLHF
  - 偏好优化
  - 类型/论文
key_finding: "在 RLHF 场景中系统检验 PPO 的两项默认设计，结论是**两项都不必要**：① **裁剪很少必要**——实测整个训练过程中损失被裁的比例**平均 < 5%**，说明策略逐轮变化很小、学习接近 on-policy；完全去掉裁剪甚至略有提升（§3.2，p.8）；② **建模部分完成序列不必要**——LLM 生成的"环境"是确定的，奖励只落在 `<EOS>`，问题可归约为 bandit，把整条生成当成单个动作就够（§3.3，p.8）。据此提出 **RLOO**（REINFORCE Leave-One-Out）：用同 prompt 的其余 k−1 条样本来给第 i 条构成无偏基线，在 **k=2 时就用更省的计算超过 RAFT**，并全面超过 DPO 与 PPO（§6、图 3，p.8）。"
method: "RLOO 估计量（式(9) 附近，§2.3，p.5）：`(1/k)Σ_i [R(y_(i),x) − (1/(k−1))Σ_{j≠i} R(y_(j),x)] ∇logπ(y_(i)|x)`；对照 Vanilla PG（无裁剪 REINFORCE）、REINFORCE w/ baseline、PPO、RAFT、DPO"
baseline: "PPO、Vanilla PG、REINFORCE(w/ baseline)、RAFT、DPO；数据 TL;DR Summarize（116k 指令 / 93k 偏好对）与 Anthropic-HH（112k 偏好对）；模型 Pythia-6.9B、Llama-7B；上下文长度 512；评测 1000 测试样本的平均奖励 + GPT-4 模拟胜率（§4.1–4.2，p.8–9）"
aliases:
  - RLOO
  - REINFORCE Leave-One-Out
  - Ahmadian2024-RLOO
related:
  - "[[2025-Hu-REINFORCE-plus-plus全局优势归一化]]"
  - "[[2024-Shao-DeepSeekMath与GRPO开山]]"
  - "[[2023-Rafailov-DPO直接偏好优化]]"
  - "[[GRPO变体群-方法选型]]"
---

# RLOO：把 PPO 的默认设计一项项去掉

> Arash Ahmadian 等（Cohere / Cohere For AI 等），2024，arXiv:2402.14740v2 · 28 页 · 原件 `raw/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE-Style.pdf`

## 证据等级

**E3 全文级**。原件已下载（arXiv 2402.14740v2，988 KB，28 页），正文与限制逐节读完；公式经 MinerU `extract` 模式转 LaTeX 后回原文页核对，页码锚点用逐页文本索引确认（`pypdf` 只读检索，2026-09-10）。

## 一句话

在 LLM 的 RLHF 里策略本来就已经很强、又额外以 prompt 为条件，因此传统 Deep-RL 里那些用来防高方差的手段（裁剪、部分完成建模）大多用不上；只用最简单的 REINFORCE 加一个留一法基线就够了。

## 机制（§2–§3，p.4–8）

### RLOO 估计量（§2.3，p.5）

`(1/k) Σ_{i=1}^{k} [ R(y_(i), x) − (1/(k−1)) Σ_{j≠i} R(y_(j), x) ] ∇logπ(y_(i)|x)`，`y_(1..k) ~ᵢᵢ𝒹 π_θ(·|x)`

- 每条样本 `y_(i)` 用**其余 k−1 条**构造期望回报的无偏估计，充当**无需参数的"价值函数"**，且每个训练步在线重建（p.5）。
- 与 REINFORCE w/ baseline 的区别：基线 `b_MA` 是全局移动平均，RLOO 的基线逐样本、逐步骤在线生成，因而更有效（p.5）。
- 代价是训练时采样时间增加（p.5）。

### 两项"不必要"的论证

**裁剪（§3.2，p.8）**：整个训练过程中、所有数据集与基座组合上，损失被裁剪的时间比例**平均 < 5% per batch**——说明策略变化缓慢、学习接近 on-policy。作者进一步**完全关闭裁剪**、乃至去掉比率 `π_θ/π_old`（令 λ=1，PPO 损失退化为 Vanilla PG），性能**不降反略升**。

**部分完成建模（§3.3，p.8）**：PPO 把每个 token 当动作，但 RLHF 中奖励只加在 `<EOS>`，其余 token 的 `log(π/π_ref)` 并不构成有意义的中间奖励。由于环境动态完全确定（`P_D({y_{<t+1},x} | s_t, y_t) = 1`），问题可归约为 **bandit**：只有初始状态（prompt）与终止状态。REINFORCE／RLOO 把整条生成当单个动作，正是这一归约的显式实现。

### 结论（§6，p.14）

作者的立场：LLM 的 RLHF 有**很强的策略初始化**，且进一步以 prompt 为条件，这**缓解了历史上对高方差与大动作空间的担忧**。

## 实验结果（§4–§5，p.8–14）

| 项 | 内容 | 位置 |
|---|---|---|
| 数据 | TL;DR Summarize（116k 指令 / 93k 偏好对）、Anthropic-HH（112k 偏好对） | §4.1，p.8 |
| 模型 | Pythia-6.9B（主）、Llama-7B（消融基座质量影响） | §4.1，p.8 |
| 上下文长度 | SFT 与奖励模型训练统一 512 token（为公平比较） | §4.1，p.8 |
| 评测 | 1000 条测试样本的平均奖励（内禀目标）＋ 以 GPT-4 为代理的模拟胜率（外禀目标） | §4.2，p.9 |
| 主要结论 | **RLOO 一致优于所有其它方法**；**Vanilla PG 一致优于 PPO** | 图 2，p.9 |
| 采样效率 | k=2 的 RLOO 即**超过或持平 k=4 的 RAFT**（同预算，两个数据集、Pythia 基座） | 图 3，p.9 |
| 鲁棒性 | RLOO 相对 RAFT 等迭代微调方法保持高鲁棒性（§6，p.14） | §5.2.2 |

## 可迁移机制

1. **"裁剪使用率"是一个可直接测量的诊断量**（§3.2，p.8）：统计每批损失被裁剪的比例。**若该比例长期很低，说明裁剪机制在该任务上近乎空转**——这是一个廉价、可机械化的检查，可用于判断是否值得引入裁剪。
2. **确定性环境 + 终端奖励 ⇒ 可归约为 bandit**（§3.3，p.8）：这是一条**结构判据**。凡"动作只影响上下文、奖励只在终止给"的任务，把整条轨迹当单个动作是合理归约。**对本课题的检测流程是否适用需要单独论证**（检测通常有中间判断步骤）。
3. **留一法基线是无参价值函数**（p.5）：在无法负担 critic 时，用同组其余样本的均值替代——**组内交叉基线**是一个通用技巧。
4. **"策略初始化很强"这一前提决定方法选择**（§6，p.14）：作者把 REINFORCE 类方法的成功明确归因于 SFT 初始化带来的低方差起点。**这是一个可证伪的前提**：在弱初始化 / 从零训练的场景下，该结论可能反转。
5. **内禀指标与外禀指标分开报**（§4.2，p.9）：用训练奖励衡量"优化内禀目标的好坏"，用胜率衡量"对齐外禀目标的好坏"。这一双指标结构可直接借用到本课题（训练损失 vs. 目标年指标）。

## 不能直接声称内容

- **不能把 RLOO 的结论搬到 RLVR／推理任务**：本文实验全部是 **RLHF 偏好优化**（TL;DR 摘要、Anthropic-HH），奖励来自**奖励模型**而非可验证规则；任务类型与当代推理 RL 差异很大。
- **不能声称"裁剪永远不必要"**：作者限定在**策略变化缓慢、接近 on-policy** 的 RLHF 设置（< 5% 裁剪率，p.8）；在强 off-policy、异步训练或多轮场景下结论可能反转。
- **不能忽略作者自陈的限制**（§7，p.14）：本文**未研究奖励模型过优化**（proxy reward 与 gold reward 的偏离）；胜率是 **GPT-4 模拟**而非真人评测；未尝试 ROUGE／BLEU 等其它奖励；也未在"单 token 动作 + 中间奖励"框架下探索 LOO 基线。
- **不能把"RLOO 优于 PPO"当作在所有基座上成立**：主实验是 Pythia-6.9B，Llama-7B 只做基座质量消融（§4.1）。
- **不能引用未在正文列出的具体胜率数值**：奖励曲线在图中（图 2、图 3），正文未给完整数值表。

## 与课题的关系

- 与 [[2025-Hu-REINFORCE-plus-plus全局优势归一化]] 构成**同一条线的两代工作**：RLOO 用留一法基线（局部），REINFORCE++ 用全局批次归一化，并对局部归一化提出"有偏"的批评。两者对"基线的作用域"给出相反的候选，**须并列引用**。
- OpenRLHF 把 RLOO 列为 `--algo.advantage.estimator rloo` 档位，是 critic-free 家族中与 GRPO 并列的实现（OpenRLHF README，2026-09-10 核验）。
- 对本课题的价值是**方法选择的前提条件检查**：作者把 REINFORCE 类的成功归因于"强策略初始化"。若本课题的检测模型初始化较弱，则该结论的前提不成立——**这是一个必须先行核验的条件，而不是可直接沿用的结论**。

## 疑问 / 待验证

- 论文未报告：种子数、方差、训练算力预算的具体数值。
- "< 5%"裁剪率是**跨任务的平均**，正文未给逐任务的分布，也未给随时间的变化。
- 图 2、图 3 的奖励曲线未配数值表，方法间的差距量级无法从正文引用。
- "Vanilla PG 优于 PPO"这一反常结论的机理，作者只归因于裁剪空转，未做进一步消融。

## 文献信息

- arXiv:2402.14740v2（2024-02-22 提交，v2 修订）· Cohere / Cohere For AI 等 · 8 位作者
- 题录核验：arXiv API 直查 `id_list=2402.14740` 返回题名《Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs》、作者、日期（2026-09-10 核验）；Zotero key `HXRQG7PU`
- 实现：OpenRLHF `--algo.advantage.estimator rloo`（OpenRLHF README，2026-09-10 核验）
- 原件：`raw/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE-Style.pdf`
