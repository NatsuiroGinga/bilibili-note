---
title: "门控 DeltaNet：以门控遗忘结合 Delta 规则"
authors:
  - Songlin Yang
  - Jan Kautz
  - Ali Hatamizadeh
year: 2025
date: 2026-08-11
venue: "ICLR 2025"
openreview: "r8H7xhYPwz"
arxiv: "2412.06464"
source_pdf: "[[raw/papers/rwkv/2025-Yang-Gated-DeltaNet.pdf]]"
tags:
  - GatedDeltaNet
  - Delta规则
  - 动态遗忘
  - 状态更新
key_finding: "公式（10）已把数据依赖全局遗忘门与 Delta 定向改写结合；因此 C12 不能把‘漂移驱动遗忘＋Delta 更新’本身当作原创，只能检验异常检测中的因果控制约束、可信有效质量状态和污染影响上限。"
---

# 门控 DeltaNet

## 一句话

门控 DeltaNet 已把自适应遗忘和 Delta 定向更新组合成统一状态规则；C12 若只是用漂移量产生遗忘／写入率，本质上是改变门的输入语义，不构成新的状态演化机制。

## 证据层级

- **全文证据**：ICLR 2025 正式全文，21 页。
- **官方源码证据**：作者标注的 NVIDIA 官方仓库，固定提交 `b53d6d3a161267432a79c1c04af69fa52bddc921`。
- **摘要证据**：摘要只支持门控用于快速遗忘、Delta 用于定向更新以及语言任务结果；不支持跨年度异常检测或污染鲁棒性。

## 方法与公式

- PDF 第 3 页 §2.2 重述标准 DeltaNet：`S_t=S_{t-1}(I-β_tk_tk_t^T)+β_tv_tk_t^T`。
- PDF 第 4 页公式（10）提出门控 Delta 规则：`S_t=S_{t-1}[α_t(I-β_tk_tk_t^T)]+β_tv_tk_t^T`，其中数据依赖标量 `α_t∈(0,1)` 控制整体状态衰减，`β_t` 控制定向改写。
- PDF 第 5 页表 1 把该式解释为带自适应权重衰减的在线更新；同页表 2 和 §3.2 的证据来自合成检索任务，展示遗忘与保留的权衡，不能外推为伪正常污染鲁棒性。
- PDF 第 6 页说明 `q/k/v` 由投影、短卷积和激活得到，`α/β` 由线性投影产生；因此“让可观测漂移进入 `α/β`”仍落在数据依赖门参数化的既有空间。

## 官方源码核验

- `lit_gpt/gated_delta_net.py` 第 147—165 行分别生成 `q/k/v`、对数衰减 `gk` 和 `β`；第 172—190 行归一化键并调用门控 Delta 算子。
- `lit_gpt/gated_delta_rule_ops/chunk.py` 第 688—711 行是循环参考实现：第 705 行先以 `exp(g_t)` 衰减状态，第 707—709 行计算预测残差、乘 `β_t` 并写回。这与论文公式（10）一致。

## C12 原创边界

### 已被占用

- 在 Delta 状态上增加数据依赖全局遗忘门。
- 用遗忘门做快速记忆清除、用 Delta 做定向替换的功能分工。
- 将状态看作测试时快速权重，并以输入生成更新率。

### 可借鉴但必须改造

- 可借鉴“遗忘与定向改写互补”的对照结构，但 C12 应把漂移量用于**约束更新行为**而不只是生成 `α_t`：例如限定每步校正影响、在可信有效质量不足时冻结／回退、在源正常与新正常参照冲突时切换写入目标。
- 若采用全局 `α_t`，必须与 RWKV-7 的逐通道衰减、标准 Gated DeltaNet、仅末端漂移特征三者同预算比较；不能仅通过换名声称“漂移感知状态演化”。

## 最小区分实验

- 强基线：官方门控 Delta 规则的同骨干实现，`α_t/β_t` 均由当前隐藏表示产生。
- 最小机制互换：隐藏表示门 vs. 漂移标量门；漂移末端拼接 vs. 漂移控制门；漂移控制门 vs. 漂移控制影响预算／回退。
- 诊断指标除主任务外必须包含高漂移正常样本召回、异常污染注入后的状态偏移范数、冻结／回退触发率和有效质量分母下界。

## 证据记录

- 原件：`raw/papers/rwkv/2025-Yang-Gated-DeltaNet.pdf`。
- 页数：21。
- SHA-256：`38f2a9588b90c28bb40c9565556f05e1d894c3cc9c4ca115f11dd73cb57db71d`。
- 正式页面：https://proceedings.iclr.cc/paper_files/paper/2025/hash/4904fad153f6434a7bcf04465d4be2cc-Abstract-Conference.html 。
- 官方源码：https://github.com/NVlabs/GatedDeltaNet/tree/b53d6d3a161267432a79c1c04af69fa52bddc921 。

