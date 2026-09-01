---
title: "FiLM: Visual Reasoning with a General Conditioning Layer"
authors: [Ethan Perez, Florian Strub, Harm de Vries, Vincent Dumoulin, Aaron Courville]
year: 2018
date: 2026-09-01
journal: "AAAI 2018；本地原件为 arXiv:1709.07871"
source_pdf: "[[raw/papers/methodology/2018-Perez-FiLM-Visual-Reasoning.pdf]]"
sha256: "765acea6f2a78b1d76961392099cd0af49cb2e7d6f06d0b3d82f1dbe9cdcd363"
arxiv_id: "1709.07871"
tags:
  - 条件化
  - 特征调制
  - FiLM
  - 类型/论文
key_finding: "FiLM 用条件输入生成逐特征仿射参数 γ、β 调制主网络（物理第 2 页式 1–2），并在物理第 3 页 Related Work 给出统一分类：拼接条件信息等价于 γ=1 的 FiLM；σ 限幅门控（LSTM 门、SE）等价于受限于 (0,1) 的条件缩放；FiLM 本身是超网络（Ha et al. 2016）的一种形式。"
method: "条件网络 f、h 从条件输入 x_i 产出 γ_{i,c}、β_{i,c}（式 1），主网络特征图按 FiLM(F|γ,β)=γ·F+β 调制（式 2）"
aliases:
  - FiLM
  - Perez2018-FiLM
  - 特征级线性调制
related:
  - "[[2017-deVries-条件BatchNorm调制视觉处理]]"
  - "[[2016-Ha-超网络]]"
  - "[[2026-Wei-ICLAD上下文表格异常检测]]"
---

# FiLM：通用条件化层

> Perez, Strub, de Vries, Dumoulin, Courville，AAAI 2018；本地原件 arXiv:1709.07871。

## 一句话

条件输入经小网络产出逐特征仿射参数 (γ, β)，对主网络特征做 `γ·F+β` 调制；论文明确把拼接偏置、σ 限幅门控、条件归一化统一为 FiLM 的特例或近亲，并把 FiLM 归入超网络框架。

## 全文证据（物理页码）

- 第 2 页式 (1)：`γ_{i,c} = f_c(x_i)`，`β_{i,c} = h_c(x_i)`；式 (2)：`FiLM(F_{i,c}|γ_{i,c},β_{i,c}) = γ_{i,c} F_{i,c} + β_{i,c}`。
- 第 3 页 Related Work（逐字核对）：
  - 拼接条件特征图或向量「simply results in a feature-wise conditional bias」，「equivalent to FiLM with γ = 1」；
  - LSTM 门、SE 网络等门控「amounts to a feature-wise, conditional scaling, restricted to between 0 and 1, while FiLM consists of both scaling and shifting, each unrestricted」；
  - 「FiLM can be viewed as using one network to generate parameters of another network, making it a form of hypernetwork (Ha, Dai, and Le 2016)」。

## 与本课题的关系

第三章候选 M-E 的门 `γ_θ(s_e)=σ(MLP(s_e))∈(0,1)` 恰是本文第 3 页所述「受限于 (0,1) 的条件缩放」特例（γ 退化为标量、β≡0、仅作用于 PLE 位移支路）。M-E 的条件化**算子**因此无新颖性可主张；可主张的只剩条件变量构造（严格过去实体统计）与挂载位置（FT 数值分词器）。详见 [[../../../.Codex/docs/RWKV/2026-09-01-M-E方向文献调研/调研报告|2026-09-01 M-E 方向调研报告]]（过程文档）。

## 边界

- 实验域为视觉推理（CLEVR），无表格、流量或分布漂移设定；其结论用于分类学定位，不用于效果迁移。
