---
schema: paper-note-search/v1
title: "MORPH: Towards Automated Concept Drift Adaptation for Malware Detection"
title_zh: "MORPH：面向恶意软件检测的自动化概念漂移适应"
authors: [Md Tanvirul Alam, Romy Fieblinger, Ashim Mahara, Nidhi Rastogi]
year: 2024
date: 2026-10-14
journal: "arXiv 2401.12790（预印本；取得版本为 arXiv 预印本，正式出处未在全文内页核到）"
doi: null
arxiv_id: "2401.12790"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2024-Alam-MORPH-Automated-Concept-Drift-Adaptation.pdf]]"
tags:
  - Android恶意软件
  - Windows恶意软件
  - 概念漂移
  - 伪标签
  - 自训练
  - 主动学习
  - 类型/论文
tasks: [Android恶意软件二分类, Windows PE 二分类, 概念漂移适应]
datasets: [AndroZoo, EMBER]
methods: [伪标签自训练, 类不对称阈值样本选择, 半监督损失]
metrics: [F1, FPR, FNR]
key_finding:
  - "MORPH 用类不对称伪标签选择（恶意样本放宽、良性样本从严）在神经网络上做自训练，用无新标注的伪标签替代一半主动学习更新。"
  - "它是 ADAPT 的前身，两篇共享同一作者组与同一『漂移主要打击恶意类』的动机假设，但 MORPH 无置信度校准、无 mixup，FPR 在训练家族受限时明显上升。"
method: "每月伪标签自训练；对预测为恶意的样本随机取低置信样本（> τ_m），对预测为良性的样本取最高置信样本（> τ_b）；半监督损失 L = L_s + λ·L_u（λ=1）"
baseline: "Static MLP、DroidEvolver/DroidEvolver++、Chen et al. 主动学习(HCC/Hi-Enc)"
aliases:
  - MORPH
  - Alam2024-MORPH
related:
  - "[[2025-Alam-ADAPT伪标签抗概念漂移]]"
  - "[[2023-Chen-Android恶意软件持续学习]]"
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
---

# MORPH：自动化概念漂移适应（伪标签自训练）

> 页码锚点：标题与摘要位于 PDF 物理第 1 页；本文其余引用按 MinerU 保留的章节号（§1–§8）给出。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2024-Alam-MORPH-Automated-Concept-Drift-Adaptation.pdf`）。取得版本为 arXiv 2401.12790 预印本，正式发表版可能与之有差异。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | AndroZoo（Chen et al. 2019–2021 子集，16,978 维）+ EMBER（Windows PE，2017–2018）；**未使用 LAMDA** |
| 特征表示 | 稀疏二值特征向量（AndroZoo API 使用 16,978 维；EMBER 2,381 维，StandardScaler 标准化） |
| 平台 | Android + Windows |
| 监督设定 | 半监督自训练：初始标注集 + 每月伪标签，**不新增人工标注**（§4.1、§6.1）；RQ2 中另与主动学习组合，每月 100 样本标注，替换一半主动更新（§6.3） |
| 是否有固定 FPR 工作点 | **无**。逐月报告 F1/FPR/FNR 曲线，未设固定 FPR 运行点 |
| 评价指标 | F1、FPR、FNR |
| 报告的主结果数字 | §6.2：平均 F1 提升 +4.07%（AndroZoo）/ +0.83%（EMBER），FNR 降低 14.78% / 5.74%；§6.3：主动学习 100 预算下 MORPH 再提 F1 +3.46%；§6.4：与 DE++ 比较平均 F1 53.8% vs 23.3% |
| 与 LAMDA 本课题的关系 | **部件来源**（类不对称伪标签阈值选样，可作 C1 伪标签门的候选部件）+ **仅对照**（无 LAMDA 结果） |

## 一、论文原结论（带章节号）

- **方法与机制**（§4.1、§4.2）：每月在无标注测试数据上生成伪标签并按类不对称阈值选样——对预测为恶意的样本随机取低置信样本（阈值 `τ_m`，较小），以纳入漂移样本；对预测为良性的样本取最高置信样本（阈值 `τ_b`，较大甚至省略），以避免误纳。样本选择动机来自 Figure 4 的核密度估计：恶意真阳的概率分布比良性真阴更宽，漂移恶意样本更宽，因此「低置信的恶意预测仍可能正确、低置信的良性预测更可能出错」（§4.1）。半监督目标 `L = L_s + λ L_u`，实验取 `λ = 1`（§4.2）。
- **阈值来源**（§6.1）：`τ_m = 0.6`，在 AndroZoo 前 6 个月（漂移更严重）上调优后**直接迁移到 EMBER**，作者称以避免在另一数据集上过拟合。
- **主结果**（§6.2）：相对静态 MLP，平均 F1 提升 4.07%（AndroZoo）/ 0.83%（EMBER），FNR 降低 14.78% / 5.74%。作者自述末尾观察到轻微 self-poisoning，但发作时间比先前工作明显延后。
- **类别覆盖受限实验**（§6.2）：在 EMBER 上仅用 top-k 家族训练时，适应算法可把 F1 提升至 36.6%（五家族），但**代价是后期月份 FPR 明显上升**。
- **与主动学习组合**（§6.3）：以月度 100 标注预算的主动学习为基准，用 MORPH 更新替换其中一半，可保持相当性能；在 Chen et al. 框架上追加 MORPH 后 F1 再增 3.46%。
- **与 DroidEvolver++ 比较**（§6.4）：DE++（五个线性模型的集成）平均 F1 23.3%，其集成式模型更新反而使性能下降 2.65%；MORPH 平均 F1 53.8%。作者结论是神经网络比线性在线模型更抗漂移、更抗 self-poisoning。
- **自述边界**（§7.2）：完全自动化并不总是可行——当新家族与训练集差异过大时，需要至少一部分样本被正确伪标注；否则必须回到主动学习。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】MORPH 的类不对称阈值选样与 ADAPT 的类自适应阈值本质是同一条动机假设（漂移主要打击恶意类）的两种实现；若 C1 要引用「伪标签门」的机制来源，ADAPT（有校准与 mixup）比 MORPH 更完整，MORPH 主要提供「早期形态 + 负证据（FPR 上升）」。
- 【推论】MORPH 的 FPR 上升发生在「训练家族受限」这一人为构造的困难面上，未必外推到 LAMDA 的自然时间漂移；但其现象提示：靠放宽阈值提高召回的可迁移代价是 FPR 失控。
- 【推论】该文未报告任何固定 FPR 工作点，故它对 LAMDA 的 FNR@固定FPR 轴**不构成占位或对照读数**。

## 三、可迁移机制（借用边界）

- **类不对称伪标签阈值**：对恶意类放宽、良性类从严。可借用的边界是「只在无标注流上生成伪标签、不引入新标注」；**不得**据此声称在 LAMDA 上有效，也不得把 `τ_m = 0.6` 直接搬到 LAMDA（该值只在 AndroZoo 前 6 个月调得，且跨数据集迁移是作者的主观选择）。
- **保留原始训练数据（warm fine-tune 而非重训）**：作者明确用该做法同时缓解 self-poisoning 与灾难性遗忘（§6.1）。借用边界是它只说明「保留旧数据有帮助」，不构成对 LAMDA 记忆容量的证明。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做任何实验，**不得**说「MORPH 在 LAMDA 上达到某指标」。
- 没有固定 FPR 工作点，**不得**引用其 FPR 数值当作「某 FPR 阈值下的检出率」。
- 没有证明伪标签选择对所有漂移类型都稳健：作者自己在 §7.2 承认新家族差异大时会失效。
- 没有做置信度校准（对比 ADAPT 的 mixup 校准），**不得**声称其伪标签在低置信区仍然可靠。

## 五、待验证假设

- 假设 A：在 LAMDA 的年度窗口上，类不对称阈值选样能否在不抬高 FPR 的前提下降低 FNR？**最小验证**：在 LAMDA 源期冻结一个静态 MLP 基线，只加类不对称伪标签选样，比较 ΔFNR 与 ΔFPR，看是否出现 MORPH 在 EMBER 上的 FPR 上升。
- 假设 B：MORPH 与 ADAPT 的差异（校准/mixup）是否是两者性能差的主因？**最小验证**：在 LAMDA 上跑「MORPH 式选样 + mixup」与「MORPH 式选样」两臂。

## 文献信息

- arXiv：https://arxiv.org/abs/2401.12790
- 上一代工作：DroidEvolver（EuroS&P 2019）、DroidEvolver++（AISec 2021）
- 后续工作（同作者组）：[[2025-Alam-ADAPT伪标签抗概念漂移]]
