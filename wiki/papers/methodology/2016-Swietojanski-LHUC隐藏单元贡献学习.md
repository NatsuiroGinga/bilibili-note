---
title: "Learning Hidden Unit Contributions for Unsupervised Acoustic Model Adaptation"
authors: [Pawel Swietojanski, Jinyu Li, Steve Renals]
year: 2016
date: 2026-09-01
journal: "IEEE/ACM Transactions on Audio, Speech and Language Processing, vol. 24, no. 8；本地原件为 arXiv:1601.02828"
source_pdf: "[[raw/papers/methodology/2016-Swietojanski-LHUC-Unsupervised-Adaptation.pdf]]"
sha256: "d9732801becdcbfc57c96ac6f53e66869cdca819aa22a5aae941799dc63423b4"
arxiv_id: "1601.02828"
tags:
  - 说话人自适应
  - 振幅门控
  - 条件化
  - 类型/论文
key_finding: "LHUC 为每个隐藏单元引入按说话人条件化的振幅函数 ξ(r)（物理第 3 页式 3，ξ 典型为值域 (0,2) 的 sigmoid），以逐单元缩放实现无监督声学模型自适应；在 4 个语料 270 个测试说话人上稳定改善。"
method: "h^{l,s}_j = ξ(r^{l,s}_j) ∘ ψ_j(w_j^T x + b_j)：基函数共享，按说话人学习振幅参数 r；扩展为 SAT-LHUC 联合训练"
aliases:
  - LHUC
  - Swietojanski2016-LHUC
  - 隐藏单元贡献学习
related:
  - "[[2018-Perez-FiLM通用条件化层]]"
---

# LHUC：按说话人门控隐藏单元振幅

> Swietojanski, Li, Renals，IEEE/ACM TASLP 24(8)，2016。

## 一句话

把「分组身份」（说话人）条件化为对隐藏单元的 σ 振幅门，是「按组身份门控表示分量」这一算子的 2016 年先例。

## 全文证据（物理页码）

- 第 3 页第 III 节式 (3)：`h^{l,s}_j = ξ(r^{l,s}_j) ∘ ψ_j(w_j^T x + b_j)`；振幅函数 `ξ: R → R+`，「typically a sigmoid with range (0, 2)」（同页）。
- 第 3–4 页 SAT-LHUC：把测试期自适应扩展为训练期联合学习说话人相关振幅。

## 与本课题的关系

M-E 的实体门 `σ(MLP(s_e))` 与 LHUC 的按组 σ 振幅门同构：把「说话人码」换成实体历史统计 `s_e`、把逐单元门收缩为标量门。**σ 振幅门控条件化算子已被占用十年**，M-E 不能以门控本身作为机制创新点。

## 边界

- 语音识别域；无漂移评价、无表格结构。仅用于算子谱系定位。
