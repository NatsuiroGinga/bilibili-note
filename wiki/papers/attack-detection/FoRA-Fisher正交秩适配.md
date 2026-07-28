---
title: "FoRA: Fisher-orthogonal Rank Adaptation for Parameter-Efficient Fine-Tuning"
authors:
  - Juneyoung Park
  - Seongbae Lee
  - Han-Sang Lee
  - Kyuho Lee
  - Minjae Kim
  - Seungheon Hyeon
  - Kiduk Kwon
  - Seongwan Kim
  - Jaeho Lee
year: 2026
date: 2026-07-22
journal: EMNLP 2026
source_pdf: "[[raw/papers/attack-detection/2605.29317.pdf]]"
tags:
  - LoRA
  - PEFT
  - Fisher信息
  - Stiefel流形
  - 正交约束
  - 类型/论文
aliases:
  - FoRA
  - Fisher正交秩适配
key_finding: "FoRA 用对角 Fisher 分数选择少量任务相关层，再对选中层的 LoRA B 因子施加 Stiefel 约束；它常能用约半参数预算优于 LoRA，但跨模型表格存在 FoRA 不及普通 LoRA或纯 Stiefel 的反例，且 Cayley 更新增加约 10%--15% 单步时间。"
method: "对角 Fisher 选层、Stiefel 约束、Cayley 切空间更新与周期 QR 重正交"
baseline: "LoRA、DoRA、AdaLoRA、随机选层、仅 Fisher 选层、仅 Stiefel"
---

# FoRA：Fisher 正交秩适配

> 原始论文：[arXiv:2605.29317](https://arxiv.org/abs/2605.29317)，17 页。以下页码均指本地 PDF 页码。

## 研究问题

FoRA 将参数高效微调拆成两个问题：先判断哪些层值得适配，再避免选中层的低秩方向塌缩。它不是“减小每层秩”，而是减少插入适配器的层数。

### Fisher 选层

第 2--3 页定义层级 Fisher 分数：

\[
F_l=\frac{1}{N}\sum_{n=1}^{N}
\sum_{\theta\in\theta_l^{\mathrm{base}}}
\left\|\nabla_\theta\mathcal L(x_n,y_n)\right\|_2^2.
\]

作者用小校准集计算一次分数，选择前 \(K\) 层。该分数来自冻结基座的梯度，训练期间不再动态更新。

### 正交低秩因子

对选中层的 \(\Delta W=BA\)，约束

\[
B\in\mathrm{St}(d_{out},r),
\qquad B^\top B=I_r.
\]

第 3 页的引理给出 \(\sigma_i(BA)=\sigma_i(A)\)，因此列正交的 \(B\) 不会进一步压缩 \(A\) 已有的非零奇异值。第 3--4 页采用 Cayley 方向更新，并每隔 \(T_{qr}=200\) 步做一次 QR 重正交；固定点求解次数为 \(n_c=5\)。完整推导见第 13--14 页。

## 实验结果

### 半预算主结果

第 4 页表 1 中，FoRA 通常用约一半 LoRA 参数获得更高平均分：

| 主干         | LoRA 参数 / 平均分 | FoRA 参数 / 平均分 |
| ------------ | ------------------ | ------------------ |
| LLaMA-3.2-1B | 15.2M / 56.5       | 7.6M / 57.4        |
| LLaMA-3.2-3B | 33.0M / 63.0       | 16.5M / 64.0       |
| LLaMA-2-7B   | 56.1M / 63.1       | 28.0M / 67.2       |
| LLaMA-3.1-8B | 56.6M / 64.0       | 28.3M / 70.8       |
| LLaMA-2-13B  | 87.8M / 64.0       | 43.9M / 71.1       |

第 5 页表 2 的组件消融显示 Fisher 选层和 Stiefel 约束均有贡献。例如 LLaMA-3.1-8B 从 LoRA 的 64.00 提高到 Fisher 选层的 66.77、纯 Stiefel 的 67.92 和 FoRA 的 69.81；Qwen-3-8B 对应为 63.08、64.38、65.86、67.97。

第 6 页表 5 在匹配参数量的语言建模实验中，FoRA 的困惑度为 7.035，低于全层 LoRA 的 7.469、半秩 LoRA 的 7.346、随机选层的 7.279 和仅 Fisher 选层的 7.381。

### 几何与行为诊断

第 7 页表 6 显示，Stiefel 和 FoRA 的有效秩分别为 28.77 与 28.07，高于 LoRA 的 22.84；相对满秩比例分别为 0.90、0.88 与 0.71。需要同时看到，Stiefel/FoRA 的权重范数约 96/81，远高于 LoRA 的 9.2，但输出相对基座的 KL 散度反而更小。这支持“权重范数不能单独代表行为偏移”。

第 8 页验证对角 Fisher 近似：层内非对角项均值 0.0035、最大值 0.047，能量占比约 0.35%；对角 Fisher 与 K-FAC 的前 8 层 Jaccard 为 1.0。但真实 Fisher 与对角近似的困惑度仍有 8.35 对 8.47 的差异，近似并非无损。

## 负面和混合结果

- 第 6 页表 4 的量化结果并不一致：LLaMA-2-7B 上 QFoRA 的 MMLU 为 38.9，低于 QDoRA 的 39.9 和 QLoRA 的 41.0；LLaMA-3.1-8B 上才明显反转为 52.1、46.8、38.7。
- 第 12 页表 7 中，Gemma-3-270M 的 LoRA 平均分 53.16，高于 FoRA 的 52.85；Gemma-2-9B、Qwen-3-4B 和 LLaMA-2-13B 上，纯 Stiefel 分别为 81.29、72.30、77.49，也高于 FoRA 的 80.66、70.69、77.08。
- 小模型和激进剪层更不稳定。作者第 9 页明确承认，小模型减少适配层时容量损失更明显。
- 主表的最大模型结果多为单次运行；论文没有为所有模型报告多随机种子置信区间。

因此，“两组件超加性”不是跨架构的无条件结论。

## 成本与复现边界

- 第 8 页与第 14 页表 8：对角 Fisher 评分耗时 29.3 秒、峰值 14.9 GB；K-FAC 为 36.8 秒、21.2 GB；真实 Fisher 为 87.7 秒、15.4 GB。作者称校准低于总训练成本的 1%。
- 第 14 页表 9 在单张 H200 上报告：LoRA 峰值 15.32 GB、10,442 词元/秒、97.5 ms/步；只适配一半层的基础执行为 12.45 GB、15,210 词元/秒、67.1 ms/步。
- FoRA 的 Cayley 更新会在上述半层执行基础上增加约 10%--15% 单步墙钟时间。作者没有给出包含完整校准、Cayley 和周期 QR 的统一端到端总时长。
- 第 14 页给出的额外复杂度为

\[
O(d_{out}d_{in}r)+O(n_c d_{out}r^2)+O(d_{out}r^2/T_{qr}).
\]

- Fisher 排名是静态的；第 8--9 页承认它可能与下游分布变化失配，也不能跟踪训练过程中的重要层漂移。

## 对当前课题的映射

### 可以支持

- Fisher 分数可作为“在哪些层注入物理表征”的候选筛选器，但需在当前恶意流量数据与生成目标上重新计算。
- 正交低秩因子和有效秩诊断可用于小规模物理适配器实验。

### 不能支持

- 论文没有物理状态、恶意流量、PINN、物理投影或跨域无标签状态实验。
- 静态 Fisher 只反映校准集的任务梯度，不能证明选出的层就是物理信息最适合进入的层。
- FoRA 约束的是权重因子，不是样本条件的状态映射；把它解释为“物理流形投影”属于待验证的新机制。

## 结论

FoRA 为“少层适配 + 正交因子”提供了有成本数据的工程参考，但反例表明复杂组合并不总优于普通 LoRA 或纯 Stiefel。当前课题应先比较普通物理投影、仅 Fisher 选层、仅正交投影和二者组合，不能直接采用论文的总体平均优势作为机制成立证据。
