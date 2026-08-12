---
title: "BlackGoose Rimer: Harnessing RWKV-7 as a Simple yet Superior Replacement for Transformers in Large-Scale Time Series Modeling"
authors:
  - Li weile
  - Liu Xiao
year: 2025
date: 2026-08-07
journal: "arXiv:2503.06121v1（预印本，未见同行评审；正文脚注自称 ongoing project）"
source_pdf: "[[raw/papers/rwkv/2025_Yang_BlackGoose_Rimer_RWKV7_Time_Series.pdf]]"
tags:
  - RWKV
  - RWKV7
  - 时间序列
  - 线性循环模型
  - 类型/论文
key_finding: "把 RWKV-7 的 time mix 与 channel mix 替换进 Timer 主干后，1.6M 参数的 Rimer 在 4 个时序数据集的 RMSE/MAE/R² 上优于 37.8M 的 Timer，训练加速 4.5x；但全文只有 4 页、零消融、零重复种子、单一基线，且作者在未来工作中明确承认长上下文能力尚未解决。"
method: "RWKV-7 time mix + channel mix 替换 Timer 的 transformer 主干；另提出 DEQ 形式的隐式 RWKV-7 层（式 2—4），Triton 算子实现"
baseline: "唯一基线 Timer-37.8M（Liu et al., 2024）"
aliases:
  - Rimer
  - BlackGoose Rimer
---

# BlackGoose Rimer

> Li weile, Liu Xiao, 2025, arXiv:2503.06121v1（2025-03-08）· PDF 共 4 页（含参考文献）
>
> 原件文件名遗留问题：`raw/` 中该 PDF 落盘为 `2025_Yang_...`，但第一作者是 **Li weile**。`raw/` 为不可变原件层，不做重命名；引用作者时以本笔记与 PDF 首页为准。

## 一句话

这是目前唯一一篇把 **RWKV-7 直接当作时序主干替换 Transformer** 的公开全文，参数量证据（1.6M 打 37.8M）值得引用，但它的实验强度远低于可作为效果依据的门槛，只能作为「RWKV-7 在时序任务上可行」的存在性证据，不能作为性能承诺。

## 论文证据（均来自全文实读）

### 架构与方法（§3，PDF 第 2—3 页）

- §3.1 只给出一条核心状态更新式（式 1）：`State_t = State_{t-1}[diag(w_t) − κ̂_t^T(a_t·κ̂_t)] + v_t^T·k̃_t·a_t`，并声明 RWKV-7 的核心是「动态演化的 WKV 状态 + time mix + channel mix」两大组件。
- §3.2 提出 **Implicit RWKV-7 layers**：借 DEQ（Bai et al., 2019）把状态更新改写成不动点方程 `z* = f(z*, x)`，展开为式 (4) `h_t = φ(W h_t + V State_{t-1}(diag(w_t) − κ_t^T(a_t·κ̂_t)) + U v_t^T·κ_t·a_t)`，激活 φ 取 ReLU，声称「latent-space iterations 可大幅提升表达力与效率」。
- **该 DEQ 层在 §4 评测中没有任何单独验证**：全文没有「RWKV-7 原式 vs DEQ 隐式层」的对照，因此无法判断报告的收益来自 RWKV-7 本身还是 DEQ 改写。

### 实验设置（§4，PDF 第 3 页）

- 数据集 4 个：ECL（表 1 中写作 ELC）、ETTH、Traffic、Weather；指标 RMSE、MAE、MAPE、R²。
- 硬件：Linux ROCm + AMD GPU（训练 Radeon Pro W7900，推理 RX6750XT），Triton 算子；声称训练时间 4.5x 加速。
- 数据集来源写为「publicly available in our Rimer repository」，**未说明与标准 TSLib 划分是否一致**；未给出回看窗口、预测步长、训练/验证/测试划分、随机种子数与重复次数。

### 实际数字（§4 表 1—表 4，逐表核对）

| 数据集 | 模型 | RMSE | MAE | MAPE | R² |
| --- | --- | --- | --- | --- | --- |
| ECL（表 1） | Timer-37.8M | 0.6488 | 0.2127 | **0.61%** | 0.9755 |
| ECL（表 1） | Rimer-1.6M | 0.2409 | 0.0814 | 0.81% | 0.9991 |
| ETTH（表 2） | Timer-37.8M | 0.5770 | 0.4050 | 6.5% | 0.9968 |
| ETTH（表 2） | Rimer-1.6M | 0.0133 | 0.0112 | 0.16% | 0.9998 |
| Traffic（表 3） | Timer-37.8M | 0.0055 | 0.0015 | 19.94% | 0.8955 |
| Traffic（表 3） | Rimer-1.6M | 0.0025 | 0.0006 | 4.01% | 0.9838 |
| Weather（表 4） | Timer-37.8M | 6.1765 | 3.6839 | 0.88% | 0.8411 |
| Weather（表 4） | Rimer-1.6M | 5.4311 | 1.3621 | 0.34% | 0.8794 |

- 摘要中的「1.13x 到 43.3x 性能提升」**是 RMSE 比值**，不是通行意义上的相对误差下降：Weather 6.1765/5.4311 = 1.137x（下界），ETTH 0.5770/0.0133 = 43.4x（上界）。跨数据集的比值差 38 倍，说明该区间由数据集尺度而非方法稳健性决定。
- **作者自己的表里存在一处反例**：ECL 上 Rimer 的 MAPE 0.81% 劣于 Timer 的 0.61%，而正文只说「lower MAPE in ETTH and Traffic」，回避了 ECL 这一项。这是全文唯一一处可核对的失败点。
- 4 个数据集里 Weather 的 R² 只有 0.8794、Traffic 0.9838，说明「一致超越」的说法在难数据集上余量很小。

### 作者自陈的局限（§5.1 未来工作，PDF 第 4 页）

- 「First, we aim to enhance its capability to handle long contexts by optimizing the state update mechanism to effectively capture extended temporal dependencies」——**作者明确承认当前 Rimer 的长上下文能力未解决**，计划靠记忆增强架构改进。
- 第二条计划把潜空间表示与状态链结合；第三条计划做 RWKV-7 与 Transformer/CNN 的混合。三条都指向「单路 RWKV-7 在长程依赖上不够」的判断。
- 第 1 页脚注 1：「This is an ongoing project」。

## 与本课题的关系

### 可直接引用

- RWKV-7 已被用作大规模时序建模的主干替换，存在公开全文与开源代码，可作为「RWKV-7 用于非语言序列任务」的先例引用。
- 参数效率对比（1.6M vs 37.8M，23x 差距，训练 4.5x 加速）可作为「线性循环主干在时序任务上参数效率高于生成式 Transformer」的**一个数据点**。

### 与先导实验结论的呼应（本课题推论，非论文结论）

- 本课题先导实验测得「窗口级字段交互 +30.1%、长时历史仅 +6.0%」。Rimer 的 §5.1 把长上下文列为**尚未解决的未来工作**，与「长时历史增益有限」方向一致，可作为旁证；但论文没有做长度消融，**不能反过来用它证明长历史无用**。
- 论文中的「channel mix」是 RWKV 块内的隐藏通道混合，**不是输入侧的多字段/多变量交互**。它对本课题「字段交互」这一维度没有提供任何证据。

### 禁止主张

- 不能把 1.13x—43.3x 写成「RWKV-7 相对 Transformer 的性能提升」，那是 RMSE 比值且含 ECL 的 MAPE 反例。
- 不能把 4.5x 训练加速外推到其他硬件：该数字来自 AMD ROCm + Radeon Pro W7900，且与 23x 参数差绑定。
- 不能称其结论经过统计检验：全文无种子、无重复、无置信区间、无显著性。
- 不能称其对比了强时序基线：唯一基线是 Timer，没有 PatchTST、DLinear、iTransformer，也没有对比同门的 [[2024-Hou-RWKV-TS-时间序列|RWKV-TS]]。
- 不能把 DEQ 隐式层的收益单独归因：论文未做该消融。

## 疑问 / 待验证

- 式 (1) 与 [[2025-Peng-RWKV7-Goose|RWKV-7 原论文]] 的式（15）—（17）在 `a_t` 的作用位置上写法不一致（原文为 `S_{t-1}[diag(w_t) − κ̂_t^T(a_t⊙κ̂_t)] + v_t^T k̃_t`），式 (4) 又混用 `κ_t` 与 `κ̂_t`。是转写笔误还是实现差异，需查其开源仓库确认，**当前不得按论文式子复现**。
- Timer 是从零训练还是加载预训练权重后微调，全文未说明；若 Timer 未按其预训练流程使用，则 37.8M 一侧被削弱，比较不公平。
- Traffic 数据集上 Timer 的 MAPE 19.94% 异常高，需核对是否为数据尺度/零值导致的指标失真。

## 原始摘要（节选核心声明）

> "we achieve a substantial performance improvement of approximately 1.13x to 43.3x and a 4.5x reduction in training time with 1/23 parameters"（Abstract，PDF 第 1 页）

## 文献信息

- arXiv:2503.06121v1，2025-03-08，cs.LG
- 代码：https://github.com/Alic-Li/BlackGoose_Rimer
- 相关笔记：[[2025-Peng-RWKV7-Goose]]、[[2024-Hou-RWKV-TS-时间序列]]、[[2024-Goldstein-GoldFinch-RWKV混合与KV缓存压缩]]
