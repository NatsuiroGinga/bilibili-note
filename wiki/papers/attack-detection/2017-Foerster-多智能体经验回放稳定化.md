---
title: "Stabilising Experience Replay for Deep Multi-Agent Reinforcement Learning"
title_zh: "Foerster 等：用多智能体重要性采样与 fingerprints 稳定深度多智能体强化学习中的经验回放"
authors: [Jakob Foerster, Nantas Nardelli, Gregory Farquhar, Triantafyllos Afouras, Philip H. S. Torr, Pushmeet Kohli, Shimon Whiteson]
year: 2017
date: 2026-09-10
journal: "ICML 2017（Proceedings of the International Conference on Machine Learning 2017，据本地 PDF 元数据 Subject 字段）；arXiv:1702.08887；本地 PDF 共 10 页"
source_pdf: "[[raw/papers/attack-detection/2017-Foerster-Stabilising-Experience-Replay.pdf]]"
arxiv_id: "1702.08887"
tags:
  - 多智能体强化学习
  - 经验回放
  - 非平稳性
  - 重要性采样
  - fingerprints
  - 技术来源
  - 类型/论文
key_finding: "指出独立 Q 学习（IQL）造成的非平稳性会让**回放记忆里的旧数据不再反映当前动力学**，二者组合因此「appears to be problematic」（§1，p.1）。给出两条修法并实测比较：①**多智能体重要性采样**——采样时把「动作采集时刻他方联合策略的概率」一并存进元组，回放时按「回放时刻的他方联合策略概率 ÷ 采集时刻的他方联合策略概率」加权（式(4)，p.4），使**旧数据自然衰减**；②**多智能体 fingerprints**——在观测里加一个低维标记（观测、探索率 ε、训练迭代号 e 的拼接），让每个智能体的值函数能分辨样本出自训练轨迹的哪一段（§4.2，p.5）。实测结论：**fingerprint 明显有效，重要性采样只在 feed-forward 模型上略有提升，且二者组合没有额外收益**（§6.1–§6.2，p.7–8）；**循环网络下两者增益都不大，3v3 任务中均无帮助**——因为轨迹本身已携带足够的「训练阶段」信息（§6.3，p.8）。"
method: "把回放记忆中的经验视为 off-environment 数据（Ciosek & Whiteson 2017）；采集时刻记录「他方联合策略在该状态下取该联合动作的概率」形成增广元组（p.4），回放时刻用该概率的重要性加权损失（式(4)）训练；部分可观测下给出含他方动作—观测历史的增广状态空间与对应 Bellman 方程（式(5)–(7)，p.4），并明确指出**部分可观测情形下的重要性比值只是近似**（p.4）。fingerprint 路线把「样本出自训练轨迹哪一段」压缩成低维标记（探索率 ε + 训练迭代号 e），使 Q 函数在多智能体下重新变为平稳（§4.2，p.5）"
baseline: "NOXP（完全不用经验回放）与 XP（朴素地把经验回放与 IQL 组合）；消融 XP+IS、XP+FP、XP+IS+FP（§5，p.6）"
aliases: [Foerster2017-Fingerprints, Stabilising-Experience-Replay, 多智能体经验回放稳定化, MAS-IS-FP]
related: ["[[2017-HernandezLeal-多智能体非平稳性综述]]", "[[2017-Foerster-LOLA对手学习感知]]", "[[2017-Lanctot-PSRO种群博弈论方法]]", "[[2017-Lowe-MADDPG多智能体actor-critic]]", "[[2025-Liu-OPERA多智能体渐进组相对策略优化]]", "[[2017-Hu-MalGAN替代检测器生成对抗样本]]", "[[2018-Lin-IDSGAN入侵检测攻击生成]]", "[[2020-Song-MAB-Malware学习型黑盒规避]]"]
---

# Foerster 等：多智能体经验回放的稳定化

> 页码锚点：本地 PDF 共 10 页。摘要与非平稳性问题陈述见 §1（**p.1**）；相关工作见 §2（**p.2**）；IQL 的非平稳性见 §3.2（**p.3**）；多智能体重要性采样与式(3)(4)(5)–(7) 见 §4.1（**p.4**）；fingerprints 与 $O'(s)=\{O(s),\epsilon,e\}$ 见 §4.2（**p.5**，Figure 1 亦在 **p.5**）；实验域见 §5.1、网络架构与超参见 §5.2（**p.6**）；总览结果见 §6（**p.6–7**）；重要性采样结果见 §6.1（**p.7**）；fingerprints 结果见 §6.2（**p.7–8**，Figure 2 在 **p.7**、Figure 3 在 **p.8**）；轨迹信息量见 §6.3（**p.8**，Figure 4 在 **p.8**）；结论与未来工作见 §7（**p.8**）。

## 一句话

这是一篇**通用多智能体强化学习方法论文，不是安全论文**：它把"对手（此处是同队学习中的队友）也在学"这一非平稳性，从"回放记忆里的数据过期"这个具体病灶入手，给出**两条互不依赖的修法**——按策略漂移量给旧数据降权，或者给值函数喂一个"这批数据有多老"的低维标记；实测**后者明显更强、且两者叠加无增益**，而**在循环网络上两者几乎都不需要**。

## 与 P4 的距离（**不属于** report (8) 四级表的任何一层）

| 层级 | 学习关系 | 典型 |
| --- | --- | --- |
| 1 | 固定/算法攻击 + 学习检测器 | CharBot / MaskDGA / Drichel |
| 2 | 学习型攻击者 + 固定目标检测器 | MAB-Malware |
| 3 | 学习型攻击者 + 学习 surrogate | MalGAN / IDSGAN |
| 4 | attacker + 实际 defender 共演化 | RELEVAGAN / 2026 bilevel |

**本文不落在任何一层，因为它根本不在安全域，也不含攻防关系。**

- **问题域**：合作型多智能体强化学习（fully cooperative multi-agent），非零和、非对抗。§3.2（p.3）："We consider a **fully cooperative** multi-agent setting"；全体智能体共享同一奖励函数 $r(s,\mathbf{u})$。任务里唯一的外部对手是**游戏 AI**（§5.1，p.6："Opponents are controlled by the game AI, which is set to attack all the time"）——这是**固定的**非学习型对手，不构成学习型 defender。
- **非平稳性的来源是队友而非敌人**：§1（p.1）"the environment becomes nonstationary from the point of view of each agent, as it contains **other agents who are themselves learning**"。这里"其他智能体"是本方的协作单位，不是攻击方。
- **角色定位：技术来源**。它提供的是"**当环境因他方学习而移动时，经验回放该怎么修**"的两条具体机制与实测取舍（见下文"可迁移机制"），可作为 DGA 单步扰动博弈中**攻击者/防御者自身在线学习时的回放设计**参照——**它既不是 P4 的先例，也不是 DGA 对抗的任何证据。**

## 机制（§4，p.4–5）

### 病灶（§1，p.1；§3.2，p.3）

深度 RL 依赖经验回放，而 IQL 让每个智能体把其他智能体当作环境的一部分——**随着其他智能体的策略在训练中改变，该环境对每个智能体而言是非平稳的**。于是：

> "the dynamics that generated the data in the agent's replay memory **no longer reflect the current dynamics** in which it is learning."
> ——§1，p.1（§3.2，p.3 原文重复）

对比：**不带回放的 IQL 反而能容忍非平稳**，只要每个智能体不断缓慢跟踪其他智能体的策略；"that seems hopeless with a replay memory constantly confusing the agent with obsolete experience"（§1，p.1）。此前的绕路办法是把回放限制在**很短的近期缓冲**或**干脆关掉回放**（Leibo 等 2017；Foerster 等 2016），代价是样本效率与稳定性（§1，p.1；§4，p.4）。

### 修法一：多智能体重要性采样（§4.1，p.4）

思路是把回放记忆中的经验当作 **off-environment** 数据（Ciosek & Whiteson 2017），因为 IQL 把其他智能体的策略当成了环境的一部分。**关键优势**：智能体的策略在训练各阶段的取值是**已知的**，所以"环境是怎么变的"可以被精确写出并做重要性校正（p.4）。

完全可观测情形下的 Bellman 方程（式(3)，p.4）中，非平稳项就是他方联合策略

$$\boldsymbol{\pi}_{-a}(\mathbf{u}_{-a}|s)=\prod_{i\in -a}\pi_i(u_i|s)$$

**采集时（$t_c$）**把它记进元组，形成增广转移元组

$$\langle s,\ u_a,\ r,\ \boldsymbol{\pi}(\mathbf{u}_{-a}|s),\ s'\rangle^{(t_c)}$$

**回放时（$t_r$）**最小化重要性加权损失（式(4)，p.4）：

$$\mathcal{L}(\theta)=\sum_{i=1}^{b}\frac{\pi^{t_r}_{-a}(\mathbf{u}_{-a}|s)}{\pi^{t_i}_{-a}(\mathbf{u}_{-a}|s)}\Big[(y_i^{DQN}-Q(s,u;\theta))^2\Big]$$

其中 $t_i$ 是第 $i$ 个样本的采集时刻。**越旧的数据重要性权重越低，因此被自然地衰减掉**（§1，p.1："this approach naturally decays data as it becomes obsolete"）。

**部分可观测情形**（p.4）：推导更复杂，作者构造增广状态空间 $\hat s=\{s,\bar{\boldsymbol{\tau}}_{-a}\}\in\hat S=S\times T^{n-1}$，配套定义 $\hat O$、$\hat r(\hat s,u)=\sum_{\mathbf{u}_{-a}}\pi_{-a}(\mathbf{u}_{-a}|\boldsymbol{\tau}_{-a})r(s,\mathbf{u})$ 与 $\hat P$（式(5)），得到形式与式(3) 类似的 Bellman 方程（式(6)(7)）。**作者明确承认**：与完全可观测情形不同，部分可观测下等式右边还含有若干间接依赖他方策略、**据作者所知不可解（intractable）**的项，因此上式给出的重要性比值**只是近似**（p.4）。

### 修法二：多智能体 fingerprints（§4.2，p.5）

动机是**重要性采样的方差**：它虽然给出无偏估计，但重要性比值常常方差很大且无上界；截断或调整权重能降方差却引入偏差（p.5）。于是作者换一条路——**不修正非平稳性，而是拥抱它**（"embrace the nonstationarity ... rather than correcting for it"，p.5）。

**核心洞察**（p.5）：每个智能体要稳定回放，**并不需要**能对所有可能的 $\boldsymbol{\theta}_{-a}$ 取值条件化，**只需要**覆盖那些**真的出现在它回放记忆里的** $\boldsymbol{\theta}_{-a}$。而"产生缓冲区内数据的策略序列"可以看成**高维策略空间中一条一维轨迹**；要稳定回放，观测只需能分辨**当前训练样本出自这条轨迹的哪一段**。这就是 hyper Q-learning（Tesauro 2003）在深度设定下可行的原因——不必把对方的网络权重当输入（那是维数灾难，p.5 明确排除）。

**对 fingerprint 的要求**（p.5）：必须与真实状态—动作值相关；应当随训练**平滑变化**，以便在不同质量的对方策略之间泛化。

**具体选择**（p.5）：

$$O'(s)=\{O(s),\ \epsilon,\ e\}$$

- $e$ = 训练迭代号。作者指出它的一个潜在问题：策略收敛之后，模型需要把多个 fingerprint 映射到同一个值，函数会更难学、更难泛化。
- $\epsilon$ = 探索率。通常按退火计划平滑变化、且与性能高度相关，因此被一并加入。
- 作者原话：实测表明"even this simple fingerprint is remarkably effective"（p.5）。

### 实验设置（§5，p.6）

- **域**：去中心化的星际争霸单位微操（§5.1，p.6）。每个智能体控制一个单位，只观测以该单位为中心的地图子集；动作为 `move[direction]`、`attack[enemy id]`、`stop`、`noop`。奖励 = 该时间步对敌方造成的伤害，外加终局奖励（本方全部单位的生命值之和）。两个变体：**m3v3** 与 **m5v5**。实现用 Torch7 + TorchCraft。
- **架构**（§5.2，p.6）：沿用 Foerster 等 2016 的循环 DQN，去掉消息通道；两种模型——两层全连接隐层的 feed-forward（FF），或单层 GRU；每个隐层 **128** 个神经元。
- **超参**（§5.2，p.6）：$\epsilon$ 在 **1500 个 episode** 内从 **1.0 线性退火到 0.02**；训练 **$e_{max}=2500$** 个 episode；每步收集一个 episode 存入回放；**每次从回放中均匀采样 $30/n$ 个 episode**（$n$ 为智能体数）并按完整展开的 episode 训练。
- **重要性权重的三项工程处理**（§5.2，p.6）：① 裁剪到区间 **[0.01, 2]**；② 按智能体数归一化，即**开 $1/(n-1)$ 次方**；③ 除以权重的**滑动平均**以保持整体学习率不变。

## 非平稳性处理方式

**本文处理的"对手在学"是队友在学；处理手段不是建模对手，而是控制回放数据的时龄信息。**

| 路线 | 做法 | 对非平稳性的态度 | 代价 |
| --- | --- | --- | --- |
| XP（朴素） | 回放 + IQL，不做处理 | 忽略 | 模型试图同时对**历史上每一个**对方策略都学一个最佳响应；"the experience replay is therefore used inefficiently, and the model cannot generalise properly from experiences early in training"（§6，p.6） |
| **XP+IS** | 按 $\pi^{t_r}_{-a}/\pi^{t_i}_{-a}$ 加权，旧数据自然衰减（式(4)，p.4） | **修正** | 部分可观测下只是近似（p.4）；随 $\epsilon$ 下降，重要性比值**多峰且方差递增**，"so few experiences contribute strongly to learning"（§6.1，p.7） |
| **XP+FP** | 把 $\{\epsilon,e\}$ 加入观测，让值函数分辨"哪一段"（p.5） | **拥抱** | 需要设计 fingerprint；收敛后多个 fingerprint 映射到同一值会更难学（p.5） |

**实测取舍（这是本文最可引用的一组结论）：**

1. **不用回放最差**。§6（p.6）："Across all tasks and models, the baseline without experience replay (NOXP) performs poorly."原因是没有轨迹多样性，$\epsilon$ 变小后过拟合贪婪策略。
2. **朴素回放已经好过不回放**。§6（p.6）："Despite the nonstationarity, the stability of experience replay enables XP to outperform NOXP in each case."
3. **重要性采样只在 feed-forward 上略有提升**。§6.1（p.7）："The importance sampling approach (XP+IS) **slightly** outperforms XP when using feed-forward models."并给出失效机制：训练早期权重表现良好、方差低；**随着 $\epsilon$ 下降，重要性比值变得多峰且方差递增**（原文给出"绝大多数重要性权重 ≤ `ε(1−ε)` 的幂"这一描述，**该处上标在 MinerU 转换中丢失，具体指数形式未核实**）。
4. **fingerprint 增益最大**。§6.2（p.7）："the simple fingerprint of adding $e$ and $\epsilon$ to the observation (XP+FP) **dramatically improves** performance for the feed-forward model."它提供了足够的消歧能力来跟踪对方策略的质量变化，使回放缓冲被正当使用；网络仍能看到多样的输入状态，但可以按已知的训练阶段调整预测值。
5. **两条修法不可叠加**。§6.2（p.7–8）：Figure 2 显示"there is **no extra benefit** from combining importance sampling with fingerprints (XP+IS+FP)"。作者的解释是二者在解决同一个非平稳性问题，只是方式不同。
6. **FP 让历史经验可迁移**。§6.2（p.8）：Figure 3 显示网络学会在不同训练阶段平滑地改变价值估计，并把高价值正确地与训练后期的小 $\epsilon$ 关联；"The fingerprint enables the **transfer of learning between diverse historical experiences**"。作者据此指出：使用重要性采样时大多数经验被强烈折价，**fingerprint 路线实际可用的数据集更大**。
7. **循环网络下两条修法基本不需要**。§6.3（p.8）："When using recurrent networks, the performance gains of XP+IS and XP+FP are **not as large**; in the 3v3 task, **neither method helps**."原因是星际争霸中的**观测轨迹本身就显著指示训练阶段**（Figure 4a/4b）——智能体可以观察到"自己或队友做了很多看似随机的动作"，从而推断样本来自训练早期。作者用一个线性模型从循环隐状态预测训练期的 $\epsilon$，**即使只用 XP、不加 fingerprint，预测精度也相当高**（Figure 4c）；而加了 fingerprint 的模型隐状态信息量更大（Figure 4d）。

## 可迁移机制

1. **"回放里的旧数据不再反映当前动力学"是可以独立识别的失效模式**（§1，p.1）。在 DGA 单步扰动博弈中，若攻击者（或检测器）维护一份"过去成功扰动/成功检出"的经验池，而对手在期间有过更新，则该池同样失效。**可迁移动作：把"数据年龄"当作一等公民登记进经验元组**，而不是假设池内样本同分布。
2. **两条通用路线：按漂移量加权（修正）或把"年龄"编码进输入（拥抱）**（式(4)，p.4；$O'(s)=\{O(s),\epsilon,e\}$，p.5）。**后者更便宜且在本任务上更强**（§6.2，p.7）。迁移时优先试"给模型一个年龄标记"，再考虑重加权。
3. **fingerprint 的设计原则：一个与"样本出自轨迹哪一段"一一对应、且随训练平滑变化的低维量**（p.5）。作者给出的候选是"探索率 $\epsilon$ + 迭代号 $e$"。**对 DGA 的对应物是"对手（检测器）当前的版本号 / 迭代号 / 攻击者的扰动预算"**——这些量在对手学习过程中天然平滑变化，且能唯一标识数据来源阶段。
4. **"高维策略空间中的一维轨迹"这一压缩论证**（p.5）：不需要对所有可能的对手参数条件化，**只需要覆盖回放里真实出现过的那些**。这为"只用一个标量而非对手的完整权重"提供了理由，是可迁移的降维论证模板。
5. **重要性权重的三项工程处理**（§5.2，p.6）：裁剪到 **[0.01, 2]**、按智能体数开 **$1/(n-1)$** 次方归一、除以**滑动平均**以保持学习率。**方差控制不靠理论，靠这三个具体动作**，可直接照搬到任何带重要性权重的经验回放实现。
6. **"两种修法互为替代而非互补"这一实测关系**（§6.2，p.7–8）：若两种机制针对同一病灶，叠加前应先做消融，否则容易把"重复解决同一问题"报告成"协同增益"。
7. **修法是否必要取决于模型是否已经看到历史**（§6.3，p.8）：循环网络的隐状态已经携带了"年龄"信息，因此显式 fingerprint 的边际收益变小。**迁移时的判据是：模型输入里若已包含足够长的历史，显式年龄标记的增益应先在消融中验证，不可默认有效。**
8. **作者自己点名了"分类上的变化数据"这一未做方向**（§7，p.8）："In the future, we would like to apply these methods to a broader range of **nonstationary training problems, such as classification on changing data**, and extend them to multiagent actor-critic methods."——**这是作者承认的空白**，引用时正好说明"该机制向监督式漂移问题迁移"**在原论文中并未验证**。

## 不能直接声称内容

- **不能说它是安全域工作或与攻击者共演化**：任务是**合作型**星际争霸微操，非平稳性来自**同队学习中的队友**，外部对手是固定规则的游戏 AI（§3.2，p.3；§5.1，p.6）。它**不落在 report (8) 四级表的任何一层**，也不能作为"攻击者—防御者共演化"的先例。
- **不能说它在分类、漂移或 DGA 上验证过**：全部实验只有 StarCraft 的 **m3v3 与 m5v5** 两个任务（§5.1，p.6）。向"变化数据上的分类"迁移是**原文列出的未来工作**（§7，p.8），**不是已完成的实验**。
- **不能把 §6.2 的"fingerprint 大幅有效"外推到其他设定**：该结论的限定条件是 **feed-forward 模型**；同一论文的 §6.3（p.8）明确说**循环网络下增益不大、3v3 任务中两条修法都无帮助**。**引用时必须带上模型类型这一限定**。
- **不能把重要性采样说成"无效"**：它在 FF 模型上**确实略有提升**（§6.1，p.7），只是弱于 fingerprint；且它在**部分可观测设定下只是近似**（p.4），理论保证只在完全可观测情形成立。
- **不能引用未核实的重要性权重表达式**：§6.1（p.7）中"绝大多数重要性权重 ≤ 某阈值"的具体指数形式在 MinerU 转换中**上标丢失**，本笔记只保留定性结论（"绝大多数权重很小、少数经验贡献主要学习信号"），**具体公式需回原件核对后方可引用**。
- **不能说其超参具有普适性**：$\epsilon$ 退火 1500 episode、训练 2500 episode、隐层 128、重要性权重裁剪 [0.01, 2]、采样 $30/n$ 个 episode 都是**该域上的任务化设定**（§5.2，p.6），论文未做超参敏感性分析。
- **不可复现性提示**：实现在 **Torch7 + TorchCraft**（§5.1，p.6）上，该工具链已停止维护；论文**未报告随机种子、未给出多次运行的方差**（Figure 2 的置信区间只标示"one standard deviation of the sample mean"）。
- **不要把它当作"safety 约束"或"安全回归约束"文献**：本文与安全约束、回归防护、鲁棒性门禁无关，全文不涉及攻击、防御、逃逸、误报等概念。

## 文献信息

- 会议与出处：本地 PDF 元数据 `Subject: Proceedings of the International Conference on Machine Learning 2017`（`pdfinfo` 实测）；arXiv 编号 **1702.08887**（据 Hernandez-Leal 等综述参考文献条目，`arXiv.org, 1702.08887v1, 2017b`，见该综述 p.52）
- 作者：Jakob Foerster\*、Nantas Nardelli\*、Gregory Farquhar、Triantafyllos Afouras、Philip H. S. Torr、Pushmeet Kohli、Shimon Whiteson（\* 为共同第一作者，p.1；作者名单亦见 PDF 元数据 Author 字段）
- 本地原件：`raw/papers/attack-detection/2017-Foerster-Stabilising-Experience-Replay.pdf`（共 10 页，含参考文献）
- 全文转换：`/tmp/dga-adv-20260910/marl/2017-Foerster-Stabilising-Experience-Replay/`（MinerU md + json，页码由 json 的 `page_idx` 实测，页号 = `page_idx` + 1）
- 被综述收录：[[2017-HernandezLeal-多智能体非平稳性综述]] 在 §6.5 "Line 2: Dynamic interactions"（p.43，探索噪声）与 "Line 4: Applications"（p.45，深度 RL 与 MAS）两处引用本文（该综述记为 `Foerster et al., 2017b`）
- 资助：ERC Horizon 2020（#637713）、Oxford-Google DeepMind 奖学金、Microsoft Research PhD 奖学金、EPSRC AIMS CDT EP/L015987/1、ERC-2012-AdG 321162-HELIOS、EPSRC Seebibyte EP/M013774/1、EPSRC/MURI EP/N019474/1；GPU 由 Microsoft Azure for Research 提供（p.9）
