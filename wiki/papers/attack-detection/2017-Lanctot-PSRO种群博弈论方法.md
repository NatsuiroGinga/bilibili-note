---
title: "A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning"
title_zh: "PSRO：策略空间响应预言机与经验博弈论分析"
authors: [Marc Lanctot, Vinicius Zambaldi, Audrūnas Gruslys, Angeliki Lazaridou, Karl Tuyls, Julien Pérolat, David Silver, Thore Graepel]
year: 2017
date: 2026-09-10
journal: "NIPS 2017（31st Conference on Neural Information Processing Systems）；本地 PDF 27 页"
source_pdf: "[[raw/papers/attack-detection/2017-Lanctot-PSRO.pdf]]"
tags:
  - 多智能体强化学习
  - 博弈论
  - 种群博弈
  - 经验博弈论分析
  - 最佳响应
  - 非平稳性
  - 技术来源
  - 类型/论文
key_finding: "提出 **PSRO（Policy-Space Response Oracles）**：把 Double Oracle 的元博弈从「动作」提升到「策略」——用深度 RL 计算**对对手元策略分布的最佳响应**（oracle），把新策略加入策略集 $\\Pi_i$，再用**经验博弈论分析**在收益张量 $U^{\\Pi}$ 上求新的元策略 $\\sigma$（§3，p.3；算法 1，p.3）。理论上统一了 InRL、迭代最佳响应、虚拟自博弈与 Double Oracle 四种方法（p.4）。同时提出 **JPC（联合策略相关性）** 指标量化独立学习者的过拟合：$R_- = (\\bar{D}-\\bar{O})/\\bar{D}$（§4.1，p.6），实测在几乎全可观测的 Laser Tag small2 上独立学习者与另一个独立学习者对局时**预期损失 34.2% 的回报**，部分可观测性加大后升到 **71.7%**，DCH 可把损失压到 5.5%–15.0%（表 1，p.7）。"
method: "PSRO：经验收益张量 $U^{\\Pi}$ + 元策略求解器（regret matching / Hedge / 投影复制者动态 PRD）+ 深度 RL oracle 近似最佳响应。DCH（Deep Cognitive Hierarchies）：固定层数的并行化实现，用**解耦元求解器**在线更新以绕开 $U^{\\Pi}$，空间从 $K^n$ 降到 $O(n^2K^2)$（§3.2，p.5）。oracle 用 ReActor 训练。"
baseline: "独立 RL（InRL）、迭代最佳响应、虚拟自博弈（fictitious play）、Double Oracle、Neural Fictitious Self-Play（NFSP）、CFR（表格法，作 NashConv 参照）"
aliases: [PSRO, DCH, Lanctot2017-PSRO, 策略空间响应预言机, 深度认知层级]
related: ["[[2017-Lowe-MADDPG多智能体actor-critic]]", "[[2017-Foerster-LOLA对手学习感知]]", "[[2020-Song-MAB-Malware学习型黑盒规避]]"]
---

# PSRO：策略空间响应预言机与经验博弈论分析

> 页码锚点：本地 PDF 共 27 页。摘要见 **p.1**；InRL 过拟合问题见 §1（**p.1**）；正规式博弈、Double Oracle 与 EGTA 见 §2（**p.2–3**）；PSRO 主算法与算法 1 见 §3（**p.3**）；"固定对手后最佳响应退化为 MDP"与四种算法的统一参数化见 **p.4**；元策略求解器与 PRD 见 §3.1（**p.4–5**）；DCH 与空间复杂度见 §3.2（**p.5**）；解耦元求解器见 §3.2.1（**p.5**）；实验环境见 §4（**p.5–6**）；JPC 指标见 §4.1（**p.6–7**）；Leduc 与 NashConv 见 §4.2（**p.7–8**）；结论见 §5（**p.8**）；附录 A（元求解器）见 **p.15**；附录 B.2（一般 $n$ 人 JPC）见 **p.16**；附录 D.1（Leduc 环境改动）见 **p.20**；附录 E.2（CFR 参照值）见 **p.22**。

## 一句话

这是**"对手池 + 元策略分布"**这一整套做法的原始形式化：把求解多智能体问题拆成"**用 RL 算对分布的最佳响应**"与"**在经验收益矩阵上求元策略**"两件交替进行的事，并把此前四种方法（InRL / 迭代最佳响应 / 虚拟自博弈 / Double Oracle）收成同一框架的特例。

## 与 P4 的距离（report (8) 四级表的第 — 层）

**本文不属于 report (8) 四级表的任何一层。** 它是**通用 MARL 方法论文**：没有攻击者、没有检测器、没有安全域对象。实验环境是第一人称网格世界（Laser Tag / Gathering / Pathfind）与 Leduc 扑克（§4，p.6）。

| 层级 | 学习关系 | 典型 | 本文是否在此层 |
| --- | --- | --- | --- |
| 1 | 固定/算法攻击 + 学习检测器 | CharBot / MaskDGA / Drichel | 否——无攻击者/检测器 |
| 2 | 学习型攻击者 + 固定目标检测器 | MAB-Malware | 否 |
| 3 | 学习型攻击者 + 学习 surrogate | MalGAN / IDSGAN | 否 |
| 4 | attacker + 实际 defender 共演化 | RELEVAGAN / 2026 bilevel | **否**——虽有双方同时学习，但**是博弈对手而非攻防双方**，且非安全域 |

**本文在本课题中的角色是技术来源，不是近邻先例。** 具体来源点：

- **opponent pool / 策略池的形式化**：$\Pi_i^{t+1} = \Pi_i^t \cup \{\pi_i^{t+1}\}$（§2 的 Double Oracle 与 §3 的 PSRO，p.2–3）——"维护一个对手（检测器）策略池"的写法来源。
- **best-response oracle 的写法**：把"对对手分布的最佳响应"交给 RL 求解（§3，p.3–4）——"针对某一对手集合训练一个最优攻击者"的写法来源。
- **meta-game / meta-strategy solver**：把选策略这件事本身当成一个在经验收益矩阵上求解的博弈（§3.1，p.4–5）。
- **JPC 指标**：$R_- = (\bar{D}-\bar{O})/\bar{D}$（§4.1，p.6）——**量化"训练时配对 vs 交叉配对"性能落差**的可直接借用度量。

**不能因为"也维护了对手池"就把它计入四级表**：四层刻画的是安全域内的攻防学习关系，本文的两个 agent 是同一博弈里的对等参与者。

## 机制（§3，p.3–5）

### 元博弈与经验博弈论分析（§2，p.2）

正规式博弈是元组 $(\Pi, U, n)$：$n$ 是玩家数，$\Pi=(\Pi_1,\cdots,\Pi_n)$ 是各玩家的策略集，$U: \Pi \to R^n$ 是**每个联合策略的收益表**。玩家各自从 $\Pi_i$ 中选策略，或从其上的混合分布 $\sigma_i \in \Delta(\Pi_i)$ 中采样。关键性质：**$\sigma_i$ 的好坏依赖于他人的策略，因此不能独立地求解或评估**（p.2）。

**Double Oracle（DO）**（§2，p.2）是 PSRO 的直接前身：在由子集 $\Pi^t \subset \Pi$ 诱导的子博弈 $G_t$ 上求均衡 $\sigma^{*,t}$，然后每个玩家从全空间 $\Pi_i$ 中加一个对 $\sigma_{-i}^{*,t}$ 的最佳响应 $\pi_i^{t+1} \in \mathrm{BR}(\sigma_{-i}^{*,t})$，即 $\Pi_i^{t+1} = \Pi_i^t \cup \{\pi_i^{t+1}\}$。DO 在两人博弈中保证收敛，但最坏情形需枚举全部策略空间（例如石头剪子布，其唯一均衡满支撑）。零和博弈中求均衡是 $|\Pi^t|$ 的多项式时间，**一般和博弈则是 PPAD-完全的**（p.2）。

**EGTA（经验博弈论分析）**（§2，p.3）：当显式枚举博弈策略代价过高时，用模拟构造一个远小于全博弈的**经验博弈**，估计各联合策略的期望收益并记入经验收益表，再对其做元推理。本文的做法是**用学习去发现新策略**，且不算精确最佳响应、而是**用 RL 算近似最佳响应**（p.3）。

### PSRO 主循环（§3，p.3）

PSRO 是 Double Oracle 的自然推广——**元博弈的选择对象是策略而不是动作**；它也推广了 Fictitious Self-Play。与先前工作不同，**任何元求解器都可插入**（p.3）。

```text
Algorithm 1: Policy-Space Response Oracles
输入: 所有玩家的初始策略集 Π
计算每个联合策略 π ∈ Π 的期望收益 U^Π
初始化元策略 σ_i = UNIFORM(Π_i)
while epoch e ∈ {1, 2, ...} do
    for 每个玩家 i ∈ [[n]] do
        for 若干 episode do
            采样 π_{-i} ~ σ_{-i}
            在 ρ ~ (π_i', π_{-i}) 上训练 oracle π_i'
        Π_i = Π_i ∪ {π_i'}
    从 Π 补齐 U^Π 中缺失的条目
    由 U^Π 计算元策略 σ
输出: 玩家 i 的当前解策略 σ_i
```

（算法 1 见 **p.3**；伪码文字按其原文转写。）

**为什么"最佳响应"能用 RL 算**（§3，p.3–4，本文的关键论证）：在（分幕式）部分可观测多智能体环境中，**当其他玩家固定时环境变为 Markov 的**，于是计算最佳响应**退化为求解某种形式的 MDP**——因此任何 RL 算法都可以用（本文用深度网络）。每个 episode 中一个玩家处于 oracle（学习）模式训练 $\pi_i'$，其余玩家的策略从对手元策略中采样固定为 $\pi_{-i}\sim\sigma_{-i}$。该轮结束时新 oracle 加入 $\Pi_i$，新策略组合的期望收益经模拟算出并写入经验收益张量 $U^{\Pi}$，**其耗时为 $|\Pi|$ 的指数级**（p.4）。

**四种方法都是 PSRO 的特例**（p.4，记 $\Pi^T=\Pi^{T-1}\cup\{\pi'\}$，$|\sigma_i|=|\Pi_i^T|$）：

| 方法 | 对应的元策略 |
| --- | --- |
| 迭代最佳响应（Iterated best response） | $\sigma_{-i}=(0,0,\cdots,1,0)$ |
| 独立 RL（InRL） | $\sigma_{-i}=(0,0,\cdots,0,1)$ |
| 虚拟自博弈（fictitious play） | $\sigma_{-i}=(1/K,1/K,\cdots,1/K,0)$，$K=\lvert\Pi_{-i}^{T-1}\rvert$ |
| Double Oracle | $n=2$，$\sigma^T$ 取元博弈 $(\Pi^{T-1},U^{\Pi^{T-1}})$ 的 Nash 均衡 |

作者对这两端的批评（p.4）：虚拟自博弈对响应的对象不敏感，只能通过反复生成同样的最佳响应来**锐化**元策略分布；而对 DO 算出的均衡策略作响应则 (i) 在 $n$ 人/一般和情形下**过拟合到某个特定均衡**，(ii) 在零和情形下无法泛化到均衡策略未触及的空间区域。折中方案是**用满支撑的元策略强制混入 $\gamma$ 的探索**。

### 元策略求解器（§3.1，p.4–5）

元求解器**输入经验博弈 $(\Pi, U^{\Pi})$，为每个玩家输出元策略 $\sigma_i$**。本文试三种：**regret matching、Hedge、投影复制者动态（PRD）**。这些求解器为每个策略（"臂"）累积数值，并基于所有玩家的元策略计算聚合值。记 $u_i(\sigma)$ 为玩家 $i$ 在收益张量 $U^{\Pi}$ 下、给定全体元策略的期望值；$u_i(\pi_{i,k},\sigma_{-i})$ 为玩家 $i$ 打第 $k$ 个策略、其余玩家按 $\sigma_{-i}$ 行动时的期望效用。策略使用探索参数 $\gamma$，**任何 $\pi_{i,k}$ 被选中的概率下界为 $\frac{\gamma}{K+1}$**（p.4）。

**投影复制者动态（PRD）**：以两人的非对称复制者动态为例，$U^{\Pi}=(\mathbf{A},\mathbf{B})$，元策略 $(\sigma_1,\sigma_2)=(\mathbf{x},\mathbf{y})$ 第 $k$ 个分量的概率变化为

$$\frac{dx_k}{dt} = x_k\left[(\mathbf{Ay})_k - \mathbf{x}^T\mathbf{Ay}\right], \qquad \frac{dy_k}{dt} = y_k\left[(\mathbf{x}^T\mathbf{B})_k - \mathbf{x}^T\mathbf{By}\right]$$

**符号含义**：$\mathbf{x}$ 对应行玩家、$\mathbf{y}$ 对应列玩家；$x_k$ 是策略 $\pi_{i,k}$ 在种群中的密度（即 $\sigma_i(\pi_{i,k})$）；$\mathbf{A}$、$\mathbf{B}$ 分别是两人的收益矩阵。实践上用步长 $\delta$ 离散化更新，并加投影算子 $P(\cdot)$ 保证探索：

$$\mathbf{x} \leftarrow P\left(\mathbf{x} + \delta\tfrac{d\mathbf{x}}{dt}\right), \qquad P(\mathbf{x}) = \arg\min_{\mathbf{x}' \in \Delta_\gamma^{K+1}} \{\lVert \mathbf{x}' - \mathbf{x} \rVert\} \ \text{若某个} x_k < \gamma/(K+1)，\ \text{否则取} \mathbf{x}$$

其中 $\Delta_\gamma^{K+1} = \{\mathbf{x} \mid x_k \geq \frac{\gamma}{K+1},\ \sum_k x_k = 1\}$ 是**规模 $K+1$ 的 $\gamma$-探索单纯形**，从而强制 $\sigma_i(\pi_{i,k}) \geq \gamma/(K+1)$（p.5）。作者把 PRD 理解为"**有方向的探索**"，区别于标准复制者动态里各向同性、无偏的扩散/变异项（p.5）。regret matching 与 Hedge 的细节在附录 A（**p.15**）：RM 累积收益遗憾后取正部归一化，Hedge 用 softmax，两者都混入 $\gamma\,\mathrm{UNIF}(K+1)$。

### DCH：并行化实现与空间复杂度（§3.2，p.5）

PSRO 的 RL 步骤收敛慢；复杂环境里上一轮学到的行为常常要重新学；而想递归推理更深的层级又需要跑很多轮。**DCH（Deep Cognitive Hierarchies）**的做法是：**先固定层数**，对 $n$ 人博弈并行启动 $nK$ 个进程（第 0 层是均匀随机）。每个进程训练**单个** oracle 策略 $\pi_{i,k}$（玩家 $i$、层级 $k$），并更新自己的元策略 $\sigma_{i,k}$，定期存盘；同时维护其他 oracle 策略 $\pi_{j,k'\leq k}$ 与当前层元策略 $\sigma_{-i,k}$ 的副本，定期从中央磁盘刷新。**它通过在线更新元策略来绕开显式存储 $U^{\Pi}$**（p.5；算法 2 见 **p.5**）。

**空间复杂度**（p.5）：PSRO 下 $K$ 个策略、$n$ 个玩家，存经验收益张量需 $K^n$；DCH 每个进程存 $nK$ 个固定大小策略与 $n$ 个大小有界（$k\leq K$）的元策略，总空间为

$$O(nK \cdot (nK + nK)) = O(n^2K^2)$$

作者明确说明代价：各进程用的是彼此略微过期的策略与元策略副本，**DCH 是 PSRO 的近似**——它用对应精度的损失换实用效率与可扩展性（p.5）。

**解耦元求解器**（§3.2.1，p.5）：DCH 需要**不需要收益张量 $U^\Pi$** 的元求解器。作者把解耦元求解器理解为**把基于采样的对抗性强盗算法应用到博弈上**（online learning 里的 full-information "专家算法" vs partial-information "强盗"，此处属后者）。同样混入 $\gamma$ 的均匀策略，这既是探索也是**保证估计无偏**的必要条件。三种解耦版本：**解耦 regret-matching、Exp3（解耦 Hedge）、解耦 PRD**；解耦 PRD 维护总体平均价值与每个臂的价值的滑动平均（p.5）。

## 非平稳性处理方式

PSRO 的答案是**"不去消除非平稳性，而是把它显式建模成一个博弈"**——把"对手会变"从噪声变成优化对象：

| 机制 | 页码 | 它怎么处理"对手在学" |
| --- | --- | --- |
| **best-response oracle 对元策略分布取响应** | §3，p.3–4 | 不再假设对手固定或均匀：oracle 训练时面对的是 $\pi_{-i}\sim\sigma_{-i}$ 的**分布**，因此学到的是对这一分布的最佳响应，而不是对某个特定对手 |
| **population / 策略池 $\Pi_i$** | §2–§3，p.2–3 | 保留历史策略而非只保留最新策略；对手学习的轨迹被记录为一个集合 |
| **meta-game 与 meta-strategy solver** | §3.1，p.4–5 | 把"该针对哪些对手"本身当成一个博弈来解，产出一个混合分布 $\sigma_i$，**使策略不绑定到单一对手** |
| **$\gamma$ 满支撑探索下界** | §3.1，p.4–5 | 强制每个历史策略保有 $\geq\gamma/(K+1)$ 的概率，防止元策略锐化到过拟合某一对手 |

作者对动机的表述（摘要 p.1 与 §1 p.1）：**InRL 学到的策略会过拟合到训练时其他智能体的策略，因而在执行时无法充分泛化**；他们为此引入 **JPC（joint policy correlation）** 指标来量化这一效应。结论中把 PSRO/DCH 提供的一般性称为一种 **"对手/队友正则化"（opponent/teammate regularization）**（§5，p.8）。

**JPC 的定义与实测**（§4.1，p.6–7）：跑 $D$ 次仅初始化种子不同的实验，每次得到 $(\pi_1^d,\pi_2^d)$；$D\times D$ 矩阵的每个元素是 $T=100$ 个 episode 上的平均回报 $\sum_{t=1}^{T}\frac{1}{T}(R_1^t+R_2^t)$。**对角线**是"一起学出来的"策略配对，**非对角线**是"分开学出来的"策略配对。定义平均比例损失

$$R_- = \frac{\bar{D} - \bar{O}}{\bar{D}}$$

$\bar{D}$ 是对角线均值，$\bar{O}$ 是非对角线均值。例（p.6，图 3）：$D=30.44$、$\bar{O}=20.03$，故 $R_-=0.342$。

| 环境 / 地图 | InRL $\bar D$ | InRL $\bar O$ | InRL $R_-$ | DCH(Reactor, 2, 10) $R_-$ | JPC 缩减 |
| --- | --- | --- | --- | --- | --- |
| Laser Tag small2 | 30.44 | 20.03 | 0.342 | 0.055 | 28.7% |
| Laser Tag small3 | 23.06 | 9.06 | 0.625 | 0.082 | 54.3% |
| Laser Tag small4 | 20.15 | 5.71 | 0.717 | 0.150 | 56.7% |
| Gathering field | 147.34 | 146.89 | 0.003 | 0.007 | — |
| Pathfind merge | 108.73 | 106.32 | 0.022 | $<0$ | — |

（表 1，**p.7**。）作者的解读：**即使在几乎全可观测的 small2 上，一个独立学习的策略在与另一个独立学习的策略对局时可预期损失 34.2% 的回报**，尽管二者是在完全相同条件下训练的；地图变大、部分可观测性增强后问题加重到 71.7%；而在不需要协调的 gathering 与 pathfind 上**观察不到 JPC 问题**（p.6–7）。

**元策略在执行期是否必要**（§4.1，p.7）：若只用最高层策略 $\pi_{i,10}$ 而不混合，$R_-=0.147,0.27,0.118$（small2–4），**比混合策略更差**，说明元策略本身有作用；但相对 InRL 仍是显著缩减（19.5%、36.5%、59.9%）。**层数取多少**（p.7）：small4 上第 5 层 $R_-=0.156$（缩减 56.1%）、第 3 层 $R_-=0.246$（缩减 44%）——第 5 层与第 10 层效果接近，第 3 层较差。

**Leduc 上的对照**（§4.2，p.7–8）：用 **NashConv** 度量距 Nash 均衡的距离

$$\mathrm{NASHCONV}(\sigma) = \sum_i^n \max_{\sigma_i' \in \Sigma_i} u_i(\sigma_i', \sigma_{-i}) - u_i(\sigma)$$

即全体玩家单方面偏离到最佳响应所能获得的收益总和（两人情形下即"可利用度"exploitability）。$\gamma=0.4$ 对最小化 NashConv 最好，$\gamma=0.1$ 对利用（exploitation）最好；解耦复制者动态最好，其次是解耦 regret-matching 与 Exp3（p.7）。与 NFSP 比较：**DCH/PSRO 训练初期收敛更快**（可能因为元策略优于虚拟自博弈的均匀随机），但曲线最终进入平台期，**NFSP 在后期收敛到更低的 exploitability**——作者归因于 NFSP 能学到更精确的混合平均策略（在树深处起作用），而 DCH/PSRO 是在顶层对**整条策略**做混合；反过来 **PSRO/DCH 对固定对手的表现更好**，因为它们能识别弱对手的缺陷并动态适应，即"用一个安全的均衡换取了适应多种打法的能力"（p.8）。

## 可迁移机制

对"DGA 单步扰动博弈（$H=1$ 重复博弈）"逐条判断。**先给结论：PSRO 是本课题最直接可借的一篇——因为它的核心循环（"对分布求最佳响应 → 在收益矩阵上求元策略"）在 $H=1$ 下不需要任何序列建模，反而比原文更简单；真正退化的是那个昂贵的 RL oracle。**

1. **JPC 指标 $R_- = (\bar{D}-\bar{O})/\bar{D}$（§4.1，p.6）——可直接借用，且 $H=1$ 下更易算。** 它度量的正是"**针对某一对手训练出的攻击者，换一个同分布下独立训练的对手后损失多少**"。$H=1$ 下不需要 episode 内的 $T=100$ 平均，$\bar D$ 与 $\bar O$ 就是"同 run 配对"与"交叉配对"两组攻击成功率之差。**这是判断"攻击者是否过拟合到某一版检测器"的现成度量。**
2. **best-response oracle 对元策略分布取响应（§3，p.3–4）——思想可借，但 RL 那部分在 $H=1$ 下退化。** 原文的 oracle 是深度 RL，因为最佳响应是"别人固定后解一个 MDP"（p.3–4）。$H=1$ 时那个 MDP **只有一个状态、一步决策**，最佳响应对已知分布就是**在有限扰动集上做期望收益的 argmax**——一次枚举即可，不需要 RL、不需要神经网络、不需要训练。**照搬 RL oracle 只会为一个 argmax 问题引入无谓的训练成本。**
3. **经验收益张量 $U^\Pi$ 与元策略求解（§3.1，p.4–5）——可直接借用。** $H=1$ 下 $U^\Pi$ 的每个元素就是"扰动策略 × 检测器策略"的收益数值，正是博弈的收益矩阵本身。在它上面跑 **regret matching**（附录 A.1，p.15）或 **PRD**（§3.1，p.4–5）就能得到扰动策略的混合分布。**这是"不把攻击策略钉死在单一检测器版本上"的直接做法。**
4. **$\gamma$ 探索下界与投影算子 $P(\cdot)$（§3.1，p.5）——可直接借用为反塌缩机制。** $\Delta_\gamma^{K+1}$ 强制每个策略概率 $\geq \gamma/(K+1)$，作用是防止元策略锐化到只押一个对手。**若担心攻击策略过度收敛到单一检测器版本，这是现成的、有公式的防空转装置。**
5. **population / 策略池（§2–§3，p.2–3）——可借，$H=1$ 下就是"对手快照池"。** 本课题的"对手在学"若表现为检测器的多次重训/多版本，策略池天然对应**检测器版本池**，不需要长序列。
6. **"对手固定则最佳响应退化为 MDP"（§3，p.3–4）——在 $H=1$ 下的正确读法是"退化为单步决策"。** 这句在原文里是**为昂贵的 RL oracle 做辩护**的论据；在 $H=1$ 下它反过来证明**不需要为单步博弈造长序列**：把单步问题写成分幕 MDP 再上 RL，是给一个 argmax 套上完整的时序机制。
7. **统一框架的定位价值（p.4）——可借为论述纪律。** 作者把 InRL / 迭代最佳响应 / 虚拟自博弈 / Double Oracle 收成同一参数化下的特例：**差别只在 $\sigma_{-i}$ 怎么取**。若本课题要说明"我们的方法与朴素做法差在哪"，这个"只差在响应对象"的表述方式比自造分类学更省力（见根 `AGENTS.md`：对齐已发表论文，不自创分类学）。
8. **DCH 的并行架构与异步过期（§3.2，p.5）——$H=1$ 下不需要。** 它解决的是"RL oracle 训练很贵、要跑很多轮"的工程问题。单步博弈里 oracle 是 argmax，耗时可忽略，异步存盘/过期副本这一整套都不适用。
9. **DCH 的层级结构（§3.2，p.5）——$H=1$ 下意义有限。** 层级刻画的是"递归推理对手在想什么"的深度；单步重复博弈里对手的"策略"只是一个动作分布，层级会迅速塌缩到元策略本身。
10. **空间复杂度 $K^n$ vs $O(n^2K^2)$（§3.2，p.5）——按规模决定是否需要。** 只有当策略数与对手数真正变大、显式张量不可承受时，解耦元求解器才值得引入；否则显式 $U^\Pi$ 更简单。

## 不能直接声称内容

- **不能把它算作 P4 的先例**：全文**没有安全域对象**——环境是第一人称网格世界（Laser Tag 的"被光标记两次即传送"、Gathering 的收集苹果、Pathfind 的到达目的地；§4，p.6）与 **Leduc 扑克**（§4，p.6）。没有恶意软件、没有 DGA、没有检测器。
- **不能声称它在域名字符空间上验证过任何东西**：观测是 21×20×3 RGB 张量与扑克的一热编码，动作是移动/转向/发光/下注——与扰动域名字符无关。
- **不能把 JPC 的数值外推到 DGA**：$\bar D$、$\bar O$、$R_-$ 全部是**该论文两个环境内**的读数，且作者明确指出在**不需要协调的任务（gathering、pathfind）上观察不到 JPC 问题**（p.6–7）——即 JPC 的存在与大小依赖任务是否需要协调，不是普适常数。
- **不能声称 PSRO 在一般和博弈中有收敛保证**：DO 的收敛保证是**两人博弈**下的；一般和博弈求均衡是 **PPAD-完全**的（§2，p.2）。PSRO 自身的收敛性本文未给证明。
- **不能声称 PSRO/DCH 全面优于 NFSP**：作者自己的实测结论是**分化的**——DCH/PSRO 初期收敛更快、对固定对手表现更好，但 **NFSP 后期收敛到更低的 exploitability**（§4.2，p.8）。只引用前半句是选择性引用。
- **不能忽略 Leduc 环境被改动过**：为了让策略能定义在固定动作集上而不依赖具体 RL 算法，作者**允许非法动作**——执行非法动作会得到终局收益下界减 1 的奖励（Leduc 中为 $-14$）并改为随机合法动作；**这使改动后的博弈变成一般和**，因此 **CFR 与 exploitability 是在原始博弈上算的**，PSRO/DCH/NFSP 的策略则先掩掉非法动作并重新归一化后才算可利用度（附录 D.1，**p.20**）。引用其可利用度数字时必须带上这一条。
- **不能把 CFR 的 NashConv 与 PSRO/DCH 的直接并列**：CFR 是**表格法、每轮需要完整过一遍博弈树**，而 PSRO/DCH/NFSP 是采样式、用一般函数逼近的学习算法（§4.2，p.7）。作者给出 CFR 在 500 轮时的 NashConv 为 **0.063591（两人）/ 0.194337（三人）**（附录 E.2，**p.22**），并说明两人 Leduc 的博弈值（任一精确 Nash 均衡下先手期望收益）为 **-0.085606424078**，即后手略有优势（p.22）。
- **不能声称 JPC 指标定义唯一**：正文给的是**对称两人、非负收益**的特例；一般 $n$ 人、非对称、任意收益的版本见附录 B.2（**p.16**），且作者指出非对称博弈下 JPC 问题**因玩家而异**，无法聚合成单一汇总值，只能报向量 $\vec{R}$（p.16）。
- **原文未报告**：PSRO 与 DCH 的墙钟时间、总 GPU 小时、能耗；也未报告在网格世界任务上 PSRO（非 DCH）与 DCH 的直接对照数（表 1 只给了 InRL 与 DCH）。

## 文献信息

- 题名：A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning
- 作者：Marc Lanctot、Vinicius Zambaldi、Audrūnas Gruslys、Angeliki Lazaridou、Karl Tuyls、Julien Pérolat、David Silver、Thore Graepel（均属 DeepMind）
- 会议出处：NIPS 2017（**本地 PDF 全文未印出会议名与页码，此条为外部题录，非全文证据**）
- 本地原件：`raw/papers/attack-detection/2017-Lanctot-PSRO.pdf`（27 页）
- 关联：本文参考文献 [65] 即 [[2017-Lowe-MADDPG多智能体actor-critic]]（`CoRR, abs/1706.02275, 2017`，**p.12**）；参考文献 [22] 为 Foerster 等《Stabilising experience replay for deep multi-agent reinforcement learning》（ICML 2017，**p.10**）
- 转换来源：MinerU 转换产物 `/tmp/dga-adv-20260910/marl/2017-Lanctot-PSRO/`（含 `page_idx` JSON，页码锚点全部由该 JSON 实测，未估算）
