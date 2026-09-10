---
title: "VAPO: Efficient and Reliable Reinforcement Learning for Advanced Reasoning Tasks"
authors: [ByteDance Seed（完整作者列表见论文 Contributions 节）]
year: 2025
date: 2026-09-10
journal: "arXiv:2504.05118v3（2025-04-07 首版，13 页，ByteDance Seed）"
source_pdf: "[[raw/papers/grpo/2025-Yue-VAPO-Efficient-and-Reliable-RL.pdf]]"
tags:
  - GRPO
  - 去评论家
  - 价值模型
  - 强化学习
  - 长思维链
  - GAE
  - 类型/论文
key_finding: "在**保留价值模型**（value-model-based）路线上把长 CoT RL 做稳：作者定位三个病灶——价值模型偏置、序列长度异质、奖励稀疏——并用七项技术系统性组合解决（§3–§5）。关键诊断是 **GAE 中固定 λ=0.95 在长序列下失效**：长度 l>100 时奖励对应的 TD 误差系数 `0.95^100≈0.006`，优势计算被有偏的自举项主导（p.3），故提出 **Length-Adaptive GAE**，让 λ_policy 的系数之和与输出长度成比例（p.3–4）。VAPO 在 Qwen2.5-32B 上 AIME24 得 **60.4**，比 DeepSeek-R1-Zero-Qwen-32B 与 DAPO 高 10 分以上，5000 步内达 SOTA 且多次独立运行无崩溃（摘要、图 1）。"
method: "PPO + 价值模型 + 七项技术：Value-Pretraining、Decoupled-GAE（来自 VC-PPO）、Length-Adaptive GAE（本文）、Token-level Policy Gradient Loss（来自 DAPO）、Clip-Higher（来自 DAPO）、Positive Example LM Loss（来自 SIL）、Group-Sampling（来自 GRPO）；消融表见 p.6（表 1）"
baseline: "Vanilla PPO（AIME24 5 分）、DeepSeek-R1-Zero-Qwen-32B（47）、DAPO（50）；基座 Qwen2.5-32B；AIME24 avg@32（摘要、表 1，p.6）"
aliases:
  - VAPO
  - Yue2025-VAPO
related:
  - "[[2025-Yu-DAPO解耦裁剪与动态采样]]"
  - "[[2024-Shao-DeepSeekMath与GRPO开山]]"
  - "[[2025-Liu-LitePPO极简组合]]"
  - "[[GRPO变体群-方法选型]]"
---

# VAPO：把价值模型路线在长 CoT 上做稳

> ByteDance Seed，2025，arXiv:2504.05118v3 · 13 页 · 原件 `raw/papers/grpo/2025-Yue-VAPO-Efficient-and-Reliable-Reinforcement-Learning.pdf`

## 证据等级

**E3 全文级**。原件已下载（arXiv 2504.05118v3，1.1 MB，13 页），正文与消融表逐节读完；公式经 MinerU `extract` 模式转 LaTeX 后回原文页核对，页码锚点用逐页文本索引确认（`pypdf` 只读检索，2026-09-10）。

**与本目录其它条目路线的区别**：GRPO／DAPO／Dr. GRPO／GSPO／SAPO／GMPO／GFPO／LitePPO 都是 **critic-free**；VAPO 反过来**坚持保留价值模型**。引用"GRPO 家族"时不得把 VAPO 混入 critic-free 一线。

## 一句话

长 CoT 上 critic-free 不是唯一解：VAPO 说明价值模型路线此前失败是**价值初始化和 GAE 折扣**没处理好，而不是价值模型本身错。

## 机制（§3–§5，p.2–6）

### 三个病灶（§3.1，p.2–3）

1. **价值模型偏置**：价值模型从奖励模型初始化，而奖励模型与价值模型目标不匹配，朴素 PPO 会崩溃、输出长度塌缩。
2. **序列长度异质**：混合长度训练时，GAE 的最优 λ 随长度变化。
3. **奖励稀疏**：长 CoT 只在终止 token 给奖励，探索-利用权衡极难。

### 七项技术（§5，p.3–5）

| 技术 | 作用 | 来源 | 位置 |
|---|---|---|---|
| Value-Pretraining | 消除价值初始化偏置 | VC-PPO | §5.1，p.3 |
| Decoupled-GAE | 价值更新目标用 λ=1.0，得到无偏梯度下降、缓解长 CoT 的奖励衰减 | VC-PPO | §5.1，p.3 |
| **Length-Adaptive GAE**（本文） | λ_policy 的系数之和与输出长度成比例，使 TD 误差在长短序列间分布更均匀 | 本文 | §5.2，p.3–4 |
| Token-level Policy Gradient Loss | 损失分母改为批次内 token 总数，避免长序列 token 被稀释 | DAPO | §5.2，p.4 |
| Clip-Higher | 缓解熵坍塌 | DAPO | §5.3，p.4 |
| Positive Example LM Loss | 对正例加语言建模损失（自模仿学习） | SIL | §5.3，p.5 |
| Group-Sampling | 组内采样降方差 | GRPO | §5.3，p.5 |

**Length-Adaptive GAE 的论证（p.3）**：固定 `λ_policy=0.95` 时，长度 `l>100` 的序列中奖励对应的 TD 系数 `0.95^100≈0.006`，实际趋零，优势计算被**可能带偏的自举 TD 误差**主导。因此让 λ 的累计系数随长度自适应。

## 实验结果（§6，p.6）

| 配置 | AIME24 avg@32 | 位置 |
|---|---|---|
| Vanilla PPO | 5 | 表 1，p.6 |
| DeepSeek-R1-Zero-Qwen-32B | 47 | 表 1，p.6 |
| DAPO | 50 | 表 1，p.6 |
| VAPO w/o Value-Pretraining | **11**（严重坍塌） | 表 1，p.6 |
| VAPO w/o Decoupled-GAE | 33 | 表 1，p.6 |
| VAPO w/o Length-Adaptive GAE | 45 | 表 1，p.6 |
| VAPO w/o Clip-Higher | 46 | 表 1，p.6 |
| VAPO w/o Token-level Loss | 53 | 表 1，p.6 |
| VAPO w/o Positive Example LM Loss | 54 | 表 1，p.6 |
| VAPO w/o Group-Sampling | 55 | 表 1，p.6 |
| **VAPO（完整）** | **60.4** | 摘要、表 1，p.6 |

**必须随结论一起转述的作者限定**：全部实验是**单一基座（Qwen2.5-32B）+ 单一基准（AIME24）**，无第二个任务域、无第二种子、无置信区间；作者未给训练算力预算。"不崩溃"是作者自述的多次运行观察（摘要），没有给出运行次数或失败判据。

## 可迁移机制

1. **折扣因子与序列长度耦合**（p.3）：当"轨迹"很长时，固定折扣因子会让远端奖励的贡献指数衰减到 0，优势被自举项主导。**这是一条与模型无关的时序信用分配判据**，凡长序列上的 RL 都需检验：远端奖励的系数是否已实际归零。
2. **价值初始化的目标错配**（§5.1，p.3）：从奖励模型初始化价值模型会引入系统性偏置，消融显示去掉后性能从 60.4 崩到 11——**这是本目录内最大单项消融落差**，说明初始化错配的破坏力远超算法细节。
3. **消融落差可作为优先级排序**（表 1，p.6）：七项技术的贡献差异极大（Value-Pretraining 49.4 分落差，Group-Sampling 5.4 分）。**引用"某技术有效"时必须带落差量级**，否则会把边际技巧与决定性组件混为一谈。
4. **正例自模仿**（Positive Example LM Loss）：只对成功样本加权语言建模损失——这与 GFPO 的"只在保留子集内算优势"是同一思想的两种实现。

## 不能直接声称内容

- **不能把 VAPO 归入 GRPO 家族或 critic-free 路线**：VAPO 是 value-model-based 的 PPO 扩展，明确以"保留价值模型"为路线选择（摘要）。它与 GRPO 系列是**对照关系**而非同族。
- **不能声称"价值模型路线优于 critic-free"**：VAPO 60.4 vs DAPO 50 的比较是在**作者自选配置**下完成的；DAPO 侧是否经过同等调参、算力是否对齐，论文未给公平性论证。
- **不能引用表 1 之外的分数**：所有数字来自 AIME24 avg@32 单基准。
- **不能把"多次运行无崩溃"当作稳定性证据**：论文未给运行次数、崩溃判据、失败率统计。
- **不能把 Length-Adaptive GAE 的形式搬到非 token 级 MDP**：该构造直接依赖"每步一个 token"的序列长度定义。
- **不能忽略作者身份声明**：本论文的作者列表在 Contributions 节而非署名页，题录引用须核对官方版本（本笔记已核 arXiv API 元数据）。

## 与课题的关系

- 对本课题的价值是**反例侧的证据**：DRIFT 第三章曾以"无评论家更省资源"为由倾向 critic-free，但 VAPO 说明在长序列、稀疏奖励下 critic-free 可能不是稳妥选择。**这不构成改用价值模型的理由**，只是要求该选择须有任务化实测依据。
- `0.95^100≈0.006` 这一量级计算是一个**可直接复用的诊断公式**：用于判断本课题若采用时序信用分配，远端奖励是否仍在起作用。

## 疑问 / 待验证

- 论文未报告：训练算力／步数以外的成本（显存、价值模型参数量）、种子数、方差、基座以外的模型。
- VAPO 的七项技术在非数学推理任务上的可迁移性无证据。
- 表 1 的消融是**逐项移除**还是**逐项添加**，论文未明确说明顺序；两种口径得到的"重要性排序"含义不同。

## 文献信息

- arXiv:2504.05118v3（2025-04-07 提交，v3 修订）· ByteDance Seed
- 题录核验：arXiv API 直查 `id_list=2504.05118` 返回题名、日期、发布日期（2026-09-10 核验）；Zotero key `FRN3NM4X`
- 相关理论分析（本轮未入库）：arXiv:2505.17997《Towards Analyzing and Understanding the Limitations of VAPO: A Theoretical Perspective》
- 原件：`raw/papers/grpo/2025-Yue-VAPO-Efficient-and-Reliable-Reinforcement-Learning.pdf`
