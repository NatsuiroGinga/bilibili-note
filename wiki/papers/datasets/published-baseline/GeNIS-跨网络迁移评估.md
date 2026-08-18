---
title: "GeNIS 跨网络迁移评估"
authors:
  - Miguel Silva
  - João Vitorino
  - Daniela Pinto
  - Ivone Amorim
  - Eva Maia
  - Isabel Praça
year: 2026
date: 2026-08-12
journal: "第 23 届安全与密码学国际会议（SECRYPT 2026）"
source_pdf: "[[raw/papers/datasets/published-baseline/2026-Silva-Generalizing-across-Networks-GeNIS.pdf]]"
doi: "10.5220/0015002100004103"
tags:
  - 网络入侵检测
  - GeNIS
  - 跨数据集泛化
  - 迁移评估
  - 类型/论文
aliases:
  - Silva2026-GeneralizingAcrossNetworks
  - GeNIS 跨网络泛化
key_finding: "统一用 HERA 重提取 60 秒、40 字段后，GeNIS 同域树模型 F1 达 100%，但训练不含 GeNIS 时在 GeNIS 上最好仅 67.05%；这直接证明同域随机分类近饱和而跨网络迁移远未饱和。"
---

# GeNIS 跨网络迁移评估

> A 类实际使用论文；11 页正式开放全文，CC BY-NC-ND 4.0，第 701–711 页。

## 一句话

该文把 GeNIS、HIKARI-2021、CICIDS2017 和 UNSW-NB15 的原始 PCAP 统一用 HERA 导出，从而把近乎完美的同域成绩与明显失败的域外迁移置于同一字段口径下，是当前最直接的“同域天花板不等于真实泛化”证据。

## 数据与统一预处理

- 四个数据集的原始 PCAP 均用 HERA 生成 60 秒流统计，以消除不同流导出器的字段计算差异（PDF 第 2–3、11 页）。
- 每个数据集做分层 70/30 训练/留出。删除协议、服务、端口等类别字段、缺失率超过 10% 的字段及仍有缺失的行，最终保留 40 个行为字段（PDF 第 3 页）。
- GeNIS 训练集为良性 19,005、恶意 238,984；测试集为良性 8,145、恶意 102,422（表 1，PDF 第 4 页）。
- 五种选择方法与 GeNIS 分类基线相同。每个数据集先取前 10 字段，四个集合的并集形成 21 个缩减字段；GeNIS 前十为 `Offset`、`SrcLoad`、`Load`、`DstLoad`、`Ssaddr`、`DAppBytes`、`Rate`、`RunTime`、`SrcRate`、`Sum`（表 6，PDF 第 5 页）。
- `Offset`、`Ssaddr` 等字段可能编码源文件或网络结构，论文虽移除地址/端口，却没有做这些连接或文件指纹字段的消融。

## 模型与调参

- 模型为 LGBM、RF、XGB、LSTM。树模型用五折交叉验证，以 F1 选择完整与缩减字段的网格配置；LSTM 是 64 单元 LSTM、32 单元全连接层，并把每行当作单步序列（PDF 第 3–4 页）。
- LSTM 输入标准化，从训练集再按 80/20 分训练/验证，最多 30 轮、早停耐心 3（表 5，PDF 第 4 页）。
- 论文未报告随机种子、重复运行、置信区间或源码。

## 同域与跨网络结果

指标为恶意正类 F1 和良性误报率，不是宏 F1；准确率被作者主动排除（PDF 第 4 页）。

| 协议 | 最强/代表性结果 | 证据 |
| --- | --- | --- |
| GeNIS 训练、GeNIS 测试，40 字段 | LGBM/RF/XGB F1 100%、FPR 0；LSTM F1 99.97%、FPR 0.16 | 表 7，PDF 第 7 页 |
| GeNIS 训练、异域测试，40 字段 | RF 在 HIKARI/CICIDS/UNSW 上 F1 67.95/86.21/0；LGBM 与 XGB 在 UNSW 均为 0 | 表 7，PDF 第 7 页 |
| GeNIS 训练、异域测试，21 字段 | RF 在 HIKARI 上 67.91%，但在 CICIDS 降至 46.04%；三个树模型在 UNSW 近 0 | 表 8，PDF 第 7 页 |
| 单一异域训练、GeNIS 测试 | 40 字段最好为 UNSW→GeNIS RF 65.72%，但 FPR 39.48%；21 字段最好为 CICIDS→GeNIS XGB 75.90%、FPR 0 | 表 7–8，PDF 第 7 页 |
| 三数据集训练且不含 GeNIS，GeNIS 测试 | 40 字段最好 RF F1 66.34%、FPR 0；21 字段最好 XGB F1 67.05%、FPR 0.21 | 表 9–10，PDF 第 9 页 |

当训练组合包含 GeNIS 时，GeNIS 测试通常又接近 100%。这说明高分主要依赖训练域中已经存在同一数据源，而不是模型普遍学会了可迁移的攻击行为（表 9–10，PDF 第 9 页）。

## 复现与不可比较项

- 与 GeNIS 发布分类基线不可逐分比较：本文重新从 PCAP 用 HERA 统一导出、采用 70/30、40/21 字段和二分类正类 F1；发布基线采用官方 `4-preprocessed` 80/20、87/16 字段。
- 本地当前缺少 `1-packets.zip`，无法严格重放该文对 GeNIS PCAP 的统一 HERA 重提取；现有 `2-flows` 可支持同源流级近似，但不能冒充论文的 PCAP 重建协议。
- 未说明缩放和特征选择是否仅在训练折拟合；缩减字段是四个数据集前十的并集，若使用被留作“未见测试域”的字段排名，会构成测试域信息参与字段设计的风险，全文未明确消除这一点。
- 未提供每类结果、多种子不确定性、校准、固定告警预算或作者源码。

## 对本课题的意义

以下是审计推论：

1. 跨网络/跨场景泛化比随机行级分类更适合作为章级问题，因为全文已直接验证性能差距存在。
2. 强基线应保留 RF、XGB、LGBM，并将严格场景留出与固定误报告警预算结合；复杂模型只有在最坏组召回和校准上超过这些树模型才值得保留。
3. 需要先做 `Offset`、连接统计、窗口状态等潜在数据源指纹消融，再判断性能下降来自真正的域变化还是捷径丢失。

## 文献信息

- DOI：<https://doi.org/10.5220/0015002100004103>
- 正式 PDF：<https://www.scitepress.org/Papers/2026/150021/150021.pdf>
- 本地 PDF SHA-256：`6e4e5c0aa6d09d0c0403725631658ed5c19e9cb07faed71dd66d5cae1375d687`

