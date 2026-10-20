---
schema: paper-note-search/v1
title: "Prototypical Networks for Few-shot Learning"
title_zh: "原型网络：少样本学习的度量空间与类原型"
authors: [Jake Snell, Kevin Swersky, Richard S. Zemel]
year: 2017
date: 2026-10-20
journal: "Advances in Neural Information Processing Systems 30 (NeurIPS/NIPS 2017)；arXiv:1703.05175"
arxiv_id: "1703.05175"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "raw/papers/methodology/2017-Snell-Prototypical-Networks-Few-Shot.pdf"
tags:
  - 原型学习
  - 度量学习
  - 少样本学习
  - 回合训练
  - 类均值
  - 类型/论文
key_finding:
  - "类原型取支持集嵌入的**均值**（Eq. 1，物理第 2 页）；查询样本按到各类原型的距离做 softmax（Eq. 2，第 2 页）。"
  - "当距离为 Bregman 散度时，类均值是使类内距离和最小的最优聚类代表，原型网络等价于指数族混合密度估计（§2.3，第 3 页）。"
  - "平方欧氏距离下原型网络等价于一个**线性分类器**（§2.4，Eq. 7–8，第 4 页）；欧氏距离显著优于余弦（§2.6，第 4 页；Fig. 2/Table 5）。"
  - "回合训练（episode）按类采样支持集与查询集（Algorithm 1，第 2–3 页）；训练时的 way 可以高于测试（§2.6，第 4–5 页）。"
  - "miniImageNet 5-way：1-shot `49.42%`、5-shot `68.20%`（Table 2，第 6 页）；Omniglot 5-way 1-shot `98.8%`、5-shot `99.7%`（Table 1，第 5 页）。"
method: "学习嵌入 f_φ；类原型 c_k = 类内嵌入均值；p(y=k|x) = softmax(-d(f(x), c_k))；回合式训练最小化真类负对数似然"
baseline: "Matching Networks、Meta-Learner LSTM、Neural Statistician、最近邻基线"
metrics: [5-way/20-way few-shot accuracy, 1-shot/5-shot]
related:
  - "[[2020-Khosla-监督对比学习|SupCon：监督对比学习]]"
  - "[[2020-Kang-长尾解耦表示与分类器|Decoupling：NCM 与分类器再平衡]]"
  - "[[INDEX|方法论论文索引]]"
---

# 原型网络：少样本学习的度量空间与类原型

> **证据等级**：本地全文（MinerU `extract`，`raw/papers/methodology/2017-Snell-Prototypical-Networks-Few-Shot.pdf`）。
> 页码为 PDF 物理页（MinerU `page_idx + 1`），已对照章节与公式位置。

## 核心机制

1. **原型 = 类内嵌入均值**。对类 k 的支持集 \(S_k\)，
   \[
   \mathbf{c}_k=\frac{1}{|S_k|}\sum_{(\mathbf{x}_i,y_i)\in S_k} f_\phi(\mathbf{x}_i)
   \]
   （Eq. 1，物理第 2 页）。原型只需要一阶统计量，预测时不必保存整个支持集。
2. **按距离的 softmax 分类**：
   \[
   p_\phi(y=k\mid\mathbf{x})=\frac{\exp(-d(f_\phi(\mathbf{x}),\mathbf{c}_k))}{\sum_{k'}\exp(-d(f_\phi(\mathbf{x}),\mathbf{c}_{k'}))}
   \]
   （Eq. 2，第 2 页）。训练目标为真类负对数似然，SGD 更新嵌入参数。
3. **为什么均值是合理的**：对正则 Bregman 散度，类均值是给定类标签下最优的聚类代表；
   原型网络因此等价于以指数族分布做混合密度估计（§2.3，Eq. 3–6，第 3–4 页）。
   平方欧氏距离对应球高斯，且 Eq. 2 可展开为线性模型 \(\mathbf{w}_k^\top f(\mathbf{x})+b_k\)，
   其中 \(\mathbf{w}_k=2\mathbf{c}_k\)、\(b_k=-\mathbf{c}_k^\top\mathbf{c}_k\)（Eq. 7–8，第 4 页）。
4. **回合训练**：每个 episode 采样 \(N_C\) 个类、每类 \(N_S\) 个支持样本、\(N_Q\) 个查询样本
   （Algorithm 1，第 2–3 页）。训练 way 高于测试 way 往往更好；训练与测试的 shot 最好一致（§2.6，第 4–5 页）。
5. **距离选择**：余弦距离不是 Bregman 散度，破坏上述混合密度解释；实验中平方欧氏距离显著优于余弦
   （§2.6，第 4 页；Fig. 2，第 6 页；Table 5，第 11 页）。

## 与 PAAT M1（原型/对比表示）的可迁移点

- **损失结构可直接落为二分类形式**。PAAT 的
  \(\mathcal{L}_{\text{proto}}=\mathrm{CE}([\mathrm{sim}(z,\mu_+),\mathrm{sim}(z,\mu_-)]/\tau,y)\)
  就是 Eq. 2 在 \(K=2\)、以相似度替代负距离时的特例。ProtoNet 给出的理论支撑是：
  当嵌入空间与距离匹配时，类均值原型是一个有明确定义的聚类代表，而不是任意可学习的分类头。
- **投影头与原型的分工**：ProtoNet 直接在嵌入上取均值，没有独立投影头；PAAT 增加 \(g:\mathbb{R}^{128}\to\mathbb{R}^{64}\)
  相当于把「原型所在的度量空间」与编码器表示解耦。这可视为对 ProtoNet 的自然扩展，但**原论文没有验证投影头**，
  因此 PAAT 不能把投影头的收益归因于 ProtoNet。
- **回合构造的经验**：训练 way 高于测试 way、训练/测试 shot 一致这两条，对 PAAT 的「年度内正负各半回合」有参考价值：
  回合的类数与每类样本数会改变原型的估计方差，应在先导实验中固定并报告，而不是逐臂调参。
- **类均值对稀有类的高方差**：ProtoNet 默认支持集能代表类分布。PAAT 的 2024 年只有 `159` 个正例、
  2025 年只有 `5` 个正例（见 `thesis/methods/第四章-原型锚定年度训练算法（PAAT）方案.md`），
  类均值原型的标准误约为 \(\sigma/\sqrt{n_+}\)；\(n_+=5\) 时原型几乎由单个样本决定。
  这解释了为什么「零训练原型融合无独立增益」并不意外：**信息在表示中，但原型估计本身不稳定**。

## 不可迁移边界

- **任务设定不同**：ProtoNet 面向「训练类与测试类不相交」的 few-shot；PAAT 是同一二分类任务在年度漂移下的训练，
  测试类与训练类相同但分布变化。ProtoNet 没有刻画原型随时间的漂移，也没有「历史原型 EMA」的概念。
- **原型的时效性**：ProtoNet 的原型在每个 episode 内由当前支持集重算；PAAT 的**运行原型**是跨批次、跨年度的 EMA。
  EMA 会滞后于概念漂移，且没有理论保证历史原型仍代表当前年度分布。ProtoNet 不能为 EMA 原型提供依据。
- **距离与归一化**：原论文结论「欧氏优于余弦」依赖于 Bregman 散度与混合密度解释；
  PAAT 使用余弦相似度且表示已归一化，二者不可直接类比。若要引用「欧氏更好」，必须重新在 PAAT 表示上实测。
- **类别数**：ProtoNet 的实验是 5/20-way；二分类下 softmax 退化为 sigmoid/BCE 的等价形式，
  原型损失的独立作用会与 BCE 高度重叠，不能把多类 few-shot 的增益直接外推到二分类。
- **训练目标**：ProtoNet 只优化原型 NLL，没有 BCE 主损失；PAAT 是 \(\mathcal{L}_{BCE}+\lambda\mathcal{L}_{proto}\) 的联合目标，
  两项的梯度尺度与最优 \(\lambda\) 未被原论文覆盖。

## 关键公式与页码锚点

| 内容 | 位置 |
|---|---|
| 原型定义 Eq. (1) | §2.2，物理第 2 页 |
| 距离 softmax Eq. (2) | §2.2，物理第 2 页 |
| Bregman 散度与混合密度 Eq. (3)–(6) | §2.3，物理第 3–4 页 |
| 线性模型重解释 Eq. (7)–(8) | §2.4，物理第 4 页 |
| 设计选择（距离、way、shot） | §2.6，物理第 4–5 页 |
| 回合训练伪代码 Algorithm 1 | §2.2，物理第 2–3 页 |
| miniImageNet 结果 Table 2 | §3.2，物理第 6 页 |
| 欧氏 vs 余弦 Fig. 2 / Table 5 | 物理第 6、11 页 |

## 与相关工作

- 与 Matching Networks 的关系：1-shot 时二者等价；平方欧氏距离下 ProtoNet 是线性分类器（§2.5，第 4 页）。
- 与 NCM（nearest class mean）同源：ProtoNet 可看作 NCM 的非线性嵌入 + 回合训练版本。
  Decoupling 一文把 NCM 作为长尾分类的强基线，见 [[2020-Kang-长尾解耦表示与分类器|Decoupling]]。

## 原始摘要要点

> "We propose prototypical networks ... learn a metric space in which classification can be performed by computing
> distances to prototype representations of each class ... a simpler inductive bias that is beneficial in this limited-data regime."
