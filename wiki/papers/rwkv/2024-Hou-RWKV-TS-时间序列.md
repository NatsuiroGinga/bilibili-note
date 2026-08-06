---
title: "RWKV-TS：超越传统循环神经网络的时间序列任务模型"
authors: [Haowen Hou, F. Richard Yu]
year: 2024
date: 2026-08-05
journal: "arXiv:2401.09093"
source_pdf: "[[raw/papers/rwkv/2024_Hou_RWKV-TS_时间序列.pdf]]"
tags:
  - RWKV
  - 时间序列
  - 长序列
  - 异常检测
  - 类型/论文
key_finding: "RWKV-TS 在五个非安全多变量时间序列异常数据集上报告与多类时序模型相近的结果，支持其作为长序列机制候选，不提供网络安全直接结论。"
method: "实例归一化、分块、RWKV 时间混合与通道混合的编码器式时间序列建模"
baseline: "TimesNet、PatchTST、DLinear、FEDformer、Autoformer、LSTM、XGBoost 等"
aliases:
  - RWKV-TS
  - Hou2024RWKVTS
related:
  - "[[2026-Sharma-PLM-NIDS-RWKV协议语言入侵检测]]"
---

# RWKV-TS：超越传统循环神经网络的时间序列任务模型

> Hou 与 Yu，2024，arXiv 预印本，13 页。

## 一句话

论文将 RWKV 改造为多变量时间序列编码器，在预测、分类、插补和异常检测任务中比较多类模型；这是主题一、二的长序列机制证据，不是安全数据上的直接验证。

## 论文原结论与证据位置

- 第 3--4 页：模型对输入做实例归一化和分块，再由时间混合、通道混合和线性输出层预测目标。
- 第 4 页表 2：作者在 ETTh2 的批量上比较训练/推理成本，所测配置为 3 层、隐藏维 768；该数值不能外推为本项目 5090 预算。
- 第 6--7 页表 7：异常检测比较 SMD、MSL、SMAP、SWaT 与 PSM；RWKV-TS 平均 F1 为 `83.89`，TimesNet 为 `85.24`，说明其并非在全部数据上占优。
- 附录 B.5：异常数据按连续、非重叠片段划分，这是可借鉴的顺序处理方式，但具体数据与安全日志、流量会话不相同。

## 本课题推论

- 该文使“在真实连续序列、预先固定的时间拆分和同一信息预算下比较普通 RWKV、轻量 Transformer 与传统基线”成为可检验的设计，而不是性能承诺。
- 其无网络安全、恶意流量、提示注入或工具调用数据，不能单独提升任何替代主题的安全证据等级。

## 可迁移机制

- 父连接或审计链内先按时间排序再切分连续、非重叠片段；父实体必须整体划入训练、校准或开发验证之一。
- 以普通 RWKV、轻量 Transformer、HGB/树模型与逐项机制消融组成同信息预算的基线矩阵。

## 不可直接声称

- 不可把论文在 SWaT 等工业控制时序上的结果写成网络流量、日志或智能体安全检测效果。
- 不可将其线性复杂度当作本项目单卡可训练的实测结论。

## 文献信息

- arXiv：<https://arxiv.org/abs/2401.09093>
- 代码：<https://github.com/howard-hou/RWKV-TS>
- 原文：[[raw/papers/rwkv/2024_Hou_RWKV-TS_时间序列.pdf]]
- Zotero：`HRZXDAMN`
