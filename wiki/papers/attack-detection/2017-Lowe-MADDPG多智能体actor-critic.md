---
title: "Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments"
title_zh: "MADDPG：集中式 critic 与分散式执行的多智能体 actor-critic"
authors: [Ryan Lowe, Yi Wu, Aviv Tamar, Jean Harb, Pieter Abbeel, Igor Mordatch]
year: 2017
date: 2026-09-10
journal: "NIPS 2017（31st Conference on Neural Information Processing Systems）；arXiv:1706.02275；本地 PDF 16 页"
source_pdf: "[[raw/papers/attack-detection/2017-Lowe-MADDPG.pdf]]"
arxiv_id: "1706.02275"
tags:
  - 多智能体强化学习
  - actor-critic
  - 非平稳性
  - 集中式训练分散式执行
  - 对手建模
  - 技术来源
  - 类型/论文
key_finding: "提出 MADDPG：**集中式训练、分散式执行**的 actor-critic——每个智能体的 critic 额外吃进**全部智能体的动作** $Q_i^{\\pi}(\\mathbf{x}, a_1,\\dots,a_N)$，而 actor 只用本地观测（式(4)–(6)，p.4–5）。核心论证是：**只要条件在联合动作上，环境对每个智能体就是平稳的**，即 $P(s'|s,a_1,\\dots,a_N,\\pi_1,\\dots,\\pi_N)=P(s'|s,a_1,\\dots,a_N)$ 对任意 $\\pi_i\\neq\\pi_i'$ 成立（§4.1，p.5）——这一条正是 replay buffer 在多智能体下失效的根因所在（§3，p.3）。实验上 MADDPG 在合作通信（命中率 84.0%）、物理欺骗（$L=2$ 时欺骗成功率约 94%）等任务上大幅优于 DDPG/DQN/Actor-Critic/TRPO/REINFORCE（表 1、表 4，p.14）。"
method: "集中式 action-value critic（每个智能体一个，吃全部动作）+ 分散式 actor（只用本地观测）；可选对手策略近似 $\\hat{\\mu}_i^j$（式(7)–(8)，p.5）；可选策略集成 $K$ 个子策略按回合随机选一（式(9)，p.6）。底层为 DDPG 的确定性策略梯度。"
baseline: "DDPG、DQN、Actor-Critic、TRPO 一阶实现、REINFORCE，以及各方法之间的对抗式互打（MADDPG vs DDPG 双向配对）"
aliases: [MADDPG, Lowe2017-MADDPG, 多智能体深度确定性策略梯度]
related: ["[[2017-Lanctot-PSRO种群博弈论方法]]", "[[2017-Foerster-LOLA对手学习感知]]", "[[2020-Song-MAB-Malware学习型黑盒规避]]"]
---

# MADDPG：集中式 critic 与分散式执行的多智能体 actor-critic

> 页码锚点：本地 PDF 共 16 页。动机与两条传统方法病灶见 §1（**p.1**）与 §2（p.2）；Markov game 形式化见 §3（**p.3**）；式(1) 见 **p.3**，式(2) 见 **p.3**，式(3) 见 **p.4**；命题 1 见 **p.4**（证明见 **p.15**）；集中式 critic 与式(4)–(6) 见 §4.1（**p.4–5**）；对手策略近似与式(7)–(8) 见 §4.2（**p.5**）；策略集成与式(9) 见 §4.3（**p.5–6**）；实验环境见 §5.1（**p.6**）；主结果见 §5.2（**p.7–9**）；对手建模消融见 §5.3（**p.9**）；集成分散消融见 §5.4（**p.9**）；结论见 §6（**p.9–10**）；算法 1 见 **p.13**；结果表 1–5 见 **p.14**，表 6 与图 8 见 **p.15**。

## 一句话

这是**"对手在学导致环境非平稳"**这一问题的原始形式化之一：把 critic 从"只看自己"改成"看所有智能体的**联合动作**"，从而使转移概率对策略变化不再敏感；执行时把这份额外信息丢掉，各智能体仍只用本地观测。

## 与 P4 的距离（report (8) 四级表的第 — 层）

**本文不属于 report (8) 四级表的任何一层。** 它是**通用 MARL（多智能体强化学习）方法论文**，没有任何安全域的攻防对象：没有恶意软件、没有 DGA、没有检测器、没有攻击者—防御者关系。四级表刻画的是"**安全域内**攻防双方的学习关系"，而本文的"智能体"是合作/竞争环境中的一般学习主体（粒子世界、通信博弈）。

| 层级 | 学习关系 | 典型 | 本文是否在此层 |
| --- | --- | --- | --- |
| 1 | 固定/算法攻击 + 学习检测器 | CharBot / MaskDGA / Drichel | 否——无攻击者、无检测器 |
| 2 | 学习型攻击者 + 固定目标检测器 | MAB-Malware | 否——无"目标检测器"概念 |
| 3 | 学习型攻击者 + 学习 surrogate | MalGAN / IDSGAN | 否——无 surrogate、无安全目标 |
| 4 | attacker + 实际 defender 共演化 | RELEVAGAN / 2026 bilevel | 否——虽有多方共演化，但**不是攻防**、更非安全域 |

**本文在本课题中的角色是技术来源，不是近邻先例。** 具体来源点：

- **joint-action critic 的原始形式化**：$Q_i^{\pi}(\mathbf{x}, a_1,\dots,a_N)$（式(4)–(6)，p.4–5）——凡本文之后讨论"critic 该不该看对手动作"，引的是这里。
- **"条件在联合动作上即平稳"** 的论证（§4.1，p.5）——把 replay buffer 在多智能体下失效的根因讲清楚的是这一句。
- **对手策略的在线近似**（式(7)–(8)，p.5）——对手建模作为**可选项**（不假设已知对手策略）的写法来源。
- **策略集成作为抗过拟合手段**（§4.3，p.5–6）——"训练时对抗策略分布、执行时对未见策略稳健"的写法来源。

**不能因为"有学习型对手"就把它计入第 4 层或第 3 层**：四级表的划分依据是**安全域内的攻防角色**，本文既无攻击者也无防御者。

## 机制（§4，p.4–6）

### 问题：两条传统路径各自失效（§3，p.3–4）

- **Q-learning / DQN 路径**：各智能体独立学 $Q_i$ 时，因彼此策略持续变化，环境从任一智能体视角看非平稳，破坏 Q-learning 收敛所需的 Markov 假设。更关键的是 **replay buffer 不能用了**——因为当任一 $\pi_i \neq \pi_i'$ 时

  $$P(s' \mid s, a, \pi_1,\dots,\pi_N) \neq P(s' \mid s, a, \pi_1',\dots,\pi_N')$$

  （§3，p.3）。这正是本文要解的那个结。

- **Policy gradient 路径**：多智能体下梯度方差被放大。命题 1（p.4，证明 p.15）：对 $N$ 个二值动作智能体、奖励为"全部动作一致"的指示函数、初始化 $\theta_i = 0.5$，单样本策略梯度估计指向正确方向的概率为

  $$P(\langle \hat{\nabla} J, \nabla J \rangle > 0) \propto (0.5)^N$$

  即**随智能体数指数衰减**。注意附录（p.14）明确该例子"**没有时间分量**"（no temporal component）。

- **Deterministic policy gradient 路径**：依赖 $\nabla_a Q^{\mu}(s,a)$，**要求动作空间连续**（§3，p.4 原话：it requires that the action space $\mathcal{A}$ (and thus the policy $\mu$) be continuous）。

### 核心：集中式 action-value critic（§4.1，p.4–5）

记 $N$ 个智能体策略参数 $\boldsymbol{\theta}=\{\theta_1,\dots,\theta_N\}$、策略集合 $\boldsymbol{\pi}=\{\pi_1,\dots,\pi_N\}$。随机策略版本对智能体 $i$ 的期望回报梯度为

$$\nabla_{\theta_i} J(\theta_i) = \mathbb{E}_{s \sim p^{\boldsymbol{\mu}},\, a_i \sim \boldsymbol{\pi}_i}\left[\nabla_{\theta_i} \log \boldsymbol{\pi}_i(a_i \mid o_i)\, Q_i^{\boldsymbol{\pi}}(\mathbf{x}, a_1, \dots, a_N)\right] \tag{4}$$

**符号含义**：$o_i$ 是智能体 $i$ 的**本地观测**（actor 只用它）；$Q_i^{\boldsymbol{\pi}}(\mathbf{x}, a_1,\dots,a_N)$ 是**集中式 action-value 函数**，输入是**全部智能体的动作** $a_1,\dots,a_N$ 加上状态信息 $\mathbf{x}$，输出是**智能体 $i$ 的** Q 值。最简单取 $\mathbf{x}=(o_1,\dots,o_N)$，也可附加其他状态信息。**每个 $Q_i^{\boldsymbol{\pi}}$ 独立学习**，因此各智能体可有任意奖励结构，包括竞争设定下的冲突奖励（p.5）。

确定性策略版本（连续策略 $\boldsymbol{\mu}_{\boldsymbol{\theta}_i}$，简记 $\boldsymbol{\mu}_i$）：

$$\nabla_{\theta_i} J(\boldsymbol{\mu}_i) = \mathbb{E}_{\mathbf{x}, a \sim \mathcal{D}}\left[\nabla_{\theta_i} \boldsymbol{\mu}_i(a_i \mid o_i)\, \nabla_{a_i} Q_i^{\boldsymbol{\mu}}(\mathbf{x}, a_1, \dots, a_N)\big|_{a_i = \boldsymbol{\mu}_i(o_i)}\right] \tag{5}$$

其中 replay buffer $\mathcal{D}$ 存的是**全部智能体的**经验元组 $(\mathbf{x}, \mathbf{x}', a_1,\dots,a_N, r_1,\dots,r_N)$。critic 的损失为

$$\mathcal{L}(\theta_i) = \mathbb{E}_{\mathbf{x}, a, r, \mathbf{x}'}\left[\left(Q_i^{\boldsymbol{\mu}}(\mathbf{x}, a_1, \dots, a_N) - y\right)^2\right], \quad y = r_i + \gamma\, Q_i^{\boldsymbol{\mu}'}(\mathbf{x}', a_1', \dots, a_N')\big|_{a_j' = \boldsymbol{\mu}_j'(o_j)} \tag{6}$$

$\boldsymbol{\mu}'=\{\boldsymbol{\mu}_{\theta_1'},\dots,\boldsymbol{\mu}_{\theta_N'}\}$ 是参数延迟的**目标策略**集合。式(5)+(6) 即作者称为 MADDPG 的算法，完整流程见**附录算法 1（p.13）**：每回合各智能体按 $a_i = \boldsymbol{\mu}_{\theta_i}(o_i) + \mathcal{N}_t$ 加噪探索，存 $(\mathbf{x}, a, r, \mathbf{x}')$ 入 $\mathcal{D}$，逐智能体采样 minibatch 更新 critic 与 actor，最后按 $\theta_i' \leftarrow \tau\theta_i + (1-\tau)\theta_i'$ 更新目标网络。

**为什么这解决了非平稳性（§4.1，p.5，全文最关键的一句）**：若已知所有智能体所采取的动作，则环境**即使策略变化也仍是平稳的**，因为

$$P(s' \mid s, a_1, \dots, a_N, \pi_1, \dots, \pi_N) = P(s' \mid s, a_1, \dots, a_N) = P(s' \mid s, a_1, \dots, a_N, \pi_1', \dots, \pi_N')$$

对任意 $\boldsymbol{\pi}_i \neq \boldsymbol{\pi}_i'$ 成立；若不显式条件在其他智能体的动作上，此式不成立（p.5）。

### 对手策略的在线近似（§4.2，p.5）

式(6) 要求知道其他智能体的策略。为放宽该假设，每个智能体 $i$ 额外维护对智能体 $j$ 真实策略 $\boldsymbol{\mu}_j$ 的近似 $\hat{\boldsymbol{\mu}}_i^j$（参数 $\phi_i^j$），**用带熵正则的极大对数似然**学习：

$$\mathcal{L}(\phi_i^j) = -\,\mathbb{E}_{o_j, a_j}\left[\log \hat{\boldsymbol{\mu}}_i^j(a_j \mid o_j) + \lambda H(\hat{\boldsymbol{\mu}}_i^j)\right] \tag{7}$$

$H$ 是策略分布的熵。于是式(6) 中的 $y$ 可替换为近似值

$$\hat{y} = r_i + \gamma\, Q_i^{\boldsymbol{\mu}'}\left(\mathbf{x}', \hat{\boldsymbol{\mu}}_i'^{1}(o_1), \dots, \boldsymbol{\mu}_i'(o_i), \dots, \hat{\boldsymbol{\mu}}_i'^{N}(o_N)\right) \tag{8}$$

$\hat{\boldsymbol{\mu}}_i'^{j}$ 是近似策略的目标网络。式(7) 可**完全在线**优化：在更新 $Q_i^{\boldsymbol{\mu}}$ 之前，从 replay buffer 取各智能体 $j$ 的最新样本做一步梯度更新 $\phi_i^j$。注意此处**直接把各智能体的动作对数概率喂给 $Q$，而不是采样**（p.5）。

### 策略集成（§4.3，p.5–6）

竞争设定下智能体会**过拟合对手行为**，得到的策略脆弱。作者改为训练 $K$ 个**子策略**，每回合为每个智能体随机选一个执行；集成目标为

$$J_e(\boldsymbol{\mu}_i) = \mathbb{E}_{k \sim \mathrm{unif}(1,K),\, s \sim p^{\mu},\, a \sim \boldsymbol{\mu}_i^{(k)}}\left[R_i(s, a)\right]$$

对 $\theta_i^{(k)}$ 的梯度为

$$\nabla_{\theta_i^{(k)}} J_e(\boldsymbol{\mu}_i) = \frac{1}{K}\,\mathbb{E}_{\mathbf{x}, a \sim \mathcal{D}_i^{(k)}}\left[\nabla_{\theta_i^{(k)}} \boldsymbol{\mu}_i^{(k)}(a_i \mid o_i)\, \nabla_{a_i} Q^{\boldsymbol{\mu}_i}(\mathbf{x}, a_1, \dots, a_N)\Big|_{a_i = \boldsymbol{\mu}_i^{(k)}(o_i)}\right] \tag{9}$$

每个子策略 $\boldsymbol{\mu}_i^{(k)}$ 各维护一个 replay buffer $\mathcal{D}_i^{(k)}$（p.6）。

## 非平稳性处理方式

三篇里 MADDPG 的答案是**"把对手动作纳入 critic 的输入，使环境重新变平稳"**——注意它**同时**用了三件东西，但角色完全不同：

| 机制 | 页码 | 它解决什么 | 是否处理"对手在学" |
| --- | --- | --- | --- |
| **集中式 critic**（式(4)–(6)） | §4.1，p.4–5 | replay buffer 失效的根因：条件在联合动作上后 $P(s'\|s,a_1,\dots,a_N)$ 与策略无关 | **是，这是主机制**——对手策略变化不再改变 critic 要拟合的目标转移 |
| **对手策略近似**（式(7)–(8)） | §4.2，p.5 | 解除"必须已知对手策略"的假设 | 是，但定位是**放宽假设**而非解决非平稳性；§5.3（p.9）实测近似对手策略能达到与真策略相同的成功率，且收敛不显著变慢（近似听众策略的 KL 散度其实相当大） |
| **策略集成**（式(9)） | §4.3，p.5–6 | 对手**过拟合**导致的脆弱性 | 是，但作用于**执行期鲁棒性**：训练时被迫与多种合作者/竞争者互动；§5.4（p.9）实测集成智能体强于单策略智能体 |

**关键区分**：MADDPG 的"平稳"不是说对手不学了，而是说**条件在联合动作上之后，转移概率不再依赖策略**——式(6) 里那个 $a_j' = \boldsymbol{\mu}_j'(o_j)$ 就是它把"对手会怎么动"显式写进 Bellman 目标的落点。

**另一条并行的病灶诊断**：命题 1（p.4、p.15）指出多智能体下**策略梯度本身的信噪比**随 $N$ 下降（$\mathbb{E}/\sqrt{\mathbb{V}}$ 递减，p.15 末段），这是方差问题而非平稳性问题，MADDPG 用 centralized critic **去掉一个不确定性来源**（其他智能体的动作）来缓解。

## 可迁移机制

对"DGA 单步扰动博弈（$H=1$ 重复博弈）"逐条判断。**先给结论：MADDPG 的三件机制里只有两件在 $H=1$ 下仍然有意义，且其中一件会退化成本问题的常规设定。**

1. **"条件在对手动作上即平稳"的论证（§4.1，p.5）——可借，但在 $H=1$ 下退化。** 该等式的实质是：一旦把 $a_{-i}$ 显式写进条件，转移就不再依赖策略。$H=1$ 时根本**没有 $s'$**，这条等式退化为"给定双方扰动动作，检测结果确定"——那正是**正规式博弈的收益函数 $U(a_i, a_{-i})$ 的定义**，不是本文的贡献。**借的是"要把对手动作显式写进条件"这一纪律，不是"这是个新机制"。**
2. **集中式 action-value critic 的 TD 机制（式(5)–(6)，p.4–5）——$H=1$ 下退化，或说不需要。** $H=1$ 无后续状态，式(6) 的 $y = r_i + \gamma Q_i^{\mu'}(\mathbf{x}',\dots)$ 中 $\gamma Q$ 项消失，$y = r_i$；随之**目标网络 $\theta_i'$、延迟参数 $\tau$、replay buffer $\mathcal{D}$ 这一整套稳定化装置全部失去作用对象**。单步不需要为 MARL 造长序列：把 $H=1$ 硬套成"episode"只会引入无关的 bootstrapping 与目标网络调参。
3. **对手策略的在线近似（式(7)–(8)，p.5）——$H=1$ 下仍有意义，且形式更简单。** 式(7) 是"用观测到的对手动作做极大似然 + 熵正则"。$H=1$ 重复博弈里对手的"策略"就是一个**动作分布**，式(7) 退化为对该分布的在线估计（不必有目标网络 $\hat{\boldsymbol{\mu}}_i'^{j}$，因为无 $s'$）。**这是本课题最直接可用的一条**：把"对手（检测器）的动作分布"在线估计出来，用于选择扰动。
4. **策略集成（式(9)，p.5–6）——可借其思想，但式(9) 的梯度形式不可直接搬。** "$K$ 个子策略按回合随机选一"在 $H=1$ 重复博弈下等价于**维护一个扰动策略的混合分布**（与 PSRO 的 population/meta-strategy 同构，见 [[2017-Lanctot-PSRO种群博弈论方法]]）。但式(9) 的梯度依赖 replay buffer $\mathcal{D}_i^{(k)}$ 与确定性策略梯度 $\nabla_{a_i}Q$，这两者在离散 DGA 扰动空间里都不成立。
5. **命题 1 的方差诊断（p.4、p.15）——可借，且它本身就是单步现象。** 附录（p.14）明确该例子"**没有时间分量**"，讨论的是 $N$ 个智能体在稀疏奖励下"朝正确方向走一步"的概率随 $N$ 指数衰减。**这条恰好说明：多智能体协调困难在 $H=1$ 就已存在，不需要长轨迹就能触发。**
6. **执行期只用本地观测（§4.1，p.4）——可借为纪律。** "集中式训练、分散式执行"是一个**信息可用性**约束：训练时可用全局信息，测试时不可。若本课题在训练期能拿到检测器侧信息、执行期不能，这个框架直接对口。
7. **$Q$ 输入随 $N$ 线性增长（§6，p.10）——需警惕。** 作者自陈这是方法的一个缺点，并提议用"只考虑邻域智能体的模块化 $Q$"缓解。若把"多方"扩到多检测器/多扰动位点，这条会先撞上。

## 不能直接声称内容

- **不能把它算作 P4 的先例**：本文**没有安全域对象**，既无攻击者也无检测器。四级表的层次由攻防角色定义，不能因为"有多个学习主体"就计入第 3 或第 4 层。
- **不能声称它验证过 DGA 或任何域名字符串任务**：全部实验在 **2D 粒子世界**（合作通信、合作导航、keep-away、物理欺骗、捕食者—猎物、隐蔽通信；§5.1，p.6–7），观测是位置/速度/ landmark 颜色，动作是连续物理位移与（经 Gumbel-Softmax 软化的）通信符号——**与域名字符空间无关**。
- **不能声称它适用于离散动作空间**：式(5)、(6)、(9) 都依赖 $\nabla_{a_i} Q$，§3（p.4）明说这**要求动作空间连续**。式(4) 是随机策略的通用策略梯度形式，可配离散动作，但论文的实测全部走确定性版本。（论文对比的 DQN 在合作通信上失败，不足以反推"离散动作不可用"。）
- **不能把绝对数字外推**：84.0%、94%、16.4%、52.4% 等均是在**特定粒子环境 + 特定超参**（2 层 64/128 单元 ReLU MLP、Adam、lr 0.01、$\tau=0.01$、$\gamma=0.95$、replay buffer $10^6$、batch 1024，附录 p.13）下、且各自在**其自己的对手配置**下测得的；跨环境不可比。
- **不能声称它保证收敛**：全文未给 MADDPG 的收敛证明；命题 1 只刻画**单样本策略梯度方向正确的概率**，不是收敛性定理。
- **不能声称对手建模"拟合得很准"**：§5.3（p.9）明说近似**并不完美**——"the approximate listener policy learned by the speaker has a fairly large KL divergence to the true policy"，只是最终成功率与用真策略相当。
- **不能省略"实验成功/失败条件鲜明"的种子数差异**：作者对成败条件鲜明的环境（合作通信、物理欺骗、隐蔽通信）用 **10 个随机种子**，其余环境只用 **3 个**（附录 p.13）——比较不同环境的稳定性时不能忽略这个差别。
- **原文未报告**：MADDPG 的墙钟时间、样本效率定量对比、参数量对比；也未报告 $N$ 增大时 centralized critic 的显存/计算开销实测（§6 p.10 只定性指出输入空间线性增长）。

## 文献信息

- 题名：Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments
- 作者：Ryan Lowe（McGill / OpenAI）、Yi Wu（UC Berkeley）、Aviv Tamar（UC Berkeley）、Jean Harb（McGill / OpenAI）、Pieter Abbeel（UC Berkeley / OpenAI）、Igor Mordatch（OpenAI）
- arXiv：<https://arxiv.org/abs/1706.02275>（编号经 [[2017-Lanctot-PSRO种群博弈论方法]] 参考文献 [65] 交叉核验，本地 PSRO 全文 **p.12** 记作 `CoRR, abs/1706.02275, 2017`）
- 会议出处：NIPS 2017（**本地 PDF 全文未印出会议名与页码，此条为外部题录，非全文证据**）
- 本地原件：`raw/papers/attack-detection/2017-Lowe-MADDPG.pdf`（16 页）
- 转换来源：MinerU 转换产物 `/tmp/dga-adv-20260910/marl/2017-Lowe-MADDPG/`（含 `page_idx` JSON，页码锚点全部由该 JSON 实测，未估算）
