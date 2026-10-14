---
title: "On the Limitations of Continual Learning for Malware Classification（持续学习在恶意软件分类上的局限）"
authors: [Mohammad Saidur Rahman, Scott E. Coull, Matthew Wright]
year: 2022
date: 2026-10-14
journal: "CoLLAs 2022（首届持续学习智能体会议），PMLR v199, pp.564–582；arXiv:2208.06568（2022-08-13）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2022-Rahman-Limitations-of-Continual-Learning-Malware.pdf]]"
tags:
  - 恶意软件
  - 持续学习
  - 灾难性遗忘
  - 回放预算
  - 类型/论文
key_finding: "11 种持续学习方法在 Drebin/EMBER 上几乎全面弱于 naive Joint 回放；正则化类（EWC/EWC-O/SI）在 Domain-IL 与 Class-IL 上贴住甚至低于 None，仅 Task-IL 部分有效；论文真正给出「随预算单调上升」曲线的是 Partial Joint Replay（回放历史数据的 1%–50%），不是 ER——ER 在 Domain-IL 上 only 75.9，远低于 None 的 93.1。"
method: "11 种 CL 方法（EWC、EWC-O、SI、LwF、GR、GR-D、RtF、BI-R、ER、A-GEM、iCaRL）× 3 种增量情景（Domain-IL / Class-IL / Task-IL）× 2 个数据集（Drebin、EMBER 2018），MLP 骨干，10 次随机初始化"
baseline: "None（顺序训练无 CL）与 Joint（全量联合回放）两条非正式下/上界"
aliases: [Rahman2022-Limitations, Limitations of CL for Malware, 2208.06568]
related:
  - "[[2025-Mohamed-MADAR多样性感知回放]]"
  - "[[2023-Amalapuram-ECBRS-PAPA网络入侵持续学习]]"
  - "[[2026-Asadi-FreeMOCA无记忆恶意代码持续学习]]"
---

# On the Limitations of Continual Learning for Malware Classification

> **本文件是结构化阅读笔记，不是 MinerU 全文转换产物。** 转换中间件留在 `/tmp/rahman_full.md`（未落库，遵守 `wiki/AGENTS.md` 不保存转换中间文件）。
> 证据等级：**本地全文**（原件 `raw/papers/attack-detection/lamda-related/2022-Rahman-Limitations-of-Continual-Learning-Malware.pdf`，19 页）
> 抽取工具：`pdf-converter`（MinerU `extract`，全 19 页，`--language en`）；页码定位用 `pdftotext` 逐页扫描。
> **该 arXiv 版物理 PDF 页码 = 文内印刷页码（每页页眉为 "Preprint"）。**

---

## 0 先说结论：两条转述的核实结果（任务核心）

| 主代理转述 | 核实裁定 | 依据 |
|---|---|---|
| ①「参数侧方法（EWC 等）在恶意软件上失效」 | **部分确认**（方向对，但缺限定条件，且 Task-IL 有反例） | Abstract p.1；Table 1 pp.7–8；§5.1 p.8；§6 p.10 |
| ②「ER 随预算单调上升」 | **部分确认 + 主语错误（推翻名词）**：单调上升的现象在原文成立，但**主语是 Partial Joint Replay，不是 ER**；ER 在 Domain-IL 上是 75.9,远低于 None | §5.2 p.9（Fig. 6/7）；Table 1 p.8 |

**②的主语错误是会给方案带来相反证据的类型**：若照抄「ER 随预算单调上升」，读者会以为「加预算就能救 ER」，而原文同一张 Table 1 里 ER 在 Domain-IL 上是 `75.9 / 65`（mean/min），**比 None 的 93.1 低 17 个百分点**。详见 §4。

---

## 1 论文原结论（与原文措辞对齐，逐条给页码）

### 1.1 总主张：CL 方法整体弱于 naive Joint 回放

- **Abstract（p.1）**：「continual learning methods **significantly underperformed naive Joint replay** of the training data in nearly all settings – in some cases **reducing accuracy by more than 70 percentage points**」；「A simple approach of **selectively replaying 20% of the stored data** achieves better performance, with **50% of the training time** compared to Joint replay.」
- **贡献列表（p.2）**：
  - 「We empirically show that **none of the CL techniques are effective in the Domain-IL setting**.」
  - 「For Class-IL, **10 of the 11 methods performed poorly**, with only iCaRL … performing marginally better against the Joint replay baseline.」
  - 「Instead of storing all prior data, we find that **replaying 20-50% data is enough to significantly outperform all CL techniques in Domain-IL** while also **reducing the training cost by 35-50%** compared with 100% Joint replay.」

### 1.2 正则化类方法（EWC / EWC Online / SI）的实际表现

**Table 1（pp.7–8）原始数字**（Mean / Min；None 与 Joint 为参照）：

| 方法 | Drebin Task-IL | Drebin Class-IL | EMBER Task-IL | EMBER Class-IL | EMBER Domain-IL |
|---|---|---|---|---|---|
| None | 85.3 / 63.7 | 45.3 / 19.7 | 75.7 / 60 | 26.6 / 9.2 | **93.1** / 91.3 |
| Joint | 99.7 / 99.3 | 99.0 / 97.5 | 97.1 / 95 | 87.7 / 85 | **95.9** / 93.2 |
| EWC | 85.1 / 62 | 46.3 / 20 | 85.9 / 72 | 8.4 / 0.1 | 92.8 / 90.0 |
| EWC-O | 83.9 / 64 | 47.1 / 20 | 78.8 / 57 | 9.0 / 0.2 | 93.1 / 91.5 |
| SI | 90.7 / 78 | 45.3 / 20.0 | 73.6 / 58 | 27.3 / 9.5 | 93.0 / 91.1 |

- **Domain-IL（EMBER，12 个月度任务）**：三个正则化方法 `92.8 / 93.1 / 93.0`，None `93.1`，Joint `95.9`——**几乎完全等于 None**。§5.1（p.8）：「we also see that **none of the CL techniques are effective**, with all of them performing closer to None than to Joint.」；§6（p.10）：「none of the CL techniques could contribute significantly in the Domain-IL setting」。
- **Class-IL**：§5.1（p.8）：「**All the regularization-based techniques and LwF perform poorly and very close to None.**」（Drebin 上 46.3/47.1/45.3 vs None 45.3；EMBER 上 8.4/9.0 甚至**低于** None 26.6。）
- **Task-IL 是明确反例**：Drebin 上 **SI = 90.7**（None 85.3，Joint 99.7）；EMBER 上 **EWC = 85.9**（None 75.7，Joint 97.1）。§5.1（p.8）：「Among the regularization techniques, **only SI yields closer to Joint level performance with 90.7% accuracy**」（Drebin 语境）；EMBER 语境下原文写「None of the regularization-based techniques yield closer to Joint baseline performance」，但表中 EWC 85.9 已显著高于 None 75.7。
- 作者对 Task-IL 的定位（§6，p.10）：「Task-IL for malware, however, is **of least significance**, as adding new tasks is likely to occur less frequently than adding new classes or observing domain shift.」

**⇒ 对转述①的裁定：方向成立，但必须带限定。** 准确表述是「参数正则化方法在 **Domain-IL 与 Class-IL** 上失效（贴住甚至低于 None），在 **Task-IL 上部分有效**」。不带限定地写「在恶意软件上失效」会被 Table 1 的 SI 90.7 / EWC 85.9 直接反驳。

### 1.3 作者给出的失效归因（§6 Discussion, p.10）

原文**不是**把失效归给「参数法特有缺陷」，而是归给**数据本身的特征空间**：

- 「**Dataset Complexity**」：t-SNE 显示 EMBER 特征空间「extremely complex with significant overlap between classes」（Fig. 8，p.10）。
- 「the **semantically-rich feature space** of the malware classification datasets… There are strong semantic constraints on the values that these features can take on… It is possible that these constraints and the inherent complexity of the classification task render **generative, distillation, and regularization-based CL methods ineffective**.」（p.10）
- 「**Real Domain Shifts**」：以往 Domain-IL 研究用 permuted-MNIST 模拟漂移，「clearly does not represent a realistic data distribution shift」；EMBER 的自然漂移「creates very difficult tasks for the classifier」（p.10，Fig. 11 在附录 C）。
- 章末结论（§7，p.10）：「We hypothesize that the **strong semantic constraints of the features** used for malware classification tasks, along with the **complex data distributions induced by natural drift** in this space, lie at the heart of the performance differences…」

### 1.4 实验设置（复现口径）

- **数据集（§3.3，pp.4–5）**：Drebin（Android，取 top 18 家族共 4,525 恶意样本，`VarianceThreshold(0.001)` 后 2,492 维二值特征；样本跨 5 年但各时间片家族样本不足，**只能做 Task-IL / Class-IL**）；EMBER 2018（Windows PE，1M 文件扫描、其中 400K goodware / 400K malware / 200K unknown，共 2,381 维）。
  - Domain-IL：仅用 2018 年 goodware + malware（剔除 unknown），**划分为 12 个月度任务**（Jan–Dec 2018，p.5）。
  - Class-IL / Task-IL：只用 2018 恶意样本；筛掉样本数 < 400 的家族后余 106 个家族，再取 **top 100 家族共 337,035 样本**（p.5）。
- **模型（§4.1，p.5）**：MLP，4 层全连接 `[1024, 512, 256, 128]`，每层 dropout 0.5 + batch norm；SGD `lr=0.01, momentum=0.9, weight_decay=1e-6`；二分类 AUC = **0.99512**（对照 Anderson & Roth 2018 的 LightGBM SOTA AUC 0.99642）。Drebin 的 Task/Class-IL 改用 Adam `lr=0.001`；EMBER top-100 的 Task/Class-IL 用 SGD `lr=0.001`；Domain-IL 用 SGD `lr=0.01`。mini-batch：Drebin 32 / EMBER 256。
- **任务切分（§4.2，p.6）**：Task-IL = Drebin 9 任务 × 2 类、EMBER 20 任务 × 5 类；Class-IL = Drebin 起始 10 类、每任务 +2 类共 5 任务，EMBER 起始 50 类、每任务 +5 类共 11 任务；Domain-IL = 12 任务。**每组实验跑 10 次不同随机参数初始化**，回放样本用「random buffer population strategy」随机选取。
- **指标**：Mean（该实验所有任务的平均准确率）与 Min（最差任务准确率）。原文特意强调 Min 的理由：「the weakest performance shows the degree to which a technique may not be suitable for use」（§5.1，p.8）。
- **基线（§4.3，p.6）**：None（顺序训练，非正式下界）与 Joint（全量联合回放，非正式上界）。
- **硬件（§4.2，p.6）**：CentOS-7，Intel Xeon 40 核 / 128 GB RAM / 4× RTX 2080Ti 12 GB。代码与处理后数据集公开于 `https://github.com/msrocean/continual-learning-malware/`。
- **评价口径提示**：全部为**准确率（accuracy）**，无 FPR 工作点、无 AUT、无时间衰减曲线指标；Domain-IL 的「月度」是 12 个等距任务。

---

## 2 部分回放（Partial Joint Replay, PJR）：曲线形状与数字（§5.2，p.9）

**这是原文唯一「随预算单调上升」的曲线。**

- 设置（p.9）：**假设存储充足**（原文：「This assumes that we have **ample storage capacity** and can maintain huge amounts of both historical and current data to be accessed at any time」），因此 CL 技术并非必需；问题变成「**需要多少历史数据才够**」。仅做 **Domain-IL**（作者称其为「the CL setting most applicable to malware classification」）。
- 预算轴：回放**占已存历史数据的比例**，共 7 档：`None(0%) / 1% / 5% / 10% / 20% / 50% / Joint(100%)`。用 early stopping，`patience = 5`。
- **平均准确率（Fig. 6，p.9）**：

| 回放比例 | 0%(None) | 1% | 5% | 10% | 20% | 50% | 100%(Joint) |
|---|---|---|---|---|---|---|---|
| 平均准确率 | 93.0 | 93.9 | 94.5 | 94.7 | 95.0 | 95.4 | 96.4 |

- **形状判定**：**单调递增，0%–50% 区间内无拐点、无饱和**。50% 处 95.4 仍低于 Joint 96.4（差 1.0）。原文未做「是否饱和」的讨论，也未外推。
- 关键量化（p.9）：20% 回放「the accuracy is only **1.4%** lower than Joint replay」；训练开销「using 20% of the replay data shrinks by **50%** compared to full Joint replay」，50% 回放「shrinks by **35%**」。
- 原文对「为何 1% 就有效」的解释（p.9）：历史样本池随任务累积、多数任务下**远大于**新数据，故 1% 已是训练数据中可观的比例。
- **训练时间曲线见 Fig. 7（p.9）**。
- 附录 C（Fig. 11，p.19）另给 MNIST（permuted）与 EMBER 的特征空间漂移 t-SNE 对照。

**⇒ 对转述②的裁定：现象确认，主语推翻。** 这条曲线的主语是 **PJR（在足量存储下按比例回放历史池）**，而**不是 ER**。见下节。

---

## 3 ER（Experience Replay）在原文里的实际表现 —— 与转述②相反的证据

**Table 1（p.8）**：

| 方法 | Drebin Task-IL | Drebin Class-IL | EMBER Task-IL | EMBER Class-IL | **EMBER Domain-IL** |
|---|---|---|---|---|---|
| None | 85.3 | 45.3 | 75.7 | 26.6 | **93.1** |
| Joint | 99.7 | 99.0 | 97.1 | 87.7 | **95.9** |
| **ER** | 99.6 | 55.2 | 94.0 | 28.0 | **75.9 / min 65** |
| A-GEM | 92.6 | 47.8 | 90.4 | 28.0 | 77.5 / min 67.4 |

- **ER 在 Domain-IL 上是全表最差的之一**（75.9，低于 None 的 93.1 达 17.2 个百分点，min 更是 65）。ER 只在 Task-IL 上表现好（Drebin 99.6、EMBER 94.0）——§5.1（p.8）：「Considering both datasets, we can see that **only ER performs reasonably well on both**」（Task-IL 语境）。
- Table 1 脚注（p.7）说明「Results in **Bold** indicate accuracy values closer to Joint performance than None」，而 ER 的 Domain-IL 数字**未被加粗**。

**⇒ 结论**：把「随预算单调上升」写成 ER 的性质，与原文 Table 1 直接冲突。原文中「预算→精度」的单调关系只在 **PJR（足量存储下的回放比例）** 上成立；**ER（固定小容量 episodic memory）在 Domain-IL 上是被原文明确判为失败的方法之一**。

---

## 4 存储预算口径是否与我们可比（任务第 3 问）

**结论：口径不同，不可直接比较。**

1. **主实验（Table 1）的容量口径：原文未披露绝对值。**
   - 对 iCaRL：§2（p.3）「iCaRL sets a memory budget beforehand, and the memory budget is **equally divided into the previously learned classes**」；附录 B（p.16）「Given a **fixed buffer size** (i.e., allocated memory), iCaRL stores samples of the earlier learned classes which are closest to the feature mean」。
   - 对 ER：附录 B（p.15）只说「examples stored in the **very small episodic memory**」，**无数字**。
   - 对 A-GEM：附录 B（p.16）只说「an episodic memory which stores **a subset** of the observed examples」，**无数字**。
   - **全文未给出任何以样本条数或字节计的绝对记忆容量**（检索 `buffer size|memory budget` 仅命中上述定性描述）。
2. **PJR 实验（§5.2）的容量口径：相对比例，且假设存储无上限。**
   预算 = 「占全部已存历史数据的百分比」（0/1/5/10/20/50/100%），历史池随任务累积而增长；原文前提是「ample storage capacity」。因此**该比例不是固定容量**，同一 20% 在不同任务的绝对条数不同。
3. **与我们（LAMDA 全程总容量上限，按样本条数计）的差距**：
   - 它的口径是 **(a) 未披露的固定缓冲（CL 方法）** 或 **(b) 无上限存储池上的回放比例（PJR）**；
   - 我们的口径是 **(c) 全程固定的总容量上限（条数）**。
   - **(b) 不能换算成 (c)**：原文自己也指出「the total set of old training samples grows larger with each task」，1% 在后期远大于早期——这说明同一比例对应**不同绝对条数**，二者不是同一约束。
   - **(a) 与 (c) 方向一致但数值不可比**，因为 (a) 的绝对值原文未给。

---

## 5 有没有讨论「复用次数／重放比例」（任务第 4 问）

- **重放比例（replay fraction）：有，是 §5.2 的全部内容**（1%–50%，p.9，见 §2）。原文用词是「the **replayed data fraction**」与「fraction of the stored data to be replayed」，**未使用 "replay ratio" 这一短语**。
- **每样本复用次数（reuse count / how many times each stored sample is replayed）：原文未述。** 全文检索 `reuse`、`number of times`、`replay count` 均**零命中**。
- **两处容易误认为「复用比例」但其实不是的表述**：
  1. **GR 的混合比 r**：附录 B 式 (5)（p.15）$\mathcal{L}_{\text{train}}(\theta_{n+1}) = r\,\mathbb{E}_{(x,y)\sim\mathcal{D}_{n+1}}[\cdot] + (1-r)\,\mathbb{E}_{(x,y)\sim\mathcal{D}_{n}}[\cdot]$，原文定义「**r represents the ratio of the mixture of the real and replayed data**」。这是**新旧数据混合比**，不是同一批存储样本被重复使用的次数。
  2. **转述 Amalapuram 2021 的结论**（§2，p.3）：「some of the results of their study mirror our own findings, namely that the **number and selection of samples used during replay are key** to the success of continual learning in the cybersecurity space.」——**这是转述他人工作，本文自身未对「回放样本条数」做受控实验**（唯一的数量实验就是 §5.2 的比例扫描）。
- **作者自陈的未来方向（§6，p.10）**：「the relative success of partial joint replay and iCaRL **demonstrate the importance of sample selection during replay** and the possibility of developing more effective strategies that ensure optimal coverage over feasible regions of the feature space.」（在 §7 Conclusion p.10 亦重复。）

**⇒ 对我们的意义**：若我们的机制围绕「**复用次数／重放比例**」展开，**本文不能作为该维度的实验依据**——它只做了「历史数据回放比例（对无上限存储池）」，既没有固定容量下的复用次数扫描，也没有把比例与固定条数预算解耦。这一点必须在方案里如实标注为**原文未覆盖**。

---

## 6 本课题推论（不是原文结论）

1. 本文对「固定容量记忆库」的负面结论只覆盖了 **ER / A-GEM / iCaRL 三种**（iCaRL 是其中唯一接近 Joint 的），**不等于所有预算型回放方法在恶意软件上都失效**——后续工作（如 MADAR 2025）正是从「选择策略」切入。**这属于推论，需另文证据。**
2. 本文 Domain-IL 的 12 个月度任务、accuracy 评价、无 FPR 工作点，与 LAMDA 的评测口径不同；把本文数字直接搬到 LAMDA 对比**不成立**。
3. 本文「PJR 在 20% 时距 Joint 仅 1.4%」是**在存储无上限假设下**得到的，不能用来论证「固定总容量下 20% 就够」。

## 7 可迁移机制

- **两基线夹逼的报告范式**：把 None 当非正式下界、Joint 当非正式上界，并以「是否被加粗（更靠近 Joint 还是 None）」作二值判定——这是一种低成本的**机制有效性筛选**，可用于本项目消融表的呈现格式。（机制来源，非本项目实验证据。）
- **Min 指标**：除 Mean 外强制报告**最差任务准确率**，用于暴露「平均好看但某任务崩掉」的方法。可作为本项目分面呈现的参照。
- **比例扫描 + 训练成本曲线双图**（Fig. 6 精度 / Fig. 7 时间）：把「预算—效果」与「预算—成本」分列，可直接借用到我们的预算敏感性分析图式。

## 8 不可直接声称的内容

- 不得写「本文发现参数法在恶意软件上失效」而不加 Domain-IL/Class-IL 限定——Task-IL 上 SI 90.7（Drebin）、EWC 85.9（EMBER）是反例。
- 不得把 §5.2 的单调上升曲线称为 ER 的曲线。
- 不得声称本文讨论了「每样本复用次数」或「重放比例在固定容量下的行为」。
- 不得把本文的 20% 换算成 LAMDA 下的绝对样本条数。
- 不得称本文报告了 FPR/AUT/固定工作点指标——它只有 accuracy（Mean/Min）。
- 本文为 CoLLAs 2022 / PMLR v199 会议论文；**「预印本」「同行评审」状态不可混用**（原件正文为 arXiv 版，页眉 "Preprint"；已确认正式发表于 PMLR v199 pp.564–582）。

## 9 疑问 / 待验证

1. **Table 1 中 ER / A-GEM / iCaRL 的绝对记忆容量原文未给**，需查其 GitHub 仓库（`https://github.com/msrocean/continual-learning-malware/`）的配置才能复原口径。**本笔记未执行该核验。**
2. Fig. 6 的完整逐任务曲线（而非仅平均）需读原图；MinerU 只给出了图题与图例（`None / Replay 1% / 5% / 10% / 20% / 50%`），**曲线形状（是否在某任务下降）未经本笔记核验**，§2 的「单调」是对**平均准确率数字**的判定。
3. ER 的 Domain-IL 崩盘（75.9）原文未在 §5.1 单独解释；§6 的归因是数据集层面的，未给出 ER 特有的归因。**属原文未述。**

## 10 原始摘要

> Malicious software (malware) classification offers a unique challenge for continual learning (CL) regimes due to the volume of new samples received on a daily basis and the evolution of malware to exploit new vulnerabilities. On a typical day, antivirus vendors receive hundreds of thousands of unique pieces of software, both malicious and benign, and over the course of the lifetime of a malware classifier, more than a billion samples can easily accumulate. Given the scale of the problem, sequential training using continual learning techniques could provide substantial benefits in reducing training and storage overhead. To date, however, there has been no exploration of CL applied to malware classification tasks. In this paper, we study 11 CL techniques applied to three malware tasks covering common incremental learning scenarios, including task, class, and domain incremental learning (IL). Specifically, using two realistic, large-scale malware datasets, we evaluate the performance of the CL methods on both binary malware classification (Domain-IL) and multi-class malware family classification (Task-IL and Class-IL) tasks. To our surprise, continual learning methods significantly underperformed naive Joint replay of the training data in nearly all settings – in some cases reducing accuracy by more than 70 percentage points. A simple approach of selectively replaying 20% of the stored data achieves better performance, with 50% of the training time compared to Joint replay. Finally, we discuss potential reasons for the unexpectedly poor performance of the CL techniques, with the hope that it spurs further research on developing techniques that are more effective in the malware classification domain.

## 11 文献信息

- 会议版：CoLLAs 2022, PMLR v199, pp.564–582 — <http://proceedings.mlr.press/v199/rahman22a/rahman22a.pdf>
- arXiv：<https://arxiv.org/abs/2208.06568>（cs.CR，cross-list cs.AI / cs.LG；提交 2022-08-13）
- Semantic Scholar CorpusID `251554057`（引用数本次未取得可靠快照）
- Zotero：本次核验时**不在库**（`zotero_semantic_search` 最高相似度 0.241，且为无关论文），已按 arXiv `2208.06568` 入库，item key **`KYJ47J7D`**（含 PDF 附件）
- 代码：<https://github.com/msrocean/continual-learning-malware/>
- 原件：`raw/papers/attack-detection/lamda-related/2022-Rahman-Limitations-of-Continual-Learning-Malware.pdf`（19 页，pdfTeX-1.40.21，Letter 612×792 pt，`/Title: Overleaf Example`）
- 抽取记录：`mineru-open-api extract <原件> -o /tmp/rahman_full.md --language en`
