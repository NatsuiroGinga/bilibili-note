---
title: "Tabular Transformers for Modeling Multivariate Time Series"
authors: [Inkit Padhi, Yair Schiff, Igor Melnyk, Mattia Rigotti, Youssef Mroueh, Pierre Dognin, Jerret Ross, Ravi Nair, Erik Altman]
year: 2021
date: 2026-08-28
journal: "ICASSP 2021，3565–3569；arXiv:2011.01843v2"
source_pdf: "[[raw/papers/methodology/ft-mechanisms/2021-Padhi-TabFormer-Tabular-Time-Series.pdf]]"
sha256: "0615b65c8fcea9a1554b3578ed94305b0a70ac689fd2f568d309a48f7adcb8aa"
arxiv_id: "2011.01843v2"
tags: [序列表格, 层次Transformer, 交易历史, 欺诈检测, 类型/论文]
key_finding: "TabBERT 先以字段 Transformer 编码单行，再以第二级 Transformer 编码同一用户的连续 10 行；它直接占用序列表格历史注意力大类，但不是当前流查询严格过去记忆的 FT 交叉注意力。"
zotero_status: "未操作：本轮 Zotero 本地 API 未运行"
---

# TabFormer：序列表格层次 Transformer

## 题录与源码

- 首页与 arXiv 标记确认题名、作者和版本；正式题录由官方仓库给出 ICASSP 2021、3565–3569。
- 官方源码与合成信用卡交易数据：<https://github.com/IBM/TabFormer>，Apache-2.0。

## 全文证据

- 物理第 2 页公式（1）把输入定义为同一实体的连续 `T` 行窗口；字段 Transformer 编码每行，第二级 Transformer 编码行间时间关系。
- 连续字段先分位数离散化为本字段词表，属于离散 tokenizer，不是 FT 的线性数值 token（物理第 1–2 页）。
- 信用卡任务含 2400 万条交易、2 万用户；训练与下游任务均用 10 条交易窗口。欺诈任务共 240 万个窗口、29,342 个正窗口（物理第 3 页）。
- 表 1：原始特征 MLP/LSTM 的 F1 为 `0.74/0.83`，TabBERT 特征加同样预测头为 `0.76/0.86`（物理第 3 页）。
- TabGPT 使用因果生成预测未来交易，但 TabBERT 表示学习与欺诈特征提取使用双向 BERT 式窗口（物理第 4 页）。

## 新颖性边界

- 已占用：同实体连续行、字段内注意力、行间 Transformer、连续值离散化与交易历史表示。
- 未覆盖：FT 当前流 84 字段自注意力保持不变；当前 `[CLS]` 只查询独立的严格 `t^-` 记忆 K/V；单流在线推理；实体低误报训练。
- 因此本文是 D1 的直接结构近邻，不是 D1 有效性的证据。
