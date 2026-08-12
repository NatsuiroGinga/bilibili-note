---
title: "预训练多尺度 RWKV-GCN 的多变量时间序列预测"
authors:
  - Jianhua Hao
  - Fangai Liu
  - Weiwei Zhang
year: 2026
date: 2026-08-08
journal: "Scientific Reports 16:10250, 2026，DOI 10.1038/s41598-026-41091-4"
source_pdf: "[[raw/papers/rwkv/2026_Hao_Pre-trained_Multi-scale_RWKV-GCN_Multivariate_Forecasting.pdf]]"
zotero_key: "XSXYQ6EB"
tags:
  - RWKV
  - 多尺度
  - 图卷积
  - 自监督预训练
  - 类型/论文
key_finding: "两阶段设计：先用通道无关（CI）掩码重建自监督预训练学纯净时序表示，再在微调阶段用多尺度 GCN 引入跨序列依赖；回看窗口预训练 512、正式实验固定 96，无回看长度消融；'w/o Pretraining' 与 'w/o 多尺度 GCN' 消融列存在但具体数值未能从版面提取。"
---

# Pre-trained multi-scale RWKV-GCN for multivariate time series forecasting

> 文件名对应关系：`raw/` 原件名 `2026_Hao_Pre-trained_Multi-scale_RWKV-GCN_Multivariate_Forecasting.pdf` 与正式题名 **Pre-trained multi-scale RWKV-GCN for multivariate time series forecasting** 一致（Scientific Reports 2026;16:10250）。模型简称 **PMSRWKV-GCN**。作者团队与光伏 2D TCN 那篇（Energy 2024）相同。

## 一句话

本批 8 篇中唯一同时具备**自监督预训练**与**显式跨序列图结构**的工作，且它的核心论断恰好与本课题相关：**跨变量信息过早引入会污染时序表示，应当先学纯净时序再引入空间**。

## 论文证据

### 两阶段框架

- 阶段一（预训练，"CI pre-training for noise-free temporal representation" 节）：采用 **通道无关（channel-independent, CI）** 策略，每个变量当作独立单变量序列，遵循 Nie 等人（PatchTST 作者）的掩码重建自监督协议。**只训练多尺度 time-mixing 模块**。原文动机："This design prevents the model from prematurely relying on **spurious correlations** and facilitates the identification of distinctive dynamics within individual series."
- 阶段二（微调）：接入 **多尺度 GCN**，把长度 L 的时间窗按 FFT 识别的主周期 `{p1,…,pk}(p_i < L)` 切成若干段，每个尺度由独立 GCN 更新节点特征 `H_i^new` 与邻接矩阵 `A_i^new`，最后加权融合（Fig. 1）。末段不足时用序列起始部分做**循环填充**以对齐周期。
- 多尺度 time-mixing 输出式(19)：`o'_t = W_o · (σ(r'_t) ⊙ MultiHead(wkv'_t))`。FFT 式(9)：`A = Avg(Amp(FFT(X)))`，X ∈ R^{L×N}。

### 实验配置（"Pre-training stage" 与 "Experimental setup" 节）

- 预训练：每个数据集 **100 epoch**，**look-back window = 512，segment length = 64**，掩码比例 **50%**（掩码位置填零），FFT 取 **k = 5** 个主频率（沿用 TimesNet 的频率稀疏性原则）。
- **泄漏控制明确**：自监督预训练"conducted strictly on the training set of each dataset. The validation and test sets are not involved... The chronological order of the time series is strictly preserved, ensuring that no future information is introduced during pre-training."
- 正式实验：**回看窗口固定 L = 96**，预测步长 {96, 192, 336, 720}；MSE 损失，batch 32，lr 1e-4，**每个实验重复 5 次**，滚动验证调参；两张 RTX 2080 Ti。
- 八个数据集：Weather、ETTh1、ETTh2、ETTm1、ETTm2、Electricity、Exchange、Traffic。超参搜索空间见 Table 2：N1（time-mixing 层数）全部为 1，N2（GCN 层数）在小数据集为 2、Electricity/Traffic 为 3；d_model 32（小数据集）/256（Electricity、Traffic）/64（Exchange）；节点向量嵌入 24 / 96。
- 对比模型结果**直接引自 TimesNet 与 MSGNet 论文**，不是本文重跑（"The results of comparison models are reported from TimesNet47 and MSGNet54."）——这是**公平性隐患**，训练预算与归一化未必一致。

### 消融

- Table 4 中包含 **"w/o Pretraining"** 列（同模型不做预训练阶段直接训练）。摘要与结论声称："Ablation studies further confirm that **CI pre-training strengthens temporal modeling**, while the **multi-scale GCN is critical for capturing strong spatial correlations**."
- **数值未提取到**：Table 4 为跨页宽表，pdftotext 版面还原后 MSE/MAE 具体格值缺失。**"w/o Pretraining" 与多尺度 GCN 的具体消融增益标为待验证**，需回查原 PDF Table 4。
- 预训练深度发现（"Experimental setup" 节）："for the CI pre-training stage, we found that using a **single time-mixing layer** achieves the best trade-off between stability and generalization across all datasets, while **deeper configurations offer no additional benefits** for univariate masked reconstruction." —— 这是一个**容量饱和**的负面发现，与本课题"长历史/多尺度加深不带来收益"同类。

### 缺失与局限

- **无回看窗口长度消融**：L 固定 96（预训练 512），无法得出有效历史长度。
- 未报告统计检验，仅"重复 5 次"，未说明报告的是均值还是最优。
- 基线数字来自他人论文，非同一 harness 重跑。
- 未见代码/权重可得性声明（提取文本中未出现 GitHub 或 Code Availability，待验证；Scientific Reports 通常要求 Data Availability Statement，需回查原文末尾）。

## 对本课题的意义

- **(a) 输入形态**：标准 LTSF 数值多变量基准，与字节流/报文不匹配。
- **(b) 有效历史**：预训练 512、微调 96，**无长度消融**，本文不能回答饱和点。
- **(c) 跨变量交互**：核心贡献之一（多尺度 GCN），但论文的立场是"**先 CI 后 CD**"——与 RWKV-CVM 的"轻量门控注入"是两条不同路线，都指向同一判断：**粗暴的早期跨变量混合会引入噪声**。
- **(d) 预训练目标与规模**：掩码重建（50% 掩码，段长 64），每数据集 100 epoch，**单数据集自监督，不是跨数据集大规模预训练**。所谓"pre-trained"规模很小，不构成基础模型意义上的预训练。
- **(e) 捷径/协议**：泄漏控制写得清楚（时序顺序保留、只在训练集预训练），但基线引用外部数字损害公平性。
- **(f) 可得性**：待验证。

## 允许主张

- 可引用其"预训练阶段用 CI 隔离跨通道干扰、微调阶段再引入图结构"的两阶段设计作为机制来源。
- 可引用其"单层 time-mixing 即最优、加深无额外收益"的负面发现。
- 可引用其掩码重建预训练协议（50% 掩码、段长 64、look-back 512）作为时序自监督的具体配置参考。

## 禁止主张

- 不能引用具体消融增益：Table 4 数值未核出。
- 不能称其为"预训练基础模型"：预训练是逐数据集、100 epoch 的小规模自监督，无跨域迁移证据。
- 不能把其对比结果当作公平比较：基线数字引自 TimesNet 与 MSGNet 原论文。

## 证据支持的构思四栏

| 可借鉴的机制／公式 | 不能再声称为本课题原创的部分 | 结合 LSPR 跨年度任务与 RWKV 后可形成的实质改造 | 最小可证伪消融与匹配强基线 |
| --- | --- | --- | --- |
| 先通道独立掩码重建、后多尺度 GCN；式（9）的 FFT 周期选择与式（19）的多尺度 RWKV 输出 | 首次提出 RWKV 通道独立预训练后再引入图结构、首次用“延迟跨通道交互以减少伪相关”作为该两阶段设计动机 | 不复刻多尺度 GCN；在 LSPR23 语义组掩码任务中，用组间预测一致性直接监督 RWKV 状态条件边可信度，并把参数、图规则和阈值冻结到 LSPR24 | 同预算比较联合掩码、通道独立掩码、Hao 式静态／多尺度图、UP2ME 式潜表示图、状态可信图；强基线含本文模型移植、UP2ME、JCCMTM 和普通 RWKV。若可信图不优于静态图，则候选 A 的新增机制被否决 |

## 待办

- 回查原 PDF Table 4，补齐 "w/o Pretraining" 在八个数据集上的 MSE/MAE 与多尺度 GCN 的消融差值。
- 回查文末 Data/Code Availability。
