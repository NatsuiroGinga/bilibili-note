---
title: "IDSGAN: Generative Adversarial Networks for Attack Generation against Intrusion Detection"
title_zh: "IDSGAN：用生成对抗网络生成规避入侵检测系统的对抗恶意流量记录"
authors: [Zilong Lin, Yong Shi, Zhi Xue]
year: 2018
date: 2026-09-10
journal: "arXiv 预印本 arXiv:1809.02077v5 [cs.CR]（本地 PDF 为 2022-05-08 版本，首版 2018-09）；本地 PDF 共 12 页，PDF 内未标注正式会议名"
source_pdf: "[[raw/papers/attack-detection/2018-Lin-IDSGAN.pdf]]"
arxiv_id: "1809.02077"
tags:
  - 对抗规避
  - 生成对抗网络
  - 入侵检测
  - 黑盒攻击
  - 替代模型
  - 功能保持约束
  - 学习型攻击者
  - P4近邻
  - 类型/论文
key_finding: "在 NSL-KDD 上用 WGAN 结构生成对抗恶意流量**特征记录**，让判别器以黑盒 IDS 的**实时预测标签**为真值去模仿它（§3.3 Discriminator，p.5；算法 1 第 8–10 行，p.7），并设计 **restricted modification 机制**：每类攻击的「功能特征」在生成中**保持不变**，只改非功能特征（§3.3，p.4；各攻击的功能特征组见 Table 1，p.5）。在黑盒 IDS 为 7 种算法时，DoS 检出率由 73.28%–84.94% 降到 **0.01%–0.72%**（EIR 99.13%–99.99%），U2R 与 R2L 由 0.64%–12.66% 降到 **0.00%–0.02%**（表 2，p.8）。与 4 种白盒对抗攻击及 2 种静态 GAN 基线相比检出率最低：MLP 目标上 DoS **0.61%**、U2R&R2L **0.00%**，对照 FGSM 7.19%/0.15%、静态 GAN 32.45%/3.39%（表 3，p.11）。**关键限定**：黑盒 IDS 在全部实验中都是**预训练后冻结**的（§4.1，p.7），论文**没有任何更新/重训 IDS 的实验**——所谓动态只发生在判别器一侧。"
method: "WGAN 结构：生成器 5 层线性（前 4 层 ReLU，输出 m 维），输入为 m 维原始样本 M 与 n 维均匀噪声 N 的拼接，输出裁剪到 [0,1]、其二值特征以 0.5 为阈值二值化（§3.3 Generator，p.5）；判别器为多层神经网络，用黑盒 IDS 对同一批样本的实时预测标签做真值来学习模仿它（§3.3 Discriminator，p.5）。损失：L_G = E_{M∈S_attack,N} D(G(M,N))（式(1)，p.6）；L_D = E_{s∈B_normal}D(s) − E_{s∈B_attack}D(s)（式(2)，p.6）——即 WGAN 的 Wasserstein 形式，RMSProp 优化（p.7）"
baseline: "JSMA、Targeted FGSM、DeepFool、CW 四种对抗攻击（按 Wang [14] 的设置），以及 Yang [15] 的无约束静态 GAN 与加上 functional 约束后的静态 GAN（表 3，p.11）"
aliases: [IDSGAN, 2018-Lin-IDSGAN, Lin2018-IDSGAN]
related: ["[[2017-Hu-MalGAN替代检测器生成对抗样本]]", "[[2020-Song-MAB-Malware学习型黑盒规避]]", "[[2022-Randhawa-RELEVAGAN共演化攻击者]]", "[[2026-Jureckova-恶意软件检测双层共演化]]", "[[2019-Cortellazzi-问题空间对抗攻击与约束]]", "[[2017-Foerster-多智能体经验回放稳定化]]", "[[2017-HernandezLeal-多智能体非平稳性综述]]"]
---

# IDSGAN：生成规避入侵检测的对抗流量记录

> 页码锚点：本地 PDF 共 12 页。摘要与贡献、黑盒设定与"查询"假设见 §1（**p.1–2**）；对 Yang [15] 静态判别器的批评见 §2（**p.3**）；数据集描述见 §3.1（**p.3**）；预处理见 §3.2（**p.4**）；restricted modification 机制见 §3.3（**p.4**，Figure 1 在 **p.4**）；Table 1 功能特征表见 **p.5**；生成器与判别器细节见 §3.3（**p.5**）；两个损失式(1)(2) 见 **p.6**；算法 1 见 **p.7**；实验设置与指标 DR/EIR（式(3)(4)）见 §4.1（**p.7–8**）；不同攻击类别结果（表 2）见 §4.2（**p.8**，Figure 2 在 **p.9**）；修改特征数鲁棒性见 §4.3（**p.10**，Figure 3 在 **p.10**）；基线对比（表 3）见 §4.4（**p.11**）；结论与未来工作见 §5（**p.11–12**）。

## 一句话

这是"**学习型攻击者 + 学习 surrogate、真目标冻结**"在流量域的对照实现：判别器被训练成**每一轮都重新拟合黑盒 IDS 的当前输出**，生成器只改攻击的"非功能特征"以保住攻击功能；但论文里**黑盒 IDS 从头到尾都是预训练好的固定模型**，"能攻击被更新的 IDS"是主张而不是被验证的事实。

## 与 P4 的距离（report (8) 四级表的第 **3** 层）

| 层级 | 学习关系 | 本文位置 |
| --- | --- | --- |
| 1 固定/算法攻击 + 学习检测器 | 攻击器固定，检测器学 | CharBot / MaskDGA / Drichel 多攻击 AT |
| 2 学习型攻击者 + 固定目标检测器 | attacker 学，deployed detector 不学 | MAB-Malware |
| **3 学习型攻击者 + 学习 surrogate** | **attacker 与 surrogate 同学，真目标固定** | **← IDSGAN 在此** |
| 4 attacker + 实际 defender 共演化 | 双方互随 | RELEVAGAN / 2026 bilevel |

### 专项核实：判别器是否"动态逼近"真实黑盒 IDS？

**是——判别器侧确有闭环逼近，但这不等于 IDS 本身在训练。**逐条列原文证据：

1. **判别器的训练目标就是模仿黑盒 IDS**。§3.3（p.5）："the discriminator is responsible for **learning and imitating** the black-box IDS based on the detected samples and their **latest predictions** from the target IDS."
2. **每一轮都重新查询、用实时标签当训练真值**。§3.3（p.5）："In adversarial training, the normal traffic records and the adversarial malicious traffic records are first classified by the black-box IDS. Then, for the imitation to the black-box IDS, **the same dataset labeled by the target IDS is shared to the discriminator as the training set whose current labels are the real-time predictions from this IDS**."算法 1（p.7）把这个循环写死成第 8–10 行：B 分类 → D 分类 → 按式(2) 更新 D。
3. **论文明确用它区分于"判别器是预训练分类器"的静态做法**。§2（p.3）批评 Yang [15]："without learning the latest knowledge of IDS like querying, the discriminator of GAN, a pretrained classifier, **cannot dynamically adapt** the generation for the attack against the **updated** IDS models."——**"查询式动态模仿"正是本文自认的增量**。
4. **但黑盒 IDS 全程冻结**。§4.1（p.7）："In the evaluation, the black-box IDS models have been **pretrained with their training set before generating adversarial samples**."算法 1（p.7）的 `Require` 只列 `S_normal`、`S_attack`、`N` 和 **`The pretrained black-box IDS B`**；循环体里只更新 G 与 D，**没有任何一步更新 B**。全文**没有**"重训 IDS 后再攻击"的实验（对照：MalGAN §4.4，p.6 至少做了 10 轮交替重训）。
5. **"能攻击被更新的 IDS"是断言**。§1 贡献（p.2）："By dynamically learning the real-time results from IDS models in adversarial training, IDSGAN can attack the **updated** IDS models powered by different algorithms."§3.3（p.5）："**Reflecting the dynamic optimization of the structure and parameters in the black-box IDS**, the IDS's real-time predictions are leveraged for the discriminator to learn the IDS dynamically."——**该句的"动态优化"是一个反事实条件（若 IDS 变了，判别器会跟上），论文从未触发这个条件**。

**结论**：IDSGAN 的判别器在**实现上**比 MalGAN 更接近"跟踪对方"（每轮重查标签），但两者的**学习关系仍是第 3 层**——真目标不参与训练、不受攻击方影响；IDSGAN 只是把"拟合代理"从一次性做成了每轮刷新。要升到第 4 层，缺的是**防守方在攻击压力下更新**这一环。

## 机制（§3，p.3–7）

### 数据与预处理（§3.1–§3.2，p.3–4）

- NSL-KDD，train = `KDDTrain+`，test = `KDDTest+`；四类恶意流量：Probing、DoS、U2R、R2L（p.3）。
- 每条记录 41 个特征：**9 个离散 + 32 个连续**，按语义划为 intrinsic / content / time-based traffic / host-based traffic 四组（p.3）。
- 预处理：三个非数值特征（protocol type、service、flag）做 one-hot 嵌入；其余数值特征 **min-max 归一化到 [0,1]**（p.4）。

### restricted modification 机制（§3.3，p.4；Table 1，p.5）

动机（p.4）：对抗记录要能**在真实网络里复现并真正发起攻击**，所以生成必须保留攻击功能。"the attack attribute would remain unaltered if we solely fine-tuned **nonfunctional** features"——于是**每类攻击的功能特征在生成中保持不变**，这些被保留的特征称为 unmodified features。

Table 1（p.5）逐类给出功能特征所在的特征组（√ 表示该组为功能特征、必须保留）：

| 攻击类别 | Intrinsic | Content | Time-based | Host-based |
| --- | --- | --- | --- | --- |
| Probe | √ | | √ | √ |
| DoS | √ | | √ | |
| U2R | √ | √ | | |
| R2L | √ | √ | | |

配套的三条实现约束（p.5）：① intrinsic 特征在**所有**攻击里都是功能特征，故**非数值特征一律不修改**；② 生成器输出裁剪到 [0,1]；③ 被修改的**二值特征**以 0.5 为阈值重新二值化。

### 生成器（§3.3 Generator，p.5）

$m$ 维原始样本 $\boldsymbol M$（已预处理）与 $n$ 维噪声 $\boldsymbol N$（$U[0,1)$）**拼接**后输入；**5 层线性**，前 4 层 ReLU $F=\max(0,x)$，输出层 $m$ 个单元以保证与 $\boldsymbol M$ 同维。损失由判别器的分类结果算得（式(1)）。

### 判别器（§3.3 Discriminator，p.5）

多层神经网络，做恶意/正常的二分类；**同时承担模仿黑盒 IDS 的职责**——训练集就是黑盒 IDS 刚刚标注过的那一批（正常记录 + 生成器产出的对抗恶意记录），标签取黑盒的实时预测。生成器的梯度**从判别器回传**（p.6）。

### 两个损失与优化（式(1)(2)，p.6；p.7）

$$L_G = \mathbb{E}_{M\in S_{attack},\,N}\, D\big(G(M,N)\big) \tag{1}$$

$$L_D = \mathbb{E}_{s\in B_{normal}} D(s) \;-\; \mathbb{E}_{s\in B_{attack}} D(s) \tag{2}$$

其中 $B_{normal}$、$B_{attack}$ 是判别器的训练集（正常记录与对抗恶意记录），**后者的标签来自黑盒 IDS**（p.6）。该形式即 Wasserstein GAN：判别器不接 sigmoid，靠 $L_D$ 拉大正常/恶意两类的打分差；生成器最小化 $L_G$ 以压低对抗样本的打分。优化器 **RMSProp**，判别器训练带 **weight clipping**（阈值 0.01，§4.1，p.7）。

### 训练循环（算法 1，p.7）

`Require`：$S_{normal}$、$S_{attack}$、噪声 $N$、**预训练黑盒 IDS $B$**。
每轮：先跑若干 G-step（G 基于 $S_{attack}$ 生成对抗样本、按式(1) 更新 G）；再跑若干 D-step（**B 先分类**训练集拿到预测标签 → D 分类同一训练集 → 按式(2) 更新 D）。

### 实验设置（§4.1，p.7）

PyTorch 实现；黑盒 IDS 用 scikit-learn 搭；Linux PC / Intel Core i7-2600。批大小 64、**100 个 epoch**、生成器与判别器学习率均 **0.0001**、判别器 weight clipping **0.01**、噪声维度 **9**（p.7）。
七种黑盒 IDS 算法：SVM、NB、MLP、LR、DT、RF、KNN，**全部在生成对抗样本之前预训练好**（p.7）。
划分（p.7）：黑盒 IDS 用 `KDDTrain+` 的**一半**训练；判别器用**另一半中的正常记录 + 生成器的对抗恶意记录**；生成器用**另一半中该攻击类别的记录**训练；测试集是该攻击类别在 `KDDTest+` 中的记录。**每次只生成一个攻击类别的对抗样本**，因为各类别待改的非功能特征不同（p.7）。

### 指标（式(3)(4)，p.8）

$$DR = \frac{\text{被正确检出的攻击数}}{\text{全部攻击数}}, \qquad EIR = 1 - \frac{\text{对抗检出率}}{\text{原始检出率}}$$

$DR$ 越低表示逃逸越多；$EIR$ 越高表示相对原始样本的逃逸增幅越大。优化目标是**低 DR + 高 EIR**（p.8）。

## 非平稳性处理方式

**攻击方处理"检测器在学"的方式：把判别器做成每轮重新查询、重新拟合的在线替身；对"检测器真的变了"只给设计、不给实验。**

- **每轮刷新的闭环**（§3.3，p.5；算法 1 第 8–10 行，p.7）：黑盒 IDS 的**实时预测**被当作判别器训练集的当前标签。这是对"目标可能变化"的结构性准备——只要 IDS 换版本，下一轮查询拿到的标签就变，判别器随之被拉向新 IDS。
- **论文把这一点写进自述增量**（§2，p.3）：静态判别器"cannot dynamically adapt the generation for the attack against the updated IDS models"；查表式动态模仿是本文相对 Yang [15] 的核心区别。§4.4（p.11）复述："IDSGAN's dynamical imitation strategy by querying the target IDS strengthens evasion attacks remarkably."
- **但非平稳从未被触发**（§4.1，p.7）：黑盒 IDS **预训练后冻结**，七种算法各训一次，**没有重训、没有版本切换、没有对抗训练式的防守方更新**。论文的非平稳性停留在**接口设计**层面。
- **没有的东西**：无对手建模（不推断 IDS 的决策边界，只拟合其输出）、无对手学习率/变化率假设、无跟踪误差或收敛性保证、无"防守方更新后攻击成功率如何衰减"的测量。
- **与 MalGAN 的差别值得记一笔**：MalGAN 的替代检测器是"训一次、之后再查询"的设定，但它**做了 §4.4 的交替重训实验**（10 轮）；IDSGAN 把"每轮重查"做成机制，却**没有做任何 IDS 更新的实验**。**"机制更像共演化"与"证据更像共演化"在本对中恰好互换**——引用时不要把机制描述误当作已验证的非平稳性处理能力。

## 可迁移机制

1. **把"必须保留的功能"显式列成一张表，作为生成器的硬约束**（Table 1，p.5；§3.3，p.4）：本文没有把功能保持做成软惩罚，而是**按攻击类别逐组冻结功能特征**，其余维度才允许改。**对 DGA 单步扰动博弈，这直接对应"哪些字符位置/长度/后缀必须保留"的白名单**——先冻结功能位，再在剩余位搜索，既保证合法又缩小搜索空间。
2. **"查询 → 用回执标签重训代理"做成每轮刷新，而不是一次性拟合**（算法 1，p.7）：这条把代理失配（MalGAN §4.3，p.5 暴露的病灶）从"无法修复"变成"每轮部分修复"。**可迁移的动作是：代理模型在每一轮攻击迭代后都用目标的最新回执 increment 更新一次**，并**单独测量代理保真度**（本文未测，见下）。
3. **用相对指标 EIR 把"原始检出率差异很大"的多个目标拉到同一尺度**（式(4)，p.8）：七个黑盒 IDS 的 DoS 原始检出率在 73%–85% 之间、U2R/R2L 只有 0.64%–12.66%，绝对值不可直接横比。**但相对指标有饱和陷阱**（见"不能直接声称内容"第 4 条），迁移时应**同时报告绝对 DR 与相对 EIR**。
4. **把"修改多少特征"当作独立的鲁棒性轴来扫**（§4.3，p.10）：做法不是调超参，而是**往 unmodified 集合里加非功能特征**（每个非功能特征组随机取 50%），从而系统性地减少可改维度。**对 DGA 的对应操作是"允许改动的字符位数"扫描**——且要注意本文的实测方向：可改维度减少后 EIR 只轻微下降或持平（DoS 在 KNN 上约降 1.00%，NB 上变化最明显），**说明该攻击对"少改几个特征"并不敏感**。
5. **攻击者只改非功能位，可以同时保住攻击语义和逃逸率**（§3.3，p.4；表 2 的 "√" 行，p.8）：加了额外 unmodified 特征后 EIR 仍有 98.50%–100%，**这是"约束不必然牺牲攻击力"的一条正面证据**——对"DGA 扰动必须保持域名可用/可注册"的约束设计是支持性先例。
6. **用黑盒的硬标签做代理训练（而非置信分数）**（§1，p.2："the outputs of the black-box IDS models can be obtained by querying IDS with traffic records"）：与 MalGAN 同构，进一步支持"只用回执标签即可驱动学习型攻击者"这一可行性。

## 不能直接声称内容

- **不能说论文验证了"能攻击被更新的 IDS"**：黑盒 IDS **预训练后冻结**（§4.1，p.7），算法 1 的 `Require` 明写 `The pretrained black-box IDS B`，全文无重训/换版实验。该主张是设计意图，**未验证**。
- **不能说它是第 4 层或共演化**：真目标不参与训练、不受攻击方影响；判别器再"动态"也只是**拟合一个静止函数**。判别器每轮刷新 ≠ 双边学习。
- **不能把 EIR ≈ 100% 读成"检出率降到零"**：$EIR = 1 - \text{对抗DR}/\text{原始DR}$（式(4)，p.8）是**相对量**。U2R/R2L 的 SVM 原始 DR 只有 **0.68%**、对抗 DR **0.00%**（表 2，p.8），绝对变化仅 0.68 个百分点，EIR 却是 100.00%。**原始检出率越低，EIR 越容易饱和到 100%，也越不稳定**。U2R/R2L 的原始检出率低是该数据集上 U2R/R2L 样本少导致的学习不足，**论文自己承认这一点**（§4.2，p.8："the insufficient learning makes the low original detection rates to U2R and R2L"）。
- **不能把表 2 与表 3 的 "Original" 混为一谈**：表 2（p.8）的 MLP DoS 原始 DR 是 **82.70%**，表 3（p.11）的 DoS "Original" 是 **79.12%**。§4.4（p.11）明说基线对比是**另一套设置**（"The detection system and attack models share the same architecture and hyper-parameters as the setting in the previous work [14]"），**两张表的数字不可互相代入**。
- **不能说它做了 DGA、加密流量或真实流量实验**：数据集只有 **NSL-KDD**，且工作在**已抽取好的 41 维流量记录**上，**不涉及原始报文、域名或加密载荷**。
- **不能说攻击功能保持已被验证**：功能保持是**结构保证**（冻结功能特征，Table 1，p.5），**没有任何实测**（无沙箱、无真实攻击复现）。§5（p.12）把"生成与实际对抗记录相符的真实恶意流量、在运行的 IDS 上实验"明确列为**未来工作**，且需**伦理委员会批准**——即本文只产出特征记录，未发起真实攻击。
- **不能把"通用性"扩大到未测类别**：§4.2（p.8）明说"Given that DoS and Probe are both attacks based on network, **we only tested on DoS**"——**Probe 未测**；U2R 与 R2L 因功能特征相同且样本量小被**合并为一组**（p.8），**两类的数字无法拆开引用**。
- **不能说 baseline 是在同等条件下对比**：表 3（p.11）中 JSMA/FGSM/DeepFool/CW 是**白盒**方法（§2，p.3 明确 Rigaki 与 Wang 的工作"均假设攻击者掌握目标模型知识"），IDSGAN 是黑盒；**该对比不是同威胁模型下的公平对照**，只能说明"白盒方法在本文设置下也拿不到 IDSGAN 的检出率"。
- **不能说判别器保真度已达标**：论文**未报告**判别器对黑盒 IDS 的拟合误差/一致率，也无"代理保真度 vs 攻击成功率"的测量——而这正是 MalGAN §4.3（p.5）暴露的关键失效点。
- **版本与出处**：本地 PDF 是 **v5（2022-05-08）**，距首版 2018-09 约四年；**论文内未标注正式会议名**，不要补写具体会议。

## 文献信息

- arXiv：<https://arxiv.org/abs/1809.02077>（本地 PDF 页边标识 `arXiv:1809.02077v5 [cs.CR] 8 May 2022`，p.1）
- 作者与单位：Zilong Lin（上海交通大学 / 印第安纳大学伯明顿分校，p.1 脚注注明本工作完成于上海交通大学）、Yong Shi、Zhi Xue（上海交通大学）
- 本地原件：`raw/papers/attack-detection/2018-Lin-IDSGAN.pdf`（共 12 页，含参考文献）
- 全文转换：`/tmp/dga-adv-20260910/marl/2018-Lin-IDSGAN/`（MinerU md + json，页码由 json 的 `page_idx` 实测，页号 = `page_idx` + 1）
- 原文自述的主要对照：Rigaki（FGSM/JSMA，白盒）、Wang（JSMA/Targeted FGSM/DeepFool/CW，白盒）、Yang 等（零阶优化 + GAN 黑盒，但特征不分功能、判别器为预训练分类器）——见 §2，p.3；对应参考文献条目 10、14、15（p.12）
