---
title: "A Simple Baseline for Predicting Events with Auto-Regressive Tabular Transformers"
authors: [Alex Stein, Samuel Sharpe, Doron Bergman, Senthil Kumar, C. Bayan Bruss, John Dickerson, Tom Goldstein, Micah Goldblum]
year: 2024
date: 2026-08-28
journal: "arXiv:2410.10648v3，Preprint Under Review"
source_pdf: "[[raw/papers/methodology/ft-mechanisms/2024-Stein-STEP-Autoregressive-Tabular-Events.pdf]]"
sha256: "22a1e0a4c991aaae2338016d385655d9d7c04831cb43e5bc230f2d5ee16ec8e9"
arxiv_id: "2410.10648v3"
tags: [因果Transformer, 表格事件, 实体序列, 欺诈检测, 类型/预印本]
key_finding: "STEP 已直接使用按实体分组、按时间排序和标签遮蔽的因果自回归 Transformer 预测当前事件；因此“因果实体历史 Transformer”不能再称新颖，D1 只能保留 FT 当前字段编码与独立记忆交叉注意力的结构差量。"
zotero_status: "未操作：本轮 Zotero 本地 API 未运行"
---

# STEP：因果自回归表格事件预测

## 题录与源码

- arXiv `2410.10648v3`，首页明确标注 `Preprint (Under Review)`，不能当作已正式发表结果。
- 官方源码：<https://github.com/alexstein0/event_prediction_step>。

## 全文证据

- 物理第 4 页公式（1）–（2）先按元字段分组、再按时间排序；实体标识只作分组键，不入模。
- 物理第 5 页把每个事件字段展开为 token，使用 decoder-only 因果遮罩和下一 token 交叉熵；数值字段分为 32 个分位数箱。
- 信用卡序列长度 10，用户级 98/2 切分，窗口不重叠且不做正类过采样；历史事件标签在检测任务中遮蔽（物理第 6–7 页）。
- 表 1 报告五数据集 AUC；无列随机的 STEP 为 `0.998/0.771/0.853/0.942/0.763`，但为预印本且比较部分沿用他文数字（物理第 8 页）。
- 物理第 9–10 页承认长历史选择仍是未来工作；公开代码用于复现。

## 新颖性边界

- 已占用：同实体历史、严格因果遮罩、当前事件标签预测、历史标签不可得处理。
- 未覆盖：FT-Transformer 的 84 字段 token、自注意力后当前 `[CLS]` 查询压缩历史记忆、记忆打乱负控、实体低误报排序。
- D1 必须把 STEP 作为强结构对照或最近邻；不得声称首次做因果实体历史 Transformer。
