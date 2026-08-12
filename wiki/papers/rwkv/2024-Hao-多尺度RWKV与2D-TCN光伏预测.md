---
title: "多尺度 RWKV 结合二维时序卷积网络的短期光伏功率预测"
authors:
  - Jianhua Hao
  - Fangai Liu
  - Weiwei Zhang
year: 2024
date: 2026-08-08
journal: "Energy（Elsevier）309:133068, 2024"
source_pdf: "[[raw/papers/rwkv/1-s2.0-S0360544224028433-main.pdf]]"
zotero_key: "88IP2C9N"
tags:
  - RWKV
  - 多尺度
  - 时序卷积
  - 光伏预测
  - 类型/论文
key_finding: "用 FFT 取 top-k 主周期驱动多尺度 time-mixing，并把 channel-mixing 整体换成二维 TCN；消融显示多尺度 time-mixing 单项贡献 MSE 相对下降 27.1%（DKASC-DG）与 9.6%（DKASC-CA），远高于本课题实测的多尺度 +0.2%，但该增益依赖光伏数据的强日周期性。"
---

# Multi-scale RWKV with 2-dimensional temporal convolutional network for short-term photovoltaic power forecasting

> 文件名对应关系：`raw/` 原件名 `1-s2.0-S0360544224028433-main.pdf` 为 Elsevier ScienceDirect 下载文件名，正式题名为 **Multi-scale RWKV with 2-dimensional temporal convolutional network for short-term photovoltaic power forecasting**（Energy 309:133068, 2024）。模型简称 **MSRWKV-2DTCN**。

## 一句话

本批中唯一给出**干净多尺度单项消融数字**的论文；它的多尺度收益比本课题实测大两个数量级，差异根源在于数据的周期结构而非机制本身。

## 论文证据

### 机制

- 用 **FFT** 把历史序列变换到频域，取 top-k 幅值 `A_{f1},…,A_{fk}` 对应的显著频率 `{f1,…,fk}` 作为主周期（正文第 5—6 页 与创新点 (1)）。
- 创新点 (2)：用 FFT 识别出的周期替换 RWKV 原始 time-mixing 块，构成**多尺度 time-mixing 块**，"extends the receptive field, preserves important information, learns multi-scale dependencies"。RWKV 基本式仍为 `k_t = W_k·(μ_k x_t + (1−μ_k) x_{t−1})`、`v_t = W_v·(μ_v x_t + (1−μ_v) x_{t−1})`（第 4 页 Table 1 旁公式区）。
- 创新点 (3)：把 RWKV 的 **channel-mixing 块整体替换为多尺度 2D TCN**（Fig. 9），用二维卷积同时建模周期内与周期间依赖，以及光伏功率与外部气象因子的复杂关系。
- 膨胀率选择（第 11 页）：明确"the selection of these dilation rates was made with careful consideration of the length of input sequence and the size of convolutional kernels, ensuring that the expanded convolutional kernel does not exceed the length of the input data"。

### 数据

- 澳大利亚 Yulara 太阳能系统的 DKASC 真实数据，两个子系统：**DKASC-DG** 与 **DKASC-CA**（Table 1 给出配置）。
- 时间跨度 2021/1/1 00:00 至（正文截断）23:55:00，**分辨率 5 分钟**（Table 2 给出各属性 Min/25%/50%/75%/Max/Mean 统计）。
- 归一化用 Min-Max，理由是不依赖分布假设并保留相对大小关系（第 9—10 页）。缺失值用前后可用点插值补齐（第 6 页公式区，`t_miss, t_pre, t_next`）。

### 消融（Table 5，第 9 页）——本课题最关心的数字

| 配置 | DKASC-DG MSE | DKASC-DG MAE | DKASC-CA MSE | DKASC-CA MAE |
|---|---|---|---|---|
| MSRWKV-2DTCN（完整） | **0.0043** | **0.0277** | **0.0047** | **0.0252** |
| w/o MSRWKV（换回原始 time-mixing） | 0.0059 | 0.0437 | 0.0052 | 0.0458 |
| w/o 2DTCN（换成普通 TCN） | 0.0075 | 0.0518 | 0.0071 | 0.0503 |
| RWKV（原始架构） | 0.0092 | 0.0622 | 0.0085 | 0.0641 |

按"误差相对下降"口径换算（分母为被消融变体的 MSE）：

- **多尺度 time-mixing 单项**：DKASC-DG (0.0059−0.0043)/0.0059 = **27.1%**；DKASC-CA (0.0052−0.0047)/0.0052 = **9.6%**。
- **2D TCN 单项**：DKASC-DG (0.0075−0.0043)/0.0075 = **42.7%**；DKASC-CA **33.8%**。
- **相对原始 RWKV 总提升**：DKASC-DG 53.3%，DKASC-CA 44.7%。
- 注意：**两个数据集上多尺度收益差 2.8 倍**（27.1% vs 9.6%），论文未讨论这一不一致。

### 季节分解（Table 6，第 9 页）

MSRWKV-2DTCN 分季节 MSE：Spring 0.0031、Summer 0.0034、Autumn 0.0042、Winter 0.0032；对照 DSN 为 0.0048/0.0047/0.0062/0.0045，CNN-LSTM 为 0.0067/0.0058/0.0086/（Winter 截断）。NRMSE 在 Autumn 最差（0.3480），说明**秋季周期结构最弱时多尺度优势下降**。

### 缺失与局限

- **没有回看窗口长度消融**：论文只在膨胀率讨论中提到输入长度约束，未报告不同输入长度下的性能曲线。本课题关心的"有效历史多长"在本文**无法回答**。
- 没有 top-k 中 k 的敏感性分析（k 的取值未在提取文本中出现，待验证）。
- 没有多种子/置信区间报告；比较基线（LSTM、TCN、DSN、CNN-LSTM、GRU-CNN、Informer、Crossformer）的训练预算是否对齐未说明。
- 未提供代码或权重链接（提取文本中未见 GitHub 或 Data Availability，待验证）。

## 对本课题的意义

- **(a) 输入形态**：5 分钟粒度的数值型多变量（功率 + 气象），与本课题窗口级流统计形态接近，与字节流不匹配。
- **(b) 有效历史**：无消融，不可用。
- **(c) 跨变量交互**：由 2D TCN 承担（功率 × 气象），单项贡献 33.8%–42.7% MSE 相对下降，是全篇最大单项——**与本课题"字段交互是主信号"方向一致**。
- **(d) 预训练**：无。
- **(e) 捷径**：光伏功率有极强日周期与夜间零值，FFT 主周期几乎必然命中 24 小时；这类"强先验周期"在加密流量中不存在（推论）。
- **(f) 可得性**：未见代码/权重。

## 允许主张

- 可引用 FFT-top-k → 多尺度 time-mixing 的构造方式作为机制来源。
- 可引用 Table 5 的四行消融作为"多尺度 time-mixing 与跨变量卷积各自可分离贡献"的证据。
- 可引用其"2D TCN（跨变量）单项贡献大于多尺度（时间尺度）单项贡献"的排序（42.7% vs 27.1%，DKASC-DG）。

## 禁止主张

- 不能把 27.1% 的多尺度收益外推到本课题：本课题实测多尺度相对单尺度仅 +0.2%，两者数据周期结构差异巨大。该文两个子数据集之间收益就已相差 2.8 倍。
- 不能声称多尺度机制普适：无跨域验证、无种子重复、无输入长度消融。
- 不能把 MSE 0.0043 与任何非同一归一化的数字比较。

## 与本课题实测的交叉检验

- 本课题实测多尺度相对单尺度仅 +0.2%，本文给出 9.6%–27.1%。差异可归因于：光伏数据由天文日周期驱动，FFT 主周期稳定且物理可解释；加密流量窗口序列在 5 秒粒度上无同等强度的确定性周期（**推论，可用 FFT 谱分析在 LSPR24 上直接证伪：若 top-k 谱能量占比显著低于光伏数据，则多尺度机制失效有直接解释**）。
