---
title: "GoldFinch: High Performance RWKV/Transformer Hybrid with Linear Pre-Fill and Extreme KV-Cache Compression"
authors:
  - Daniel Goldstein
  - Fares Obeid
  - Eric Alcaide
  - Guangyu Song
  - Eugene Cheah
year: 2024
date: 2026-08-07
journal: "arXiv:2407.12077v1（预印本，EleutherAI / Recursal AI）"
source_pdf: "[[raw/papers/rwkv/2024_Goldstein_GoldFinch_RWKV_Transformer_Hybrid.pdf]]"
tags:
  - RWKV
  - RWKV6
  - 混合架构
  - KV缓存
  - 线性注意力
  - 类型/论文
key_finding: "在 Finch(RWKV-6) 之上叠加 1/6—1/3 层全注意力并共享单层压缩键缓存，即可把 1.5B 级模型的 minipile 损失从 2.3856 降到 2.2762 并取得满分 MQAR；纯 Finch 在 MQAR 上随序列变长而失效，这是「单路 RWKV 表达力有界」的直接实验证据，但代价是长度外推变脆。"
method: "Finch-C2（改进 RWKV-6 时间混合）占前 2/3 层 + GOLD 注意力层占后 1/3 层；TokenCat 键压缩，全局单层键缓存，无值缓存"
baseline: "Finch(RWKV-6) 1.60B、Llama 1.47B，同 tokenizer 同超参同数据（minipile）"
aliases:
  - GoldFinch
  - Goldstein2024-GoldFinch
---

# GoldFinch

> Goldstein et al., 2024, arXiv:2407.12077v1（2024-07-16）· PDF 共 17 页（正文至第 11 页，其后为致谢与参考文献）
>
> 注意：本文基于 **Finch（RWKV-6）**，不是 RWKV-7。其结论迁移到 RWKV-7 属推论。

## 一句话

GoldFinch 用「线性层做前 2/3、少量全注意力做后 1/3、KV 缓存压到单层 d/16」证明了一件对本课题有用的事：**纯线性循环主干在需要精确按键取值（associative recall）时确实打不过注意力，而补足这一缺口只需要极少量注意力层**。

## 论文证据（均来自全文实读）

### 状态容量的界（§1，第 1 页）

- 原文对线性注意力的定位：递归线性注意力用一个固定大小的隐状态充当对过去的记忆，「The limited size of this state constrains the capacity of this memory.」这是全文动机的起点，也是本课题「状态容量是否够用」问题的直接文献表述。

### 架构（§1 三条贡献 + §3，第 2—7 页）

- 前 2/3 层用 Finch-C2：去掉 gate、GroupNorm 换成跨头 LayerNorm、键乘 `1−w` 保持 kv-state 行归一化、把 Finch 的 u（bonus）项换成数据相关的第二 Value。
- 键压缩（§3.2 式 14）：`c_t = x_t W^{KD} ∈ R^{D/16}`，压缩矩阵是**全局的、非逐层的**。
- TokenCat 解压（§3.3 式 15）：`k_t^D = RMSNorm(concat(x_t^0, c_t) W^{KU})`，即把压缩键与最初的 token embedding 拼接后再升维；值不缓存，由原始 token 索引经嵌入表现场生成。
- 缓存规模（表 1，第 2 页）：GoldFinch 每 token 只需 `1 + d_model/16` 项，预填充复杂度 O(1)/token。256k 上下文、32 层、hidden 4096 时为 **0.068GB**，对比 Llama2 的 128GB、Jamba 4GB、YOCO 4GB。摘要称比传统缓存小 756—2550 倍。
- 位置编码：因为键由 Finch-C2 层输出生成，**训练长度内不需要显式位置编码**；但外推到未见长度仍需额外位置编码机制（§1 贡献 5，第 3 页）。

### 主实验（§4.1，表 2、表 3，第 7—8 页）

L24 / D2048 / ctx2048，minipile，同 tokenizer 同超参，4 GPU：

| 架构 | 参数量 | 最终损失 ↓ |
| --- | --- | --- |
| Llama | 1.47B | 2.3905 |
| Finch | 1.60B | 2.3856 |
| GoldFinch（后 1/3 层 GOLD，16:1 压缩） | 1.45B | **2.2762** |
| GoldFinch（后 1/3 层 GOLD，1:1 压缩） | 1.45B | 2.2762 |

- **16:1 压缩与 1:1 不压缩的损失完全相同（2.2762）**，即该压缩几乎零代价。
- 下游评测（表 3）：GoldFinch 1.45B 的 LAMBADA ppl 48.2，对比 Finch 81.9、Llama 71.7；平均准确率 44.2% vs 42.8% / 43.0%。唯一被反超项是 arc_c（GoldFinch 18.3% 低于 Finch 19.6%、Llama 19.3%）。
- 公平性处理：为给 Llama 最有利条件，作者给它加了 RWKV small-init embedding 且不使用 GQA。

### 消融（§4.2 表 4，第 8—9 页，L12/D768/ctx1024）

| 架构 | 损失 ↓ |
| --- | --- |
| Finch-C2 without k*=1−w | 2.7293 |
| Finch | 2.7191 |
| Llama | 2.7125 |
| Finch-C2 without second value | 2.7105 |
| Finch-C2 | 2.7082 |
| GPTAlpha with RoPE | 2.6684 |
| GoldFinch，后 1/2 层 GOLD | 2.6637 |
| GoldFinch，后 1/3 层 GOLD + RoPE | 2.6590 |
| Finch-C2，后 1/3 层 GPTAlpha（不压缩不共享） | 2.6586 |
| GoldFinch，后 1/3 层 GOLD | 2.6582 |
| GoldFinch，**后 1/6 层 GOLD** | **2.6578** |

关键读法（本课题最看重的一段）：
1. 纯线性（Finch-C2 2.7082）→ 混入注意力（2.658 区间）**跨了约 0.05 损失**，而 Finch-C2 相对 Finch 的全部改进只有 0.011。**注意力带来的增益比线性侧的架构微调大一个量级。**
2. **后 1/6 层 GOLD（2.6578）已经不逊于后 1/3（2.6582），且优于后 1/2（2.6637）**。注意力层比例存在饱和甚至反转，少量即够。
3. GoldFinch（2.6582）≈ 无压缩无共享的 Finch-C2+GPTAlpha 混合（2.6586），说明压缩与跨层共享没有损失建模能力。

### 联想召回（§4.3，图 3、图 4，第 9 页）

- 用 Arora et al. (2023) 的 MQAR 设置：**GoldFinch 取得满分 MQAR，超过传统 attention-free 语言模型**；图 3 明确「序列长度增加对应任务难度增加」，图 4 显示 Finch 与 GoldFinch 在序列变长时的差距持续存在。
- 作者归因：GoldFinch 之所以能解 MQAR，是因为它是**使用了注意力的混合架构**。

### 长上下文（§4.4，第 9—10 页）

- 模型仅在 1024 上下文预训练，在 PG19 上测到 65536：
  - **Finch（纯 RWKV-6）在整个 65536 长度上保持较低损失**；
  - **GoldFinch 无位置编码版在约 2 倍训练长度处损失显著上升并高位平台化**；
  - GoldFinch + RoPE 较好但损失仍随长度上升；只有再用插值 RoPE 才能全程低损失。
- 结论：混合注意力换来了召回能力，**代价是长度外推鲁棒性反而不如纯线性主干**。
- 长上下文微调时冻结整个 RWKV 部分、只更新 GOLD 层与输出头，FLOPs 约减少 3 倍；非 RoPE 版在微调长度内部分成功但外推仍失败。

### 作者报告的负面结果（§4.5，第 10—11 页）

- 把已预训练的 1.6B Finch 检查点升级成 GoldFinch 的两种方法「thus far … neither method has performed to our satisfaction」：
  - 方法一（顶部追加 4 层 GOLD，+11% 参数，续训 1 亿 token）：性能与原模型持平，但不清楚新 GOLD 层是否学到有价值的东西；
  - 方法二（冻结嵌入与 RWKV 层，用新 GOLD 注意力替换上 1/3，训 75 亿 token）：minipile 验证损失与基座相当，但 **LAMBADA 分数变差**，作者归因于保持层数不变所需的「brain surgery」抹掉了上 1/3 的 Finch time-mix 参数。

### 规模与可信度边界（§5，第 11 页）

- 「Most of the experiments … were performed over a short period of time on a single node containing 8 RTX 4090 cards」，作者希望未来在更大模型、更多 token 上验证。
- 全部主实验数据集只有 minipile，上下文长度 2048。
- **文本内部不一致**：第 3 页称在 minipile 上训练了 1.5 万亿 token，而 minipile 是公认的小规模数据集，此数字与表 2 的设置不自洽，引用时不得使用该 token 数。

## 与本课题的关系

### 对「单路 RWKV-7 是否够用」提供的证据

- **提供了明确的反面证据（但限定在 RWKV-6 与语言/MQAR）**：纯 Finch 在 MQAR 类「按键精确取值」任务上随长度增加而失效，混入注意力后满分。若本课题的攻击状态检测需要跨窗口精确回指某个具体历史事件（如特定五元组或特定握手），单路 RWKV 的固定状态存在容量瓶颈，这条证据是可引用的。
- **同时提供了「够用」方向的证据**：补足缺口所需注意力极少（1/6 层已饱和），且压缩到 d/16 单层缓存零损失。也就是说，即使要混合，成本远低于半数注意力。
- **提供了不要盲目混合的证据**：§4.4 显示混合后长度外推鲁棒性下降，纯 Finch 反而在 64x 训练长度上稳定。本课题是**固定四窗口、长度不外推**的设定，因此混合带来的外推劣势不显著，但混合带来的 MQAR 收益也需要先验证任务是否真的含联想召回成分。

### 与先导实验结论的关系（本课题推论）

- 本课题先导实验测得「窗口级字段交互 +30.1%、长时历史仅 +6.0%」。GoldFinch 的增益全部来自**跨长距离精确检索**（MQAR、LAMBADA ppl 从 81.9 降到 48.2 都是长程指代类指标）。若本课题的长时历史增益本来就只有 6.0%，则 GoldFinch 式混合能撬动的空间同样有限，**优先级应低于窗口内字段交互建模**。这是推论，需在本课题数据上做「加 1/6 注意力层」的最小消融才能裁决。

### 禁止主张

- 不能称 GoldFinch 是 RWKV-7 混合：它基于 RWKV-6（Finch），RWKV-7 的动态状态演化不在其实验范围内。
- 不能把 0.068GB / 756—2550 倍缓存压缩写成本课题的显存结论：那是 256k 上下文、32 层、hidden 4096 的解析式估算，不是实测。
- 不能把 minipile 上 1.5B 级语言建模的损失差外推为流量或攻击检测的检测率差。
- 不能引用「1.5 万亿 token minipile」这一数字（文本自相矛盾）。
- 不能称检查点升级方案可用：作者明确报告两种方法均未达满意。

## 与相关工作的关系

- 上游：[[RWKV-面向Transformer时代的循环语言模型|RWKV]] → [[2024-Peng-RWKV5-RWKV6-Eagle与Finch|Finch(RWKV-6)]] → 本文 Finch-C2。
- 同类混合思路：[[RWKV-X-线性复杂度混合语言模型|RWKV-X]]（RWKV-7 + Top-k 块稀疏注意力）解决的是同一类「线性主干长程检索不足」问题，但走稀疏注意力而非压缩全注意力，可与本文互为对照。
- 下一代主干：[[2025-Peng-RWKV7-Goose|RWKV-7]]。

## 疑问 / 待验证

- 「1/6 层注意力已饱和」只在 L12/D768/ctx1024 的小规模消融上成立，1.5B 规模未复测该比例，是否随规模变化未知。
- MQAR 满分依赖全注意力；若本课题窗口数只有 4，是否还存在 MQAR 式召回需求，需要先在自有数据上做长历史消融再决定是否引入注意力。
- 表 4 中 GoldFinch 后 1/6 层优于后 1/3 层的差距仅 0.0004，单次运行、无种子重复，不能当作显著差异。

## 原始摘要（节选核心声明）

> "Our cache size savings increase linearly with model layer count, ranging from 756-2550 times smaller than the traditional transformer cache for common sizes"（Abstract，第 1 页）

## 文献信息

- arXiv:2407.12077v1，2024-07-16，cs.CL
- 代码：https://github.com/recursal/GoldFinch-paper ；权重：https://huggingface.co/recursal/GoldFinch-paper （Apache 2.0）
- 相关笔记：[[2025-Peng-RWKV7-Goose]]、[[RWKV-X-线性复杂度混合语言模型]]、[[2025-Li-BlackGoose-Rimer-RWKV7时序建模]]
