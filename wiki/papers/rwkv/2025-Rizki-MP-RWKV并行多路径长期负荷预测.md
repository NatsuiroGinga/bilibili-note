---
title: "面向长期电力负荷预测的并行处理架构 MP-RWKV"
authors:
  - Adil Rizki
  - Achraf Touil
  - Abdelwahed Echchatbi
  - Mustapha Ahlaqqach
year: 2025
date: 2026-08-08
journal: "Engineering Proceedings（MDPI）97(1):26, 2025，SMILE 2025 会议论文，DOI 10.3390/engproc2025097026"
source_pdf: "[[raw/papers/rwkv/engproc-97-00026.pdf]]"
tags:
  - RWKV
  - 跨变量注意力
  - 电力负荷预测
  - 会议论文
  - 类型/论文
key_finding: "在 RWKV-TS 上加双路径（自适应时间混合算子 ATMO + 跨变量注意力 CVA），48 小时输入下相对 RWKV-TS 的 MSE 相对下降在 24/48/72 h 处分别为 5.6%/3.3%/2.8%——增益随预测步长增大而衰减；四页会议论文，消融只在正文声称存在，未给出可核验的消融表。"
---

# A Parallel Processing Architecture for Long-Term Power Load Forecasting（MP-RWKV）

> 文件名对应关系：`raw/` 原件名 `engproc-97-00026.pdf` 为 MDPI 出版社文件名，正式题名为 **A Parallel Processing Architecture for Long-Term Power Load Forecasting**（Eng. Proc. 2025, 97, 26）。模型简称 **MP-RWKV（Multi-Path Recurrent Weighted Key–Value）**。第一作者与 RWKV-CVM（Electricity 2026）同为 Adil Rizki，数据集也同为 Tetouan，属同一线索的早期会议版本。

## 一句话

同一作者在 RWKV-CVM 之前的尝试：不是轻量门控，而是**双路径并行**（时间路径 + 跨变量注意力路径）；结论方向一致（跨变量有增益），但论文体量小、证据强度弱于其期刊后继。

## 论文证据

### 机制（正文第 6—8 页）

- 两条并行路径：
  - **ATMO（Adaptive Time-Mixing Operator）**：自适应时间混合，替代 RWKV-TS 的单路径时间混合；
  - **CVA（Cross-Variable Attention）**：跨变量注意力，显式建模变量间关系；
  - **自适应路径融合**（第 8 页）："Unlike the single-path processing in RWKV-TS, our model dynamically balances the contributions of **temporal and cross-variable information** based on the forecasting context."
  - 另有 context state 机制与 position-aware attention（摘要）。
- 损失：`L(θ) = L_MSE(θ) + λ·L_temporal(θ)`，其中 `L_MSE(θ) = (1/n)Σ‖y_i − ŷ_i‖²`，`L_temporal` 为时间一致性项（λ 取值未给出，待验证）。
- 复杂度（Table 1）：Transformer O(L²D) 时间 / O(L²+LD) 空间 / 可并行；RNN、LSTM 线性时间但不可并行；**MP-RWKV-TS 线性时间 + 部分可并行**。

### 数据

- Tetouan（摩洛哥）三区（Quads、Smir、Boussafou）配电网数据，2017 全年，**10 分钟粒度，52,416 条**；365 天，每天 144 点，总时长 8736 小时。与 RWKV-CVM 同一数据集。

### 结果（Table 2，第 9 页，48 小时输入）

| 预测步长 | MP-RWKV-TS MSE | RWKV-TS MSE | Informer MSE | Transformer MSE |
|---|---|---|---|---|
| 24 h | **0.0552** | 0.0585 | 0.0597 | 0.1153 |
| 48 h | **0.0798** | 0.0825 | 0.0910 | 0.1855 |
| 72 h | **0.0812** | 0.0835 | 0.0964 | 0.1866 |

- 换算成相对 RWKV-TS 的**误差相对下降**：24 h **5.6%**、48 h **3.3%**、72 h **2.8%**。**增益随步长单调衰减**——与 RWKV-CVM（增益集中在长步长）方向相反，同一作者、同一数据集上的两篇结论互相矛盾，需注意引用时不要混用。
- Autoformer 在 48 h 上出现 MSE 1.2121 的异常值，说明基线调参可能不充分。
- 摘要声称在 24 h–432 h 全范围取得最低 MAE，但正文提取到的 Table 2 只覆盖到 120 h 的短期表（"short-term power load forecasting (48 h input)"），**24–432 h 全范围表未在提取文本中出现，标为待验证**。
- 显著性：正文写"statistical significance of performance differences is assessed through **paired t-tests with p < 0.05**"，但未见具体 p 值。

### 消融

- 正文第 9 页声称："comprehensive **ablation studies** were performed to analyze the individual contributions of key architectural components, including the Adaptive Time-Mixing Operator, Cross-Variable Attention mechanism, and multi-path integration strategy."
- **但提取文本中未出现对应的消融结果表**。四页会议论文体量下，**ATMO / CVA / 多路径三者的单项贡献数字标为未提供或待验证**。这是本篇最大的证据缺口。

### 其他缺失

- 无回看窗口长度消融（输入固定 48 h）。
- 无多种子重复报告。
- 未见代码/权重可得性。

## 对本课题的意义

- **(a) 输入形态**：10 分钟粒度数值多变量，与本课题窗口级流统计形态接近。
- **(b) 有效历史**：输入固定 48 小时，无长度消融，不可用。
- **(c) 跨变量交互**：CVA 是核心之一，但**没有可核验的单项消融数字**，证据强度远低于 RWKV-CVM（Table 4）与光伏 2D TCN（Table 5）。
- **(d) 预训练**：无。
- **(e) 捷径/协议**：会议论文，基线调参存疑（Autoformer 异常值）。
- **(f) 可得性**：未见。

## 允许主张

- 可引用 MP-RWKV 作为"在 RWKV 骨干上并行加跨变量路径"的架构先例。
- 可引用 Table 2 的 24/48/72 h 数字与由此换算的 5.6%/3.3%/2.8% 相对下降。
- 可引用其复杂度表（线性时间 + 部分可并行）的定位。

## 禁止主张

- 不能引用其消融结论：正文声称做了但未给出可核验的表。
- 不能引用摘要中"24 h–432 h 全范围最低 MAE"：对应表未核出。
- 不能把它与同作者 RWKV-CVM 的结论合并叙述：两篇在"增益随步长的走向"上相反。

## 优先级判断

本篇是**低权重参考**：会议 proceedings、四页、无可核验消融、无代码。若要引用同一作者线索的跨变量结论，优先引用 [[2026-Rizki-RWKV-CVM门控跨变量混合]]（期刊版、三种子、控制变量消融、明确局限）。
