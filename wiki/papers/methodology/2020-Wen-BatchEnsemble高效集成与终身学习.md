---
title: "BatchEnsemble: An Alternative Approach to Efficient Ensemble and Lifelong Learning"
authors: [Yeming Wen, Dustin Tran, Jimmy Ba]
year: 2020
date: 2026-10-20
journal: "ICLR 2020（arXiv:2002.06715v2）"
source_pdf: "[[raw/papers/methodology/2020-Wen-BatchEnsemble-EfficientEnsembling-LifelongLearning.pdf]]"
sha256: "9971405a14d7a23f7e12bbf748138536e1d1d941459a997109c12338be58256c"
arxiv_id: "2002.06715v2"
zotero_item_key: "Z76PRWPW"
tags:
  - 参数高效集成
  - 终身学习
  - 持续学习
  - BatchEnsemble
  - 成员分配
  - ICLR2020
  - 类型/论文
key_finding: "BatchEnsemble 用共享慢权重与成员专属秩一快权重的 Hadamard 积生成各成员权重；在终身学习中把每个任务绑定到一个成员，首个任务训练共享权重与第一组快权重，后续任务只训练本任务快权重，从而在 Split-CIFAR100（20 任务）与 Split-ImageNet（100 任务）上以无回放方式实现与渐进网络相当的精度，同时计算与内存开销显著更低（物理页 5 至 7，式 6 至 7，表 1）。"
method: "共享权重 W 与成员快权重 r_i s_i^T 的逐元素积生成成员权重；批内按成员切分子批并用式 (5) 向量化；终身学习阶段每任务只优化该任务的秩一快权重"
baseline: "Vanilla、EWC、渐进神经网络 PNN、DEN、RCL、BN-Tuned、逐任务独立 ResNet-50（上界）、朴素集成、MC-dropout（其他任务）"
aliases:
  - Wen2020-BatchEnsemble
  - BatchEnsemble
related:
  - "[[2025-Gorishniy-TabM参数高效集成]]"
  - "[[2016-Ha-超网络]]"
  - "[[2018-Perez-FiLM通用条件化层]]"
---

# BatchEnsemble：高效集成与终身学习的替代路线

> Wen、Tran、Ba，ICLR 2020，arXiv:2002.06715v2（2020-02-20），物理页 1 至 20。

## 一句话

BatchEnsemble 把每个集成成员的权重写成「所有成员共享的慢权重 × 成员专属秩一快权重」的 Hadamard 积；在终身学习设定下，**每个任务分配一个成员**，首个任务训练共享权重与第一组快权重，后续任务只训练本任务的快权重，因此无需回放缓冲即可在 100 个顺序任务上不遗忘。

## 原件与核验状态

- 题录核实：Zotero arXiv 导入返回标题、作者 `Wen, Yeming; Tran, Dustin; Ba, Jimmy`、日期 `2020-02-17`、`arXiv:2002.06715`（item key `Z76PRWPW`）。
- 会议状态核实：PDF 每页页眉为 `Published as a conference paper at ICLR 2020`，物理第 1 页起可见。
- 全文来源：Zotero 附件 PDF（本机路径 `/Users/bilibili/Zotero/storage/MYN6DVSJ/Wen 等 - 2020 - BatchEnsemble An Alternative Approach to Efficient Ensemble and Lifelong Learning.pdf`），已用 PDF 直读核对物理第 5 至 7 页。
- **仓库原件尚未落盘**：本次会话未提供 Bash 工具，无法把 PDF 复制进 `raw/papers/methodology/`、无法计算 SHA-256、无法运行 MinerU。`source_pdf` 指向的是待补的目标路径；**该文件当前不存在**。补做时需复制原件、计算哈希并回填本页 `sha256` 字段。

## 方法核心

### 1. 权重生成（物理第 4 页，式 1）

对第 \(i\) 个成员，

\[
W_i = W \circ F_i,\qquad F_i = r_i s_i^\top ,
\]

其中 \(W\) 为所有成员共享的慢权重，\(r_i\in\mathbb{R}^m\)、\(s_i\in\mathbb{R}^n\) 为成员专属的输入/输出尺度向量。每个成员每层只增加 \(m+n\) 个参数，而不是复制整块 \(m\times n\) 权重。

### 2. 批内并行（物理第 4 至 5 页，式 5）

把输入按成员切成 \(M\) 个子批，用矩阵 \(R,S\)（每行一个成员的 \(r_i,s_i\)）一次完成全部成员的前向：

\[
Y = \phi\big(((X\circ R)W)\circ S\big).
\]

测试时把输入重复 \(M\) 次，使 \(B\cdot M\) 个样本一次前向，再对各成员预测取平均（物理第 5 页「Ensembling During Testing」）。

### 3. 开销（物理第 5 页 §3.2）

- 额外计算只有 Hadamard 积；ResNet-32、集成规模 4 时参数量只多 **10%**，而朴素集成多 **3 倍**。
- 代价是若保持原 mini-batch，每成员只见到 \(1/M\) 的数据；可通过增大批大小或增加训练迭代补偿（物理第 8 页实验采用后者）。

## 终身学习：成员与任务的绑定（方向 B 的正源）

物理第 5 页 §3.3 给出明确定义：

- 设 \(T\) 个任务按顺序到达。任务 \(t\) 的预测使用
  \[
  W^t = W \circ (r_t s_t^\top),
  \]
  **「each ensemble member is in charge of one lifelong learning task」**——每个任务对应一个成员。
- 首个任务同时训练共享权重与第一组快权重（式 6，物理第 5 页）：
  \[
  \min_{W,s_1,r_1} L_1(W,s_1,r_1;D_1).
  \]
- 后续任务只训练本任务的快权重（式 7，物理第 5 页）：
  \[
  \min_{s_t,r_t} L_t(s_t,r_t;D_t).
  \]
- 共享权重 \(W\) 只在第一个任务上训练；后续任务不再更新。因此旧任务模型逐位不变，**构造上完全防止灾难性遗忘**，也不需要保存任何旧任务数据（第 5 至 6 页）。
- 测试时按任务描述符选用对应成员 \(W^t\)；「对所有已见任务的平均性能」是**评价指标**，不是跨成员集成平均（第 5 页）。

### 作者自述的边界（物理第 6 页「Limitations」）

1. 每个终身任务只拟合**秩一扰动**，任务差异大时表达能力是真实担忧。
2. 共享权重只在首个任务上训练，**只有第一任务的知识能显式迁移到后续任务**；第二与第三任务之间没有显式迁移。作者建议可加 PNN 式侧连接，但在 Split-CIFAR100/Split-ImageNet 上未用到，留作未来工作。

## 实验结果

### 终身学习（物理第 6 至 7 页，图 3，表 1）

- Split-CIFAR100：\(T=20\)，ResNet-18（略减滤波器），**每个任务一个不同的最终全连接层**（利用任务描述符）；与 PNN 精度相当，**4 倍加速、50 倍内存节省**，并保持 PNN 的无遗忘性质。
- Split-ImageNet：\(T=100\)，ResNet-50 + 每任务一个最终线性分类器；参数开销 **20%**（30M 对 25M），在逐任务验证精度上稳定优于同参数量的 BN-Tuned；PNN 因内存无法扩展到 100 任务。
- 表 1（物理第 6 页，相对 vanilla，LeNet / Split-CIFAR100）：

  | 方法 | 计算 | 内存 |
  | --- | --- | --- |
  | Vanilla | 1 | 1 |
  | BatchEnsemble | 1.11 | 1.10 |
  | DEN | 9.58 | 5.31 |
  | PNN | 1.12 | 4.16 |
  | RCL | 26.41 | 2.52 |

### 多样性分析（物理第 10 页 §5；附录 E，物理第 17 至 18 页）

- 用成员预测不一致率度量多样性。训练数据受限时，BatchEnsemble 的成员多样性与独立初始化的朴素集成**相当**，明显高于 dropout 集成。
- 论文把「CIFAR-100 增益大于 CIFAR-10」归因于每类训练样本数（500 对 5000）：**数据越少，秩一快权重带来的伪独立初始化越接近真正的独立初始化**。
- 附录 B（物理第 15 页）：快权重初始化为随机符号向量即可获得足够多样性，无需显式多样性损失；各成员训练不同子批也有助于多样性。

## 与 TabM 的关系

- TabM（Gorishniy 等，ICLR 2025）是 BatchEnsemble 思想在表格 MLP 上的特化：线性层同样使用共享主权重与成员专属适配参数，训练各成员损失均值，推理平均成员概率。
- 差别：TabM 的成员适配参数**不绑定任务**，全部成员在所有数据上共享训练批次（或各自子批）；BatchEnsemble 的终身学习用法**把成员固定分配给任务**，且后续任务不再更新共享权重。
- 因此 TabM4 的 `k=4` 是预算内的并行集成，**不能**直接当作「4 个年度锚定成员」；要落到方向 B，需要重新定义成员—年度绑定与推理时的年度选择规则。

## 对两个候选方向的可迁移点

### 方向 B（成员-年度锚定）

可迁移：

1. **「一任务一成员」的参数化正源**：成员不是独立网络，而是共享慢权重上的秩一快权重；年度数 12 时，成员参数开销为每层 \(12(m+n)\)，而不是 12 份权重。
2. **无回放的构造性无遗忘**：旧年度成员冻结即可，不需要在训练新年度时回放旧年度数据——这比本课题当前依赖回放缓冲的方案更强，但前提是推理时能拿到年度描述符。
3. **任务描述符接口**：原论文用「每任务一个最终分类层」处理不同类集合；LAMDA 的年度是**同一二分类标签空间**的分布漂移，不能照搬「每任务一个分类头」。

必须注意的边界：

1. **年度描述符在推理时是否可得**：BatchEnsemble 的终身学习测试需要任务标签 \(t\) 来选成员；LAMDA 的 Domain-IL 测试年度若可用（按年度切分评测），方向 B 可行；若要求无年度标识的连续流推理，需要额外的年度路由器，原论文不提供。
2. **共享权重只训练首年**：作者明确说只有第一任务知识能迁移。LAMDA 的年度漂移若需要后续年度互相迁移，必须改成共享权重的持续更新或加侧连接，这不是原文做法。
3. **秩一表达力**：作者自述任务差异大时秩一扰动可能不足；LAMDA 的年度分布差异（已测得 \(p(x\mid y)\) 漂移 33.5× 采样噪声）是否超出秩一容量，需实验判定。
4. **成员数等于任务数**：原论文成员数随任务数增长（20/100），没有「固定 k 个成员覆盖 12 年」的实验；若固定 k=4 做年度组锚定，属于任务适配，不是原文验证过的设定。

### 方向 A（缺口加权集成容量调度）

- 原文的可迁移证据是**数据量—多样性—增益**三者关系：训练数据越少，秩一成员越接近独立初始化，集成增益越大（第 10 页、附录 E）。这支持「稀缺年度更值得投入成员容量」的方向性假设。
- **但不能直接支持「按正例稀缺度动态调制成员数/噪声」**：原文的稀缺是**总训练样本数**，不是类别不平衡中的正例数；集成规模 \(M\) 在所有实验中固定（分类与翻译为 4，终身学习等于任务数），没有随数据量调整；也没有成员噪声调度（快权重初始化固定为随机符号）。
- 因此方向 A 若引用本文，只能作为「稀缺→多样性收益更高」的机制线索，不能声称原文实现了自适应容量。

## 疑问 / 待验证

- 在二分类、同一标签空间、按年度 Domain-IL 的设定下，秩一成员能否承载 12 个年度的分布差异？需要与 TabM4 同预算的对照实验。
- 年度描述符不可得时，能否用无标签年度推断（如回放缓冲的年度分块统计）替代？这会把方向 B 变成「成员-年度路由」问题，需另找路由文献。
- 固定 \(k<12\) 的年度组锚定（如 4 个成员各覆盖 3 年）与 \(k=12\) 的一年一成员，在相同参数预算下哪个更优？原文无此消融。

## 原始摘要

> Ensembles, where multiple neural networks are trained individually and their predictions are averaged, have been shown to be widely successful for improving both the accuracy and predictive uncertainty of single neural networks. However, an ensemble's cost for both training and testing increases linearly with the number of networks, which quickly becomes untenable. In this paper, we propose BatchEnsemble, an ensemble method whose computational and memory costs are significantly lower than typical ensembles. BatchEnsemble achieves this by defining each weight matrix to be the Hadamard product of a shared weight among all ensemble members and a rank-one matrix per member. Unlike ensembles, BatchEnsemble is not only parallelizable across devices, where one device trains one member, but also parallelizable within a device, where multiple ensemble members are updated simultaneously for a given mini-batch. Across CIFAR-10, CIFAR-100, WMT14 EN-DE/EN-FR translation, and out-of-distribution tasks, BatchEnsemble yields competitive accuracy and uncertainties as typical ensembles; the speedup at test time is 3X and memory reduction is 3X at an ensemble of size 4. We also apply BatchEnsemble to lifelong learning, where on Split-CIFAR-100, BatchEnsemble yields comparable performance to progressive neural networks while having a much lower computational and memory costs. We further show that BatchEnsemble can easily scale up to lifelong learning on Split-ImageNet which involves 100 sequential learning tasks.

## 文献信息

- arXiv：<https://arxiv.org/abs/2002.06715>（v2，2020-02-20）
- 会议：ICLR 2020（PDF 页眉）
- 官方代码：<https://github.com/google/edward2>
- Zotero item key：`Z76PRWPW`
- BibTeX 键：`Wen2020_Z76PRWPW`

## 证据等级

- 题录：Zotero arXiv 导入（API 路径）核实标题、作者、日期、arXiv ID。
- 会议状态：PDF 页眉直读核实。
- 全文：Zotero 附件 PDF 全文提取 + 物理第 5 至 7 页直读核对；公式、表 1、终身学习协议与作者自述边界均回到页码。
- 仓库原件与 SHA-256：**未完成**（无 Bash 工具）。
- 可支撑：BatchEnsemble 的权重参数化、终身学习成员分配、Split-CIFAR100/ImageNet 结果、作者自述边界、多样性—数据量分析。
- 不可支撑：任何 LAMDA 年度协议下的效果、固定 \(k\) 年度组锚定的优劣、年度描述符不可得时的路由行为。
