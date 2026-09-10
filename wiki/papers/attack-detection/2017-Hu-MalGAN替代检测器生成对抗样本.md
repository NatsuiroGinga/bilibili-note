---
title: "Generating Adversarial Malware Examples for Black-Box Attacks Based on GAN"
title_zh: "MalGAN：用替代检测器生成绕过黑盒恶意软件检测器的对抗样本"
authors: [Weiwei Hu, Ying Tan]
year: 2017
date: 2026-09-10
journal: "arXiv 预印本 arXiv:1702.05983v1 [cs.LG]，2017-02-20；本地 PDF 共 7 页，PDF 内未标注正式发表出处"
source_pdf: "[[raw/papers/attack-detection/2017-Hu-MalGAN.pdf]]"
arxiv_id: "1702.05983"
tags:
  - 对抗规避
  - 生成对抗网络
  - 恶意软件检测
  - 黑盒攻击
  - 替代模型
  - 学习型攻击者
  - P4近邻
  - 类型/论文
key_finding: "用**替代检测器（substitute detector）**拟合黑盒恶意软件检测器，再让生成器最小化替代检测器对对抗样本给出的恶意概率（式(2)、式(3)，p.3）。黑盒检测器全程不被攻击方训练，只被查询、只回传标签（§2.3，p.3；算法 1，p.3）。在 6 个黑盒分类器上把 TPR 从 92.20%–97.89%（训练集）/92.27%–95.64%（测试集）压到 **0.00%–0.20%**（同训练集，表 1，p.4）；训练集不同时 RF/DT 仍为 0.80%/2.11%（测试集）、其余四种 ≤0.01%（表 2，p.5）。对照迁移来的梯度法（Grosse 等，白盒）把 TPR 只降到 93.52%（训练集）/90.96%（测试集），重训替代网络后训练集 46.18% 但测试集仍 90.12%（§4.3，p.5）。§4.4（p.6）另做检测器与 MalGAN **交替重训 10 轮**：检测器重训后 TPR 回到 100%，MalGAN 重训后 1 个 epoch 内回到 0%。"
method: "GAN 结构：生成器 G(·) 以「恶意特征向量 m ⊕ 噪声 z」为输入，经 sigmoid + 二值化得到待加特征 o'，最终对抗样本 m' = m | o'（逐元素按位或，只增不减），并用光滑函数 G_θg(m,z)=max(m,o) 让梯度可穿过（式(1)，p.2）；替代检测器 D_θd 用黑盒检测器给出的预测标签为真值做拟合（式(2)，p.3），生成器最小化 log D(G(m,z))（式(3)，p.3）"
baseline: "Grosse 等的白盒梯度法（迁移到黑盒并用替代网络，§4.3，p.5）；随机森林/逻辑回归/决策树/SVM/MLP/投票集成六种黑盒检测器（§4.1，p.4）"
aliases: [MalGAN, 2017-Hu-MalGAN, Hu2017-MalGAN, MalGAN替代检测器]
related: ["[[2018-Lin-IDSGAN入侵检测攻击生成]]", "[[2020-Song-MAB-Malware学习型黑盒规避]]", "[[2022-Randhawa-RELEVAGAN共演化攻击者]]", "[[2026-Jureckova-恶意软件检测双层共演化]]", "[[2019-Cortellazzi-问题空间对抗攻击与约束]]", "[[2017-Foerster-多智能体经验回放稳定化]]", "[[2017-HernandezLeal-多智能体非平稳性综述]]"]
---

# MalGAN：用替代检测器生成对抗样本

> 页码锚点：本地 PDF 共 7 页。威胁模型与架构总览见 §2.1（**p.2**）；生成器与式(1) 见 §2.2（**p.2**）；替代检测器见 §2.3（**p.3**，Figure 1 亦在 **p.3**）；训练损失式(2)(3) 与算法 1 见 §3（**p.3**）；实验设置见 §4.1（**p.4**）；表 1 同训练集结果见 **p.4**（Figure 2 在 **p.5**）；表 2 不同训练集结果见 **p.5**；对照梯度法见 §4.3（**p.5**，Figure 3 在 **p.6**）；检测器重训实验与表 3 见 §4.4（**p.6**）；结论见 §5（**p.6**）。

## 一句话

这是"**学习型攻击者 + 学习 surrogate、真目标冻结**"这一模式的早期原型：用一个神经网络去拟合黑盒检测器，再让生成器专门骗这个替身，从而在**只能查询标签、拿不到置信分数**的条件下把检测率压到接近零；论文同时用 §4.4 的交替重训实验说明"攻击方重训远快于防守方重训"，但**从未把检测器放进攻击方的联合优化里**。

## 与 P4 的距离（report (8) 四级表的第 **3** 层）

| 层级 | 学习关系 | 本文位置 |
| --- | --- | --- |
| 1 固定/算法攻击 + 学习检测器 | 攻击器固定，检测器学 | CharBot / MaskDGA / Drichel 多攻击 AT |
| 2 学习型攻击者 + 固定目标检测器 | attacker 学，deployed detector 不学 | MAB-Malware |
| **3 学习型攻击者 + 学习 surrogate** | **attacker 与 surrogate 同学，真目标固定** | **← MalGAN 在此** |
| 4 attacker + 实际 defender 共演化 | 双方互随 | RELEVAGAN / 2026 bilevel |

**判定依据（全部取自原文）**：

- **真目标是外部系统，攻击方不训练它**。§2.1（p.2）："The black-box detector is an external system... Malware authors do not know what machine learning algorithm it uses and do not have access to the parameters of the trained model." 攻击方**只知道它用哪类特征**（p.2："the only thing malware authors know about the black-box detector is what kind of features it uses"）。
- **替代检测器是代理，靠查标签拟合**。§2.3（p.3）："The goal of the substitute detector is to fit the black-box detector. The black-box detector will detect this training data first and output whether a program is benign or malware. **The predicted labels from the black-box detector are used by the substitute detector.**" 式(2)（p.3）的 $L_D$ 正是拿 $BB_{Benign}$（黑盒判为良性的集合）与 $BB_{Malware}$（黑盒判为恶意的集合）做二分类拟合——**训练信号是黑盒的硬标签，不是黑盒的梯度**。
- **算法 1 只更新两个网络的权重**。§3 算法 1（p.3）第 6、7 行只出现 $\nabla_{\theta_d}L_D$ 与 $\nabla_{\theta_g}L_G$，**没有任何一步更新黑盒检测器**。
- 生成器优化的是**替代检测器**的判分，而非真目标：式(3)（p.3）$L_G=\mathbb{E}_{m\in S_{Malware},z}\log D_{\theta_d}(G_{\theta_g}(m,z))$，论文自述"Since the substitute detector tries to fit the black-box detector, the training of the generator will further fool the black-box detector"——**这是一种转述的期望，不是被优化的目标本身**。

**必须同时报告的反面证据（§4.4，p.6）**：本文确实做了**检测器与 MalGAN 交替重训**的实验——"We alternated retraining the black-box detector and retraining Mal-GAN for **ten times**"，结果十次都与表 3 相同。这使它比单纯的"目标冻结"更接近共演化。但它**仍不是第 4 层**，理由有三：①该重训是**论文假想的防守方动作**（"If antivirus vendors collect enough adversarial malware examples, they can retrain..."），不是被建模的学习型 defender；②交替**不是联合优化**，两方各自独立训练，没有共享目标、没有对手感知的更新规则；③论文的结论方向是"攻方重训更快"（1 个 epoch 内把 TPR 从 100% 拉回 0%，p.6），属于**速度不对称论证**，不是共演化机制的实证。

## 机制（§2–§3，p.2–3）

### 三个角色与数据流

1. **黑盒检测器**（外部，冻结）：输入程序特征向量，输出"良性/恶意"标签；用 RF、LR、DT、SVM、MLP 与投票集成六种实现（§4.1，p.4）。
2. **生成器** $G_{\theta_g}$（学习）：$M$ 维恶意二值特征向量 $\boldsymbol m$ 与 $Z$ 维噪声 $\boldsymbol z\sim U[0,1)$ 拼接 → 多层前馈 → sigmoid 输出 $\boldsymbol o\in(0,1)^M$ → 以 0.5 为阈值二值化得 $\boldsymbol o'$（§2.2，p.2）。
   - **只增不减**：最终对抗样本 $\boldsymbol m'=\boldsymbol m \mid \boldsymbol o'$（逐元素按位或）。原文明写不放心的理由（p.2）："we only consider to add some irrelevant features to malware. Removing a feature from the original malware may crack it."举例："WriteFile" API 被删掉程序就无法正常写入，恶意软件可能失效。
   - **梯度直通的技巧**（式(1)，p.2）：$G_{\theta_g}(\boldsymbol m,\boldsymbol z)=\max(\boldsymbol m,\boldsymbol o)$。$m$ 中已为 1 的维度输出恒为 1、梯度被挡住；为 0 的维度输出神经网络的实数值，梯度可以回传。$\boldsymbol m'$ 就是 $G_{\theta_g}(\boldsymbol m,\boldsymbol z)$ 的二值化版本。
3. **替代检测器** $D_{\theta_d}$（学习）：吃程序特征向量 $\boldsymbol x$，输出"$\boldsymbol x$ 是恶意"的预测概率；训练数据的**真值标签不用**，改用黑盒检测器打出的标签（§2.3，p.3）。

### 两个损失

$$L_D = -\mathbb{E}_{\boldsymbol x\in BB_{Benign}}\log\!\big(1-D_{\theta_d}(\boldsymbol x)\big) - \mathbb{E}_{\boldsymbol x\in BB_{Malware}}\log D_{\theta_d}(\boldsymbol x) \tag{2, p.3}$$

$$L_G = \mathbb{E}_{\boldsymbol m\in S_{Malware},\ \boldsymbol z\sim p_{uniform[0,1)}} \log D_{\theta_d}\big(G_{\theta_g}(\boldsymbol m,\boldsymbol z)\big) \tag{3, p.3}$$

要点：式(3) 的期望取自**真实恶意数据集** $S_{Malware}$，而**不是**黑盒标为恶意的集合（p.3 明确区分）；$L_G$ 对 $\theta_g$ 最小化，即压低"替身认为它恶意"的概率，与常规 GAN 中生成器抬高判别器判真的方向相反（此处"真"= 良性）。

### 训练循环（算法 1，p.3）

每轮：采样恶意 minibatch $M$ → 生成 $M'$ → 采样良性 minibatch $B$ → **用黑盒给 $M'$ 与 $B$ 打标签** → 按 $\nabla_{\theta_d}L_D$ 更新替代检测器 → 按 $\nabla_{\theta_g}L_G$ 更新生成器。恶意与良性 minibatch 大小的比例，与两个数据集规模之比相同（p.3）。

## 非平稳性处理方式

**攻击方处理"检测器在学"的方式：用交替重训换来速度不对称，而不是把对手建进模型。**

- **主体设定里检测器根本不学**：全文的攻防关系是"攻击方查询—拟合—生成"，检测器是静止的查询接口。非平稳性在此设定下**尚不存在**。
- **§4.4（p.6）人为引入一次非平稳**：防守方（AV 厂商）收集对抗样本→重训黑盒→公开更新；攻击方拿到新版→重训 MalGAN→再攻击。论文交替做了 **10 次**，结论是表 3 每次相同：

| | 检测器重训后、MalGAN 未重训 | MalGAN 重训后 |
| --- | --- | --- |
| 训练集 | 100% | 0% |
| 测试集 | 100% | 0% |

（表 3，p.6；TPR 指检测器对对抗样本的检出率，100% = 全部被检出，0% = 全部逃逸。）

- **论文给出的非平稳性论证是"时间成本不对称"**而非机制（p.6）：厂商要凑够对抗样本并标注是长期过程，"Adversarial malware examples have enough time to propagate before the black-box detector is retrained and updated"；而攻击方重训 MalGAN 快得多——"reducing TPR from 100% to 0% can be done **within one epoch**"。结论原文用到"passive position"（被动地位）。
- **另一处理由是"分布可控"**（§2.1，p.2 与 §5，p.6）：对抗样本的分布由生成器权重决定，攻击方可以频繁改变该分布，"making the black-box detector cannot keep up with it, and unable to learn stable patterns from it"。这是**把非平稳性当作攻击资源**的表述，不是对它的建模。
- **没有的东西**：无对手建模、无对手感知的更新规则、无收敛或遗憾保证、无对对手学习率的假设。§4.2（p.4）自述 GAN 训练本身就不稳（"the convergence curve is a bit shaking... the training of GAN is usually unstable"）。

## 可迁移机制

1. **"代理拟合 + 在代理上优化"的两段式，能把纯黑盒问题变成有梯度的白盒问题**（§2.3，p.3）：代理的训练信号是目标模型的**硬标签**，不需要任何置信分数或梯度。对"DGA 单步扰动博弈"，这对应：当真检测器只回黑白时，先用查询回执训一个 substitute，再在 substitute 上做扰动搜索。
2. **只增不减的离散算子 + 光滑化直通**（§2.2，p.2）：$\boldsymbol m'=\boldsymbol m\mid \boldsymbol o'$ 把"保持原样本可用性"编码进算子结构，$\max(\cdot,\cdot)$ 再把梯度引过二值化。**DGA 的对应物是"只做字符替换/插入、不删关键字符"的算子约束**——先由算子结构保证合法性，再解决梯度问题。
3. **把"未修改"作为结构约束而非事后过滤**：本文不让生成器碰任何需要保留的特征（由 OR 结构保证，p.2）。这与 IDSGAN 的 restricted modification（功能特征表，Table 1，p.5）是同一思路的两种实现，可作为"DGA 单步扰动必须保留攻击功能"这一约束的设计参照。
4. **用替代模型的表现间接论证真目标（转述性论证）**：论文通篇没有"真目标梯度"，其有效性主张依赖"代理论证"（p.3 原话）。**这是该路线的结构性弱点**：替代与真目标在对抗样本分布上会失配——§4.3（p.5）正是这一失配的实证（见下条）。
5. **§4.3 给出替代模型失配的直接反例，价值高于其正面对照**（p.5）：把 Grosse 等的白盒梯度法迁到黑盒并用替代网络时，**迭代过程中对抗样本分布逐渐偏离替代网络的训练分布**，导致替代网络不再逼近真目标——TPR 收敛到 93.52%（训练集）/90.96%（测试集）；即使每轮用当前对抗样本**重训替代网络**，训练集降到 46.18%，**测试集仍为 90.12%**（p.5 原话归因："the odd probability distribution of these adversarial examples limits the generalization ability of the substitute neural network"）。**对 DGA 的启示：任何"代理拟合 + 代理上搜索"的方案都必须单独验证代理在对抗分布上的保真度，训练集改善不代表测试集改善。**
6. **报告"攻防重训的时间不对称"这一可测量量**（§4.4，p.6）：本文可精确引用的量是"攻方重训 1 个 epoch 即可把检出率从 100% 拉回 0%"。若本课题要做攻防交替实验，**每轮墙钟/步数应双向记录**，而不是只报攻击成功率。

## 不能直接声称内容

- **不能说它是第 4 层或共演化**：真目标在主体设定中冻结（§2.1、§2.3、算法 1，p.2–3）；§4.4 的交替重训是**假想的厂商动作 + 独立交替训练**，不构成联合优化，见上文判定依据。
- **不能说它做了 DGA 或域名空间实验**：特征空间是 **160 维系统级 API 二值特征向量**（§4.1，p.4），样本是 Windows 程序（从 `malwr.com` 抓取，p.4 脚注 1），**与域名字符空间不是同一问题空间**。
- **不能把其 TPR 数字与 DGA 工作并列**：指标是"对对抗样本的真阳性率"，与 CharBot/MaskDGA 的 TPR@FPR、Drichel 的 ROC-AUC 等**不同指标、不同目标模型、不同威胁模型**。
- **不能把 0% 说成"完全绕过"**：① 只在二值特征、只增不减的算子下成立；② 数据集无时间隔离，训练/测试仅随机划分（§4.1，p.4 的两种划分都在同一份 18 万程序集合内）；③ 黑盒检测器是**同分布的**ML 模型，不是生产 AV。
- **不能声称真实场景可复现**：无沙箱功能保持验证（对比 MAB-Malware 用 Cuckoo 验证），论文**未报告**生成样本是否仍能执行或保持恶意功能——论文只从结构上论证"不删除特征所以不破坏功能"（p.2），**这是论证不是实测**。
- **不能说"检测器重训无效"**：§4.4 明确说检测器重训后**能检出全部对抗样本**（表 3 中间列 = 100），论文的主张只是"攻方重训更快"。
- **论文自身的稳定性限制**：§4.2（p.4）自述收敛曲线抖动、GAN 训练不稳定；实验为单次运行，**未报告种子、方差或置信区间**；超参（$Z=10$、170-256-160、160-256-1、lr 0.001、最多 100 epoch、Adam）在验证集上调得，验证集按"取验证集上检测率最低的 epoch"选模型（§4.1，p.4）——**该选择规则本身使用了攻击成功性作为模型选择依据**。
- **出处未经核实**：本地 PDF 为首版 arXiv 预印本（`arXiv:1702.05983v1 [cs.LG]`，2017-02-20，见 p.1 页边标识），**PDF 内未标注任何正式会议或期刊**；引用时不应写具体会议名。

## 文献信息

- arXiv：<https://arxiv.org/abs/1702.05983>（本地 PDF 为 **v1**，页边标识 `arXiv:1702.05983v1 [cs.LG] 20 Feb 2017`，p.1）
- 作者与单位：Weiwei Hu、Ying Tan（通讯作者，p.1 脚注），北京大学机器感知重点实验室 / 智能科学系
- 本地原件：`raw/papers/attack-detection/2017-Hu-MalGAN.pdf`（共 7 页，含参考文献）
- 全文转换：`/tmp/dga-adv-20260910/marl/2017-Hu-MalGAN/`（MinerU md + json，页码由 json 的 `page_idx` 实测，页号 = `page_idx` + 1）
- 交叉核验：IDSGAN 参考文献第 5 条亦记为 `arXiv:1702.05983`（`2018-Lin-IDSGAN` 全文，p.12），与本地 PDF 页边标识一致
- 资助：NSFC 61375119、北京市自然科学基金 4162029、973 计划 2015CB352302（p.7）
