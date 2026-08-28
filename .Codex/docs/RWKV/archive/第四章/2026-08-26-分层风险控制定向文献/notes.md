---
title: 长度分层 Tong 证书定向文献调研笔记
date: 2026-08-26
tags:
  - 类型/排查
  - RWKV/第四章
  - 风险控制
  - 组条件保形
---

# 长度分层 Tong 证书 — 定向文献调研笔记

> 代理：`stratified_risk_control_literature_opus`，模型 `claude-opus-5[1m]`
> 计划见同目录 `task_plan.md`

---

## 0 检索元数据与边界

### 本地混合索引收据

| 项 | 值 |
|---|---|
| 重建命令 | `uv run --project scripts/literature_search --locked python -m scripts.literature_search build --offline --json` |
| 重建后 `index_sha256` | `92b80cf592754e81fbf66774fce930dd5283eade608a5550c8d40da707f11a86` |
| 向量通道 | `vector_count=38245`，`vector_dimension=384`，`vector_device=mps:0`，无回退 |
| `papers` 集合 | `504` 篇笔记，`7496` 块 |
| 重建前状态 | `stale=true`（`source_added`/`source_changed`），且 `vector_count=0`（此前为 lexical-only 构建） |
| 重建后残余 `stale` | `true`，但差异**仅在** `plans/recovery/reports/research-notes`（本任务自建 `task_plan.md` 与其他代理并发写入）；`papers` 集合 `added=changed=deleted=0` |

**结论**：`--scope paper` 的检索结果建立在完全当前的论文语料上，向量通道已实际运行。检索模式统一为 `--mode hybrid --offline`。

### 入库后二次重建收据（任务收尾）

六篇新笔记写入后再次执行 `build --offline`，退出码 `0`：

| 项 | 值 |
|---|---|
| `index_sha256` | `9bd7919e00a272a47f2675a2003ab09ea991109a601cf88d00c36d94c7826cfd` |
| `vector_count` | `38778`（增量：`reused=38440`，`reembedded=338`） |
| 索引文件 | `.cache/literature-search/index.sqlite3`，`233,644,032` 字节 |

**可检索性验证**：查询 `组条件覆盖 分组保形预测 每组误报率 分层预算分配`（`--scope paper --mode hybrid`）返回前 5 名中，本次入库的 p-filter、Vovk、Bates、Barber 分列第 1、2、3、5 位。新笔记确已进入检索通路。

### 边界措辞（强制）

以下全部结论限定为「**本次检索所及**」：本地 504 篇论文笔记的混合检索，加上针对三束主题的定向在线检索。
**不得**写成「文献中不存在」「首次提出」。在线返回的题录未经全文核验者一律标为候选。

---

## 1 束 A：组条件 / Mondrian 保形与条件风险控制

### 查询式与命中

| 通道 | 查询式 | 结果 |
|---|---|---|
| 本地 hybrid | `组条件覆盖 分组保形预测 条件有效性 每组误报率控制` | 前 5：Tibshirani 协变量移位保形、Angelopoulos 保形风险控制、Gibbs 自适应保形、Tong NP 分类、Clausen CBAM。**无任何 Mondrian／组条件专论** |
| 本地 hybrid | `有限样本风险控制 上置信界 Clopper-Pearson 分布无关保证` | 前 5：Paxson、Farinhas 非交换 CRC、NMoE、Angelopoulos CRC、PRED。**无 RCPS／LTT** |
| 在线 | `Mondrian conformal prediction group-conditional validity Vovk conditional validity inductive conformal predictors` | 命中 Vovk 2012（arXiv:1209.2673）、Kandinsky CP（arXiv:2502.17264）、Gibbs–Cherian–Candès（arXiv:2305.12616） |
| 在线 | `Barber Candes Ramdas Tibshirani limits of distribution-free conditional predictive inference impossibility` | 命中 Barber et al. 2021（arXiv:1903.04684，DOI `10.1093/imaiai/iaaa017`） |
| 在线 | `Bates Angelopoulos RCPS Learn then Test Clopper-Pearson upper confidence bound risk` | 命中 Bates et al. 2021 JACM（arXiv:2101.02703）、Angelopoulos et al. LTT（arXiv:2110.01052，AoAS 19(2):1641–1662, 2025） |

### 直接近邻清单

| 论文 | 出处 | 证据等级 | 与本机制的关系 |
|---|---|---|---|
| **Vovk 2012**, Conditional validity of inductive conformal predictors | ALMLR / arXiv:1209.2673 | **E3 全文级**（已入库） | **机制正源**。组条件控制的标准做法 |
| **Barber, Candès, Ramdas, Tibshirani 2021**, The limits of distribution-free conditional predictive inference | Information and Inference 10(2):455–482 | **E3 全文级**（已入库） | **负面结果边界**，同时给出本机制可行性的正面依据 |
| Gibbs, Cherian, Candès, Conformal Prediction with Conditional Guarantees | arXiv:2305.12616 | 题录级 | 把组条件推广到协变量函数类；未入库 |
| Kandinsky Conformal Prediction | arXiv:2502.17264 | 题录级 | 允许**重叠**组与分数化组成员；未入库 |
| **Bates, Angelopoulos, Lei, Malik, Jordan 2021**, Distribution-Free Risk-Controlling Prediction Sets | JACM 68(6):43 / arXiv:2101.02703 | **E3 全文级**（已入库） | UCB 校准族；**Remark 4（物理第 7 页）明确二元损失下精确二项界最紧且「should always be used」** |
| Angelopoulos, Bates, Candès, Jordan, Lei, Learn then Test | AoAS 19(2):1641–1662 (2025) / arXiv:2110.01052 | 题录级＋摘要级 | 把风险控制改写为多重检验，支持非单调风险与 λ 网格上的 FWER 校正 |
| Angelopoulos et al. 2024, 保形风险控制 | 本地已有 | E3（旧笔记） | 单调有界损失的期望控制，**交换性依赖** |

### 束 A 要回答的两个问题

**问题 1：组条件有限样本 FPR 控制的标准做法与保证形式是什么？**

**答（E3 全文级，Vovk 2012）**：标准做法是**条件归纳保形预测（conditional ICP）**，由一个「归纳 m-分类法」`K : Z^m × Z → K` 定义（物理第 7 页）。p 值改为**在同类别内**计算：

> `p_y := (|{i : κ_i = κ_y & α_i ≤ α_y}| + 1) / (|{i : κ_i = κ_y}| + 1)`（物理第 7 页式 (10)）

**Proposition 3**（物理第 8 页）：在交换性下，给定 `Z_{l+1}` 的类别，错误概率不超过 `ε`，对**任意** `ε` 与任意条件 ICP 成立。取 `K(·,(x,y)) := y` 即得**标签条件 ICP**。

保证形式有两支，须分清：

- **类别条件的边际保证**（Prop 3）：对每个类别，误差 ≤ `ε`，无 `δ`。
- **训练条件的 (ε, δ) PAC 保证**（Prop 2a，物理第 5 页）：`ε_E ≥ ε + sqrt(-ln δ / (2n))`，`n` 为校准集大小。**这是与本课题 Tong 证书同型的双参数形式**，但 Vovk 用的是 **Hoeffding 型修正**，而本课题用 **Clopper–Pearson 精确二项上界**（更紧）。

**问题 2：δ 在组×方向上的分裂有无既有方案？**

**本次检索所及，没有找到把 `δ` 同时按「组 × 决策方向」二维分裂的既有方案。**分解为三个已有片段：

- Vovk Prop 3 给出**组维度**的条件有效性，但**不带 `δ`**（无有限样本置信预算）。
- Vovk Prop 2a 给出**`δ` 维度**的训练条件保证，但**对池化整体**，不按组分裂。
- Vovk 在 §4 引言（物理第 7 页）明确指出动机之一是「在不同区域可能想要不同的显著性水平」，并举垃圾邮件例（把正常邮件判为垃圾的代价远大于反向）。**这是「方向不对称预算」的动机陈述，但该文未给出跨组×方向的 `δ` 分配定理。**
- 束 B 的 p-filter 给出**多层预算并存**的分配理论，但作用在 FDR 而非 FPR，且不含 `δ`。

**裁决**：`δ` 的「组 × 方向」二维分裂在本次检索所及范围内**没有直接既有方案**；本课题采用的均分（Bonferroni）是保守且合法的默认，但其**最优性未验证**。

---

## 2 束 B：分层多重检验预算分配

### 查询式与命中

| 通道 | 查询式 | 结果 |
|---|---|---|
| 本地 hybrid | `分层多重检验 预算分配 加权 Bonferroni 错误发现率 分组假设` | 前 5：Almeida 协变量移位高概率风险控制、BAYWATCH、Carterette statAP、Gupta C2 信标、StealthCup。**无多重检验专论** |
| 在线 | `"p-filter" Barber Ramdas simultaneous FDR control multiple groupings partitions hierarchical` | 命中 Barber & Ramdas 2017 JRSS-B 79(4):1247–1268（DOI `10.1111/rssb.12218`，arXiv:1512.03397）；Ramdas et al. 统一框架 arXiv:1703.06222 |

### 直接近邻

| 论文 | 出处 | 证据等级 | 关系 |
|---|---|---|---|
| **Barber & Ramdas 2017**, The p-filter: multi-layer FDR control for grouped hypotheses | JRSS-B 79(4):1247–1268 | **E3 全文级**（已入库） | **束 B 最强近邻**：桶级与池化预算并存的既有分配理论 |
| Ramdas, Barber, Wainwright, Jordan, A unified treatment of multiple testing with prior knowledge using the p-filter | arXiv:1703.06222 / AoS | 题录级 | 统一四类先验知识；未入库 |
| Katsevich & Sabatti, Multilayer knockoff filter | 题录级（经在线摘要转述） | 题录级 | 多分辨率同时 FDR 控制 |

### 束 B 要回答的问题

**问题：桶级预算与池化预算并存时的既有分配理论是什么？**

**答（E3 全文级，Barber & Ramdas 2017）**：p-filter 直接处理这一情形，且结论与本课题当前做法**存在重要差异**。

- **设定**：输入 `n` 个 p 值与 `M ≥ 1` 个划分（称「层」，layers），每层 `m` 自带目标水平 `α_m`。最细划分（`n` 个单点组）对应通常的 FDR，**最粗划分（全部 `n` 个假设归为一组）对应池化**（摘要第 16–18 行；物理第 1 页）。
- **主定理 Theorem 4**（物理第 11 页）：对每个 `m = 1, …, M`，

  > `E[FDP_m(t̂_1, …, t̂_M)] ≤ α_m · (H⁰_m / G_m)`

  即**每层各自按自己的 `α_m` 同时受控**。
- **关键差异**：这里**没有把一个全局预算 Bonferroni 均分到各层**。各层预算独立指定，耦合通过 Theorem 3（物理第 11 页）的**联合阈值搜索**——取 `T̂(α_1,…,α_M)` 可行域中每维的最大点——实现，而不是靠预算分裂。
- **划分无需嵌套**：原文明确「in general the M partitions do not need to be nested; they are not constrained to form a hierarchy of partitions」（物理第 11 页，Theorem 4 之后）。
- **特例回收**：`M=1` 且取最细划分即精确回收 BH；取最粗划分即回收 Simes 全局检验（物理第 1 页摘要）。

**对本课题的直接含义（待验证推论，非文献原结论）**：本课题现在把 `δ=0.05` 按「方向 × 层」**均分**（Bonferroni），是保守做法。p-filter 证明了在 FDR 语义下，多层预算**可以不经均分而同时成立**。是否存在 FPR／`δ` 语义下的对应结果，本次检索所及**未找到**，须标为**待验证**。

---

## 3 束 C：安全告警预算的分面控制

### 查询式与命中

| 通道 | 查询式 | 结果 |
|---|---|---|
| 本地 hybrid | `告警预算 误报疲劳 安全运营 分面控制 每组误报率` | 前 6：Alahmadi 99% 误报、StealthCup、**Ho Hopper 横向移动告警预算**、BAYWATCH、Almeida、Choi 预指定预测校正 |
| 在线 | `intrusion detection per-group false alert budget alert fatigue subgroup false positive rate control stratified` | 命中 CALIBURN（arXiv:2605.24696）、PACT（arXiv:2605.22324）、SOC 告警疲劳综述（ACM CSUR，DOI `10.1145/3723158`）、CRC-SGAD（arXiv:2504.02248） |
| 在线 | `Transcendent conformal evaluator malware classification per-class thresholds calibration Barbero Jordaney` | 命中 Transcend（USENIX Sec 2017）、Transcendent（arXiv:2010.03856，IEEE S&P 2022） |

### 直接近邻

| 论文 | 出处 | 证据等级 | 关系 |
|---|---|---|---|
| **CALIBURN 2026**, Operationally Calibrated Streaming Intrusion Detection with Regime-Dependent Conformal Risk Control | arXiv:2605.24696 | **E3 全文级**（已入库） | **束 C 最强近邻**：IDS ＋ 告警预算 ＋ 保形风险控制 |
| **Barbero et al. 2022**, Transcending Transcend | IEEE S&P 2022 / arXiv:2010.03856 | **E3 全文级**（已入库） | 安全域**逐类**保形阈值的最直接先例 |
| Ho et al. 2021, Hopper | 本地已有 | E3（旧笔记） | 用户给定告警预算 `B` 作为**上界**，但是排序式预算，无条件保证 |
| Alahmadi et al. 2022, 99% False Positives | 本地已有 | E3（旧笔记） | 告警疲劳的定性证据 |
| Jordaney et al. 2017, Transcend | USENIX Security 2017 | 题录级 | Transcendent 的前身；未单独入库 |
| SOC 告警疲劳综述 2025 | ACM CSUR, DOI `10.1145/3723158` | 题录级 | 未入库 |

### 束 C 要回答的问题

**问题：本课题「实体长度分面的误报预算」在安全域有无直接近邻？**

**答：本次检索所及，没有找到把「实体级分面」与「有限样本条件误报证书」二者合一的安全域工作。**两个最接近的先例各自缺一半：

**CALIBURN（E3，物理第 18 页）**——有告警预算与保形风险控制，但保证是**边际的**：

> 原文：a Conformal Risk Control wrapper that converts an operator-supplied alert budget `α` into a **marginally-valid** threshold `τ̂_α` under exchangeability of validation and test negatives.（物理第 18 页 §3.3 末）

- 「regime-dependent」指跨**攻击流行率区间**（LITNET-2020 `5.2%`、UNSW-NB15 约 `64%` 等三档）的**经验性能依赖**，是该文报告的**失效发现**，不是条件保证。原文摘要称「conformal risk control is strongly regime-dependent across attack prevalence」，并说 CALIBURN 在稀有攻击区间达 AUC-PR `0.943`，但在高流行率区间「degenerates」。
- 分析单元是**流（flow）**，不是实体；预算语义来自 SLO 燃烧率（`99.9%` SLO → 至多 `0.1%` 流消耗预算，物理第 19 页）。

**Transcendent（E3，物理第 8、14 页）**——有逐类阈值，但**不是证书**：

- 确有 per-class rejection thresholds（物理第 8 页 §III 概述）。
- 但阈值由**约束优化搜索**得到：目标函数 `F`（如保留元素的 F1）在约束函数 `G`（如逐类拒绝元素数）不超过 `C` 下最大化，原始工作用**穷举网格搜索**，本文改为**随机搜索**以避开维度灾难（物理第 14 页）。
- **没有 `δ`，没有有限样本上界**。也提到实践中可「manual (e.g., picking a quartile visually using an alpha ...)」（物理第 8 页），即经验分位选阈——这正是 Tong 2018 所反对的做法。

**研究空白证据（本次检索所及）**：安全域现有工作在「分面」与「证书」上二选一——Transcendent 有分面无证书，CALIBURN 有证书（边际）无分面，Hopper 有预算无条件保证。

---

## 4 新颖性差量表

**参照最近邻**：束 A 的 Vovk 2012 条件 ICP（机制正源）＋束 B 的 Barber–Ramdas p-filter（预算分配）＋束 C 的 CALIBURN / Transcendent（安全域应用）。

| # | 差量维度 | 最近邻的做法 | 本课题「长度分层 Tong 证书」 | 证据状态 |
|---|---|---|---|---|
| 1 | **统计量类型** | Vovk 条件 ICP 基于**交换性下的非一致性分数秩**（p 值，式 (10)，物理第 7 页） | 基于 **Neyman–Pearson 次序统计量 ／ 单侧 Clopper–Pearson 精确二项上界**，控制的是**类型一错误上界**而非覆盖 | **有全文支撑**：Vovk 物理第 7–8 页 vs Tong 2018 已入库笔记 |
| 2 | **保证的双参数结构** | Vovk Prop 3 给类别条件误差 ≤ `ε`（**无 `δ`**）；Prop 2a 给 `(ε,δ)` 但**对池化**且用 Hoeffding；Bates RCPS Definition 1（物理第 2 页）给 `(γ,δ)` 但**池化、不分组** | 每个**桶**各自签发 `(q, δ')` 证书，`δ` 按方向×层分裂后用 **CP 精确上界** | **有全文支撑**（Vovk 物理第 5、8 页；Bates 物理第 2 页）。**CP 的选择现有直接文献依据**：Bates Remark 4（物理第 7 页）称二元损失下精确二项界最紧且「should always be used」，附录 B Theorem B.1（物理第 29 页）给出构造，较 Bentkus 界改进一个 `e` 因子。**差量因此不在「用 CP」，而在「逐桶各签一份」** |
| 3 | **δ 的二维分裂** | 本次检索所及**无既有方案**；p-filter 的多层预算**不经均分**即同时成立（Theorem 4，物理第 11 页） | 按「方向 × 层」均分 `δ=0.05`（保守 Bonferroni） | **差量成立但方向不利**：本课题做法比 p-filter **更保守**，最优性**待验证** |
| 4 | **分析单元** | CALIBURN 为**流**级（物理第 18 页）；Transcendent 为**样本／应用**级；Vovk 为**样例**级 | **实体级**（实体 = 一组流的聚合），且分层键是**实体的流数长度** | **有全文支撑**（CALIBURN、Transcendent 全文） |
| 5 | **分层键的语义** | Vovk 的 taxonomy 通常取**标签**（label-conditional）；CALIBURN 的 regime 取**攻击流行率** | 取**实体观测长度**（流数桶）——一个与「证据累积量」直接相关、且**不接触最终标签**的协变量 | **有全文支撑**（Vovk 物理第 7 页 label taxonomy；CALIBURN 摘要 regime 定义） |
| 6 | **序贯路径统计量** | Vovk、Barber、Bates 均为**单次批量**判定；CALIBURN 为流式但按单流判定 | 池化路径取「**路径最大**」（M1' Tong 池化路径最大 Q0），即在实体的观测路径上取极值后再证书化 | **待验证**：本次检索所及未见把路径极值统计量纳入组条件证书的工作，但**未做穷尽检索**，标为待验证 |
| 7 | **告警预算语义** | CALIBURN 预算来自 **SLO 燃烧率**，作用于流比例（物理第 19 页）；Hopper 预算是**排序截断上界** | 预算是**实体级 FPR 上界 `q=4%`**，且**每桶各自**受同一或分配后的预算约束 | **有全文支撑**（CALIBURN 物理第 18–19 页；Hopper 已入库笔记） |
| 8 | **联合告警事件重校准** | 本次检索所及未见近邻 | C11 变体在分层 Tong 之上做「联合告警事件重校准」 | **待验证**：未检索到直接近邻，也未排除；不得据此声称首创 |
| 9 | **可行性已被数值核验** | — | 本机精确二项计算：`n=3949/δ'=0.05⁄12` → 可证最大 FP `125`、经验率 `3.17%`、证书税 `0.83pt`；`n=486`（最细分裂）→ `1.65%`／`2.35pt` | 已核验（数学），来自实施计划 V1 台账 |

**三句话版本**：

1. 组条件有限样本控制的**机制本身不是新的**——Vovk 2012 的条件 ICP（物理第 7 页式 (10)、第 8 页 Prop 3）已经给出按分类法分层计算 p 值并获得类别条件保证的标准做法。
2. 本课题的差量集中在**统计量与单元**：把秩式 p 值换成 NP 次序统计量／Clopper–Pearson 精确上界，把样例级换成**实体级**且分层键取**观测长度**，并在池化侧取**路径最大**统计量——注意**「用 CP」本身不是差量**（Bates RCPS 物理第 7 页 Remark 4 已明确二元损失下应当始终采用精确二项界），差量在「**逐桶各签一份**」；其中路径极值进组条件证书这一条**本次检索所及未见近邻，标为待验证**。
3. 本课题的 **`δ` 按「方向×层」均分是保守做法而非创新**：p-filter（Theorem 4，物理第 11 页）已证明多层预算可以不经均分而同时受控，因此这一维度上本课题**弱于**已有理论，应作为局限或后续改进方向，**不得写成贡献**。

---

## 5 与本课题冲突的负面结果

### 5.1 条件覆盖的不可能性定理——**不阻断本机制**

**Barber, Candès, Ramdas, Tibshirani 2021（E3 全文级）**：

- **Proposition 1**（物理第 7 页，转述自 Vovk 2012 与 Lei–Wasserman 2014）：若 `Ĉ_n` 满足 `(1−α)` **对象条件覆盖**，则对几乎所有非原子点 `x`，`E[leb(Ĉ_n(x))] = ∞`。即**精确的对象条件覆盖在分布无关设定下不可能非平凡地达到**。
- **Vovk 2012 Proposition 4**（物理第 8–9 页）独立给出同型结论。

**关键区分（决定本机制是否被阻断）**：该不可能性针对**对象条件**（conditioning on 具体 `X_{n+1}=x`），**不针对有限划分的组条件**。两条直接证据：

1. Barber et al. **脚注 3**（物理第 3 页）明确写道，Vovk 2012 的训练条件覆盖「is very different from the type of conditioning that we consider here」。
2. Barber et al. **物理第 11 页式 (7)** 把「有限个子群内覆盖」单列，并明确其为 Vovk 2012、Lei–Wasserman 2014 所**可达**的版本：

   > `P{Y_{n+1} ∈ Ĉ_n(X_{n+1}) | X_{n+1} ∈ X_k} ≥ 1 − α`，for some **fixed partition** `R^d = X_1 ∪ … ∪ X_K`

**裁决**：本课题的长度桶是**预先固定的有限划分**，落在式 (7) 的可达情形，**不被不可能性定理阻断**。

### 5.2 复杂度代价定理——给出分层粒度的理论边界

**Barber et al. Theorem 4**（物理第 15 页）：当条件集类 `X` 的 `VC_a.e.(X) ≥ 2n + 2` 时，`(1−α, δ, X)` 条件覆盖的长度下界**退化为仅要求边际覆盖所能得到的平凡下界**——即分层不再带来任何好处。反向地，§4.2.2（物理第 15 页起）证明 **VC 维低时高效预测可行**。

**对本课题的含义（推论，非文献原结论）**：`K` 个长度桶构成的固定划分 VC 维远低于 `2n+2`（`n` 为校准样本量，本课题为数千量级），因此处在**可行侧**。但该定理给出一条**明确的失效方向**：桶数不能随样本量增长而无限细化。

### 5.3 真正的代价是样本饥饿，不是不可能性

- Vovk **Prop 2a**（物理第 5 页）：`(ε,δ)` 有效性要求校准集 `n` 显著超过 `N := (−ln δ)/(2ε²)`，修正项按 `sqrt(−ln δ / (2n))` 增长——**组越小，代价越大**。
- 本课题已用精确二项计算量化该代价（「证书税」）：`n=3949` → `0.83pt`；`n=486` → `2.35pt`。**代价随桶细化单调上升，与理论方向一致。**

### 5.4 交换性前提在跨年场景可能不成立

本地已有笔记（`wiki/papers/methodology/2024-Angelopoulos-保形风险控制.md`）记录：CRC 的「基本保证依赖交换性」。Gibbs 笔记亦记录自适应保形「不自动给每个时间点、每个协议条件或每个攻击子类的条件覆盖」。
**含义**：分层证书在**源年内**成立；跨年（LSPR23→LSPR24）不自动继承，须另行处理。这与已有的 Tong 笔记边界一致（「不能声称源域次序统计量对 LSPR24 仍提供同一有限样本保证」）。

---

## 6 入库清单

**6 篇全部完成载荷级入库**（PDF 原件 + 全文笔记 + Zotero 条目附 PDF）。

| # | 论文 | `raw/` 原件（页数） | `wiki/` 全文笔记 | Zotero |
|---|---|---|---|---|
| 1 | Vovk 2012 条件归纳保形 | `raw/papers/methodology/2012-Vovk-Conditional-Validity-Inductive-Conformal.pdf`（23） | `wiki/papers/methodology/2012-Vovk-条件归纳保形预测.md` | `BTUXMTL4` |
| 2 | Barber et al. 2021 条件预测推断的极限 | `raw/papers/methodology/2021-Barber-Limits-Distribution-Free-Conditional-Predictive-Inference.pdf`（34） | `wiki/papers/methodology/2021-Barber-条件预测推断的极限.md` | `GXS9LEYJ` |
| 3 | Barber & Ramdas 2017 p-filter | `raw/papers/methodology/2017-Barber-Ramdas-p-filter-Multilayer-FDR-Grouped-Hypotheses.pdf`（22） | `wiki/papers/methodology/2017-Barber-Ramdas-p-filter多层分组FDR控制.md` | `UNL7F38G` |
| 4 | Bates et al. 2021 RCPS | `raw/papers/methodology/2021-Bates-Distribution-Free-Risk-Controlling-Prediction-Sets.pdf`（34） | `wiki/papers/methodology/2021-Bates-分布无关风险控制预测集.md` | `7YL8GW7G` |
| 5 | CALIBURN 2026 | `raw/papers/attack-detection/2026-CALIBURN-Regime-Dependent-Conformal-Risk-Control-IDS.pdf`（58） | `wiki/papers/methodology/soc-alert-operations/2026-CALIBURN-区间依赖保形风险控制的告警预算.md` | `VS3N78LQ` |
| 6 | Barbero et al. 2022 Transcendent | `raw/papers/attack-detection/2022-Barbero-Transcendent-Conformal-Evaluation-Malware.pdf`（19） | `wiki/papers/attack-detection/2022-Barbero-Transcendent逐类保形拒识阈值.md` | `X8EXBQ66` |

**下载曲折记录**：Bates RCPS 的 arXiv PDF 为 `15,500,831` 字节，前四次下载均因超时被截断导致 xref 损坏；改用 `curl -C -` 断点续传后取得完整文件，`pdfinfo` 报 34 页。

**笔记合同状态**：六篇全部通过 `literature_search lint --strict`（`paper-note-search/v1`，`error_count=0`）。**这是本仓库首批满足 v1 严格模式的论文笔记**——对照组 `2024-Angelopoulos-保形风险控制.md` 在同一检查下有 19 项错误，全库此前无一篇含 `cannot_support` 字段。新笔记因此额外具备 `doi`／`arxiv_id`／`tasks`／`methods`／`supports`／`cannot_support` 等结构化列，可被后续检索直接命中。

**索引同步**：`wiki/papers/methodology/INDEX.md` 新增「组条件控制与分层预算分配」小节并在既有风险控制、告警预算两节各补一条；`wiki/papers/attack-detection/INDEX.md` 新增「安全域的分面阈值与告警预算」小节并加方法学入口交叉链接。

---

## 7 未关闭疑点

1. **`δ` 二维分裂的最优性未验证**：p-filter 证明 FDR 语义下多层预算无需均分；FPR／证书语义下是否有对应结果，本次检索所及未找到，也未穷尽检索。**这是当前最需要关闭的疑点**，因为它直接决定本课题的 `δ` 均分该写成局限还是可改进项。
2. **路径最大统计量的两个未决问题**：其一，进组条件证书这一做法未检索到直接近邻，但**未做穷尽检索**，不得据此声称首创；其二，Bates RCPS Theorem 1（物理第 5 页）要求风险关于阈值**单调**，路径极值统计量下单调性**未验证**，若不成立须改走 Learn-then-Test 式多重检验路线。
3. **Gibbs–Cherian–Candès（arXiv:2305.12616）与 Kandinsky（arXiv:2502.17264）未入全文**：二者分别处理协变量函数类与**重叠组**，可能进一步压缩本课题差量，目前仅题录级。**建议下一轮优先补这两篇。**
4. **Learn-then-Test（arXiv:2110.01052，AoAS 2025）未入库**：把风险控制改写为多重检验并支持非单调风险与 λ 网格 FWER 校正，是疑点 2 的直接备选路线，目前题录级＋摘要级。
5. **联合告警事件重校准（C11）**无检索到的近邻，标为待验证。
6. **Transcend（Jordaney et al., USENIX Security 2017）原文未单独入库**，逐类阈值的原始形式只经 Transcendent 转述。
7. **p-filter 的 PRDS 假设（式 (5)）在本课题实体级 p 值上是否成立未验证**。长度桶间实体互不重叠，独立性比一般基因组场景更可能成立，但未做检验。
8. **Transcendent 的后续负面证据仅摘要级**：一篇 2026 年工作报告其 CCE 评估器在 family-vs-family 设定下显著更差，该结论只经在线摘要转述，未取全文。
