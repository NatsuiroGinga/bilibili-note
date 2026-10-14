---
schema: paper-note-search/v1
title: "ADAPT: A Pseudo-labeling Approach to Combat Concept Drift in Malware Detection"
title_zh: "ADAPT：用伪标签对抗恶意软件检测概念漂移"
authors: [Md Tanvirul Alam, Aritran Piplai, Nidhi Rastogi]
year: 2025
date: 2026-10-14
journal: "arXiv 2507.08597（预印本；任务简报称 RAID 2025，未在本原件内页核到）"
doi: null
arxiv_id: "2507.08597"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2025-Alam-ADAPT-Pseudo-Labeling-Concept-Drift.pdf]]"
tags:
  - Android恶意软件
  - Windows恶意软件
  - PDF恶意文档
  - 概念漂移
  - 伪标签
  - 半监督学习
  - 主动学习
  - 类型/论文
tasks: [恶意软件二分类, 恶意软件家族多分类, 概念漂移适应]
datasets: [Drebin, APIGraph, BODMAS, EMBER, PDF Malware]
methods: [自适应漂移感知伪标签, 特征掩码增强与标签一致性, mixup 置信度校准, 模型无关自训练]
metrics: [F1, FPR, FNR, Absolute Exposure, Wilcoxon p]
key_finding:
  - "ADAPT 用类自适应伪标签阈值（恶意 τ_m、良性 τ_b 各自随当月预测均值更新）加 mixup 校准，在五个跨 Android/Windows/PDF 数据集上均优于静态模型与四个自训练基线。"
  - "它报告 F1/FPR/FNR 与累积暴露（AE），但不设固定 FPR 工作点；论文明确承认不直接处理灾难性遗忘与对抗投毒，并把二者列为未来工作。"
method: "类自适应阈值伪标签 + 特征掩码增强（同类替换 + 预测一致才纳入）+ mixup 校准；L = L_sup + L_bce 式组合，重训或微调"
baseline: "ARF、DroidEvolver++(DE++)、Insomnia、MORSE；Oracle（用真标签重训）"
aliases:
  - ADAPT
  - Alam2025-ADAPT
related:
  - "[[2024-Alam-MORPH自动概念漂移适应]]"
  - "[[2025-Li-LFreeDA无标签漂移适应]]"
  - "[[2023-Chen-Android恶意软件持续学习]]"
---

# ADAPT：伪标签抗概念漂移

> 页码锚点：标题与摘要位于 PDF 物理第 1 页；本文其余引用按 MinerU 保留的章节号（§I–§XI 与附录 A–H）给出。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2025-Alam-ADAPT-Pseudo-Labeling-Concept-Drift.pdf`）。取得版本为 arXiv 2507.08597 预印本。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | Drebin、APIGraph（Android，2012–2021）；BODMAS、EMBER（Windows PE，2018–2020）；PDF Malware（Hidost，2012 十周，950 维）；**未使用 LAMDA** |
| 特征表示 | 稀疏二值特征向量（Drebin 16,978 维、APIGraph 1,159 维、PE 2,381 维、PDF 950 维） |
| 平台 | Android + Windows + PDF |
| 监督设定 | 初始标注集 + 伪标签，**不新增标注**（§IV）；扩展主动学习：每月 50 样本标注（§VIII）；另评估**无源**（source-free，不访问原训练数据）变体（附录 D） |
| 是否有固定 FPR 工作点 | **无**。报告 F1/FPR/FNR 绝对数值与逐月曲线，未设固定 FPR 运行点 |
| 评价指标 | F1、FPR、FNR；另引入 Absolute Exposure（累积漏检暴露，§VII-A）与 Wilcoxon 符号秩检验（§VII-E） |
| 报告的主结果数字 | Table II（均值/五种子）：Drebin XGBoost+ADAPT F1 `57.1`、FPR `0.24`、FNR `56.6`（基线 XGBoost 为 `44.9/0.66/65.6`）；APIGraph MLP+ADAPT F1 `76.8`；BODMAS `99.6`；EMBER `93.5`；PDF `98.6`。Table VII（主动学习 50/月）：Drebin `81.7`、APIGraph `89.4` |
| 与 LAMDA 本课题的关系 | **部件来源**（类自适应伪标签阈值、mixup 校准、标签一致增强可直接借为 C1 伪标签门部件）+ **仅对照**（无 LAMDA 结果） |

## 一、论文原结论（带章节号）

- **核心机制**（§IV-A）：把固定伪标签阈值改为**类自适应阈值**——分别对恶意与良性计算当月预测概率均值 `μ_m, μ_b`（式 1–2），再与先验阈值按 `λ` 线性混合得到 `τ_m^updated, τ_b^updated`（式 3–4）。动机是 Figure 3：恶意类平均预测概率始终低于良性类，说明漂移主要打击恶意类。
- **增强与标签一致性**（§IV-B）：用 Wu et al. 的特征掩码增强，但做两处修改——掩码替换值只取**同类**样本；增强样本只有在当前模型预测与原始标签一致时才纳入（避免增强把样本推过决策边界，Figure 4）。
- **置信度校准**（§IV-C）：用 mixup（式 5 后的混合损失）改善校准，从而让「高置信即更可能正确」的阈值假设更成立，缓解 self-poisoning；对随机森林等不支持分数目标的模型，取插值系数较大者的标签。
- **主结果**（§VII、Table II）：XGBoost+ADAPT 在 Drebin/BODMAS/EMBER 取得最高 F1，MLP+ADAPT 在 APIGraph 最好，RF+ADAPT 在 PDF 最好。Drebin 上 RF/XGBoost/MLP 的绝对 F1 增益为 16.6 / 12.2 / 9.6 个百分点，主要来自 FNR 下降，且未抬高 FPR（相对基线 XGBoost 还降 63.6%）。
- **误差结构**（§VII-C、Table III、Fig. 11）：增益主要来自 FNR 下降；最优良性阈值 `τ_b` 高达 0.96–0.98，恶意阈值 `τ_m` 仅 0.63–0.70；因此 `err_{p,b}`（恶意误标为良性）显著低于 `err_{p,m}`。
- **消融**（§VII-D、Table IV）：在 APIGraph 前 6 个月上逐个移除自适应阈值/增强/mixup，各部件对 F1 与 FNR 均有贡献；移除自适应阈值会显著抬高 FNR。
- **与主动学习兼容**（§VIII、Table VII）：在 50/月标注预算下，XGBoost+AL 之上再加 ADAPT 使 F1 再增 0.4%（Drebin）/ 0.7%（APIGraph）。
- **多分类与未知家族**（§IX）：11 类（BODMAS/EMBER）上 ADAPT 比 XGBoost 基线 +2.8% 平均 F1；EMBER 上新家族逃逸成功率 9.8% / 7.1% / 6.6%（对应 5/10/20 个新家族），AUC 稳定在 0.706–0.713。
- **自述边界**（§X）：明确**不处理**对抗样本与投毒，并明确**不直接处理灾难性遗忘**（只在附录 E 分析其影响）；特征仅静态。
- **无源变体**（附录 D）：不访问原训练数据时，Drebin 首年平均 F1 比基线 +11.3%，仅落后半监督变体 1.76%；APIGraph +0.82%，落后 3.97%。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】ADAPT 的类自适应阈值是 MORPH 类不对称阈值的「可解释化 + 校准化」升级版，两篇构成同一条动机线；若 C1 需要一个「零新增标注的伪标签基线」，ADAPT 是比 MORPH 更强的版本。
- 【推论】ADAPT 的增益集中体现在 FNR 下降、FPR 基本不升（甚至下降），与本工作树关心的「安全回归」方向一致；但它**没有**固定 FPR 工作点，所以不能直接贡献 FNR@固定FPR 读数。
- 【推论】论文自述不处理灾难性遗忘（附录 E 显示 Drebin 上存在遗忘），这与 LAMDA 的持续学习合同存在缺口：ADAPT 在 LAMDA 上可能需要叠加回放/正则机制。

## 三、可迁移机制（借用边界）

- **类自适应伪标签阈值**（式 3–4）：把阈值绑到当月类预测均值。借用边界：可直接放进 C1 的伪标签门；但 `λ`、`τ_m`、`τ_b` 需在 LAMDA 源期重新标定（作者的 0.6/0.9x 只在各自数据集调得）。
- **mixup 校准**：借用边界是它只改善「置信度可信度」，**不**等于消除 self-poisoning；作者自己也只在 APIGraph 上给了校准曲线证据（Fig. 12）。
- **标签一致增强**：掩码替换限同类 + 预测一致才纳入。借用边界：这是「增强不改变标签」的一个可执行实现；但作者承认特征一致性（生成样本是否合法）**未被强制**。
- **Absolute Exposure（AE）指标**：累积漏检暴露，可作为 LAMDA 时间轴上「暴露-成本」的辅助指标。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做实验，**不得**说「ADAPT 在 LAMDA 上达到某指标」。
- 没有固定 FPR 工作点，**不得**把其 FPR 数值当作某阈值下的工作点读数。
- 未处理灾难性遗忘与投毒（§X 自述），**不得**声称其在 LAMDA 长期持续学习下稳定。
- 增强生成的特征不保证是合法样本（作者自述「feature consistency is not explicitly enforced」，§IV-B），**不得**声称增强样本满足 Android/PE 依赖约束。
- 各数据集只跑 5 个随机种子且部分 ΔFPR 为负（误差增大），**不得**只引用最好的 F1 数字。

## 五、待验证假设

- 假设 A：在 LAMDA 上，类自适应阈值相对固定阈值的增益是否与 ADAPT 报告的方向一致（FNR 降、FPR 不升）？**最小验证**：LAMDA 源期静态基线上加「固定阈值」vs「类自适应阈值」两臂，比较 ΔFNR/ΔFPR。
- 假设 B：ADAPT 的灾难性遗忘缺口在 LAMDA 上是否真实存在？**最小验证**：在 LAMDA 最后窗口模型上回测最早窗口，看 F1/FNR 是否退化。

## 文献信息

- arXiv：https://arxiv.org/abs/2507.08597
- 前身：[[2024-Alam-MORPH自动概念漂移适应]]
- 同期无标签路线：[[2025-Li-LFreeDA无标签漂移适应]]
