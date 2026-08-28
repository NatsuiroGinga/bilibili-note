---
title: "FATA-Trans: Field And Time-Aware Transformer for Sequential Tabular Data"
authors: [Dongyu Zhang, Liang Wang, Xin Dai, Shubham Jain, Junpeng Wang, Yujie Fan, Chin-Chia Michael Yeh, Yan Zheng, Zhongfang Zhuang, Wei Zhang]
year: 2023
date: 2026-08-28
journal: "CIKM 2023"
doi: "10.1145/3583780.3614879"
source_pdf: "[[raw/papers/methodology/ft-mechanisms/2023-Zhang-FATA-Trans-Sequential-Tabular.pdf]]"
sha256: "42c69d08723e5066648e86d7e4ac3733aa71d38402de5627698ff1619348d854"
arxiv_id: "2310.13818"
tags: [序列表格, 字段类型, 时间感知位置, 历史统计, 类型/论文]
key_finding: "FATA-Trans 已把同实体序列、历史统计静态字段、静态/动态字段分路和时间间隔纳入层次 Transformer；但没有证明历史统计逐样本按严格过去计算，也没有当前查询到独立只读记忆的交叉注意力。"
zotero_status: "未操作：本轮 Zotero 本地 API 未运行"
---

# FATA-Trans：字段与时间感知序列表格模型

## 题录与源码

- CIKM 2023，DOI `10.1145/3583780.3614879`，11 个物理页。
- 官方源码：<https://github.com/zdy93/FATA-Trans>。

## 全文证据

- 物理第 3 页公式（1）–（3）把同一标识符的 `l` 条连续记录定义为窗口。
- 物理第 4–5 页公式（4）–（10）分别编码静态与动态字段，再叠加字段类型 embedding 和同时包含次序、时间间隔的位置 embedding。
- 信用卡数据静态字段包括历史交易金额均值/标准差、最常见商户类别与交易方式；评论数据包括历史评分均值、计数及高低评分比例（物理第 6 页）。
- 信用卡按 2018 年前后作时间切分；预训练移除异常标签，评论任务遮蔽最后评分；训练用长度 10 窗口（物理第 6–7 页）。
- 表 1：FATA-Trans 在三任务 AUC 为 `0.9992/0.8057/0.7206`；表 3 消融时间位置、字段类型设计与预训练（物理第 7–8 页）。

## 有效性与边界

- 论文没有给每一历史统计的逐时点拟合合同；“历史”是否包含当前窗口之后记录无法由全文机械证明，故不能当作严格因果前缀先例。
- 架构是窗口内层次自注意力，不是当前流对独立历史记忆的单向交叉注意力。
- 已占用“历史统计作为字段”和“字段/时间感知序列 Transformer”大类；D1 只能主张严格过去、查询方向、FT 特有挂载和单流部署差量。
