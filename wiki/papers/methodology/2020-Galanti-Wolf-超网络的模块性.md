---
title: "On the Modularity of Hypernetworks"
authors: [Tomer Galanti, Lior Wolf]
year: 2020
date: 2026-09-01
journal: "NeurIPS 2020；本地原件为 arXiv:2002.10006"
source_pdf: "[[raw/papers/methodology/2020-Galanti-Wolf-Modularity-of-Hypernetworks.pdf]]"
sha256: "3bc73488399c2a914ee7c9b96faaab3172e45db9e125a258eb6d16b647279c25"
arxiv_id: "2002.10006"
tags:
  - 超网络
  - 表达力理论
  - 参数复杂度
  - 条件化
  - 类型/论文
key_finding: "在 Sobolev 目标类上证明条件化方式的参数复杂度分离：任意网络类达到 ε 逼近的参数量下界 Ω(ε^{-m/r})（物理第 5 页 Theorem 1）；嵌入法 q(x, e(I)) 的主网络复杂度必须 Ω(ε^{-(m1+m2)})，随 x 维与条件维之和增长（物理第 6 页 Theorem 2，Theorem 3 推广到嵌入维依赖 ε）；而超网络可为每个条件实例提供复杂度 O(ε^{-m1/r}) 的独立逼近器，具备模块性。"
method: "泛函逼近论：N-width 下界、连续选择子构造；覆盖 sigmoid、tanh、clipped-ReLU 等激活"
aliases:
  - Galanti-Wolf2020
  - 超网络的模块性
  - Modularity of Hypernetworks
related:
  - "[[2016-Ha-超网络]]"
  - "[[2018-Perez-FiLM通用条件化层]]"
---

# 超网络的模块性：条件化方式之间的可证明分离

> Galanti, Wolf，NeurIPS 2020。这是「条件化表示」方向当前掌握的最硬理论工具。

## 全文证据（物理页码）

- 第 5 页 Theorem 1：激活 σ 分段 C¹ 且 σ′∈BV(R) 时，逼近 `W_{r,m}` 至误差 ε 的网络类参数量 `N_f = Ω(ε^{-m/r})`。
- 第 6 页 Theorem 2：神经嵌入法 `q(x, e(I))`（条件经编码后拼入主网络）在 `W_{1,m}` 上主网络复杂度 `Ω(ε^{-(m1+m2)})`——**与条件维 m2 挂钩，无法模块化**；Theorem 3 去掉嵌入输出维 O(1) 假设后结论仍非最优。
- 第 5–6 页第 4 节：超网络 `g(·; f(I))` 可为每个 I 达到 `O(ε^{-m1/r})` 的最优逐实例复杂度（模块性）。

## 与本课题的关系

回答「有没有理论更厚的同类形式」：**有**。若机制一坚持「实体统计条件化表示」方向，把 M-E 的标量门升级为低秩超网络（`s_e` 生成分词器位移向量组）可直接引用 Thm 1–3 作表达力论证，理论厚度远超 M-E 现有的零门退化＋算子计数。迁移代价：参数量升至数万–十万级（仍在预算内）；但**条件变量 `s_e` 的跨年漂移弱点原样继承**，且表达力定理不提供漂移稳健性保证——理论厚度与本课题主病灶（跨年泛化）不同轴。

## 边界

- 纯逼近论结果，无泛化界、无漂移设定；「更强表达力」在时间切分表格基准上反而常与更差迁移相关（见 [[2025-Rubachev-TabReD工业级时间切分表格基准]]）。
