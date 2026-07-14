---
title: "Improving Generalization in Intent Detection: GRPO with Reward-Based Curriculum Sampling"
authors:
  - Zihao Feng
  - Xiaoxue Wang
  - Ziwei Bai
  - Donghang Su
  - Bowen Wu
  - Qun Yu
  - Baoxun Wang
year: 2025
date: 2026-07-14
journal: arXiv preprint
doi: "arXiv:2504.13592"
source_pdf: "[[raw/papers/2504.13592v2.pdf]]"
tags:
  - NLP
  - 强化学习
  - 意图检测
  - GRPO
  - 课程学习
  - 类型/论文
aliases:
  - GRPO-RCS
  - Feng2025-GRPO-RCS
  - 意图检测 GRPO 课程采样
key_finding: "GRPO 强化学习训练的意图检测模型在泛化能力上碾压 SFT（未见意图 +83%、细分意图 +83%、合并意图 +94%、跨语言均有效），配合 RCS 课程采样仅用 60% 数据即可超越全量 SFT；Base Model 经过 GRPO 训练后不输 Instruct Model"
method: "GRPO（Group Relative Policy Optimization）+ ReAct Prompting + 规则奖励（格式 + 准确率）+ RCS（Reward-based Curriculum Sampling）两阶段课程学习"
baseline: "Qwen2.5-7B-Instruct SFT 全量微调；与 GRPO（无 RCS）对比"
---

# Improving Generalization in Intent Detection: GRPO with Reward-Based Curriculum Sampling

> 腾讯 PCG + 哈工大，2025-04-21（v2）
> arXiv:2504.13592 · 7 位作者 · 12 页 · 基础模型：Qwen2.5-7B-Instruct

---

## 一句话

用 GRPO 强化学习替代 SFT 做意图检测训练，模型不再死记"query → label"映射，而是学会理解指令和推理——在未见意图、细分意图、合并意图、跨语言四种泛化场景下全面碾压 SFT。配合 RCS 课程采样策略（第一阶段全量训练收集 reward → 第二阶段只训低分样本），仅用 60% 的数据就超越了全量 SFT。意外发现：Base Model 经过 GRPO 后不输 Instruct Model，说明模型的核心能力来自预训练而非对齐。

---

## 背景：意图检测泛化为什么难

### 问题本质

任务型对话系统中，意图检测模块负责判断用户 query 属于哪个意图（如"订机票""查天气"），然后路由到对应的 API 工具。现实是：**可集成的 API 工具不断增多，新工具上线时模型没见过对应的意图类别**。

### 三种泛化场景

论文定义了意图检测的三个真实泛化维度：

| 场景 | 含义 | 例子 |
|------|------|------|
| 未见意图（Unseen） | 全新的任务类别，训练集中完全不存在 | 新增"唱儿歌""讲故事"等儿童场景 |
| 细分意图（Subdivided） | 原有大类拆分为细粒度子类 | "文本聊天"拆为：文本处理 / 安全话题 / 自由聊天 |
| 合并意图（Grouped） | 多个旧类合并为一个新类（Agent 升级） | "好友推荐"+"聊天机器人推荐"→"推荐" |

### 现有方法为什么不行

- **零样本改写**（NLI 格式 / 常识知识引入）：碰到复杂工具关系和分布偏移时性能退化严重
- **LLM 原生零样本推理**：依赖 LLM 自身的泛化能力，不可控
- **SFT 微调**：学到的只是"query → label"的映射，碰到新 label 直接束手无策——论文中 SFT 在 Subdivided 和 Grouped 测试集上**准确率为 0%**，因为模型只会从训练集见过的 10 个类别中选

---

## 方法核心

### GRPO 强化学习训练

不直接学 P(y|x)，而是让模型通过 ReAct Prompting 生成推理过程，然后用**规则奖励**（而非偏好模型）来指导训练：

```
系统 prompt: "You are a helpful assistant."

指令模板：
  你是帮助用户从工具列表中选择正确工具的 Agent。
  对每个工具，先给出描述和参数，再给出处理多轮对话的逻辑说明。
  
  ## Tool APIs
  {tools text}
  
  ## Task Logic
  {logic text}
  
  ## Output Format
  Last Tool: ...
  Question: ...
  Thought: 你应该思考要做什么
  Action: 要执行的动作
  Finish!
```

**两个规则奖励函数**：

```
R = λ_format × R_format + λ_answer × R_answer

R_format: 输出是否严格遵循三行格式（Thought/Action/Finish!）→ 0 或 1
R_answer:  预测意图是否与 ground truth 完全匹配 → 0 或 1
```

**为什么要用规则奖励而不是偏好模型**：意图检测是确定性问题（答对/答错），不需要人类偏好判断。规则奖励更简洁、无偏、无需额外标注。

### RCS：Reward-based Curriculum Sampling

论文发现 GRPO 在意图检测上收敛极快（几十步就接近 SFT），导致后续训练中 reward 方差极小，模型不再从简单样本中受益。

**两阶段课程学习**：

```
阶段一：全量数据 GRPO 训练 60 步
        ↓
    对每个样本，计算 G 次采样的累计 Score：
    Score_i = Σ(j=1..G) (λ_format × R_format_ij + λ_answer × R_answer_ij)
        ↓
阶段二：筛选 Score_i < (λ_format + λ_answer) × G 的样本（即"低分挑战样本"）
        ↓
    仅用这些挑战样本继续训练
```

**关键发现**：

- 阶段二**完全不用简单样本**，不仅没有灾难性遗忘，反而性能进一步提升
- 最终仅用了 60% 的训练数据就超越了全量 SFT 和全量 GRPO
- 正样本（简单样本）混入越多反而越差——挑战样本的浓度才是关键

| 挑战:正样本比例 | MultiWOZ Avg |
|:---:|:---:|
| 1:2 | 94.8 |
| 1:1 | 95.0 |
| 2:1 | 95.4 |
| **1:0（纯挑战样本）** | **96.0** |
| 全量 SFT | 93.3 |
| 全量 GRPO | 93.3 |

---

## 实验结果

### GRPO vs SFT：泛化能力的全面碾压

**MultiWOZ 2.2（领域留一法）**：

| 留出领域 | SFT 对该领域 | GRPO 对该领域 | GRPO 优势 |
|:---|:---:|:---:|:---:|
| Hotel | 37.1% | **87.1%** | +50.0% |
| Restaurant | 57.1% | **91.2%** | +34.1% |
| Taxi | 53.4% | **74.2%** | +20.8% |
| Train | 47.9% | **90.6%** | +42.7% |
| Attraction | 43.8% | 43.1% | -0.7%（唯一例外） |

**TODAssistant（三类泛化）**：

| 场景 | SFT | GRPO | 提升 |
|:---|:---:|:---:|:---:|
| Unseen5（全新类别） | 44.5% | **90.6%** | +46.1% |
| Subdivided（细分类别） | 0.0% | **83.1%** | +83.1% |
| Grouped（合并类别） | 0.0% | **93.6%** | +93.6% |

SFT 模型在 Subdivided 和 Grouped 上**准确率为 0%**——因为 SFT 学死了"只能输出 10 个类别"的映射，而 GRPO 学会了理解指令中的新工具描述。

**跨语言泛化**：仅用英文 MultiWOZ 训练 → 中文 TODAssistant 零样本测试，GRPO 达到 **65.2%**（SFT 几乎为零）。

### CoT（思考过程）的价值取决于任务复杂度

| 数据集 | w/o Thought | w/ Thought | 分析 |
|:---|:---:|:---:|:---|
| TODAssistant（机器生成） | 域内 97.8 | 域内 96.8 | 域内无需 CoT |
| TODAssistant 泛化 | Unseen 86.4 | Unseen **90.6** | 泛化场景有收益 |
| MultiWOZ（人工构造） | 76.1 | **93.3** | 复杂任务收益巨大 |

MultiWOZ 模型输出平均 **56 tokens**（vs TODAssistant 的 37 tokens），说明 MultiWOZ 的意图识别需要更长的推理链，CoT 的价值因此更明显。

### Base Model vs Instruct Model

| 模型 | MultiWOZ Avg |
|:---|:---:|
| Qwen2.5-7B + GRPO | **91.93** |
| Qwen2.5-7B-Instruct + GRPO | 93.25 |

Base Model 收敛更慢，但最终效果与 Instruct Model 持平。**这意味着意图检测能力来自预训练阶段**，后续的指令对齐只是帮助模型更好地调用已有能力。

### 「Aha Moment」在意图检测中不会出现

论文发现：R1 式的「模型自己增加推理长度→获得更高奖励→学会深度推理」的 aha moment，在意图检测任务中**不存在**。因为意图检测的推理链条太短，不需要深度思考。如果把格式奖励放宽，Base Model 确实会增加输出长度——但增加的都是**任务无关内容**，目的是刷格式奖励而非真正推理。

---

## 我的理解

这篇论文的价值不在技术创新——GRPO、课程学习、ReAct 都是现成的——而在于**系统性地揭示了一个反直觉的事实**：SFT 在意图检测这个看似简单的任务上，不仅泛化差，而且泛化差的原因是**它学得太好了**。

SFT 把模型训练成了一个「从 10 个候选标签中选一个」的分类器。当标签集合改变（新增/细分/合并），这个分类器就废了。GRPO 不做分类——它训练模型理解「工具描述 → 匹配用户需求」的推理过程，所以工具列表怎么变都能应对。

这对应到 DeepSeek-R1 范式的核心哲学：**不要教模型选什么答案，教它怎么想**。

**RCS 课程采样的洞察**：简单样本在 RL 中不仅无用，而且有害——它们占据了训练算力却不贡献梯度信号（reward 方差接近零）。用 RCS 筛掉这些样本，相当于把算力集中到「模型还没学会的东西」上。这和人类学习中的「刻意练习」是同一个原理。

**Base Model = Instruct Model** 这个发现很重要：它暗示很多「对齐」工作其实是在做**格式适配**而非**能力注入**。模型的能力在预训练阶段就锁定了。这对实际部署的意义是——如果你只需要做意图检测，Qwen2.5-7B（非 Instruct）加上 GRPO 就够，省掉了指令微调的成本，甚至可能更适合你的自有指令格式。

**和 mHC 的共同点**：两篇论文都在解决一个「在大规模下暴露的根本性缺陷」——mHC 发现 HC 的 W 矩阵在 27B 时崩溃，这篇发现 SFT 在意图 schema 动态变化时崩溃。两者都在 7B 规模下表现正常，上规模后才出问题。这再次验证了 DeepSeek 的研究风格：**不在小规模上自嗨，用大模型的崩溃来暴露真实问题**。

**对我的运维场景有什么启发**：虽然这是 NLP 论文，但方法论可迁移。比如 MCDN 踢点决策——当前基于规则的阈值判断，如果未来引入模型做踢点/恢复决策，"意图检测的泛化问题"就是一个类比：新机房 / 新运营商 / 新业务模式上线时，模型的"意图"（该不该踢）需要泛化到未见过的资源拓扑。GRPO + RCS 的思路提示我们：**训练时就应该让模型面对多样化的资源拓扑，而不是死记历史案例**。

---

## 与相关工作的关系

- **DeepSeek-R1 (Guo et al. 2025)**：本文直接启发源——R1 证明了 RL 可以激发 LLM 的推理泛化，本文把这个思路搬到意图检测这个具体下游任务
- **DeepSeekMath / GRPO (Shao et al. 2024)**：GRPO 方法论的来源，本文是 GRPO 在对话系统领域的首次系统应用
- **ReAct (Yao et al. 2023)**：本文使用的 Prompting 框架
- **MultiWOZ 2.2 (Zang et al. 2020)**：本文使用的基准数据集
- **SFT 在意图检测上的已有工作**：零样本 BERT-Adapter (Comi et al. 2023)、常识知识注入 (Siddique et al. 2021)、LLM 零样本 (Parikh et al. 2023)——本文系统性地对比并超越了所有这些方法
- **课程学习 / 难度采样**：RCS 的课程学习思想有普适性，可与 Hard Example Mining、Focal Loss 等做关联

---

## 疑问 / 待验证

- RCS 目前是**离线**的（需要先跑一轮 GRPO 收集 reward），论文提到后续可以做在线版——在线 RCS 的实时采样策略怎么设计？是否可以用 reward 的移动平均来动态调整采样阈值？
- 论文只在 7B 规模上实验，更大模型（如 70B）上 GRPO 的优势是否保持？SFT 在更大模型上是否也会有更好的泛化（因为大模型本身的 zero-shot 能力更强）？
- RCS 筛掉简单样本的"副作用"——如果简单样本和新任务之间存在潜在关联（比如都是"信息检索"类意图），筛掉它们是否会丢失这种隐式知识迁移？
- Base Model = Instruct Model 的结论是否只在意图检测这种相对简单的单任务上成立？如果换成多意图检测（一个 query 对应多个意图），是否需要更强的指令跟随能力？
- 意图检测的泛化本质是"指令理解"能力，这和 GRPO 在其他指令理解任务（如工具调用、代码生成）上的泛化是一致的吗？还是意图检测有特殊性？

---

## 原始摘要

> Intent detection, a critical component in task-oriented dialogue (TOD) systems, faces significant challenges in adapting to the rapid influx of integrable tools with complex interrelationships. Existing approaches, such as zero-shot reformulations and LLM-based dynamic recognition, struggle with performance degradation when encountering unseen intents, leading to erroneous task routing. To enhance the model's generalization performance on unseen tasks, we employ Reinforcement Learning (RL) combined with a Reward-based Curriculum Sampling (RCS) during Group Relative Policy Optimization (GRPO) training in intent detection tasks. Experiments demonstrate that RL-trained models substantially outperform supervised fine-tuning (SFT) baselines in generalization. Besides, the introduction of the RCS, significantly bolsters the effectiveness of RL in intent detection by focusing the model on challenging cases during training. Moreover, incorporating Chain-of-Thought (COT) processes in RL notably improves generalization in complex intent detection tasks, underscoring the importance of thought in challenging scenarios. This work advances the generalization of intent detection tasks, offering practical insights for deploying adaptable dialogue systems.

---

## 文献信息

- arXiv: [2504.13592](https://arxiv.org/abs/2504.13592)（v2: 2025-04-21）
- 页数：12 页
- 代码：未公开
- 作者单位：腾讯 PCG（平台与内容事业群）+ 哈工大计算学部
