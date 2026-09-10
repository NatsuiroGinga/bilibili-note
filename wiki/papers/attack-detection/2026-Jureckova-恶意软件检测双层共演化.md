---
title: "Adversarial Co-Evolution of Malware and Detection Models: A Bilevel Optimization Perspective"
authors: [Olha Jurečková, Martin Jureček, Matouš Kozák, Róbert Lórencz]
year: 2026
date: 2026-09-10
journal: "arXiv:2604.22569v1（2026-04-24），10 页"
source_pdf: "[[raw/papers/attack-detection/2026-Jureckova-Bilevel-Malware-CoEvolution.pdf]]"
tags:
  - 对抗规避
  - 学习型攻击者
  - 双侧共演化
  - 双层优化
  - 迭代最优响应
  - 恶意软件检测
  - 累积回放
  - P4先例
  - 类型/论文
key_finding: "把恶意软件检测的攻防写成双层问题：外层防御者最小化分类损失、内层攻击者（MAB-malware）在当前模型上最大化逃逸（式(2)(3)，p.5），并用**迭代最优响应**近似求解（算法 1，p.4）。三家族实测：一次对抗训练在 DCRat 上几乎无效（ER 仍 **90.00%**），迭代双层把 ER 压到 **0%–1.89%**（表 1–3，p.7–8），同时把成功逃逸的平均查询次数抬高最多两个数量级（Strab：**31.17 → 3118.0**，表 2，p.8）。"
method: "双层优化 + 迭代最优响应（IBR）：防御者用「原始训练集 ∪ 历轮全部对抗样本」累积重训（式(5)，p.6；算法 1 p.4），攻击者每轮用 MAB-malware 在**原始**样本上、对**最新**模型重新搜索（式(4)，p.5）；模型统一为 Random Forest，特征为 EMBER 2018，攻击者被假定对当前模型完全访问（白盒，§4.3，p.4）"
baseline: "Exp(1) 非对抗训练的 RF 基线；Exp(2) 单次对抗增广重训（one-shot adversarial training）；攻击者为 MAB-malware"
aliases: [2026-Jureckova-Bilevel-Malware-CoEvolution, Bilevel-Malware-CoEvolution, Jureckova2026-Bilevel, 恶意软件检测双层共演化]
related: ["[[2020-Song-MAB-Malware学习型黑盒规避]]", "[[2022-Randhawa-RELEVAGAN共演化攻击者]]", "[[2017-Hu-MalGAN替代检测器生成对抗样本]]", "[[2018-Lin-IDSGAN入侵检测攻击生成]]", "[[2024-Drichel-DGA检测鲁棒分类]]", "[[2019-Cortellazzi-问题空间对抗攻击与约束]]", "[[2019-Peck-CharBot规避攻击]]"]
---

# 恶意软件与检测模型的对抗共演化：双层优化视角

> 页码锚点：本地 PDF 共 10 页。题名、关键词、摘要 **p.1**；§1 引言 **p.1–2**；§2 相关工作 **p.2**；§3 背景 **p.3**（§3.1 PE 对抗攻击与式(1) **p.3**；§3.2 MAB-malware **p.3**）；§4 方法 **p.3–5**（§4.1 **p.4**；§4.2 **p.4**；§4.3 双层与算法 1、白盒假设 **p.4**；§4.4 最终评价 **p.5**）；§5 博弈与双层形式化 **p.5–6**（§5.1 式(2)(3) **p.5**；§5.2 **p.5**；§5.3 式(4)(5) **p.5–6**）；§6 实验 **p.6–9**（§6.1 数据 **p.6**；§6.2 指标 **p.6**；§6.3 Mokes **p.6**＋表 1 **p.7**；§6.4 Strab **p.7**＋表 2 **p.8**；§6.5 DCRat **p.7**＋表 3 **p.8**；§6.6 迭代演化 **p.7**＋表 4 **p.8**；§6.7 讨论 **p.8**；§6.8 收敛 **p.9**）；§7 结论 **p.9**。

## 一句话

这篇不发明新的攻击或新的检测器，而是把"对抗训练只做一次"这件事**结构化地做多次**：每一轮用攻击者在**当前**模型上重新搜出的逃逸样本，累积进防御者的训练集，直到攻击者再也搜不出新样本。三家族实测显示一次对抗训练在 DCRat 上会失效（ER 仍 90.00%），而迭代双层能把 ER 压到 0%–1.89%，并把成功逃逸的查询代价抬高最多两个数量级。

## 与 P4 的距离（report (8) 四级表的第 **4** 层）

| 层级 | 学习关系 | 典型 | 本文位置 |
| --- | --- | --- | --- |
| 1 固定/算法攻击 + 学习检测器 | 攻击器固定，检测器学 | CharBot / MaskDGA / Drichel | |
| 2 学习型攻击者 + 固定目标检测器 | attacker 学，deployed detector 不学 | MAB-Malware | |
| 3 学习型攻击者 + 学习 surrogate | attacker 与 surrogate 同学，真目标固定 | MalGAN / IDSGAN | |
| 4 attacker + 实际 defender 共演化 | 双方互随 | RELEVAGAN / 2026 bilevel | **← 本文在此** |

**判定依据（逐条对原文）**：

1. **defender 是谁**：被评测的那个分类器本身（`f_θ`，§5.1，p.5），实现为 Random Forest（§4.1，p.4；§4.4，p.5）。**没有 surrogate、没有替代模型**；攻击者每轮的目标模型就是"该实验方案下最近一次训练出的防御模型"（§4.4「the target classifier used by the MAB-malware agent during the evaluation phase corresponds **exactly** to the most recently trained defender model」，p.5）。
2. **defender 在哪里更新、更新什么**：在**外层**更新分类器参数 θ——最小化在攻击者最优响应下的平均损失：

$$\min_{\theta \in \Theta} \frac{1}{|D^{train}|}\sum_{(x,y)\in D^{train}} \left[\mathcal{L}\left(f_\theta(x+\delta^*(\theta)),\, y\right)\right] \qquad (2)$$

   并**用累积历史攻击集重训**（算法 1 的 Defender step，p.4；式(5)，p.6）：

$$f_{i+1} = \mathrm{Train}\left(D^{train} \cup \bigcup_{j=0}^{i} (D_{adv}^{train})_j\right) \qquad (5)$$

   注意：定义在**原始 `D^train` 样本加扰动后**的样本上计算损失，且所有对抗样本**保持正确标签 malware**（§4.3「All samples retain correct labels」，p.4）。
3. **attacker 是谁、学什么**：MAB-malware（多臂强盗式 RL 攻击者，§3.2，p.3）。它每轮解**内层最大化**：

$$\delta^*(\theta) \in \arg\max_{\delta \in S(x)} \mathcal{L}_{\mathrm{atk}}\left(f_\theta(x+\delta),\, y\right) \qquad (3)$$

   `S(x)` 是功能保持变换集（式(1) 要求 `Sem(x) = Sem(x_adv)`，p.3）。
4. **是否与 attacker 同步**：**是，按迭代轮次交替**（§4.3「Iterative Cycle (for i = 1 to Max iter)」，p.4）：先训练初始 `f_0` → 攻击者产出 `(D_adv^train)_0` → 循环内「Defender 用截至 i-1 轮的全部攻击样本重训 `f_i`」→「Attacker 对 `f_i` 重新搜出 `(D_adv^train)_i`」。外层/内层关系由 §5.1 明写：「the **inner problem** represents the attacker's best response δ*(θ) to a fixed model θ, while the **outer problem** represents the defender's quest for parameters θ that are robust to that optimal response.」（p.5）
5. **停止条件**：以收敛判据终止——「The optimization terminates when no new adversarial samples are generated.」（表 4 题注，p.8）；§5.3 补充「Given the discrete nature of the PE file transformation space S(x), we monitor convergence through the stability of the evasion rate across successive iterations.」（p.5）；目标是达到实际的 **ε-Nash 均衡**（§5.3，p.5；§6.8，p.9）。

**与 RELEVAGAN 的关键差别（同为第 4 层但机制不同）**：本文的共演化是**轮次粒度**的（3–5 轮收敛，§6.7，p.8），不是 batch 粒度；防御者的更新是**重新训练**（`Train(...)`，式(5)，p.6），不是同一网络上的连续梯度步。**攻击者每轮无记忆**：MAB-malware 反复作用在**原始** `D^train` 样本上（§4.3，p.4），不复用上一轮的对抗样本、也不跨轮保留策略状态——记忆全部挂在防御者一侧。

## 机制（§3–§5，p.3–6）

**（1）攻击侧（§3.1、§3.2，p.3）**：对抗样本 `x_adv = x + δ`，受限于 `δ ∈ S(x)` 且 `Sem(x) = Sem(x_adv)`（式(1)，p.3）——PE 空间是**离散**的，且扰动必须保持二进制可执行与原恶意载荷。MAB-malware 把攻击过程写成多臂强盗，分两阶段：（a）**探索**阶段依次选择并施加宏/微级变换，直到逃逸成功或达到修改预算；（b）**精炼**阶段逐个复评变换，若删除某变换不影响逃逸则丢弃它，从而减少所需修改数（§3.2，p.3）。代表性变换：追加良性内容（overlay／新节）、插入或重命名节、使证书/调试相关字段失效、改可选头校验和、语义保持的代码改动（§3.2，p.3）。

**（2）防御侧三种方案（§5.2，p.5）——同一双层问题的三种近似**：

| 方案 | 双层视角 |
| --- | --- |
| Exp 1 基线 | 非策略性防御者：假定 `δ = 0`，只解外层，完全忽略内层最大化 |
| Exp 2 对抗重训 | 一步反应式防御：先对基线模型 `f_θ0` 解一次内层得到 `(D_adv^train)_0`，再**只更新一次** θ |
| Exp 3 双层 IBR | 策略性防御者：用**迭代最优响应**近似完整双层解 |

**（3）算法（§4.3 算法 1，p.4）**：

```text
Input: D^train, Max_iter
Init:  Train f_0 on D^train
       (D_adv^train)_0 ← MAB-malware(f_0, D^train)
for i = 1 to Max_iter:
    Defender: D_aug^train ← D^train ∪ ⋃_{j=0}^{i-1} (D_adv^train)_j ;  f_i ← Train(D_aug^train)
    Attacker: (D_adv^train)_i ← MAB-malware(f_i, D^train)
return f_{Max_iter}
```

   `Max_iter` **由经验确定**（§4.3「with Max iter determined empirically」，p.4），原文未给固定值；实际收敛发生在 3–5 轮（§6.7，p.8）。

**（4）威胁模型**：攻击者被假定**对当前模型 `f_i` 有完全访问**，即白盒（§4.3，p.4）。作者的理由是遵循 Kerckhoffs 原则、评估最坏情况下的防御边界。

**（5）评价**：模型同时在**干净测试集**与**对抗测试集**（干净集 + 其恶意样本的 MAB-malware 扰动版本，良性样本不变）上评价（§4.4，p.5；§6.2，p.6）。测试集在三个实验中**固定不变**，且从不用于训练或对抗样本生成（§4.1，p.4）。

## 非平稳性处理方式

**原文有明确的处理项，方式是"累积回放"+"收敛早停"，没有 ensemble、没有 surrogate、没有窗口遗忘、没有在线漂移检测。**

- **防御者侧——累积回放（cumulative replay）**：每一轮的训练集是**全部历史攻击样本的并集**，不做时间窗截断、不做样本重加权：

$$f_{i+1} = \mathrm{Train}\left(D^{train} \cup \bigcup_{j=0}^{i} (D_{adv}^{train})_j\right) \qquad (5) \quad \text{(p.6)}$$

  这是本文对付"对手在变"的核心机制——旧攻击留下的样本永久留在训练集里，保证防御边界单调扩张。§6.7 把该设计的效果直接写成结论：「a single round of augmentation only covers a narrow subset of the attack surface, allowing the attacker to easily find alternative evasion paths.」（p.8）
- **攻击者侧——无记忆重搜**：每轮 MAB-malware 都作用在**原始** `D^train` 恶意样本上、以**当前**模型为目标（§4.3，p.4；式(4)，p.5）。即攻击者不是"接着上一轮改"，而是"对着新模型从头再搜一遍"。非平稳性因此**单侧化**：防御方带记忆，攻击方每轮重置。
- **停止条件——收敛即停**：当某一轮不再产生新的成功对抗样本时终止（表 4 题注，p.8）；§5.3 用"跨轮逃逸率是否稳定"作为收敛监控量（p.5）；判据是可机械判定的（逃逸集不再增长）。
- **作者对设定本身的自限**：攻击者白盒是**上界设定**（§4.3，p.4）；作者在 §6.8 明确把结果限定为「the maximum achievable robustness for the **EMBER 2018 feature set** used on our dataset and **Random Forest** architecture」（p.9）。
- **原文未做**：没有对攻击者侧的非平稳性做稳定化（无 league／PSRO／策略池），没有对防御者的重训频率、遗忘窗口或样本权重做消融，也没有把"攻击者在防御者更新后重新适应"的中间轨迹单独画出（表 4 只给每轮新增/累计样本数）。

## 实验结果（§6，p.6–9）

**数据（§6.1，p.6）**：三个恶意软件家族 Mokes / DCRat / Strab，特征集为 **EMBER 2018**，恶意二进制来自 **RawMal-TF**。这三个家族是被选出来的，因为 MAB-malware 对 EMBER 目标分类器在其上成功率很高：Mokes **2058/2216**、DCRat **1010/1026**、Strab **1595/2191** 生成成功。**所有报告结果都来自每家族 500 条的平衡子集（250 恶意 + 250 良性）**——作者明说是为了让迭代双层实验在算力上可做。模型统一为 Random Forest（§4.1 p.4；§4.4 p.5）。

**指标（§6.2，p.6）**：Acc / Prec / Rec（式(6)）；**Evasion Rate (ER)** = 成功绕过检测的恶意样本占比；**Average Queries (Avg Q)** = MAB-malware 找到一次成功扰动所需的平均查询次数（攻击复杂度代理量）。

**表 1 — Mokes（p.7）**

| 实验 | 干净 Acc/Prec/Rec | 对抗 Acc/Prec/Rec | ER (%) | Avg Q |
| --- | --- | --- | --- | --- |
| (1) Baseline | 1.00 / 1.00 / 1.00 | 0.68 / 1.00 / 0.51 | **95.83** | 15.93 |
| (2) Adv. Train | 1.00 / 1.00 / 1.00 | 0.97 / 1.00 / 0.94 | **6.25** | 932.33 |
| (3) Bilevel | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | **0.00** | - |

**表 2 — Strab（p.8）**

| 实验 | 干净 Acc/Prec/Rec | 对抗 Acc/Prec/Rec | ER (%) | Avg Q |
| --- | --- | --- | --- | --- |
| (1) Baseline | 0.90 / 0.92 / 0.89 | 0.64 / 0.92 / 0.50 | **77.36** | 31.17 |
| (2) Adv. Train | 0.92 / 0.96 / 0.89 | 0.74 / 0.96 / 0.61 | **45.28** | 79.71 |
| (3) Bilevel | 0.98 / 0.98 / 0.98 | 0.97 / 0.98 / 0.96 | **1.89** | **3118.0** |

**表 3 — DCRat（p.8）**

| 实验 | 干净 Acc/Prec/Rec | 对抗 Acc/Prec/Rec | ER (%) | Avg Q |
| --- | --- | --- | --- | --- |
| (1) Baseline | 0.98 / 1.00 / 0.96 | 0.66 / 1.00 / 0.49 | **96.00** | 16.44 |
| (2) Adv. Train | 0.99 / 1.00 / 0.98 | 0.68 / 1.00 / 0.52 | **90.00** | 60.13 |
| (3) Bilevel | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | **0.00** | - |

**表 4 — 逐轮新增/累计对抗样本（p.8）**

| 家族 | 逐轮 新增 / 累计 | 收敛 |
| --- | --- | --- |
| Mokes | 130/130，139/269，5/274，4/278 | 4 轮；§6.8 称第 4 轮零可利用性 |
| DCRat | 155/155，155/310，155/465 | 3 轮"阈值式"收敛；§6.8 称第 3 轮 |
| Strab | 128/128，118/246，25/271，99/370，1/371 | 5 轮，累计最多（371） |

**其他关键读数**

- **一次对抗训练会失效**：DCRat 上 Exp 2 的 ER **不降反升至 90.00%**，对抗召回停在 0.49（表 3，p.8；§6.7，p.8 称「a single round of augmentation only covers a narrow subset of the attack surface」）。
- **攻击代价**：Strab 上成功逃逸的 Avg Q 由 31.17 升到 **3118.0**，约**两个数量级**（表 2，p.8；§6.7，p.8；摘要 p.1）。
- **干净护栏不退化**：Strab 干净 Acc 0.90→0.98、DCRat 0.98→1.00，加固没有牺牲干净性能（§6.7，p.8）。
- **跨家族难度读数**：Mokes 快速收敛、DCRat 呈"阈值式"（连续 3 轮各 155 条后骤降）、Strab 是"更复杂的共演化动态"（128, 118, 25, 99, 1），需要更大的累计样本量（371 vs Mokes 278）（§6.6，p.7）。
- **原文未报告**：壁钟训练时间、每轮的训练成本、Avg Q 的方差/置信区间、多种子重复；**也未见对抗测试集恶意样本的绝对条数**（只能由 ER 反推）。

## 可迁移机制

1. **把攻防写成显式双层、把两种防御写成同一双层问题的两种近似**（§5.2，p.5）：Exp1 = 解 `δ=0` 的外层；Exp2 = 只解一次内层的单步近似；Exp3 = 迭代最优响应。这套写法让"一次对抗训练为什么不够"成为**同框架内的对照**，而不是另起炉灶。DGA 三臂设计可直接复用这个叙事骨架。
2. **累积回放全部历史攻击样本**（式(5)，p.6）：防御方训练集只增不减，是对付"攻击者每轮换招"的最廉价手段。DGA 上对应"历轮扰动域名池全部保留进分类器训练集"。
3. **以"本轮是否还有新的成功逃逸"作为停止条件**（表 4 题注，p.8；§5.3，p.5）：不依赖梯度、可机械判定，非常适合 DGA 单步扰动博弈——逃逸集不再增长即停，且天然对应课程/迭代实验的终止门禁。
4. **把攻击者代价作为第一类指标报出来**（§6.2 Avg Q，p.6；§6.7，p.8）：ER 降到 0 有时只是因为攻击者预算被卡住；`31.17 → 3118.0` 才是"防御真的变强"的旁证。DGA 实验应同时报成功率与尝试/查询次数，缺一不可。
5. **按家族分组报告收敛轮数**（§6.6，p.7）：Mokes 4 轮、DCRat 3 轮阈值式、Strab 5 轮且需要 371 条累计样本——"收敛轮数"本身就是对手难度的读数。DGA 应按 DGA 家族或对抗方法分组报，而不是只给总体均值。
6. **把"干净指标不退步"单列为一条结论**（§6.7，p.8）：Strab/DCRat 上干净准确率反而升高。DGA 的干净护栏应照此作为独立结论申报，而不是塞进脚注。
7. **白盒攻击者作为上界设定要说清适用面**（§4.3，p.4；§6.8，p.9）：作者用 Kerckhoffs 原则论证白盒合理，但在结论处把结果限定在"该特征集 + 该架构下的最大可达鲁棒性"。DGA 上若用白盒/可微代理搜索，必须同样把结论限定回特征与架构。

## 不能直接声称内容

- **不能说双层优化解决了 DGA 漂移或时间漂移**：全文对象是 Windows PE 二进制 + EMBER 2018 特征（§6.1，p.6），**没有 DGA／域名空间实验**，也没有时间轴实验。
- **不能把 ER = 0% 说成"攻击不可能"**：作者自己把结果限定为「the maximum achievable robustness for the EMBER 2018 feature set used on our dataset and Random Forest architecture」（§6.8，p.9）；扩展到 DNN／GBDT 是未来工作（§7，p.9）。
- **不能说结论建立在完整数据集上**：所有结果来自每家族 **500 条**平衡子集（250 恶意 + 250 良性，§6.1，p.6），作者明说是为让迭代实验在算力上可行的妥协。
- **不能说攻击者是现实的自适应攻击者**：MAB-malware 被假定对当前模型**完全访问**（白盒，§4.3，p.4），属上界设定；真实黑盒攻击者的代价-收益曲线可能不同。
- **不能说它是"双侧联合学习模型"**：攻击者每轮从零重搜（§4.3，p.4），不携带跨轮策略状态、不做参数更新；"共演化"体现在**防御方带记忆、攻击方对更新后的模型重新适应**这一交替结构上。
- **不能把正文的"最后为 0"当成表 4 读数**：§6.6（p.7）写 Mokes 新增样本"from 130 to 5 and finally 0"，而**表 4（p.8）第 4 轮记的是 4（累计 278）**，第 4 轮并非 0；两处不一致。引用时应以表 4 数字为准，并注明正文另有"最后为 0"的表述。
- **不能把 Avg Q 的 `-` 读成 0**：Mokes 与 DCRat 的 Bilevel 行 Avg Q 为 `-`（表 1，p.7；表 3，p.8），其含义应是 ER=0 时没有成功逃逸样本可统计，但**原文未作说明**。
- **不能引用文献综述中的数字当作本文读数**：§2（p.2）的 `15.9%` 最高逃逸率（Kozak & Jureček 2023）与 Gym-malware `5.73 秒/样本`（Louthanová et al. 2024）均引自他人工作。
- **不能与 DGA 的逃逸率数字并列**：目标模型、问题空间（二进制改写 vs 域名字符扰动）、威胁模型（白盒 vs 查询式）、指标口径全不相同。

## 文献信息

- arXiv：<https://arxiv.org/abs/2604.22569>（v1，2026-04-24；编号取自 PDF 首页 arXiv 戳 `arXiv:2604.22569v1 [cs.CR] 24 Apr 2026`）
- 正式出处：**原文未标注会议或期刊**；版式为 SciTePress 会议模板（含 `Keywords:`、ORCID 脚注），作者单位是捷克技术大学 FIT
- 作者（取自 PDF 元数据）：Olha Jurečková、Martin Jureček、Matouš Kozák、Róbert Lórencz
- 资助：CTU 基金 SGS26/187/OHK3/3T/18 与 OP VVV CZ.02.1.01/0.0/0.0/16_019/0000765（p.9）
- 本地原件：`raw/papers/attack-detection/2026-Jureckova-Bilevel-Malware-CoEvolution.pdf`
- 转换件：`/tmp/dga-adv-20260910/marl/2026-Jureckova-Bilevel-Malware-CoEvolution/2026-Jureckova-Bilevel-Malware-CoEvolution.md`（中途产物，非持久保存）
