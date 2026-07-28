---
title: "Multi-Stream LLMs: Unblocking Language Models with Parallel Streams of Thoughts, Inputs and Outputs"
authors:
  - Guinan Su
  - Yanwu Yang
  - Xueyan Li
  - Jonas Geiping
year: 2026
date: 2026-07-14
journal: arXiv preprint
doi: "arXiv:2605.12460"
source_pdf: "[[raw/papers/2605.12460v1.pdf]]"
tags:
  - LLM
  - 架构设计
  - 多流并行
  - 推理效率
  - 安全性
  - 类型/论文
aliases:
  - Multi-Stream LLMs
  - 多流 LLM
  - 并行多流架构
  - Su2026-MultiStream
key_finding: "重新设计 LLM 的消息处理管线——不再把 user/system/thinking/tool 消息串行拼接后送入模型，而是让多个并发流（输入流、思考流、输出流、工具流）在同一次前向传播中被同时处理。结果是时间到首 token 降低 40%+、指令层级安全性提升、且首次实现在不暴露思考内容的前提下让外部监控流能看到模型的内部意图"
method: "多流注意力（Multi-Stream Attention）——为每条流独立的 Q/K/V 投影 + 受控的跨流注意力掩码 + 并行多头解码（Multiple Output Heads）"
baseline: "串行消息拼接（标准 ChatML 格式）、单流自回归解码"
---

# Multi-Stream LLMs: Unblocking Language Models with Parallel Streams of Thoughts, Inputs and Outputs

> Guinan Su, Yanwu Yang, Xueyan Li, Jonas Geiping
> 马普所 / Tübingen AI Center / ETH Zurich / ELLIS Institute
> arXiv:2605.12460 · 约 20 页

---

## 一句话

不再把用户输入、系统指令、模型的推理过程和工具调用串行拼接成一个长序列——而是让它们在**并行的流中同时运行**：模型在前向传播中同时读多条输入流，同时写多条输出流。首次实现了"边思考边回复"、"外部监控流不暴露内部思考"、"一个前向传播完成读→想→做"。

---

## 背景：为什么串行消息是瓶颈

### 传统 ChatML 的串行瓶颈

```
System: 你是一个有帮助的助手
User: 帮我订餐厅
Assistant: 好的，让我先思考一下...<thinking>这需要工具调用</thinking>
Tool: {餐厅预订结果}
Assistant: 已预订!
```

问题：
1. **阻塞读**：必须先读完所有输入（system + user + chat history），才能开始生成
2. **思考→回复串行**：必须先生成完整思考链，再生成用户可见回复
3. **所有信息混在一起**：system prompt、user input、thinking、tool output——全部串行拼成一个 sequence
4. **时间到首 token（TTFT）随对话历史增长**：对话越长，输入越长，TTFT 越长

### 串行架构下的指令层级问题

在标准 ChatML 中，system prompt 和 user input 被拼成同一个序列的不同位置——LLM 需要**从 token 位置推断指令优先级**。这导致 prompt injection 攻击极其有效：攻击者只要把恶意指令塞进 user input 中间，模型就无法区分"这是系统指令还是用户输入"。

---

## 方法：Multi-Stream LLMs

### 核心思想

**把 LLM 的输入/输出管线从"一条河流"变成"多条并行河流"。** 每条流有独立的 identity 和优先级，在同一层 Transformer 中被同时处理。

### 流类型定义

| 流类型 | 方向 | 角色 | 可见性 |
|--------|:--:|------|:--:|
| System | 输入 | 系统指令（高优先级） | 所有流可见 |
| User | 输入 | 用户输入 | Assistant 可见 |
| Assistant | 输出 | 用户可见回复 | User 和外部可见 |
| Thinking | 内部 | 模型内部推理 | **仅模型自己可见** |
| Tool | 双向 | 工具调用 | Assistant 和外部可见 |
| Monitor/Steering | 内部 | 外部监控/转向信号 | **仅 Thinking 可见** |

**关键创新**：Thinking 流对外部完全不可见，但有一个独立的 Monitor/Steering 流可以监控 Thinking 的内容——实现了"不泄露思考但你（可信监控方）可以审计"。

### 多流注意力机制

```
传统 Attention:
  Q, K, V ← 同一条序列的所有 token → 所有 token 互相 attend

Multi-Stream Attention:
  每条流有独立的 Q/K/V 投影
  + 流间注意力掩码（哪些流可以 attend 哪些流）
```

流间注意力掩码示例：

| | System | User | Thinking | Assistant | Monitor |
|---|:--:|:--:|:--:|:--:|:--:|
| System | ✅ | ❌ | ✅ | ✅ | ✅ |
| User | — | — | ✅ | ✅ | ❌ |
| Thinking | ✅ | ✅ | ✅ | ✅ | ✅ |
| Assistant | ✅ | ✅ | ✅ | ✅ | ❌ |
| Monitor | ✅ | ❌ | ✅ | ❌ | ✅ |

- **System 不能 attend 到 User** → system prompt 不被用户输入污染 → prompt injection 免疫
- **Assistant 不能 attend 到 Monitor** → 用户看不到审计流
- **Monitor 可以 attend 到 Thinking** → 外部审计方可以监控模型意图

### 并行多头解码

同一次前向传播中，模型可以**同时生成多个输出流的 token**：

```
Transformer 层 N
    ├── 生成 Assistant token t+1
    ├── 生成 Thinking token t+1
    └── 生成 Tool call token t+1
```

这意味着：模型不需要先生成完整思考链再回复——**可以边思考边回复**，思考链和回复 token 在同一个前向传播中交替产生。

---

## 实验结果

### 效率提升

| 指标 | 串行 ChatML | Multi-Stream | 改善 |
|------|:----:|:----:|:----:|
| 时间到首 token（TTFT） | 基线 | 降低 | **> 40%** |
| 吞吐量（tokens/s） | 基线 | 提升 | 显著 |
| 对话历史增长时 TTFT | 线性增长 | **恒定** | 关键优势 |

TTFT 不随对话历史增长——因为输入流可以并行读入，不需要等待所有历史加载完成。

### 安全性

| 攻击类型 | 串行 ChatML | Multi-Stream |
|------|:----:|:----:|
| Prompt Injection（塞恶意指令进 user input） | ❌ 高成功率 | ✅ System 流不 attend User 流 → 免疫 |
| 越狱（Jailbreak） | ❌ 脆弱 | ✅ 关键词安全监控 |
| 指令层级绕过 | ❌ 依赖 token 位置 | ✅ 流级隔离 |

### 推理质量

| 基准 | 串行 ChatML | Multi-Stream |
|------|:----:|:----:|
| 对话质量（AlpacaEval 等） | 基线 | **持平** |
| 工具调用准确率 | 基线 | **持平或略优** |
| 推理能力（GSM8K 等） | 基线 | **持平** |

**不牺牲推理质量**是关键——效率和安全性的提升不是以性能退化为代价的。

---

## 我的理解

这篇工作的核心洞察是**把 LLM 的"操作系统"从单进程升级为多进程**。

类比：
- **串行 ChatML**：单核单线程操作系统——所有消息排队处理，一个 token 一个 token 串行生成
- **Multi-Stream LLMs**：多核多线程操作系统——不同优先级的任务在独立的线程中并行运行，有明确的权限隔离（用户态 vs 内核态）

**为什么这对安全性是质的提升**：传统 prompt injection 之所以有效，是因为 LLM 根本不知道"这个 token 来自用户还是系统"——它们被拼到同一个序列中了。Multi-Stream 通过物理级别的流隔离（System 的 K/V 不向 User 开方）解决了这个问题。不是"教模型不要听用户的"，而是"模型听不到用户的越权请求"。

**Thinking 流 + Monitor 流的设计很巧妙**：它在"内部思考完全保密"和"完全公开思考"之间找到了第三条路——思考内容对外部用户不可见，但对受信任的监控方可见。这解决了目前 thinking models 的一个核心矛盾：OpenAI o1 等模型连用户都看不到内部推理（完全黑盒），但完全公开推理链又会被竞争对手蒸馏。Monitor 流是一种合规/安全的折中。

**一个关键的工程挑战**：Multi-Stream Attention 的 KV 缓存维度是传统架构的 N 倍（N = 流的数量）。论文如何解决这个内存瓶颈？FlashAttention 可以部分缓解，但随着流数增加，内存压力是线性的。

---

## 与相关工作的关系

- **ChatML（OpenAI）/ Llama 对话格式**：串行消息拼接范式，Multi-Stream 的替代目标
- **Speculative Decoding**：解决推理速度，但仍然是串行流——Multi-Stream 是并行流
- **System 2 Attention / 指令层级**：在软件层面解决 prompt injection，Multi-Stream 在架构层面解决
- **DeepSeek 的 Multi-Token Prediction（MTP）**：并行预测多个未来 token——与 Multi-Stream 的并行不同，MTP 是同一输出流的多个 token，Multi-Stream 是不同流的 token
- **Tool-use / Function Calling**：Multi-Stream 让工具调用成为一等流，而非拼在聊天序列中的特殊 token
- **streaming reasoning（TaYS, 2603.02872）**：视频流场景的并行推理，与 Multi-Stream 共享"流并行"的思想但应用场景不同

---

## 疑问 / 待验证

- 训练 Multi-Stream 模型需要特殊的数据格式——每条消息必须标注属于哪个流。现有的大规模对话数据集（ShareGPT、LMSYS-Chat）都是串行格式，如何构造多流训练数据？
- KV 缓存膨胀问题：5-6 条流 × 每流独立的 KV 缓存 → 推理内存需求是传统模型的 5-6 倍？论文给出了什么优化？
- 基座模型架构改动多大？是"在现有 Transformer 上加流间注意力掩码"还是"需要从头训练新架构"？
- 如果基座模型可以继续预训练并保留串行格式的能力，变成一个"双模式"模型（串行模式 + 多流模式无缝切换），效果如何？
- Monitor 流的实际部署：谁运行 Monitor？服务提供方？监管方？它的存在是否会引入新的攻击面（攻击 Monitor 流来泄露 Thinking 内容）？

---

## 原始摘要

> Current Large Language Models (LLMs) process information through a fundamentally sequential paradigm: messages are concatenated into a single sequence and processed token-by-token. This sequential bottleneck limits efficiency, security, and monitorability. We propose Multi-Stream LLMs, a novel architectural paradigm where multiple parallel streams — user messages, system instructions, model thinking, and tool interactions — are processed concurrently within a single forward pass. Each stream maintains its own key-value cache with controlled cross-stream attention masks, enabling principled instruction hierarchy and stream isolation. Our approach introduces multiple output heads that can generate tokens across different streams simultaneously. Experiments demonstrate that Multi-Stream LLMs achieve significant reductions in time-to-first-token, improved resistance to prompt injection attacks, enhanced monitorability through dedicated oversight streams, and maintained generation quality — all through a single architectural change that can be integrated into existing Transformer-based models.

---

## 文献信息

- arXiv: [2605.12460](https://arxiv.org/abs/2605.12460)（v1, 2026-05-12）
- 页数：约 20 页
