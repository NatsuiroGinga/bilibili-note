---
schema: paper-note-search/v1
title: "Supervised Contrastive Learning"
title_zh: "监督对比学习：多正例对比损失"
authors: [Prannay Khosla, Piotr Teterwak, Chen Wang, Aaron Sarna, Yonglong Tian, Phillip Isola, Aaron Maschinot, Ce Liu, Dilip Krishnan]
year: 2020
date: 2026-10-20
journal: "Advances in Neural Information Processing Systems 33 (NeurIPS 2020)；arXiv:2004.11362"
arxiv_id: "2004.11362"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2020-Khosla-Supervised-Contrastive-Learning.pdf"
tags:
  - 监督对比学习
  - 表示学习
  - 多正例
  - 温度参数
  - 投影头
  - 类型/论文
key_finding:
  - "把自监督对比学习扩展为**监督版本**：同一类别的所有样本都作为正例，而不是只把同一图像的两个增广视图作为正例（Eq. 2，物理第 5 页）。"
  - '两种多正例写法中，**正例求和放在 log 外**的 \(\mathcal{L}_{out}^{sup}\) 明显更好：ImageNet ResNet-50 上 `78.7%` vs `67.4%`（Table 1，第 5 页）。'
  - "梯度结构天然实现**难正例/难负例挖掘**，无需显式 hard mining（§3.2.2，第 5 页；补充材料 §7，第 15 页）。"
  - "ImageNet ResNet-50 `78.7%`、ResNet-200 `81.4%`，分别高于交叉熵 `78.2%` 与 `80.6%`（Table 3，第 6 页）；CIFAR-10 `96.0` vs `95.0`、CIFAR-100 `76.5` vs `75.3`（Table 2，第 6 页）。"
  - "采用**两阶段训练**：先对比预训练编码器，丢弃投影头，再在冻结表示上训练线性分类器（§3、§4.5，第 4、9 页）。"
method: "双视图 batch（2N）；编码器输出 L2 归一化表示 r，投影头输出 z；SupCon 损失在 z 上计算；推理时丢弃投影头，冻结表示训练线性分类器"
baseline: "交叉熵、SimCLR、Max-Margin、N-pairs loss"
metrics: [ImageNet top-1/top-5, CIFAR top-1, ImageNet-C mCE, transfer mAP/accuracy]
related:
  - "[[2017-Snell-原型网络少样本学习|ProtoNet：类均值原型]]"
  - "[[2020-Kang-长尾解耦表示与分类器|Decoupling：表示与分类器分离]]"
  - "[[INDEX|方法论论文索引]]"
---

# 监督对比学习：多正例对比损失

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2020-Khosla-Supervised-Contrastive-Learning.pdf`）。
> 页码为 PDF 物理页；补充材料页码单独标注。

## 核心机制

1. **框架**（§3.1，物理第 4 页）：对每个 batch 做两次随机增广，得到 \(2N\) 个视图；
   编码器 \(Enc(\cdot)\) 输出 \(D_E=2048\) 维表示并做单位球归一化；
   投影头 \(Proj(\cdot)\) 输出 \(D_P=128\) 维、再次归一化。对比损失只作用在投影输出 \(z\) 上。
2. **自监督损失**（Eq. 1，第 4–5 页）：每个 anchor 只有 1 个正例（同一图像的另一视图），
   分母包含 \(2N-2\) 个负例。
3. **监督损失**（Eq. 2–3，第 5 页）：正例集合 \(P(i)\) 为同一标签的所有其他样本（包括同图像的另一视图），
   \[
   \mathcal{L}_{out}^{sup}=\sum_i \frac{-1}{|P(i)|}\sum_{p\in P(i)}
   \log\frac{\exp(z_i\cdot z_p/\tau)}{\sum_{a\in A(i)}\exp(z_i\cdot z_a/\tau)}
   \]
   另一种写法把正例求和放进 log（\(\mathcal{L}_{in}^{sup}\)）。二者不等价；
   因 log 为凹函数，\(\mathcal{L}_{in}^{sup}\le\mathcal{L}_{out}^{sup}\)，
   但实验与梯度分析都支持 \(\mathcal{L}_{out}^{sup}\)：正例归一化因子放在 log 外才能消除正例偏差
   （Eq. 4–6，第 5–6 页）。
4. **隐式难例挖掘**：对归一化表示，难正例/难负例的梯度贡献大，易例贡献小；
   负例越多，难正例的效应越强（§3.2.2，第 5 页；补充材料 §7，第 15–17 页）。
5. **两阶段训练**（§3，第 4 页；§4.5，第 9 页）：先做对比预训练（ResNet-200 700 epochs，较小模型 350 epochs），
   丢弃投影头；再用交叉熵训练线性分类器（约 10 epochs）。推理模型参数量与同编码器的交叉熵模型相同。

## 实验结果（本地全文核验）

| 设置 | 交叉熵 | SupCon | 位置 |
|---|---:|---:|---|
| ImageNet, ResNet-50, AutoAugment | `78.2` | `78.7` | Table 2/3，第 6 页 |
| ImageNet, ResNet-200, Stacked RandAugment | `80.6` | `81.4` | Table 3，第 6 页 |
| CIFAR-10, ResNet-50 | `95.0` | `96.0` | Table 2，第 6 页 |
| CIFAR-100, ResNet-50 | `75.3` | `76.5` | Table 2，第 6 页 |
| ImageNet-C mCE, ResNet-50（越低越好） | `68.6` | `67.2` | 第 7 页表格 |
| ImageNet-C mCE, ResNet-200（越低越好） | `52.4` | `50.6` | 第 7 页表格 |

- 超参：\(\tau=0.1\)；batch size 最大 6144（ResNet-50）/4096（ResNet-200）；对温度做损失缩放以保证稳定（§4.5，第 9 页）。
- 迁移学习：SupCon 与交叉熵、SimCLR 在 12 个下游数据集上**大体持平**（Table 4，第 8 页），
  说明增益主要来自同分布分类，不应把 SupCon 当作普适的迁移学习提升手段。

## 与 PAAT M1（原型/对比表示）的可迁移点

- **二分类的直接映射**：PAAT 的类别只有正/负两类。SupCon 在 \(K=2\) 时，
  每个 anchor 的正例是 batch 内同标签样本，负例是另一类样本；这与 PAAT「在回放缓冲的历史正负例上学习」语义一致，
  且比 ProtoNet 的类均值损失更强地约束**类内紧凑性**（ProtoNet 只约束到类均值的距离）。
- **投影头设计有直接依据**：SupCon 明确使用 \(2048\to128\) 的投影头并在推理时丢弃；
  PAAT 的 \(128\to64\) 投影头与此同构。可迁移的经验是：**投影头只服务表示学习，不应进入最终分类器**。
- **正则化与温度**：单位球归一化 + 温度 \(\tau\) 是稳定训练的关键；PAAT 若用余弦相似度，应显式固定 \(\tau\) 并做损失缩放，
  避免温度过小导致数值不稳（§4.5，第 9 页）。
- **两阶段 vs 联合训练**：SupCon 的两阶段（对比预训练 → 冻结表示训练分类器）为 PAAT 提供了一个可对照的实验臂：
  `L = L_BCE + λL_proto` 的联合训练是否优于「先 M1 预训练、后 BCE 微调」，原论文不能回答，但给出了两阶段是可用的强基线。
- **隐式难例挖掘**：对 PAAT 的稀有正例，SupCon 的梯度结构会自动放大「与正类原型不一致的正例」的贡献；
  这可能缓解「正例被负例淹没」的问题，但也会放大标注噪声与年度漂移造成的假正例。

## 不可迁移边界

- **需要大量正例与大批量**：SupCon 的增益依赖每个 anchor 有多个正例（batch 内平均 \(N/C\) 个）。
  PAAT 的 2024 年只有 `159` 个正例；若平衡回合中正例有放回重复，batch 内 512 个「正例」实际只对应约 159 个不同样本，
  对比损失会把重复样本当作独立正例，**夸大类内一致性**，并可能过拟合。原论文没有覆盖「正例大量重复」的设定。
- **双视图增广假设**：SupCon 需要标签保持的增广来构造同一图像的两个视图；PAAT 的 Android 行为特征/表格特征
  不一定存在语义保持的增广。若用 dropout 或噪声视图替代，分布与图像增广不同，不能直接引用其结论。
- **类别条件稳定假设**：SupCon 把「同标签」视为「同分布」。年度漂移下同标签样本的边际分布已变化，
  跨年正例可能并不同质；把所有同标签样本等权拉近，可能把历史概念与当前概念强行对齐。
- **类别数**：SupCon 的收益在 10/100/1000 类上验证；二分类下 softmax 竞争被压缩为两类竞争，
  对比损失与 BCE 的重叠更大，原论文没有二分类消融。
- **两阶段与漂移**：SupCon 假设预训练数据与下游数据同分布；PAAT 的年度训练要求表示持续更新，
  冻结表示再训练分类器的做法与「年度持续学习」不完全兼容。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| 框架（双视图、编码器、投影头、归一化） | §3.1，物理第 4 页 |
| 自监督对比损失 Eq. (1) | §3.2.1，物理第 4–5 页 |
| 两种监督对比损失 Eq. (2)–(3) | §3.2.2，物理第 5 页 |
| 梯度与正例归一化 Eq. (4)–(6) | §3.2.2，物理第 5–6 页 |
| 与 triplet / N-pairs 的关系 | §3.2.3，物理第 6 页 |
| ImageNet / CIFAR 结果 Table 2–3 | §4.1，物理第 6 页 |
| 鲁棒性 ImageNet-C | §4.2，物理第 7 页 |
| 迁移学习 Table 4 | §4.4，物理第 8 页 |
| 训练细节（\(\tau=0.1\)、batch、epochs） | §4.5，物理第 9 页 |
| 梯度推导 / 难例挖掘 / 温度消融 | 补充材料 §6–§10，物理第 13–19 页 |

## 与相关工作的关系

- 与 ProtoNet：ProtoNet 用类均值作为唯一原型，SupCon 用成对对比拉近所有同类样本；前者是「到均值的距离」，后者是「同类两两距离」。
- 与 Decoupling：SupCon 的两阶段训练与 Decoupling 的「表示/分类器解耦」同构；Decoupling 进一步指出，长尾下表示学习本身可能不需要平衡采样。
  见 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]。

## 原始摘要要点

> "We extend the self-supervised batch contrastive approach to the fully-supervised setting ... Clusters of points belonging
> to the same class are pulled together ... while simultaneously pushing apart clusters of samples from different classes."
