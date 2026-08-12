---
title: "线性 Transformer 是快速权重编程器：DeltaNet 原始状态更新"
authors:
  - Imanol Schlag
  - Kazuki Irie
  - Jürgen Schmidhuber
year: 2021
date: 2026-08-11
venue: "ICML 2021；PMLR 139:9355–9366"
arxiv: "2102.11174"
source_pdf: "[[raw/papers/rwkv/2021-Schlag-Fast-Weight-Programmers-DeltaNet.pdf]]"
tags:
  - DeltaNet
  - 快速权重
  - Delta规则
  - 原始论文
key_finding: "这是线性序列模型中 DeltaNet 更新的原始论文：公式（20）—（24）先读取当前键的旧值，再以动态写入强度插值并执行显式移除／写入；C12 的方向性状态校正并非新机制。"
---

# 线性 Transformer 是快速权重编程器

## 一句话

这篇 ICML 2021 论文而非 2024 年并行化工作，是现代 DeltaNet 状态更新的原始来源；其动态学习率、旧值移除和新值写入已经覆盖 C12 当前状态核的核心结构。

## 证据层级

- **全文证据**：PMLR 正式全文 12 页＋官方补充材料 4 页。
- **官方源码证据**：作者官方仓库，固定提交 `ebe13ea2e6409da91d12d22175f4f6efe8bf2f0a`。
- **历史来源边界**：论文明确说明其受 Widrow 与 Hoff（1960）的误差校正 Delta 规则启发；本文的贡献是把该规则变成端到端可学习的快速权重序列更新，而不是发明 Delta 规则本身。

## 原始机制

- PDF 第 4 页 §4.2 公式（20）先以 `v̄^(i)=W^(i-1)φ(k^(i))` 读取旧关联；公式（21）由当前输入产生动态 `β^(i)=σ(W_βx^(i))`；公式（22）在新值与旧值之间插值。
- 同页公式（23）显式写成 `W^(i)=W^(i-1)+v_new⊗φ(k)-v̄⊗φ(k)`，标注为 write／remove；公式（24）化简为 `W^(i)=W^(i-1)+β^(i)(v^(i)-v̄^(i))⊗φ(k^(i))`。
- 同页正文明确称这是带动态学习率的 Delta 规则，用于修正当前键值关联。补充材料第 1 页公式（38）—（40）给出从移除／写入到误差修正形式的完整推导。
- 论文实验是合成检索、机器翻译和语言建模；没有异常污染、概念漂移或跨年度网络流量证据。

## 官方源码核验

- `synthetic/linearAttention.py` 第 270—288 行实现作者的更新规则：第 283 行读取旧值，第 284 行移除旧关联，第 286 行计算带 `β` 的新旧值插值，第 287 行写入新关联。
- 源码还包含另一种快速权重更新变体；C12 比较时应引用论文定义的 `ours` 分支，不能只依据仓库注释给变体归因。

## C12 原创边界

### 已被占用

- 从固定维状态中读取当前方向的旧值、计算预测残差并沿同一方向改写。
- 显式的 remove／write 两步解释。
- 由当前表示产生动态学习率／写入强度。
- 把状态视为在线可编程快速权重。

### 可借鉴机制

- 以“读出旧正常原型—计算受信目标残差—有界写回”替代无语义的矩阵外积命名，便于定义污染影响和回退条件。
- C12 若保留分子／有效质量状态，可把其解释为受权正常充分统计量；但必须与本文的快速权重 Delta、普通指数移动平均和 CANDI 参考库在同预算下区分。

### 必须避免的换名

- “可信 Delta”“漂移 Delta”“正常 Delta”若只改变 `β` 的输入或 `v` 的语义，仍是本文公式（24）的任务化实例。
- “停止梯度门”不改变前向状态递推；它是训练估计策略，不能把既有前向公式变成新机制。

## 最小区分实验

- 同状态维度实现原始 DeltaNet，`β` 由隐藏表示产生；然后依次加入三信号可信权重、有效质量归一化、漂移控制影响预算／回退。
- 报告每步状态变化范数、异常注入的累计影响、高漂移正常样本被拒率及回退后恢复时间；仅主任务分数不足以证明机制差异。

## 证据记录

- 主文：`raw/papers/rwkv/2021-Schlag-Fast-Weight-Programmers-DeltaNet.pdf`，12 页，SHA-256 `207db79c22d7d063e6f81df614050d96a33172a631c7b2df7e75308b74f78f38`。
- 补充材料：`raw/papers/rwkv/2021-Schlag-Fast-Weight-Programmers-DeltaNet-supplement.pdf`，4 页，SHA-256 `ec04c07aeafade9064f82936688c4b9270df0efeabb39722a63a12e372ddc25b`。
- 正式页面：https://proceedings.mlr.press/v139/schlag21a.html 。
- 官方源码：https://github.com/ischlag/fast-weight-transformers/tree/ebe13ea2e6409da91d12d22175f4f6efe8bf2f0a 。

