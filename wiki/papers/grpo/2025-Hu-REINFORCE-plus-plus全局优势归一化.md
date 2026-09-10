---
title: "REINFORCE++: Stabilizing Critic-Free Policy Optimization with Global Advantage Normalization"
authors: [Jian Hu, Jason Klein Liu, Haotian Xu, Wei Shen]
year: 2025
date: 2026-09-10
journal: "arXiv:2501.03262v9（2025-01-04 首版，v9 修订，16 页）"
source_pdf: "[[raw/papers/grpo/2025-Hu-REINFORCE-plus-plus-Global-Advantage-Normalization.pdf]]"
tags:
  - 去评论家
  - 强化学习
  - 大语言模型
  - 优势归一化
  - RLHF
  - 过拟合
  - 类型/论文
key_finding: "指出 GRPO／RLOO 一类方法依赖的**提示级（局部）优势归一化**有三个问题：优势估计不准、易过拟合、且是**有偏估计**（摘要、§2.2，p.2）。REINFORCE++ 改为在**整个全局批次**上归一化优势：`A^{norm} = (A − mean(A|A∈D_batch)) / (std(A|A∈D_batch) + ε)`（式(5)，p.3），批次大（如 1024+）时均值／标准差收敛为稳定常数，估计**随批量增大渐近无偏**（p.3）。给两个变体：`REINFORCE++`（k=1，通用 RLHF）与 `REINFORCE++_{w/i}`（k>1 组采样，复杂推理）。最尖锐的实证是**小数据过拟合对照**：30 道 AIME-24 训练题上 GRPO 训练集 95.0% 但 AIME-25 Pass@1 **0.0**，而全局归一化的 REINFORCE++ 训练集 71.0、AIME-25 Pass@1 **2.5**、Pass@16 **40.0**（§4.2.1，p.5–6）。"
method: "PPO 目标 ＋ 全局优势归一化（式(4)(5)，p.3）；k=1 通用版与 k>1 组采样版（§3.2，p.3–4）；KL 惩罚按 k1 式直接写入奖励"
baseline: "GRPO（k=4）、RLOO（k=4）、ReMax（k=1+1）、PPO；Llama-3-8B-SFT ＋ Bradley-Terry 奖励模型（约 700K 人类偏好对）、20,000 条 prompt（§4.1，p.4）"
aliases:
  - REINFORCE++
  - Hu2025-REINFORCEpp
related:
  - "[[2024-Shao-DeepSeekMath与GRPO开山]]"
  - "[[2025-Liu-LitePPO极简组合]]"
  - "[[2025-Yu-DAPO解耦裁剪与动态采样]]"
  - "[[2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE风格]]"
  - "[[GRPO变体群-方法选型]]"
---

# REINFORCE++：全局优势归一化

> Jian Hu 等，2025，arXiv:2501.03262v9 · 16 页 · 原件 `raw/papers/grpo/2025-Hu-REINFORCE-plus-plus-Global-Advantage-Normalization.pdf`

## 证据等级

**E3 全文级**。原件已下载（arXiv 2501.03262v9，1.2 MB，16 页），正文与实验逐节读完；公式经 MinerU `extract` 模式转 LaTeX 后回原文页核对，页码锚点用逐页文本索引确认（`pypdf` 只读检索，2026-09-10）。

**版本提示**：该论文迭代到 **v9**，是本目录内版本号最高的一篇。正文标题页题名为《REINFORCE++: Stabilizing Critic-Free Policy Optimization with Global **Normalization**》，arXiv 元数据题名为 "…with Global **Advantage** Normalization"。两者指同一篇。

## 一句话

GRPO 在单个 prompt 的内部小样本上算均值／标准差，样本少因而估计不准且容易过拟合；REINFORCE++ 把这个统计量搬到整个批次上算，批次足够大时它收敛成稳定常数。

## 机制（§2–§3，p.2–4）

### 局部归一化的问题（§2.2，p.2）

作者列出三条：优势估计不准、倾向过拟合、**是理论上"有偏"的估计量**（摘要）。在 k=1（每个 prompt 只采一条）时，局部归一化甚至**不存在**（p.3）。

### 全局归一化（§3.1，式(4)(5)，p.3）

`A_{q,o_t} = r(o_{1:T}, q) − β·Σ_{i=t}^{T} KL(i)` …(4)

`A^{norm}_{q,o_t} = ( A_{q,o_t} − mean(A | A ∈ D_batch) ) / ( std(A | A ∈ D_batch) + ε )` …(5)

- 全局批次规模通常 ≥1024，故 `mean(·)`、`std(·)` 收敛为稳定常数（p.3）。
- 估计量**随 N→∞ 偏差消失**，且对异常值稳健（p.3）。

### 两个变体（§3.2，p.3–4）

| 变体 | 适用 | 说明 |
|---|---|---|
| `REINFORCE++`（k=1） | 通用 RLHF | 每个 prompt 采一条，最大化效率与 prompt 多样性 |
| `REINFORCE++_{w/i}`（k>1） | 复杂推理 | 先组采样，再叠加全局归一化的两步优势计算 |

作者的"最佳实践"主张（§5，p.9）：**通用任务不需要组采样（k>1），甚至可能次优**；组采样只在奖励稀疏的复杂推理任务上有必要。

## 实验结果（§4，p.4–9）

| 项 | 内容 | 位置 |
|---|---|---|
| 通用 RLHF 设置 | Llama-3-8B-SFT + Bradley-Terry 奖励模型（~700K 偏好对），20,000 条 prompt | §4.1，p.4 |
| 通用 RLHF 结果 | REINFORCE++（k=1）得分 **46.7**，与 GRPO（k=4）**46.8** 统计持平；但回答更短（**832** vs 860 token），每 token 得分更高（0.0561） | §4.1，p.4 |
| 训练动态 | GRPO 奖励上升快但 **KL 散度同步快速上升**（作者判为"破解奖励模型"）；REINFORCE++ KL 明显更低 | §4.1，p.4（图 2） |
| **小数据过拟合对照** | 30 道 AIME-24 训练、AIME-25 评测：**GRPO 训练集 95.0% 但 AIME-25 Pass@1 = 0.0**；REINFORCE++ 训练集 71.0、AIME-25 **Pass@1 2.5 / Pass@16 40.0** | §4.2.1，p.5–6（表 2、图 3） |
| 逻辑推理（K&K） | 简单题（2–3 人）GRPO 有竞争力；**难／OOD 题（8 人）GRPO 坍塌**；REINFORCE++ 在 ≥4 人的全部任务上更好，平均 **62.1 vs 55.7** | §4.2.1，p.6（图 4） |
| RL from Zero | Qwen2.5-Math-Base 从零训练：REINFORCE++ 在更难的 AIME-24、AMC-23 上 OOD 泛化更好，在分布内 MATH-500 保持竞争力 | §4.2.1，p.6（表 3） |
| 多步 RL | Qwen2.5-Base-7B 用 Python 工具解数学题 | §4.3，p.7 |

**必须随结论一起转述的作者限定**：核心对照是**作者自建实验**（OpenRLHF 框架，§4，p.4）；GRPO 侧的过拟合结论来自**一个 30 题的小数据集**，作者用它放大效应，**不能据此推断 GRPO 在常规数据规模下也会如此**。

## 可迁移机制

1. **统计量的作用域选择是一个独立的自由度**（式(5)，p.3）：均值／标准差可以取自局部组、整个批次，或任意中间粒度。**样本量决定估计方差**，这是纯统计论证，不依赖任务。
2. **"小分母"与过拟合的联系**（p.2–3）：局部归一化在小组内方差极小时会把噪声放大为巨幅梯度，进而快速拟合训练 prompt。**对本课题直接可用**：任何组相对方法在 "一组样本全同" 时都有这个风险，而检测任务的"明确样本"正是这种情形。
3. **KL 散度作为"奖励破解"的在线指示器**（§4.1，图 2，p.4）：奖励与 KL 同时快速上升 → 疑似在破解奖励模型。这是一个**训练中可实时监控的诊断量**，比事后评测廉价。
4. **在更难／OOD 的切片上比较方法**（§4.2.1，图 4，p.6）：GRPO 在简单题上不输、在难题上坍塌——**只在平均指标上比较会掩盖方法差异**。这条对本课题"分面评测"的要求有直接支持价值。
5. **k=1 的可行性**（§5，p.9）：通用任务上组采样并非必要。**这是对"GRPO 必须组采样"的一个反证**，对采样成本受限的场景有意义。

## 不能直接声称内容

- **不能声称全局归一化在所有场景都优于组归一化**：通用 RLHF 上二者统计持平（46.7 vs 46.8，p.4）；优势主要体现在**过拟合与 OOD 切片**上。
- **不能把"GRPO 会灾难性过拟合"写成一般结论**：该结论来自 30 题训练集的人为设置（§4.2.1，p.5）；作者用它做机制演示，不是常态性能比较。
- **不能把 REINFORCE++ 当作"新算法"**：它用的是 PPO 目标（式(1)(4)），唯一改变是优势归一化的作用域（p.3）。
- **不能忽略版本号**：本文已迭代到 v9，题名在 arXiv 元数据与 PDF 首页间有 "Advantage" 一词的差异，引用须指明版本。
- **不能把结论外推到非 LLM 任务**：全部实验是语言模型（Llama-3-8B、Qwen2.5-Math/Base），无表格数据或分类任务。
- **不能把"k=1 更优"外推到推理任务**：作者自己限定 k=1 只适用于通用域，复杂推理仍需 k>1（§5，p.9）。

## 与课题的关系

- **对 DRIFT 第三章的反过拟合证据最有价值**：本课题的核心病灶就是"在源年上表现好、在目标年退化"，而 REINFORCE++ 的 30 题实验正是一个**受控的过拟合演示**（训练集 95.0 / OOD 0.0）。这条证据支持"检查训练集与目标集的差距"作为止损判据。
- 与 [[2025-Liu-LitePPO极简组合]] 互为独立佐证：LitePPO 的 Takeaway 3（组级均值 + 批次级标准差）明确引用了本文并称"批次级归一化在某些场景下更好"（LitePPO p.7）。**两篇独立工作得到同向结论**，可提高该结论的可信度。

## 疑问 / 待验证

- 论文未报告：种子数、方差、"统计持平"的检验方法与置信区间。
- §4.1 的 KL 差异是否在同等奖励水平下比较，论文未给 KL 的具体数值。
- 表 2 的 `Pass@1 2.5 / Pass@16 40.0` 差距极大，作者未讨论原因。
- §5.2 "第三方验证"节（p.9）所述的第三方结论，本轮未展开核验。

## 文献信息

- arXiv:2501.03262v9（2025-01-04 提交，v9 修订）· 4 位作者（Jian Hu, Jason Klein Liu, Haotian Xu, Wei Shen）
- 题录核验：arXiv API 直查 `id_list=2501.03262` 返回题名《REINFORCE++: Stabilizing Critic-Free Policy Optimization with Global Advantage Normalization》、作者、日期（2026-09-10 核验）；Zotero key `3567TVIM`
- 实现：OpenRLHF 提供 `--algo.advantage.estimator reinforce` 与 `reinforce_baseline` 两个档位（OpenRLHF README，2026-09-10 核验）
- 原件：`raw/papers/grpo/2025-Hu-REINFORCE-plus-plus-Global-Advantage-Normalization.pdf`
