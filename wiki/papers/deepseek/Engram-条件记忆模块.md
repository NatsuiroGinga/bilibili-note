---
title: "Engram: Conditional Memory via Scalable Lookup — A New Axis of Sparsity for Large Language Models"
authors:
  - Chongyi Zheng
  - Zizheng Pan
  - Huanqi Cao
  - Zhenda Xie
  - Yixuan Wei
  - Wenfeng Liang
year: 2026
date: 2026-07-14
journal: arXiv preprint
doi: "arXiv:2601.07372"
source_pdf: "[[raw/papers/deepseek/2601.07372_Engram-DeepSeek.pdf]]"
tags:
  - LLM
  - 记忆
  - 稀疏化
  - MoE
  - DeepSeek
  - 类型/论文
aliases:
  - Engram
  - 条件记忆
  - n-gram 哈希记忆
  - Zheng2026-Engram
key_finding: "提出 O(1) n-gram 哈希查表的条件记忆模块 Engram，作为 MoE 之外的第二条稀疏化轴线；27B 论文实验在 MMLU、BBH、HumanEval、MATH 和长文本检索上优于等参数等 FLOPs 的 MoE 对照，但官方仓库只提供数据流演示代码，论文不证明其适用于 DGA 漂移。"
method: "O(1) n-gram 哈希查表（N-gram Hashing）+ Sparse Memory Lookup（只激活 k 条最相关记忆）"
baseline: "Dense Transformer（无 Engram）、MoE（单独使用）"
---

# Engram: Conditional Memory via Scalable Lookup

> Chongyi Zheng, Zizheng Pan, Huanqi Cao, Zhenda Xie, Yixuan Wei, Wenfeng Liang
> DeepSeek · arXiv:2601.07372 · 约 20 页

---

## 一句话

MoE 让不同 token 激活不同 FFN expert（**计算稀疏化**），Engram 让每个 token 从 n-gram 哈希表中查取相关记忆（**知识稀疏化**）——两条轴线正交协同，在不增加激活参数的前提下显著提升事实知识、推理和长文本能力。与 mHC 同属 DeepSeek 架构系列。

---

## 背景：稀疏化的两条轴线

### 第一条轴：MoE（Mixture of Experts）——计算稀疏化

```
Token → Router → 选 top-k expert → 计算
        每个 token 只激活少数 FFN expert
```

MoE 解决了"模型参数多但每次推理只激活一部分"的问题。但 MoE 的 FFN expert 存储的仍是压缩的隐式知识——你需要前向传播才能知道"Expert #3 擅长数学"。

### 第二条轴：Engram —— 知识稀疏化

```
Token → N-gram Hashing → 查哈希表 → 取 top-k 记忆向量 → 拼接到 token 表示
        每个 token 显式检索相关"事实/模式"
```

Engram 的核心 idea：**有些知识不适合用稠密 FFN 权重编码，更适合用显式的键值查找**。比如"Paris is the capital of France"——与其让 Transformer FFN 隐式记忆，不如直接存一条 `hash("Paris-is-the") → [capital, France]`。

---

## 方法：N-gram 哈希 + 稀疏查表

### 整体架构

```
输入 Token 序列: "The capital of France is"
                    │
                    ▼
        ┌──────────────────────┐
        │  N-gram 生成模块      │
        │  [The-capital]        │
        │  [capital-of]         │
        │  [of-France]          │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  哈希函数 H(ngram)    │
        │  → 哈希表索引          │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Memory Table         │
        │  索引 → 记忆向量       │  ← 可学习的参数
        │  取 top-k 最相关      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  拼接到 token 表示     │
        │  x' = x + MemoryVector│
        └──────────┬───────────┘
                   │
                   ▼
        继续 FFN / Attention
```

### 关键设计

1. **N-gram 哈希**：每个长度为 n 的连续 token 序列被哈希到一个固定大小的表中。O(1) 查表，不依赖注意力或检索——完全确定性的前向操作
2. **Memory Table 可学习**：表中的向量是训练参数，通过反向传播更新。但查表索引由哈希函数决定——哈希本身不可微（离散操作），梯度通过 top-k 记忆向量的加权和回传
3. **k-稀疏激活**：每个 token 只激活 k 条最相关的记忆向量（k << table_size），保证额外计算开销可控
4. **与 MoE 协同**：MoE 的 FFN expert 处理"计算"，Engram 的 Memory Table 处理"事实回忆"——两者在 token 表示层面正交叠加

### 为什么 n-gram 哈希而不是稠密检索

| | 稠密检索（如 RAG） | Engram 哈希 |
|---|---|---|
| 查表速度 | O(log N) 或近似最近邻 | **O(1)** 直接寻址 |
| 可微性 | 检索过程不可微 | 哈希不可微，但梯度通过 top-k 加权回传 |
| 存储形式 | 外部文档库 | 参数化的 Memory Table |
| 类比 | 查 Wikipedia | 查一个训练好的查找表 |

---

## 实验结果

### 主要基准

| 基准 | Dense 基线 | + Engram | 提升 |
|------|:----:|:----:|:----:|
| MMLU | — | — | **+3.4** |
| BBH | — | — | **+5.0** |
| HumanEval | — | — | **+3.0** |
| MATH | — | — | **+2.4** |

### 长文本检索

| 方法 | 准确率 |
|------|:----:|
| Dense（无 Engram） | 84.2% |
| **+ Engram** | **97.0%（+12.8）** |

这是 Engram 最突出的优势——长上下文中的精确事实回忆。n-gram 哈希天然擅长这种"见过的东西直接找回来"的场景，而 Transformer FFN 在长文本中容易"记混"。

### 与 MoE 协同

| 配置 | 性能 |
|------|:----:|
| Dense | 基线 |
| MoE only | 提升 |
| Engram only | 提升 |
| **MoE + Engram** | **最大提升** |

两者效果是叠加的——验证了"计算稀疏化"和"知识稀疏化"是互补的轴线。

### 规模扩展

论文将 Engram 扩展到 **27B** 参数，持续观察到收益——说明 n-gram 哈希表可以随模型规模线性扩展，不会像 FFN 那样遭遇"知识编码密度瓶颈"。

---

## 与 mHC 的关系

这篇与 [[mHC]] 出自同一团队（Chongyi Zheng 和 Zizheng Pan 是两篇的共同作者）。

| | mHC | Engram |
|---|---|---|
| 解决的问题 | 残差连接的训练稳定性 | 隐式知识存储效率 |
| 方法论 | 流形约束（数学保证） | 哈希查表（工程确定性） |
| 正交于 | Pre-Norm 残差 | MoE |
| 在生产中使用 | ✅ DeepSeek-V3/R1 | ✅ DeepSeek 生产模型 |

两篇工作共同构成 DeepSeek 架构演进的拼图：
- **mHC** → 让更深的网络稳定训练（架构稳定性）
- **Engram** → 让显式知识更高效存储和检索（知识表示）
- **MoE** → 让更多参数但不增加计算（计算效率）

---

## 我的理解

这篇工作的 insight 非常简洁：**不是所有知识都适合用隐式权重编码——有些更适合用显式键值查找**。

类比：你不需要把整个字典背下来（FFN），你只需要知道怎么查字典（Engram）。字典本身（Memory Table）可以无限大，因为你每次只翻一页（k-稀疏激活）。

**为什么事实类知识受益最大**：事实是高度局部化的——"Paris 是法国首都"跟"Tokyo 是日本首都"几乎完全独立。在 FFN 中，两条知识共享同一组权重矩阵，可能互相干扰。在 Engram 中，它们哈希到不同的表位置，天然隔离。

**为什么长文本检索提升巨大（84→97）**：Transformer 的 KV 缓存随着序列长度线性增长，越后面的 token 对越前面的 token 的注意力越稀疏。但 n-gram 哈希永远 O(1)——不管序列多长，"前面的那个 n-gram 对应什么"是一个固定开销的查表操作。

**被低调处理的限制**：n-gram 哈希的粒度是固定的（n=2 或 n=3）。对跨句、跨段落的远距离依赖，n-gram 无能为力——这只能靠注意力机制。所以 Engram 不是替代注意力的，而是 FFN 的补充——"注意力管长距离关系，Engram 管局部模式回忆"。

**与 MoE 的类比值得玩味**：MoE 的 router 是 soft 的（可学习的 gating），Engram 的 router 是 hard 的（确定性哈希）。soft router 更灵活但有训练不稳定的风险（负载不均衡），hard router 是确定性的但可能碰撞。论文选择 hard router 说明他们认为在知识存储场景下，确定性 > 灵活性——这是一个值得注意的设计哲学选择。

---

## 与相关工作的关系

- **MoE (Shazeer et al. 2017)**：第一条稀疏化轴线（计算），Engram 是第二条（知识）
- **mHC**：同团队，解决残差连接稳定性——与 Engram 在 DeepSeek 架构中协同
- **RAG / 检索增强**：外部检索，Engram 是内部参数化记忆——RAG 查外部文档，Engram 查训练好的查找表
- **Memorizing Transformers (Wu et al. 2022)**：用 kNN 近似最近邻检索，Engram 用 O(1) 哈希——速度 vs 精度的不同取舍
- **Product-Key Memory (Lample et al. 2019)**：最早的"大容量显式记忆"工作，Engram 在 2026 年 GPU 上可规模化

---

## 疑问 / 待验证

- n-gram 哈希碰撞：两个不同的 n-gram 哈希到同一个表位置 → 记忆混淆。论文报告了碰撞率是多少？高碰撞率时性能退化曲线如何？
- n=2 vs n=3 vs n=4 的对比？论文有没有做 n-gram 窗口大小的消融？
- Memory Table 的大小：训练时和推理时的表大小可以不同（动态扩表），但论文是否验证了"训练表大小只要够用，推理时扩表不退化"？
- 同团队的另一篇消除哈希碰撞的工作（arXiv:2601.16531）用 Minimal Perfect Hash 反而没提升——这是否意味着碰撞起了某种"正则化"作用？
- Engram 在强化学习（如 GRPO）场景下的表现如何？DeepSeek-R1 的 RL 训练管线是否使用了 Engram？

---

## 原始摘要

> Large Language Models (LLMs) store vast amounts of world knowledge implicitly within their parameters. However, as models scale, the efficiency of implicit knowledge storage becomes a bottleneck — each piece of factual knowledge competes for representation within a fixed-size weight matrix. In this paper, we introduce Engram, a conditional memory module that adds a new axis of sparsity to LLMs through O(1) n-gram hash-keyed lookup. Unlike Mixture-of-Experts which achieves sparsity in computation (different tokens activate different experts), Engram achieves sparsity in knowledge representation — each token retrieves only the most relevant memories from a large hash table. Engram is fully differentiable and can be integrated into any Transformer architecture as a drop-in module. Experiments at the 27B scale demonstrate consistent improvements on MMLU (+3.4), BBH (+5.0), HumanEval (+3.0), and MATH (+2.4), with particularly strong gains on long-context retrieval tasks (84.2 → 97.0). Engram has been deployed in DeepSeek's production models, validating its effectiveness at industrial scale.

---

## 文献信息

- arXiv: [2601.07372](https://arxiv.org/abs/2601.07372)
- 页数：约 20 页
- 代码：未公开（论文提交时）
