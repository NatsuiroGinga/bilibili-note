---
title: "Are Transformers Effective for Time Series Forecasting?"
authors: [Ailing Zeng, Muxi Chen, Lei Zhang, Qiang Xu]
year: 2022
date: 2026-08-13
journal: "arXiv:2205.13504v3 [cs.AI]，2022 年 8 月 17 日，15 页（本 PDF 未标注 AAAI 2023 版式；原件文件名中的 2023 指其后续正式发表年份，未在 PDF 内核实）"
source_pdf: "[[raw/papers/methodology/2023-Zeng-Are-Transformers-Effective-Time-Series-Forecasting.pdf]]"
sha256: "97abddd1821cc72942c8d7ddde7e99466bb91f1bddc37c2b54e0e97be7b5be1b"
tags:
  - 简单基线
  - 时间序列预测
  - 序列建模
  - 负面结果
  - 评价方法论
  - 类型/论文
key_finding: "单层线性模型 LTSF-Linear 在 9 个长期预测基准上全面超过 FEDformer、Autoformer、Informer、Pyraformer 与 LogTrans，改进幅度 20%~50%（摘要与第 4 页 5.2 节；表 2，第 5 页）；打乱输入序列后 Transformer 的误差几乎不变而线性模型显著变差，说明前者本就没有利用时序顺序（表 5，第 7 页）。"
method: "把长期时序预测的组合函数退化为沿时间轴的一层线性层 X̂_i = W X_i，并给出两个变体 DLinear（趋势-季节分解后各接一层线性）与 NLinear（减去序列末值再线性再加回）；随后用回看窗口扫描、远近输入对比、输入打乱、逐步把 Informer 简化为线性、嵌入消融与训练数据量对比六组实验诊断 Transformer 的失效来源"
baseline: "FEDformer-f、Autoformer、Informer、Pyraformer、LogTrans，以及重复回看窗口末值的 Closest Repeat"
aliases:
  - LTSF-Linear
  - DLinear
  - Zeng2022-Transformer是否有效
related:
  - "[[2018-Shen-SWEM简单词嵌入池化基线]]"
  - "[[2019-Dacrema-神经推荐进步幻觉]]"
  - "[[2022-Audibert-深度网络是否有助于多变量时序异常检测]]"
  - "[[2022-Kim-时序异常检测的严谨评价]]"
---

# 一层线性层打穿长期时序预测的 Transformer

> Zeng, Chen, Zhang, Xu（CUHK / IDEA），arXiv:2205.13504v3 · 15 页

## 一句话

作者指出自注意力本质上是置换不变的、天生"反顺序"，于是用一层线性层作为长期预测基线，在 9 个基准上全面胜出 20%~50%；更关键的是打乱输入顺序后 Transformer 误差几乎不动而线性模型崩掉，直接证明这些 Transformer 并没有在提取时序关系。

## 题录

- 题名（逐字抄自 PDF 第 1 页）：Are Transformers Effective for Time Series Forecasting?
- 作者单位：The Chinese University of Hong Kong；International Digital Economy Academy (IDEA)（第 1 页）
- arXiv：2205.13504v3 [cs.AI]，2022 年 8 月 17 日（第 1 页左侧竖排标记）
- DOI：未在原件中定位
- 原件：`raw/papers/methodology/2023-Zeng-Are-Transformers-Effective-Time-Series-Forecasting.pdf`
- 代码：<https://github.com/cure-lab/LTSF-Linear>（摘要，第 1 页）

## 核心方法

- 问题设定（第 2 页，第 2 节）：给定 C 个变量、回看窗口长度 L 的历史 `X = {X_1^t, ..., X_C^t}_{t=1..L}`，预测未来 T 步。迭代多步（IMS）方差小但有误差累积，直接多步（DMS）在 T 大或单步模型有偏时更准；作者指出既有 Transformer 论文的非 Transformer 基线全部是 IMS，因此对比不公平。
- LTSF-Linear（第 4 页，图 2）：`X̂_i = W X_i`，其中 `W ∈ R^{T×L}` 是沿时间轴的一层线性层，跨变量共享权重，完全不建模变量间相关性。
- DLinear（第 4 页）：先用移动平均核把输入拆成趋势项与余项（季节项），各接一层线性层后相加，用于有明显趋势的数据。
- NLinear（第 4 页）：先减去序列最后一个值，过线性层后再加回，是针对分布漂移的极简归一化。
- 诊断实验设计（第 5–8 页）：回看窗口 `L ∈ {24,48,72,96,120,144,168,192,336,504,672,720}` 扫描；Close/Far 输入对比；Shuf.（整段随机打乱）与 Half-Ex.（前后半段互换）；把 Informer 逐步退化为 Att.-Linear → Embed+Linear → Linear；位置与时间戳嵌入消融；全量与一年数据的训练规模对比。

## 关键数字（含页码/表号）

- 数据规模（表 1，第 5 页）：ETTh1&ETTh2 变量 7、17,420 步、1 小时粒度；Traffic 变量 862、17,544 步；Electricity 变量 321、26,304 步；Exchange-Rate 变量 8、7,588 步、1 天粒度；Weather 变量 21、52,696 步、10 分钟粒度；ILI 变量 7、966 步、1 周粒度。
- 主表（表 2，第 5 页，MSE，越低越好）：Electricity T=96 上 Linear/DLinear=0.140 对 FEDformer 0.193（IMP. 27.40%）；Traffic T=96 上 Linear=0.410 对 FEDformer 0.587（IMP. 30.15%）；Exchange T=96 上 DLinear=0.081 对 FEDformer 0.148（IMP. 45.27%）；ILI T=24 上 NLinear=1.683 对 FEDformer 3.228（IMP. 47.86%）；ETTm1 T=96 上 DLinear=0.299 对 FEDformer 0.379（IMP. 21.10%）。改进幅度最小的是 ETTh1 T=96（IMP. 0.80%，NLinear 0.374 对 FEDformer 0.376）。
- 朴素基线也能赢（表 2，第 5 页与正文）：仅重复回看窗口末值的 Repeat 在 Exchange-Rate 上（T=96 时 MSE=0.081）超过全部 Transformer，作者称约 45%。
- 回看窗口（第 5–6 页，图 4）：随着 L 增大，Transformer 的 MSE 停滞甚至变差，而全部 LTSF-Linear 显著改善；作者判断 Transformer 在更长输入下是在拟合时序噪声。
- 远近输入几乎无差（表 3，第 6 页）：Electricity 上 FEDformer Close=0.251 / Far=0.265，Autoformer 0.255 / 0.287；Traffic 上 FEDformer 0.631 / 0.645，Autoformer 0.677 / 0.675。说明模型只依赖回看窗口的粗略统计。
- 逐步简化 Informer 反而更好（表 4，第 6 页，MSE）：Exchange T=96 上 Informer 0.847 → Att.-Linear 1.003 → Embed+Linear 0.173 → Linear 0.084；ETTh1 T=720 上 1.181 → 0.902 → 1.051 → 0.515。
- 打乱输入的关键消融（表 5，第 7 页）：ETTh1 上平均性能下降 Linear 81.06%、FEDformer 73.28%、Autoformer 56.91%、Informer 1.98%；Exchange 上 Linear 下降 27.26%（Half-Ex. 46.81%），而 FEDformer −0.09%、Autoformer 0.09%、Informer −0.12%，即 Transformer 对顺序几乎无感。全部结果为 5 次运行均值。
- 嵌入消融（表 6，第 7 页）：Informer 去掉位置嵌入后 Traffic T=96 的 MSE 从 0.719 升到 1.035；Autoformer 同时去掉位置与时间戳嵌入后 T=720 从 0.638 恶化到 1.300；FEDformer 因频域归纳偏置受影响最小（0.649 → 0.663）。
- 训练数据量不是瓶颈（表 7，第 8 页）：Traffic 上只用一年数据（8,760 小时）训练的 FEDformer 在全部四个预测长度上误差都低于用全量（17,544×0.7 小时）训练，Autoformer 在四个长度中的三个上同样更低。
- 效率（表 8，第 8 页）：DLinear MACs 0.04G、参数 139.7K、推理 0.4ms、显存 687MiB；vanilla Transformer 4.03G / 13.61M / 26.8ms / 6091MiB；Informer 3.93G / 14.39M / 49.3ms / 3869MiB。

## 与本课题（LSPR23→LSPR24 加密恶意流量跨年度迁移）的关系

- 与本课题最直接对应的一篇。本课题实测"序列 + 因果前缀均值 `ctx = cumsum(h)/cumsum(mask)`（AP 0.1848–0.2879）优于完整 RWKV-7 状态递归"，与本文"一层线性/分解线性优于全部 Transformer"是同一类现象：当任务信号主要来自窗口内的统计量而非精细顺序时，带状态的复杂序列模型只会增加优化难度与过拟合风险。
- 表 5 的打乱实验是本课题应当立刻复制的最小证伪实验。把同一流内的包序列或同一实体内的流序列随机打乱后重训，如果 AP 基本不变，说明本课题的递归模块同样没有在利用顺序，那么放弃完整状态递归就有了本课题自己的实验证据，而不只是文献类比。
- NLinear 的做法（减去序列末值、过线性层、再加回）是针对分布漂移的极简归一化，成本几乎为零，可直接作为本课题跨年度迁移的候选预处理消融项：对逐流特征或实体级聚合量做同类的"减去参考值"归一化，检验 LSPR24 上 AP 是否提升。这是可执行的候选，不是已验证结论。
- 表 4"逐步把 Informer 简化为线性、性能反而单调变好"提供了一个清晰的消融范式：本课题可按同样方式把 RWKV-7 逐步退化为（去状态衰减 → 去门控 → 纯前缀均值），观察 AP 是否单调改善，从而定位是哪一个组件在损害性能。
- 效率对照（表 8）支持在论文中论证"简单聚合器在同等或更好效果下具有数量级的推理与显存优势"，这对面向在线检测的系统章节有用。

## 局限（不可直接声称的内容）

- 任务是多变量数值回归预测（MSE/MAE），不是极不平衡的二分类检测，本文结论不能直接迁移到 AP、DR@FPR 等指标。
- 全部基准为周期性较强的传感/交通/电力/气象数据，与加密流量的突发、稀疏、强异质特性不同；作者自己也承认"Not all time series are predictable"（第 2 页）。
- 论文没有跨年度或显式的域迁移评价：训练与测试在同一数据集内按时间切分，NLinear 针对的"distribution shift"是序列水平漂移，不是本课题意义上的跨年度域漂移。因此本文不能作为"分布漂移下模型退化的受控测量"的证据。
- 论文没有实体级聚合的对照，不能支持本课题"实体级（2-IP 无向对）聚合后 AP 0.5233–0.5475"的结论。
- 作者明确说明其贡献不在于提出线性模型，而在于提出质疑并给出对比（第 8 页），因此引用时不宜把 LTSF-Linear 表述为方法创新。
- 本 PDF 为 arXiv v3 预印本，未含正式会议版式；若论文中需标注 AAAI 2023，须另行核对正式版。

## 可引用的逐字原文（≤15 词）

- "LTSF-Linear surprisingly outperforms existing sophisticated Transformer-based LTSF models in all cases"（摘要，第 1 页）
- "the temporal modeling capabilities of Transformers for time series are exaggerated"（第 2 页，引言末）
- "existing Transformers do not preserve temporal order well"（第 7 页，5.3 节）

## 证据记录

- 来源类型：完整论文（15 页，`pdftotext -layout` 抽取后逐页核对；`file` 判定为 PDF 1.5，sha256 已记录）
- 支持：简单线性聚合在长期时序预测上全面胜过 Transformer；打乱输入实验可判定序列模型是否真的利用了顺序；逐步简化消融可定位有害组件
- 限制：回归指标、周期性数据、无跨域迁移、无不平衡分类、无实体级聚合证据
- 论断强度：有支持（简单基线优于复杂序列模型；顺序敏感性诊断范式）/ 推论（迁移到加密流量跨年度检测）

## 文献信息

- arXiv：<https://arxiv.org/abs/2205.13504>
- 代码：<https://github.com/cure-lab/LTSF-Linear>
