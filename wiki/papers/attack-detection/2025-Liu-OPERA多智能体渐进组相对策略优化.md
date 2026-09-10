---
title: "OPERA: A Reinforcement Learning--Enhanced Orchestrated Planner-Executor Architecture for Reasoning-Oriented Multi-Hop Retrieval"
title_zh: "OPERA 与 MAPGRPO：多智能体渐进组相对策略优化（该名称已被占用）"
authors: [Yu Liu, Yanbing Liu, Fangfang Yuan, Cong Cao, Youbang Sun, Kun Peng, Weizhuo Chen, Jianjun Li, Zhiyuan Ma]
year: 2025
date: 2026-09-10
journal: "arXiv:2508.16438v4（2025-08-22 首版），17 页"
source_pdf: "[[raw/papers/attack-detection/2025-Liu-OPERA.pdf]]"
arxiv_id: "2508.16438"
tags:
  - GRPO
  - 多智能体
  - MAPGRPO
  - 分阶段训练
  - 组相对优势
  - GRPO×MARL锚点
  - 类型/论文
key_finding: "提出 **MAPGRPO**（Multi-Agents Progressive Group Relative Policy Optimization）：对 N 个异构智能体**按顺序**逐个优化，$\\theta_k^*=\\arg\\max_{\\theta_k}\\mathcal{J}_k(\\theta_k\\mid\\theta_{<k}^*)$（定义 1，式(5)，p.4）。其组构造有一个与本课题相关的具体设计：每组由 **G−1 个当前策略采样候选 + 1 个来自离线预打分数据集 $\\mathcal{D}_{scored}$ 的最优样本**组成（算法 1 第 4–6 行，p.4），即用离线数据人为抬高组内基线。消融显示 MAPGRPO 使 EM 从 GRPO 的 34.8% 升到 **39.7%**（Musique，Table 2，p.6）。**关键作用：`MAPGRPO` 这一名称在 2025 年已被本文占用。**"
method: "OPERA 架构（Plan / Analysis-Answer / Rewrite 三类智能体）+ MAPGRPO 三阶段顺序训练；每阶段用 GRPO 损失更新，优势由组均值基线给出（式(2)，p.4），KL 系数 β 约束（式(4)，p.4）；组内混入离线预打分样本作 `cbest`"
baseline: "CoT、SFT、标准 GRPO（同架构不同优化方式）；主表另有 HotpotQA / 2WikiMultiHopQA / Musique 上的多跳检索基线"
aliases: [OPERA, MAPGRPO, Liu2025]
related: ["[[2026-Cang-Graph-GRPO边级组相对策略优化]]", "[[2026-Feng-M2GRPO曼巴多智能体组相对策略优化]]", "[[2024-Shao-DeepSeekMath与GRPO开山]]"]
---

# OPERA 与 MAPGRPO

> 页码锚点：本地 PDF 共 17 页（正文 7 页 + 附录 10 页）。问题形式化见 §3 `Problem Formulation`（p.3）；架构总览见 §3 `Overview and Architecture`（p.3）；**MAPGRPO 与算法 1 见 §3（p.3–5）**；理论分析见 §3（p.5）；实验见 §4（p.5–7）；消融 Table 2 见 §4 `Ablation Studies`（**p.6**）；附录见 p.10–17。

## 一句话

这是**"`MAPGRPO`"这一名称在文献中已被占用**的直接证据，且它给出了一个对本课题有参考价值的组构造技术：**把离线预打分样本混进组内充当基线锚点**。

## 与 P4 的距离（通用 MARL 方法论文，不属安全域四级表）

| 层级 | 学习关系 | 典型 |
| --- | --- | --- |
| 1 | 固定/算法攻击 + 学习检测器 | CharBot / MaskDGA / Drichel |
| 2 | 学习型攻击者 + 固定目标检测器 | MAB-Malware |
| 3 | 学习型攻击者 + 学习 surrogate | MalGAN / IDSGAN |
| 4 | attacker + 实际 defender 共演化 | RELEVAGAN / 2026 bilevel |

**不属四级表任何一层**：任务是**多跳检索问答**（HotpotQA / 2WikiMultiHopQA / Musique），三个智能体是**协作分工**（规划 / 分析回答 / 重写），不是对抗关系。角色是 report (8) 所记的 **"`MAPGRPO` 名称已有使用"** 这一反面证据。

## 机制（§3，p.3–5）

**GRPO 复习**（式(1)–(4)，p.4）：目标 $\mathcal{J}_{GRPO}(\theta)=\mathbb{E}_{x}[\mathbb{E}_{y_i\sim\pi_\theta}[A_i(x,y_i)]]$；优势 $A_i = r(x,y_i) - \frac{1}{G}\sum_j r(x,y_j)$（式(2)）——**相对组均值**；策略梯度式(3)；损失式(4) 加 KL 项 $\beta\mathbb{D}_{KL}[\pi_\theta||\pi_{ref}]$ 防坍缩。

**定义 1（MAPGRPO）**（p.4）：给定 $N$ 个带异构奖励函数 $\{r^{(k)}\}$ 的专门智能体，**逐个顺序优化**：

$$\theta_k^* = \arg\max_{\theta_k} \mathcal{J}_k(\theta_k \mid \theta_{<k}^*)$$

即后一个智能体在前序智能体**已优化完成**的条件下训练。

**组构造（本文最特殊之处）**（算法 1，p.4）：每个 batch 内，先生成 $G-1$ 个候选，再**从离线预打分数据集 $\mathcal{D}_{scored}$ 中取分数最高的样本** $c_{best}\leftarrow\arg\max_{c\in\mathcal{D}_{scored}(q)} r_{pre}(q,c)$，把它并入候选集合，然后对这 $G$ 个候选算奖励并用 GRPO 损失更新。**三阶段（Plan → Analysis-Answer → Rewrite）各自重复该流程。**

**训练对象**：三个智能体参数 $\{\theta^*_{plan},\theta^*_{ana},\theta^*_{rew}\}$ **分别、顺序**优化（算法 1，p.4）。

## 实验结果（§4，p.5–7）

- **主结果**（p.6）：HotpotQA **57.3% EM**（最强基线 45.7%）、2WikiMultiHopQA **60.2%**（44.3%）、Musique **39.7%**（24.3%）。
- **训练方法的递进**（Table 2 讨论，p.6）：CoT **21.2%** EM → SFT **24.3%** → GRPO **34.8%** → **MAPGRPO 39.7%**。作者解释 MAPGRPO 的增益来自"专门的奖励函数 + 顺序训练更贴合规划/推理/检索各自的不同要求"。
- **架构影响大于训练方法**（p.6）：去掉 Plan Agent 使 Musique EM 从 39.7% 跌到 **17.1%**（低于未训练的 CoT 基线 21.2%）；去掉 Rewrite Agent 降到 34.5%；**两者同时去掉降到 16.7%（比单独去掉任一个都差）**——作者据此论证组件间存在相互依赖，不是可独立替换的模块叠加。
- 该结论对本课题的提示：**"组件协同"的论证需要"单独去掉"与"同时去掉"的对照**，而不是只报完整模型的最优值。

## 非平稳性处理方式

**不处理对抗性非平稳**。三智能体是协作者而非对手；没有对手建模、种群、replay 或双人博弈。所谓"progressive"指的是**智能体之间按阶段推进**，不是"对手随训练变化"。

## 可迁移机制

1. **`MAPGRPO` 名称已被占用（本笔记的核心用途）**：若本课题方案在正文使用该缩写，**必须改换命名或明确引用本文**，不得暗示为首创。同理，"多智能体 + 组相对策略优化"这一组合已有本文与 Graph-GRPO、M²GRPO 三条独立先例。
2. **顺序优化取代联合优化**（定义 1，式(5)，p.4）：当多个被优化对象有**异构奖励**且相互依赖时，逐个在"前者已更新"的条件下优化，是一种可用的替代方案。**对本课题的对应是：攻击侧与防守侧若奖励异构，可否顺序交替而非同步更新**——这是一个形式上的选项（但本文的无对抗性使其只能作形式参考）。
3. **用离线预打分样本抬高组内基线**（算法 1，p.4）：把已知"好"的样本混进组内，会**改变组均值基线**，从而使当前策略采样得到的样本优势被重新标定。**这是"在组相对基线里注入先验"的具体做法**，若本课题需要让组基线对齐某个参考分布，这是一条实现路径。
4. **组件协同要用双删除对照证明**（p.6）：单独删除 vs 同时删除两个组件的对照显示**协同效应**（16.7% 低于任一单独删除），可作为"机制不可分解"论证的检验形态参考。

## 不能直接声称内容

- **不能把 MAPGRPO 当作本课题提出的机制**：该名称与该方法均为 2025 年已有工作。
- **不能把它算作 P4 近邻**：任务域是多跳检索问答，无安全数据、无攻击者、无检测器。
- **不能把其"顺序优化"等同于对抗博弈的交替更新**：这里没有对手，顺序来自工程依赖（规划结果供后续阶段使用），不是对对手变化的响应。
- **不能把 39.7% EM 与任何安全指标并列**：指标是问答 EM，任务完全不同。
- **它是预印本（arXiv v4）**，未经同行评议；report (8) 亦据此降低其证据权重。

## 文献信息

- arXiv：<https://arxiv.org/abs/2508.16438>（v4；首版 2025-08-22）
- 本地原件：`raw/papers/attack-detection/2025-Liu-OPERA.pdf`
- 来源核验：report (8) 台账标记 **◐**（"OPERA / MAPGRPO， arXiv 2025，摘要；`MAPGRPO` 名称已有使用"）；本次经 arXiv API 复核题录并**本地全文核验机制**
- 台账记录：`.Codex/docs/2026-09-10-DGA对抗文献入库/notes.md`
