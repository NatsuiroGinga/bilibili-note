---
title: "RWKV-TS+：面向多种时序任务的自适应长程提示"
authors:
  - Huaxin Pang
  - Xiaoxia Xie
  - Yu Li
  - 等
year: 2026
date: 2026-08-08
journal: "IEEE TKDE，DOI 10.1109/TKDE.2026.3717305（作者版，卷期待定）"
source_pdf: "[[raw/papers/rwkv/RWKV-TS_Adaptive_Long-range_Prompt_for_Multiple_Time_Series_Tasks.pdf]]"
tags:
  - RWKV
  - 时间序列
  - 长程依赖
  - 提示学习
  - 类型/论文
key_finding: "把「有效历史」等同于批次内 N×P，用跨批次提示向量把感受野扩到 B×N×P；但其自身敏感性分析承认最优批大小是 64 而非最大值，长期预测在 ETTh1/Weather 上反而劣于 RWKV-TS，属于典型的长程收益不单调案例。"
---

# RWKV-TS+：Adaptive Long-range Prompt for Multiple Time Series Tasks

> 文件名对应关系：`raw/` 中原件名为出版社原始文件名 `RWKV-TS_Adaptive_Long-range_Prompt_for_Multiple_Time_Series_Tasks.pdf`，正式题名为 **RWKV-TS+: Adaptive Long-range Prompt for Multiple Time Series Tasks**（IEEE TKDE 2026 已录用作者版）。

## 一句话

这篇论文的价值不在于"长程有用"，而在于它给出了一个可直接复用的观察：**RNN 类时序模型在工程实现上的真实回看窗口 = 批内 patch 数 × patch 长度，而不是理论上的 T**；而它自己的批大小消融又反过来说明把这个窗口拉满并不最优。

## 论文证据

### 问题定义与机制（Section I，第 1—2 页；Section III，第 4—6 页）

- 第 1—2 页明确写出：理论上 WKV 算子可在长度 T 上聚合依赖，但"in practical implementation (seeing open-source code), the batching and patching strategies result in the independence between each batch"，真实回看窗口被限制为 **N × P**（N 为批内 patch 数，P 为每 patch 时间长度），且 N × P ≪ T。
- 提出三模块：Patch Features Collector（批内聚合出 boost 向量）、Time Features Aggregator（构造跨批 WKV）、Long Prompt Operator（把上一批历史投影为 prompt 向量注入下一批）。感受野从 N×P 扩到 **B × N × P**（B 为批大小），即 B 倍提升，最大配置下最多 T/(B×P) 倍。
- 式(1) `M_b^pt = W_M · (μ_M ⊙ x_b^pt + (1 − μ_M) ⊙ x_{b,T})`：prompt 向量与上一批末位 token 做 token shift 后进入 time-mixing。式(10) 为 t>1 时的常规 token shift。
- 第 6 页 `O_b = O_b / o_{b,1} ∈ R^{T×D}`，即 prompt 位输出被丢弃并做归一化。**新增可学习参数为 0**（第 6 页明确 `N_params(pt embed) = 0`），参数量与 RWKV-TS 完全一致。

### 长期预测（Table II，第 7 页）

| 模型 | ETTh1 MSE | ETTh2 MSE | ETTm1 MSE | ETTm2 MSE | Weather MSE | ILI MSE |
|---|---|---|---|---|---|---|
| RWKV-TS | 0.433 | 0.375 | 0.376 | 0.287 | **0.231** | — |
| RWKV-TS+ | 0.444 | **0.352** | **0.355** | **0.257** | 0.249 | 1.961 |
| PatchTST | **0.413** | 0.330 | 0.351 | 0.255 | 0.225 | 1.443 |

- **负面数据点（正文未强调）**：RWKV-TS+ 在 ETTh1（0.444 vs 0.433）和 Weather（0.249 vs 0.231）上**劣于**自己的骨干 RWKV-TS。PatchTST 在 ETTh1、ETTh2、Weather、ILI 上全面优于 RWKV-TS+。论文只在表下标注 ETTm2 的 `↓10.5%`（0.287→0.257），未标注反向的两列。
- 论文自陈 PatchTST 优势来自非因果设计："This non-causal design lacks future masking, which permits 'look-ahead' behavior where early patches aggregate information from subsequent patches within the same window."（第 7—8 页）——这是对基线的**评测协议缺陷指控**，与本课题关心的捷径问题同类。

### 分类、异常检测、插补

- 分类（Table III，第 8 页）：平均准确率 **74.9%**，第二名 TimesNet **73.6%**，即 **+1.3 个百分点**；论文写作"outperforming ... by 1.7%"是相对比值，不是百分点。错误相对下降口径 = (26.4−25.1)/26.4 = **4.9%**。摘要中的 "improved by up to 28.3%" 是**单一数据集 HandWriting** 相对 RWKV-TS 的提升，不是平均。
- **关键限制自陈**：分类任务中"each batch contains a single sequential sample, and these samples are independent with no temporal coherence between them. Introducing enhanced features from the previous batch into the current batch is therefore meaningless."（第 8 页）→ 分类分支被改成把 prompt 与当前批拼接 `[p_b, X_b]`，**跨批时序机制在该任务上被弃用**。分类提升 3.8%（vs RWKV-TS，SelfRegulationSCP2）来自"样本间属性特征"而非时序历史。
- 异常检测（Table IV）：相对 RWKV-TS 平均 F1 **+1.6%**，最大提升 7.4%（MSL）。论文明确承认 "RWKV-TS+ does not achieve optimal performance, but is close to ... other SOTA baselines"，并归因于 **各数据集最优历史窗口不同**："SMAP signals require shorter look-back windows due to their rapid fluctuation period, whereas MSL benefits from longer temporal context."
- 插补（Table V）：多数据集平均 MSE 0.120 → 0.114，论文称 5.0% 收益；但 TimesNet 在 ETTh1（0.078）、ETTm1（0.027）等列显著优于 RWKV 系。

### 有效历史长度与批大小敏感性（Section V-E，第 9—10 页；Fig. 9）

- 论文自己写明："the batch size governs **the effective length of historical sequence information** integrated by the RWKV-TS+ model"，并在 ETTm1 等四个基准上做批大小消融（Fig. 9，覆盖长期预测与异常检测两类任务）。
- **反转证据**：效率对比（Section V-F）用 batch size = 256 做基准测试，但同段落写 "We also report the efficiency of the proposed model under **optimal performance conditions (with a batch size of 64)**"。即最优性能点在 64 而非可用的最大批，历史越长越好并不成立。
- Fig. 9 的逐点数值在 pdftotext 版面提取中未能可靠还原，**具体饱和/反转曲线标为待验证**，需回查原 PDF 图。

### 其他

- prompt 初始化消融（Table VI/VII）：Zeros 初始化在长期预测与分类上最优（PEMS-SF ACC 0.8439 vs Normal 0.8150；SR-SCP1 0.9215 vs 0.9146；SMAP F1 0.8317 vs 0.8228）；但 SWaT 上 Normal 0.9722 略优于 Zeros 0.9718。
- 效率（Table VIII）：参数量与 RWKV-TS 相同，训练显存低于 FEDformer/PatchTST 但**高于 RWKV-TS**（缓存批级 prompt 矩阵），推理时间**长于 RWKV-TS**（time-mixing 被执行两次）。
- 代码：正文给出 `https://github.com...` 链接（第 6 页脚注区），提取文本被截断，**完整 URL 与权重可得性待验证**。

## 对本课题的意义

- **输入形态匹配度**：低。四个下游任务全是规整采样的数值型多变量序列（ETT/Weather/ILI/UEA/SMD 等），没有字节流、报文或流统计表格。本课题三类数据的字段语义与之不同。
- **有效历史机制可迁移**：其 "真实回看窗口 = N×P" 的诊断可直接用于解释我们 LSPR24 的 20 秒（4 窗）饱和——但结论方向相反：他们认为是实现约束，我们的实测显示是**信号本身饱和**（长历史池化仅 +14.1%，未达 16.1% 门槛）。
- **交叉印证**：本课题"长程无用"与该文异常检测段落自陈的"最优窗口随数据集变化，SMAP 需要更短窗口"一致；也与其批大小最优值为 64（非最大）一致。

## 允许主张

- 可引用其对"批内独立导致真实回看窗口 = N×P"的工程诊断。
- 可引用其"最优历史窗口随数据集/任务变化"的自陈，作为长程收益非单调的同行证据。
- 可引用其零新增参数的跨批 prompt 构造方式作为机制来源。

## 禁止主张

- 不能说 RWKV-TS+ 证明了长程历史普遍有益：其在 ETTh1 与 Weather 上劣于自身骨干。
- 不能把 28.3% 当作整体提升：那是单数据集（HandWriting）相对 RWKV-TS 的值。
- 不能把分类任务的收益归因于长程时序：论文自己声明该分支的跨批时序机制无意义并已被替换。
- 不能把该文结果外推到加密流量检测。

## 待验证假设（本课题推论，未经实验）

- 跨批 prompt 依赖"批次顺序等于时间顺序、训练不打乱"。若批次被 shuffle，则 prompt 携带的是任意历史片段。论文未报告是否禁用 shuffle，也未做 shuffle 消融，这是一个**潜在评测协议缺陷**，属推论，需回查其开源实现。
- 推理时预测结果依赖同批其他样本（prompt 由上一批产生），意味着**同一条流的判定会随批组成变化**。用于在线检测时这是可用性问题，需实验确认。
