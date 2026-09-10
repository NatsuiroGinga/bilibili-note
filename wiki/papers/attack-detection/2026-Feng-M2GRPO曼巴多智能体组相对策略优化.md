---
title: "M$^{2}$GRPO: Mamba-based Multi-Agent Group Relative Policy Optimization for Biomimetic Underwater Robots Pursuit"
title_zh: "M²GRPO：把组相对优势扩展到多智能体的机器人追捕工作"
authors: [Yukai Feng, Zhiheng Wu, Zhengxing Wu, Junwen Gu, Junzhi Yu]
year: 2026
date: 2026-09-10
journal: "arXiv:2604.19404v1（2026-04-21），9 页"
source_pdf: "[[raw/papers/attack-detection/2026-Feng-M2GRPO.pdf]]"
arxiv_id: "2604.19404"
tags:
  - GRPO
  - 多智能体
  - 组相对优势
  - Mamba
  - CTDE
  - GRPO×MARL锚点
  - 类型/论文
key_finding: "明确把 GRPO 扩展到多智能体（称 MAGRPO）：N 个智能体各自在 $G$ 个并行环境中执行同一任务，对每个智能体在**其并行组内**对回报做标准化得优势 $A_j^i=(R_j^i-\\overline{R}^i)/(\\mathrm{Std}^i(R)+\\tau)$（式(5)，p.4），再用 PPO 式裁剪目标更新（式(6)，p.4）；作者自述该设计**不需要价值函数或全局基线**，并用 CTDE（集中训练、分散执行）保持可扩展性（§III-B，p.4）。任务是仿生水下机器人追捕，与安全无关。"
method: "Mamba 策略骨干 + 交互编码 + 时序建模分支；MAGRPO 组归一化优势（式(5)）+ PPO 裁剪比率目标（式(6)）；奖励 = 捕获奖励 + 辅助引导奖励 + 安全奖励（式(7)，p.4）"
baseline: "消融：去掉时序建模分支、去掉交互编码、把 Mamba 换成普通 MLP（§IV-B，Table I）"
aliases: [M2GRPO, MAGRPO, Feng2026]
related: ["[[2026-Cang-Graph-GRPO边级组相对策略优化]]", "[[2025-Liu-OPERA多智能体渐进组相对策略优化]]", "[[2024-Shao-DeepSeekMath与GRPO开山]]"]
---

# M²GRPO：多智能体组相对策略优化

> 页码锚点：本地 PDF 共 9 页。方法见 §III（**p.3–5**）；Mamba 策略见 §III-A（p.3–4）；**MAGRPO 见 §III-B（p.4）**；奖励设计见 §III-C（p.4–5）；算法与实现见 §III-D（p.5）；消融见 §IV-B（**p.6**）。
> **署名待核**：本轮提取文本未逐字核对完整作者列表，引用前须回原件首页复核（已登记为待办）。

## 一句话

又一篇"**GRPO 已被扩展到多智能体**"的直接证据——与 Graph-GRPO 同属 report (8) 所列的 **GRPO×MARL 已有先例**，本课题**不得再把"多智能体 GRPO"本身作为创新主张**。

## 与 P4 的距离（通用 MARL 方法论文，不属安全域四级表）

| 层级 | 学习关系 | 典型 |
| --- | --- | --- |
| 1 | 固定/算法攻击 + 学习检测器 | CharBot / MaskDGA / Drichel |
| 2 | 学习型攻击者 + 固定目标检测器 | MAB-Malware |
| 3 | 学习型攻击者 + 学习 surrogate | MalGAN / IDSGAN |
| 4 | attacker + 实际 defender 共演化 | RELEVAGAN / 2026 bilevel |

**不属于四级表任何一层**：这是**机器人控制**任务（仿生水下机器人追捕逃逸者），多智能体是**协作追捕**而非对抗学习。角色与 Graph-GRPO 相同——"GRPO × MARL 不能声称新"的锚点。

## 机制（§III-B，p.4）

系统含 $N$ 个智能体，每个智能体 $i$ 在 $G$ 个并行环境中执行同一任务。设 $R_j^i$ 为智能体 $i$ 在第 $j$ 个环境的平均回合回报，则**组归一化优势**（式(5)）：

$$A_j^i = \frac{R_j^i - \overline{R}^i}{\mathrm{Std}^i(R) + \tau}, \quad j=1,\dots,G$$

其中 $\overline{R}^i$ 是智能体 $i$ 在 $G$ 个环境上的平均回报，$\tau$ 为稳定化系数。**"组"= 同一智能体的并行环境集合，而不是同一 input 下的多样本。**这是与 Graph-GRPO 及原始 GRPO 的关键差别，引用时须区分。

作者自述该设计"**消除了对显式价值函数或全局基线的需求**"，并在多环境采样下保证稳定的信用分配（p.4）。

**策略更新**（式(6)，p.4）：使用 PPO 式裁剪目标，含概率比率 $\rho_{j,t}^i(\theta)$ 与裁剪阈值 $\epsilon$，$L^i(\theta)=\mathbb{E}_{j,t}[\min(\rho A, \mathrm{clip}(\rho,1-\epsilon,1+\epsilon)A)]$。

**CTDE**（p.4）：集中训练时智能体共享环境信息并**并行**更新策略以促进协调；执行时各自仅依赖局部观测与历史，**分散执行**。作者强调"although **no centralized critic is used**, this CTDE paradigm preserves scalability"。

**奖励设计**（§III-C，式(7)，p.4）：$r^i = r^i_{cap} + r^i_{aux} + r^i_{safe}$（捕获奖励 + 辅助引导 + 安全奖励）；捕获奖励在追捕者与逃逸者欧氏距离低于阈值 $R_c$ 时给固定值 12；系数与阈值由**小范围先导扫描**做量级平衡选取。

**消融**（§IV-B，Table I，p.6）：完整模型最强；**去掉交互编码退化最大**，去掉时序建模亦有退化，把选择性状态空间（Mamba）骨干换成普通 MLP 进一步下降。

## 非平稳性处理方式

**不处理对抗性非平稳**：目标是协作追捕一个（非学习的）逃逸者，不存在"对手随我方更新而更新"。其"稳定性"来自**组归一化降低方差**与 CTDE 的训练/执行分离，**与双侧博弈的 moving-target 问题不是同一件事**。

## 可迁移机制

1. **组可以定义为"同一策略在多个并行环境/实例上的回报集合"**（式(5)，p.4）：说明 GRPO 的"组"并非必须是"同一 prompt 的多样本"，**只要组内元素共享一个可比的基线即可**。这是设计组相对权重时的另一种组划分方式。
2. **无价值函数的组归一化基线可替代 critic**（p.4）：与 GRPO 原思想一致，在多智能体下同样成立，且作者明确以"不需要全局基线"为卖点。
3. **比率裁剪 + 组归一化优势的组合**（式(6)，p.4）：即"GRPO 的组相对优势接 PPO 的裁剪目标"，是一种可直接借用的更新式组合。
4. **稳定性系数 $\tau$**（式(5)，p.4）：分母加小常数的做法与组标准差可能趋零的退化情形相关，**在组内奖励高度同质时需要该保护**。
5. **CTDE 的训练/执行分离**（p.4）：集中训练可用全局信息，部署时只需局部观测——**若本课题未来需要真实部署式的攻击/防御策略，这是标准的可行路径**。

## 不能直接声称内容

- **不能把 MAGRPO 称为本课题的机制贡献**：多智能体 GRPO 已有本文与 Graph-GRPO、OPERA/MAPGRPO 等多个先例。
- **不能把它算作 P4 近邻**：任务域是机器人追捕，无攻击者—防守者结构、无安全数据。
- **不能把其"组"与 GRPO 原式或 Graph-GRPO 的"组"混同**：本文的组是**并行环境**，Graph-GRPO 的组是**同一 query 的多拓扑**，原始 GRPO 的组是**同一问题的多输出**。三者含义不同。
- **原文有一处表述张力须登记**：§III-B（p.4）写 "no centralized critic is used"，而 §III-C（p.4）写 "under CTDE **centralized value estimation**"。二者是否矛盾需回原文（含图表与附录）复核后再引用，**本轮不裁定**。
- **它是 2026 年预印本**，证据权重低于已正式发表工作。
- **作者列表本轮未逐字核对**，引用前须回原件首页。

## 文献信息

- arXiv：<https://arxiv.org/abs/2604.19404>（v1，2026-04-21）
- 本地原件：`raw/papers/attack-detection/2026-Feng-M2GRPO.pdf`
- 来源核验：report (8) 台账标记 **◐**（arXiv 2026，摘要级）；本次经 arXiv API 复核题录（`ti:"M2GRPO"` 零命中，改 `all:"M2GRPO"` 才命中，因题名含 LaTeX `M$^{2}$GRPO`）
- 台账记录：`.Codex/docs/2026-09-10-DGA对抗文献入库/notes.md`
