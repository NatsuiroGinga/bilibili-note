---
title: "RADLADS：大规模快速注意力蒸馏到线性注意力解码器"
authors:
  - Daniel Goldstein
  - Eric Alcaide
  - Janna Lu
  - Eugene Cheah
year: 2025
date: 2026-08-07
journal: "arXiv 预印本（arXiv:2505.03005v2，2025-05-07，Recursal AI / EleutherAI）"
source_pdf: "[[raw/papers/rwkv/2025_Goldstein_RADLADS_Rapid_Attention_Distillation_to_Linear_Attention_Decoders.pdf]]"
tags:
  - RWKV
  - RWKV7
  - 线性注意力
  - 知识蒸馏
  - 架构转换
  - 类型/论文
key_finding: "用 350—700M token（不到教师预训练量的 0.005%）就能把 Qwen2.5 的 softmax 注意力换成纯 RWKV 循环状态，7 个短上下文基准接近甚至超过教师；但 MMLU 是唯一在全部 5 个转换模型上都稳定掉分的基准（−3.5 到 −5.9 个百分点），且论文没有报告任何长上下文或检索基准，因此它给的是成本保证，不是长程能力保证。"
---

# RADLADS：注意力蒸馏到线性注意力

## 一句话

RADLADS 证明"用 RWKV 换掉 Transformer 骨干"在工程上便宜且几乎无损，但它测的全是短上下文基准，唯一稳定的损失恰好落在最依赖检索的 MMLU 上 —— 对本课题而言，它是可行性证据，不是长时状态容量的证据。

## 论文证据

### 协议（第 4—5 页 §4）

三步（外加一步权重搬运），全部用 DCLM 数据集（第 8 页 §7）：

- **Setup**：教师的 `W_q, W_k, W_v, W_o` 直接搬进学生对应的 receptance/key/value/output；无对应者用标准预训练初始化（第 4 页 §4.1）。
- **Step 1 注意力隐状态对齐**：冻结教师，在每层教师注意力旁并联一个可训练的 RWKV 替换层，用 L2 / MSE 拟合序列混合器隐状态输出。序列长 512，100M token，学习率 1e-3 余弦退火到 1e-5（第 5 页 §4.2、第 8 页表 7）。
- **Step 2 logit 蒸馏**：整模型对齐教师 logits，KL 损失，序列长 512，250M—700M token，恒定 1e-5。论文明确"超过约 500M token 不再改善英文基准"（第 5 页 §4.3）。
- **Step 3 上下文扩展**：无教师，普通交叉熵，**序列长 16384**，100M token（第 5 页 §4.4、第 8 页表 7）。显存紧张时可用 3a：只解冻 decay 与 tokenshift，学习率提到 1e-4。
- 成本：7B 在 8×Mi300X 上约 0.75+5.5+1 小时；72B 约 7.5+54+6 小时（第 8 页表 8）。摘要称 72B 转换成本低于 2000 美元。

### 架构（附录 B，第 14—15 页）

- **RAD-RWKV6（"RADFinch"）**：基于 RWKV6-C2，改用 GLA 内核（去 bonus）、sigmoid 门，靠 RWKV6-C2 的状态平衡去掉状态归一化。递归为 `wkvₜ = diag(wₜ)·wkv_{t−1} + kₜᵀvₜ`（式 12）。
- **RAD-RWKV7（"RADGoose"）**：基于 RWKV-7，**去掉 tokenshift**、加 RoPE、去 bonus。递归为 `wkvₜ = wkv_{t−1}(diag(wₜ) − κ̂ₜᵀ(aₜ⊙κ̂ₜ)) + vₜᵀk̃ₜ`（式 31），与 RWKV-7 正文式（15）—（17）同形。
- 第 3—4 页 §3 记录了关键的架构—拟合关系：用 GLA 内核去掉 off-by-one decay 和 bonus 后，"模型在 Step 1 能明显更贴近原 softmax 注意力隐状态"；"RWKV-7 拟合得更近更快，用更少算力就达到更低蒸馏损失"。

### 成绩（第 6 页表 2/表 3，第 7 页 §5）

相对分定义为 `(s−r)/(t−r)`，s 学生、t 教师、r 随机猜测。RADLADS 的 QRWKV7-7B-Instruct 相对分 lambada 0.982、MMLU 0.924、其他均值 1.013，在第 1 页表 1 中全面高于 SUPRA（100B token）、MOHAWK（3-5B）、Mamba in the Llama（20B）、LOLCats（40M）、ARWKV（60M/830M）、Llamba（8-12B）。

第 6 页表 3 绝对分数逐模型对教师的差值（本笔记按原表复算）：

| 学生 | MMLU 学生/教师 | 差值 | 其余 6 项最大退步 |
|---|---|---|---|
| QRWKV6-7B-Instruct | 0.657 / 0.717 | −0.060 | hella −0.015 |
| QRWKV7-7B-Instruct-RoPE | 0.682 / 0.717 | −0.035 | lambada −0.012 |
| QRWKV6-32B-Instruct | 0.766 / 0.818 | −0.052 | hella −0.022 |
| QRWKV6-QwQ-32B | 0.743 / 0.799 | −0.056 | hella −0.011 |
| QRWKV6-72B-Instruct | 0.775 / 0.834 | −0.059 | hella −0.017 |

arc_c、arc_e、piqa、winogrande 上学生多次**超过**教师（如 QRWKV6-32B winogrande 0.782 vs 0.729）。RWKV-7 版本的 MMLU 差值（−0.035）明显小于 RWKV-6 版本（−0.060）。

### 消融与负结果（第 8—9 页 §6、§8）

- 表 6（RAD-RWKV6、7B、100M+500M token）：完整 MMLU 0.6572；`use rope` 0.6610（几乎无差）；`no tokenshift` 0.6584（几乎无差，但 winogrande 由 0.7111 掉到 0.6875）；`no gate` 0.6417（明显掉分）；`use groupnorm` 0.6340（最差）。**门控是 RAD-RWKV6 里唯一确认重要的组件**。
- 第 3—4 页 §3：tokenshift 在 RAD-RWKV6 有用，在 RAD-RWKV7 "essentially no benefit"；门控在 RAD-RWKV6 必须全秩，在 RAD-RWKV7 降秩也够用。
- §8 负结果（第 8—9 页）：先做基于注意力分数的 "step 0" 不带来收益，训练久了反而损失更高；**跳过 Step 1 直接蒸馏 logits 会显著变差，损失平台期更高，加训也补不回来**；QKVO 随机初始化比搬教师权重差；Step 2 冻结 MLP 和 embedding 显著变差；增大 batch 无益（优化步数才是关键）；LoRA 降秩普遍有害，只在 embedding 上无害。
- §9 局限（第 9 页）：每个新架构都需要针对 RADLADS 反复调试；**RAD-RWKV7 在 32B 以上出现训练稳定性下降**，作者仍在修；转换对推理型模型（QwQ）的影响未知。

## 允许主张

- 把预训练 softmax 注意力换成纯 RWKV 循环状态，在 7B—72B 规模上是可行的，且成本远低于重新预训练；Step 1 隐状态对齐是不可省的关键步骤（第 9 页 §8）。
- 状态更新的表达力直接决定拟合 softmax 注意力的难度：GLA 内核优于原 RWKV-6，RWKV-7 又优于两者（第 3—4 页 §3，第 6 页表 3 的 MMLU 差值印证）。
- 权重可迁移性说明 QKVO 与 RWKV 的 r/k/v/o 存在有意义的对应关系，不是纯随机重初始化。
- 门控是 RWKV 时间混合中不可删的组件；tokenshift 在 RWKV-7 状态核下可以删掉（第 8 页表 6、第 3 页 §3）。

## 禁止主张

- **不能说 RADLADS 证明了线性注意力在长序列上无损。** 7 个基准（lambada、MMLU、arc_c、arc_e、hellaswag、piqa、winogrande）全是短上下文任务；Step 3 虽训练到 16384 上下文，但论文**没有报告任何长上下文、检索或 needle 类评测**。
- 不能把"接近教师"读成"等于教师"。MMLU 在 5 个转换模型上无一例外掉 3.5—5.9 个百分点。
- 不能把语言模型基准结论外推为流量或攻击检测效果，论文全程只做英文 NLP 评测。
- 不能把 8×Mi300X 的小时数当作本课题 RTX 5090 的时间预算依据。
- 不能忽略作者自报的 RAD-RWKV7 在 32B+ 训练不稳（第 9 页 §9），这直接影响"把 RWKV-7 当大模型骨干"的可行性判断。

## 本课题映射

### 可迁移机制

- **两阶段对齐范式**：先逐层对齐序列混合器隐状态，再对齐全模型输出。若本课题需要从一个已训好的 Transformer 流量模型迁移到 RWKV-7 骨干，这套协议可以直接复用，且负结果告诉我们 Step 1 不能跳。
- **同参数量替换式消融**：表 6 通过增删单个机制（rope / tokenshift / gate / groupnorm）在同一 7B 骨干上比较，是本课题机制消融的可参照写法。
- **相对分指标** `(s−r)/(t−r)`：在教师能力不同的情况下做跨模型比较时有用，可迁移到本课题跨基座对比。

### 本课题推论（论文未声明）

- 5 个模型中 MMLU 是**唯一**稳定退步项，而 arc/piqa/winogrande 常常反超教师。合理推论是：压缩状态的代价集中在**需要精确回忆大量离散事实**的任务上，而非需要局部推理的任务。这与论文引用的 Zoology（第 1 页引 Arora et al. 2023，关于高效语言模型的 recall）方向一致，但**论文本身从未做这个归因**，属推论，未验证。
- 若上述推论成立，则对本课题是**有利**信号：攻击状态检测更接近"局部模式 + 状态跟踪"而非"海量事实回忆"，压缩状态的短板未必落在关键路径上。此为推论。
- tokenshift 在 RWKV-7 中可删而不掉分（第 3 页 §3、第 8 页表 6），说明当状态更新足够表达时，额外的**局部时间混合算子是冗余的**。注意：tokenshift 是跨位置的短卷积，不是跨字段混合，因此这条**不能**用来推断本课题的字段交互模块可删。

### 与本课题先导结论的关系

- 本课题先导实验得到"窗口级字段交互 +30.1%、长时历史仅 +6.0%"。RADLADS **既不支持也不否定**这一结论：它没有任何字段维度的实验，也没有长上下文评测。把它写进论文时只能作为"线性注意力骨干可替代 Transformer"的工程可行性引用。
- RADLADS 的证据结构反而提醒：**声称长时收益必须配长上下文评测**。RADLADS 做了 16384 上下文扩展却不报长上下文分数，是本课题在写作时应当避免的证据缺口。

### 待验证假设

- **H1**：若本课题存在已训练的 Transformer 流量基线，能否用 RADLADS 三步协议在极小 token 预算内迁移到 RWKV-7 并保持指标？需要以"跳过 Step 1"作为对照消融复现论文的负结果。
- **H2**：压缩状态的损失是否在流量任务上同样集中于"精确回忆"类子任务（如稀有 IP/端口模式匹配）？需要按子任务拆分误差才能判定。

## 相关

- [[2025-Peng-RWKV7-Goose]] —— RAD-RWKV7 是其去 tokenshift、加 RoPE、去 bonus 的变体（附录 B.2 式 31）。
- [[2024-Peng-RWKV5-RWKV6-Eagle与Finch]] —— RAD-RWKV6 基于 RWKV6-C2。
- [[RWKV-X-线性复杂度混合语言模型]] —— 走的是混合稀疏注意力路线，与 RADLADS 的"纯 RNN"路线构成对照。
