---
schema: paper-note-search/v1
title: "CharBot: A Simple and Effective Method for Evading DGA Classifiers"
title_zh: "CharBot：规避DGA分类器的简单有效方法"
authors: [Jonathan Peck, Claire Nie, Raaghavi Sivaguru, Charles Grumer, Femi Olumofin, Bin Yu, Anderson Nascimento, Martine De Cock]
year: 2019
date: 2026-09-07
journal: "IEEE Access 7, 91759–91771"
doi: "10.1109/ACCESS.2019.2927075"
arxiv_id: "1905.01078"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2019-Peck-CharBot.pdf]]"
tags: [DGA检测, 对抗规避, CharBot, 低误报, 黑盒攻击, 类型/论文]
aliases: [CharBot, Peck2019]
tasks: [DGA生成, DGA二分类规避, 对抗重训, 低FPR评价]
datasets: [Alexa, Qname, Bambenek, CharBot, DeepDGA, DeceptionDGA]
methods: [良性域名两字符替换, LSTM.MI, FANCI, B-RF]
metrics: [TPR@FPR, AUC, 未注册率, Levenshtein成本]
key_finding:
  - "黑盒、仅需良性域名列表即可生成规避样本：从 Alexa 良性域 SLD 中随机替换两个字符（不做插入/删除），FPR 0.1% 时未针对性训练的 LSTM.MI 对 CharBot 的 TPR 仅 5.58%、B-RF 仅 1.69%，FANCI 甚至无法建立 0.1% FPR 阈值（PDF 物理第7至8页，表 IV–V）。"
  - "本文的对抗训练是「一次性生成对抗域名列表后并入训练集」的静态增广，非白盒迭代对抗训练（§VI-C，p.9 明确列为未来工作）；即便如此，加入 CharBot 重训后 FPR 0.1% 时 LSTM.MI 的 TPR 只升到 55.19%、B-RF 仅 1.84%，FANCI 在 1% FPR 下也只有 22.26%。"
supports: ["低FPR下良性近邻式规避是必须评价项", "一次性静态对抗增广不足以修复低FPR工作点"]
cannot_support: ["所有字符串模型都无法防御", "跨年未知家族等同CharBot", "本文结果等价于迭代白盒对抗训练"]
related: ["[[2018-Schuppen-FANCI]]", "[[2019-Sidi-MaskDGA规避攻击]]", "[[2024-Drichel-DGA检测鲁棒分类]]", "[[2023-Drichel-DGA分类器偏差审计]]"]
---

# CharBot

> 页码锚点：本地 PDF 共 12 页。攻击算法见 §III（**p.4**）；数据集见 §IV（p.4–5）；被评测模型见 §V-A 至 §V-C（p.5–6）；结果与表 IV–V 见 §V-D（p.7–8）；对策与对抗训练讨论见 §VI（p.9）。
> 本笔记于 2026-09-10 依本地 PDF 全文重写，补入攻击机制原文、威胁模型与对抗训练消融原始数字（题录经 arXiv API 复核，见 `.Codex/docs/2026-09-10-DGA对抗文献入库/notes.md`）。

## 一句话

从良性排行榜域名（Alexa）的二级域中随机替换两个字符即可在 FPR 0.1% 下绕过 LSTM、随机森林与 FANCI，且论文自带的对抗重训只是**一次性静态增广**，在低 FPR 工作点上仍留下巨大缺口。

## 攻击方法（§III，p.4）

CharBot 不是梯度驱动的优化，而是**在良性域名上做随机字符替换**。算法 1 的完整流程（p.4）：

- **输入**：① 合法域名列表——本文取 10,000 个二级域（SLD）长度 ≥ 6 的 Alexa 域名；② TLD 列表；③ 用作伪随机种子的日期。
- **步骤**：(1) 从列表中随机选一个 SLD $d$；(2) 随机选两个下标 $i,j$（$1 \le i,j \le |d|$）；(3) 从 DNS 合法字符集（字母、数字、连字符）的**均匀分布**中选两个替换字符 $c_1,c_2$，并保证与原字符不同；(4) 置 $d[i] \leftarrow c_1$、$d[j] \leftarrow c_2$；(5) 从 22 个 TLD（com、at、uk、pl、be、biz、co、jp、cz、de、eu、fr、info、it、ru、lv、me、name、net、nz、org、us）中随机选一个追加。

**算子集（精确形式，供复现引用）**：

| 算子 | 本文是否使用 | 精确形式 |
| --- | --- | --- |
| 替换 substitution | **是，唯一算子** | 恰好 **2 个位置**；字符从 DNS 合法字符集（字母 + 数字 + 连字符）的**均匀分布**采样，且保证与原位置字符**不同** |
| 插入 insertion | **否** | 原文列为"可能的扩展"，未采用（p.4） |
| 删除 deletion | **否** | 同上；§VI-A（p.9）指出加入插入/删除后才需要编辑距离，本文按替换即用 Hamming 距离 |
| 相邻交换 swap | **否** | 未出现 |
| 字符重复 repetition | **否** | 未出现 |

- **位置选择**：两个下标 $i,j$ 各自在 $[1,|d|]$ 上**独立均匀**抽取；原文未加 $i \ne j$ 约束。
- **变体数**：**每种子恰好 1 个域名**。测试集 10,000 条 = 10,000 个不同种子各生成 1 条（表 I，p.6），不是"每域名生成 N 个变体"。
- **黑盒下无排序/优先级**：替换字符**均匀随机**采样，无梯度、无显著性、无 beam search。第 3 步的成本函数 $c(x,\tilde{x})$ 是**事后论证**该设计合理，算法本身并不优化它。
- **TLD 处理**：从固定的 22 个 TLD 中随机选一个追加，不修改原 TLD。

作者理由是更简单的攻击更可能被真实攻击者采用，因而构成更大的安全关切（p.4）。

**替换数固定为 2 的取舍**（p.4）：替换字符越多生成域名越像随机串、越易被检出；只替换 1 个字符时检出率下降但更多域名已被合法注册。2 个字符在"被检出率"与"已注册率"之间取得平衡。实测 500 抽样中 CharBot 生成域名 **100% 未注册**（DeepDGA 99.8%、DeceptionDGA 98.8%，p.5 与表 I）。

**对抗成本函数**（p.4）：

$$c(x,\tilde{x}) = \begin{cases} d_L(x,\tilde{x}) & \tilde{x} \text{ 未注册} \\ \infty & \text{否则} \end{cases}$$

其中 $d_L$ 为 Levenshtein（编辑）距离。已注册域名成本为无穷，因为攻击者根本不能使用它。

## 威胁模型（黑盒，p.4、p.9）

- **不需要目标模型的任何知识或查询**：只需要一份公开良性域名列表、一份 TLD 列表和一个日期种子。论文自述这是"**第一个不基于生成对抗网络的黑盒对抗机器学习攻击**"（§VII，p.9）。
- **部署成本极低**：Python 实现 17,983 字节 + Alexa 数据 145,008 字节，合计最多 162,991 字节；相比之下 DeepDGA 需内嵌至少 6,539,192 字节的模型，约为 CharBot 的 **40 倍**（p.4）。文件体积不构成部署障碍。
- **成功判据**：能生成大量唯一、未注册、且不被 DGA 分类器判为恶意的域名（p.4）。

## 被评测模型与数据（§IV–§V，p.4–6）

三个分类器（均为二分类：良性/恶意，§V，p.5）：

| 模型 | 结构 | 来源 |
| --- | --- | --- |
| **LSTM.MI** | 嵌入层 + LSTM + sigmoid 单节点输出，用代价敏感学习处理类不平衡 | Tran et al. |
| **FANCI** | 21 项人工特征随机森林（9 棵树，7 棵 Gini、2 棵熵，每棵取 2–18 个特征） | Schüppen et al. |
| **B-RF** | 26 项人工特征随机森林（100 棵树，每棵最多 20 特征，熵准则） | Sivaguru et al. |

对照组 DGA：**DeepDGA**（GAN 生成）与 **DeceptionDGA**（Spooren et al. 提供）。

数据（§IV，p.4–5）：Alexa 前 100 万（良性）、Bambenek 100 万 DGA 域名（2017-06-24、07-22、07-23 三天）、Qname 100 万被动 DNS 域名（2015-09 至 2018-08，按"至少解析两次、无 NXDomain、跨度 >30 天"弱标注为良性）。AlexaBamb 与 QnameBamb 各 200 万条（每类 100 万）。Alexa 与 Qname 仅 537 条重合，故 Qname 用于检验迁移性。80%/20% 划分，指标为 TPR 与部分 AUC，报告在 **FPR 0.1% 与 1%** 两个工作点。

## 实验结果（§V-D，表 IV–V，p.7–8）

干净数据上 LSTM.MI 最强：AlexaBamb 在 FPR 0.1% 时 TPR 96.79%、AUC 94.91%；B-RF 为 85.72%、82.93%；**FANCI 无法建立 0.1% FPR 的阈值**，只能报 1% FPR（p.7）。

对 CharBot 的检测率（表 V，p.8；单位 %）：

| 训练集 | 模型 | CharBot @FPR 0.1% | CharBot @FPR 1% | 干净 TPR @0.1% |
| --- | --- | --- | --- | --- |
| AlexaBamb | LSTM.MI | **5.58** | 15.50 | 96.79 |
| AlexaBamb | B-RF | **1.69** | 27.59 | 85.72 |
| AlexaBamb | FANCI | 无法建立该工作点 | **3.05** | — |
| QnameBamb | LSTM.MI | 15.25 | 31.90 | 81.98 |
| QnameBamb | B-RF | 18.80 | 61.05 | 82.75 |

换用 Qname 训练会让模型更容易检出 CharBot（说明存在数据依赖性），但 0.1% FPR 下仍远不足用（p.7）。作者用核密度估计比较特征分布（图 2）指出：CharBot 域名的特征分布比 DeepDGA 更接近 Alexa，因为它在 Alexa 上只引入少量拼写错误；这解释了规避成功，也预示防御可能需要很高的 FPR。

## 论文自身的对抗训练消融（§V、§VI-C，p.7–9）——本课题的直接对照

**这是本笔记的核心。** CharBot 论文的"adversarial retraining"做法是（p.5）：

- 用 CharBot / DeepDGA 的不同种子各生成 100,000 条训练样本与 10,000 条测试样本；DeceptionDGA 取 150,000 条中采样；
- **把对抗样本一次性并入原始训练集**，再评估模型在 0.1% / 1% FPR 下对 CharBot 的检测率。

论文在 §VI-C（**p.9**）明确承认这不是通常意义上的对抗训练：

> "Our adversarial training procedure in this paper has consisted of generating a list of adversarial domains once and then augmenting the training data with them. However, adversarial training is usually done iteratively ... This requires a **whitebox attack** which is able to take the model parameters into account."

作者把**白盒迭代对抗训练**列为未来工作，本文并未执行。

加入 CharBot 重训后的检测率（表 V，p.8；单位 %）：

| 训练集 | 模型 | CharBot @0.1% | CharBot @1% | 重训后干净 TPR @0.1% |
| --- | --- | --- | --- | --- |
| AlexaBamb + CharBot | LSTM.MI | **55.19** | 81.08 | 95.50（原 96.79） |
| AlexaBamb + CharBot | B-RF | **1.84** | 64.33 | 84.62（原 85.72） |
| AlexaBamb + CharBot | FANCI | 无法建立该工作点 | **22.26** | — |
| QnameBamb + CharBot | LSTM.MI | 52.67 | 81.96 | 82.91（原 81.98） |
| QnameBamb + CharBot | B-RF | 43.47 | 85.82 | 83.03（原 82.75） |

三条可直接引用的读数：

1. **干净性能几乎不降**（表 IV，p.8）：AlexaBamb 下 LSTM.MI 加 CharBot 重训后 0.1% FPR 的 TPR 96.79%→95.50%、AUC 94.91%→95.35%；B-RF 85.72%→84.62%。即"加对抗样本"并不显著损害干净性能。
2. **但低 FPR 工作点远未修复**：B-RF 在 0.1% FPR 下几乎没动（1.69%→1.84%）；LSTM.MI 升到 55.19%，仍有约 45% 的 CharBot 域名漏检；FANCI 在 1% FPR 下也只有 22.26%。
3. **1% FPR 不可用**：作者明确指出 LSTM.MI 与 B-RF 在 1% FPR 下有时能超过 80% 检测率，但"1% FPR 被认为太高、不实用"（p.7）。

## 可迁移机制

1. **规避样本可由防护方自己的良性语料合成**（p.4）：攻击者不需要任何恶意样本或模型知识，只要一份公开的良性域名排行榜。"良性域名的近邻"本身即是攻击面——**任何只吃域名字符串的模型，其决策边界附近必然存在大量未被注册的良性拟态样本**。
2. **离散输入的对抗成本应由"可用性"定义，而非 $\ell_p$ 距离**（p.4）：这里用"是否已注册"给出 $\infty$ 惩罚，把编辑距离约束在有意义的区域内。**这是离散域对抗优化的成本函数范式**：连续域的 $\ell_p$ 约束在域名空间没有对应物。
3. **替换预算存在可用性—隐蔽性权衡**（p.4）：扰动越少越隐蔽但越可能撞上已注册域名；越多越易被检出。这是一个可以显式建模的双目标。
4. **一次性静态对抗增广不足**（§VI-C，p.9）：该文自己指出了静态增广与迭代白盒对抗训练的差别，并把后者留给未来工作——**这正是"相对对抗优化"类方案在文献中的缺口位置**。
5. **交叉攻击迁移是防御的硬约束**：加 CharBot 重训后，模型对 DeepDGA 的检测率在部分配置下反而更低（表 V，p.8，如 AlexaBamb+CharBot 的 LSTM.MI 对 DeepDGA 为 92.54%，低于 AlexaBamb+DeepDGA 的 98.35%）——**针对单一攻击的硬化不等于通用鲁棒性**。

## 不能直接声称内容

- **不能说本文验证了白盒迭代对抗训练**：本文只做了一次性静态增广，白盒迭代在 §VI-C（p.9）被明确列为未做的未来工作。
- **不能把 CharBot 的检测率外推到本课题模型**：被评测的只有 LSTM.MI、FANCI、B-RF 三个字符级模型，数据是 2018–2019 年的 Alexa/Bambenek/Qname；与本课题的 DRIFT 双分支、条件记忆或字段令牌模型无任何实验交集。
- **不能声称"所有字符串模型都无法防御"**：论文自身的表态是"我们推测这一脆弱性对任何仅依赖域名字符串的分类器都固有"（§VII，p.9）——**这是推测，不是本文实验结果**。
- **不能把 CharBot 与真实恶意 DGA 等同**：CharBot 是作者为演示脆弱性而构造的算法，不来自在野恶意软件家族；它生成的域名 100% 未注册（表 I，p.6），与真实 DGA 的注册/使用模式不同。
- **不能引用 DeepDGA/DeceptionDGA 的数字当作 CharBot 的数字**：三者在各表分列。
- **AUC@FPR 的定义**：本文的"AUC@0.1%FPR"是 ROC 曲线在 FPR∈[0, 0.001] 上的积分（p.5 脚注），不是整条 ROC 的 AUC，引用时须写全称。

## 与本课题的关系

- 条件记忆若直接记住训练期良性 n-gram，可能加重 CharBot 式"良性近邻"规避，因此随机替换与相似良性负控必须进入最低比较表。
- 本文给出了**"静态对抗增广在低 FPR 下失效"的原始对照数字**；本课题若提出相对对抗优化，需要说明它相较于这种一次性增广多做了什么，并至少在同等低 FPR 工作点上比较。
- 本文的低 FPR（0.1% / 1%）报告惯例、以及"干净性能不降 ≠ 低 FPR 修复"的分离，与本课题的双向判据（ΔFPR 不增且 ΔFNR/ΔAP 改善）同构。

## 文献信息

- arXiv：<https://arxiv.org/abs/1905.01078>（v2，2019-05-03 提交）
- 正式出处：IEEE Access 7, 91759–91771, 2019；DOI `10.1109/ACCESS.2019.2927075`
- **官方实现：无公开仓库**。§REPRODUCIBILITY（p.10）原文仅为 "we are open to sharing all of our code as well as data sets of CharBot samples **upon request**"。检索到的 `FloRRenn/CharBot-The-Domain-Generation-Algorithms-`（GitHub）为第三方按论文复现，引用时须标明非官方、非作者发布。
- 本地原件：`raw/papers/attack-detection/2019-Peck-CharBot.pdf`
- 题录核验记录：`.Codex/docs/2026-09-10-DGA对抗文献入库/notes.md`
