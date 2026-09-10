---
title: "Proximal Policy Optimization Algorithms（PPO）"
authors: [John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov]
year: 2017
date: 2026-09-10
journal: "arXiv:1707.06347v2（2017-07-20 首版，12 页，OpenAI）"
source_pdf: "[[raw/papers/grpo/2017-Schulman-PPO-Proximal-Policy-Optimization.pdf]]"
tags:
  - PPO
  - 强化学习
  - 策略梯度
  - 信任域
  - 裁剪
  - 家族始祖
  - 类型/论文
key_finding: "用**裁剪的代理目标**替代 TRPO 的约束优化：`L^{CLIP}(θ) = Ê_t[ min( r_t(θ)Â_t, clip(r_t(θ), 1−ε, 1+ε)Â_t ) ]`（式(7)，§3，p.3），只保留 `r_t` 落在 `[1−ε, 1+ε]` 内时的较小者，从而**用一阶方法近似信任域更新**，无需二阶求解、无需约束优化。另给一个自适应 KL 惩罚的替代形式（§4，式(8)，p.4），并建议在小批量上做多轮（multi-epoch）更新（§5，p.5）。论文同时明确 PPO 使用 actor-critic，优势由学习到的价值函数估计——**GRPO 家族的全部后续工作都是在去掉这个 critic 并改动本式**。"
method: "裁剪代理目标（式(7)，p.3）＋ 价值函数损失（式(9)）＋ 熵奖励，联合优化（式(9)，p.4）；替代方案为自适应 KL 惩罚（式(8)，p.4）；算法伪码 Algorithm 1，p.5"
baseline: "TRPO 等信任域方法；实验在 Atari、MuJoCo 连续控制与人形机器人任务上（§6，p.5–7）"
aliases:
  - PPO
  - Schulman2017-PPO
  - Proximal Policy Optimization
related:
  - "[[2024-Shao-DeepSeekMath与GRPO开山]]"
  - "[[2025-Yu-DAPO解耦裁剪与动态采样]]"
  - "[[2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE风格]]"
  - "[[GRPO变体群-方法选型]]"
---

# PPO：裁剪代理目标

> John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov（OpenAI），2017，arXiv:1707.06347v2 · 12 页 · 原件 `raw/papers/grpo/2017-Schulman-PPO-Proximal-Policy-Optimization.pdf`

## 证据等级

**E3 全文级**。原件已下载（arXiv 1707.06347v2，3.3 MB，12 页），正文逐节读完；公式经 MinerU `extract` 模式转 LaTeX 后回原文页核对，页码锚点用逐页文本索引确认（`pypdf` 只读检索，2026-09-10）。

**收录理由**：PPO 不属于 GRPO 家族，但**是本目录内全部 critic-free 方法的共同祖先与参照基线**——GRPO 的组相对优势、DAPO 的 Clip-Higher、GSPO 的序列级裁剪、SAPO 的软门、Simoni-GTPO 的去 KL，全都以对本节的修改来定位自身。列入家族谱系作**根节点**。

## 一句话

把 TRPO 的"约束在 KL 球内"换成"裁剪重要性比率"，用一阶方法拿到近似同等的单调改进保证，代价是引入一个需要调的超参 ε。

## 机制（§3–§5，p.3–5）

### 裁剪代理目标（§3，式(7)，p.3）

`L^{CLIP}(θ) = Ê_t[ min( r_t(θ)·Â_t , clip(r_t(θ), 1−ε, 1+ε)·Â_t ) ]` …(7)

其中 `r_t(θ) = π_θ(a_t|s_t) / π_θold(a_t|s_t)`。

- 取 `min` 的效果（p.3）：当 `Â_t > 0` 时，若 `r_t > 1+ε` 则梯度被截断；当 `Â_t < 0` 时，若 `r_t < 1−ε` 则梯度被截断。**只惩罚"朝有利方向走得太远"的更新**，反向的比率变化不被惩罚（这是裁剪切而不对称的根源，也是 DAPO Clip-Higher 与 SAPO 软门的着力点）。
- 与 TRPO 的对比（p.3）：TRPO 需要二阶求解与约束优化；本式只需一阶梯度。

### 替代方案：自适应 KL 惩罚（§4，式(8)，p.4）

`L^{KLPEN}(θ) = Ê_t[ r_t(θ)Â_t − β·KL[π_θold(·|s_t) ‖ π_θ(·|s_t)] ]`，并给出 β 的自适应调整规则（按实测 KL 与目标 KL 的比值缩放，p.4）。作者报告裁剪形式实验效果更好，但未否证 KL 形式。

### 完整目标与算法（§5，式(9)，p.4–5）

`L^{CLIP+VF+S}(θ) = Ê_t[ L^{CLIP}(θ) − c₁·L^{VF}(θ) + c₂·S[π_θ](s_t) ]` …(9)

- `L^{VF}` 是价值函数的平方误差——**PPO 是 actor-critic**。
- `S` 是熵奖励，鼓励探索。
- Algorithm 1（p.5）：固定长度轨迹、T 步、多轮 minibatch 更新——**"同一批数据多轮更新"正是后续 off-policy 比率受限的根源**。

## 实验（§6，p.5–7）

| 项 | 内容 | 位置 |
|---|---|---|
| 对比目标 | 裁剪 vs KL 惩罚 vs 无裁剪 | §6.1，p.5 |
| 连续控制 | 与 TRPO、ACER、A2C 等对比 | §6.2，p.6 |
| 人形机器人 | 高维连续控制 | §6.3，p.6–7 |
| Atari | 与 A2C、ACER 对比 | §6.4，p.7 |

## 可迁移机制

1. **信任域的两种实现方式**（§3 vs §4，p.3–4）：裁剪（硬、免调 β、但不对称）与 KL 惩罚（软、需调 β）。**GRPO 家族后续的每一次"裁剪修正"（Clip-Higher、序列级裁剪、软门、去 KL）都是在这两个选项之间重新选点**，引用任一修正时都应回到本节的原始取舍。
2. **`min` 的不对称性**（式(7)，p.3）：`min` 只对"有利于优势方向且超出上界"的更新设限，对反向变化不设限——**这是后来 DAPO 认为会压制低概率 token、导致熵坍塌的结构原因**。
3. **多轮 minibatch 更新引入 off-policy**（Algorithm 1，p.5）：同一批 rollout 更新多轮意味着旧策略数据被反复使用，比率 `r_t` 偏离 1。**这是"重要性比率"问题在本家族中最上游的来源**。
4. **一组通用超参的存在性**（摘要、§6）：PPO 的核心卖点之一是同一套超参在多个域上可用。**这也提示：任何新增的"修正"都应以"增加超参数量"为代价**——SAPO 加 τ、GMPO 加聚合选择、GTPO 加 α 与 γ，都是这条权衡的实例。

## 不能直接声称内容

- **不能把 PPO 的实验结论搬到 LLM**：全部实验是 **Atari 与 MuJoCo 连续控制／人形机器人**（2017 年），**没有任何语言模型实验**。PPO 在 LLM 上的适用性是后续工作（如 InstructGPT）建立的，不是本文的结论。
- **不能把本文的 ε 默认值当作 LLM RL 的推荐值**：论文的超参表（附录 §A，p.11）面向连续控制与 Atari，与 LLM RL（如 DAPO 的 0.2/0.28、GSPO 的 3e-4/4e-4）量级完全不同。
- **不能声称 PPO 的裁剪能保证单调改进**：作者写作"近似"信任域，论文未给单调性证明；单调改进的保证属于 TRPO。
- **不能忽略 PPO 需要 critic**：式(9) 的价值函数项是 PPO 的组成部分；"PPO 去掉 critic 就变成 GRPO"这一说法成立的前提是同时替换优势估计方式（组相对），而不只是删掉一项。

## 与课题的关系

- 作为家族根节点，本笔记的用途是**给所有下游修正定位**：GRPO 换掉 critic 与优势；DAPO 解耦裁剪上下界并改采样与损失归约；Dr. GRPO 改优势归一化；GSPO 改比率粒度；GMPO 改聚合算子；SAPO 把裁剪换成软门；Simoni-GTPO 去掉 KL 并加冲突掩码。
- 对本课题的选择：DRIFT 第三章目前的工作假设是 critic-free（TTA 与轻量适应方向），PPO 的 critic 成本论证在 [[2025-Yue-VAPO价值模型增强PPO]] 中被反向质疑。**两侧证据都需在自有任务上实测**，本笔记不构成选型依据。

## 疑问 / 待验证

- 论文未报告：种子数、方差、训练算力；2017 年的实验规模与现代 RL 不可比。
- §6.1 的"裁剪优于 KL"结论是在其自建任务上得出，未在 LLM 上复核。
- 论文的 Algorithm 1 采用固定轨迹长度；变长轨迹（LLM 场景）下的实现差异（如按 token 归一化）本文未涉及，而这正是 Dr. GRPO／DAPO 争论文档的焦点。

## 文献信息

- arXiv:1707.06347v2（2017-07-20 提交，v2 修订）· OpenAI · 5 位作者
- 题录核验：arXiv API 直查 `id_list=1707.06347` 返回题名《Proximal Policy Optimization Algorithms》、作者、日期（2026-09-10 核验）；Zotero key `99PMC6CL`
- 原件：`raw/papers/grpo/2017-Schulman-PPO-Proximal-Policy-Optimization.pdf`
