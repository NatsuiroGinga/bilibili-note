# 损失门控/预热微检索（2026-10-21）

任务：为「初始化期去相关惩罚把成员推入全负预测病理，拟在 BCE<0.5 后激活惩罚」寻找先例。
通道：Crossref、arXiv API、OpenAlex、WebSearch；Semantic Scholar 本轮全程 429，未使用。
边界：只登记题录与可得性，不下载全文；Rosen 1996 用本地原件 PDF 复核。

## 检索式与空结果（可复现）

- arXiv API：`ti:"saddle point problem in high-dimensional non-convex optimization"` → Dauphin et al. 2014（arXiv:1406.2572）。
- arXiv API：`all:"all-negative" AND all:classifier` → 无相关命中（返回图论、分割等不相关条目）。
- Crossref：`query.title=all-negative prediction` → 无相关命中。
- Crossref：`query.title=constant output neural network collapse` → 无相关命中（多为电源控制、结构预测）。
- WebSearch：`"all-negative" prediction collapse binary classification`、`"always predicts the negative class"`、`"logit collapse" OR "output collapse"` → 均未找到专门命名「全负输出鞍点」的论文。
- 命中项：KL annealing / cyclical annealing、DANN λ ramp、Kendall 不确定性加权、NCL/Rosen、Harangi 2023、Dynamic NCL 2026。

## 1. 辅助损失的门控/预热

### (1) Bowman et al. 2016 — VAE 的 KL cost annealing

- 题录：Samuel R. Bowman, Luke Vilnis, Oriol Vinyals, Andrew M. Dai, Rafal Jozefowicz, Samy Bengio, *Generating Sentences from a Continuous Space*, CoNLL 2016, DOI `10.18653/v1/K16-1002`（Crossref 已核）。
- 原文（ar5iv 全文，§3.1 "KL cost annealing"）：训练开始把 KL 项权重设为 0，随后逐渐增至 1；图 2 为典型 sigmoid annealing schedule；"The rate of this increase is tuned as a hyperparameter."
- 证据等级：全文 HTML 已核；无本地原件/笔记。
- 对本设计：**支持「初始化期关闭、随后缓启」辅助项**，但它是**按训练进度的时间表**，不是按主损失阈值触发。

### (2) Fu et al. 2019 — 周期退火

- 题录：Hao Fu, Chunyuan Li, Xiaodong Liu, Jianfeng Gao, Asli Celikyilmaz, Lawrence Carin, *Cyclical Annealing Schedule: A Simple Approach to Mitigating KL Vanishing*, NAACL 2019, DOI `10.18653/v1/N19-1021`（Crossref 已核）。
- 原文：单调 KL annealing 是 de facto standard（β 从 0 渐增至 1）；本文改为重复「递增—重置」多个周期，默认 M=4、R=0.5；动机是训练初期缺少好的 latent code，单调退火会低估先验、使模型退化为点估计。
- 证据等级：全文 HTML 已核。
- 对本设计：支持显式调度，但提示**调度形状会影响结果**；硬阈值开关比连续 ramp 更粗，文献没有对应支持。

### (3) Ganin & Lempitsky 2016 — DANN 的 λ ramp

- 题录：Yaroslav Ganin, Evgeniya Ustinova, Hana Ajakan, Pascal Germain, Hugo Larochelle, François Laviolette, Mario Marchand, Victor Lempitsky, *Domain-Adversarial Training of Neural Networks*, JMLR 17(59):1–35, 2016；arXiv:1505.07818（arXiv API 已核题名/作者/2015 提交）。
- 原文（ar5iv 式 (18) 附近）：`λ_p = 2/(1+exp(-γ·p)) - 1`，p 为 0→1 的训练进度，γ=10；"The domain adaptation parameter λ is initiated at 0 and is gradually changed to 1"；动机原文："This strategy allows the domain classifier to be less sensitive to noisy signal at the early stages of the training procedure."
- 证据等级：全文 HTML 已核。
- 对本设计：**最直接的「辅助损失缓启」先例**；仍是进度调度，不是主损失阈值门控。

### (4) Kendall et al. 2018 — 不是门控

- 题录：Alex Kendall, Yarin Gal, Roberto Cipolla, *Multi-Task Learning Using Uncertainty to Weigh Losses for Scene Geometry and Semantics*, CVPR 2018, DOI `10.1109/CVPR.2018.00781`（Crossref 已核）。
- 原文：用 homoscedastic uncertainty 学习各任务权重；全文检索 `warm|anneal|ramp|schedule` 仅命中「用幂律退火学习率」，没有损失权重 0/1 开关、阈值触发或训练进度调度。
- 对本设计：**不算门控**，不能引作「BCE<0.5 后激活」的先例；它只说明软性自适应加权可行。

### (5) Barlow Twins / VICReg / SimSiam 的负向核对

- 题录：Barlow Twins arXiv:2103.03230；VICReg arXiv:2105.04906；SimSiam arXiv:2011.10566（arXiv API 均已核题名/日期）。
- 全文检索 `warm|ramp|anneal|schedule`：三者只出现**学习率 warmup/余弦退火**，没有辅助损失权重的 ramp-up。
- 系数：Barlow λ=5e-3 固定；VICReg λ=25、μ=25、ν=1 固定（前一日全文笔记）；SimSiam 只有单一相似度损失，无辅助 λ。
- 对本设计：**无 ramp-up 先例，也无反对证据**；属于「未使用调度」的负向结果。

## 2. 集成去相关文献里的 λ 调度

### (1) Rosen 1996（本地原件 PDF 第 6–9 页复核）

- 题录：Bruce E. Rosen, *Ensemble Learning Using Decorrelated Neural Networks*, Connection Science 8(3–4):373–384, 1996, DOI `10.1080/095400996116820`（Crossref/OpenAlex/S2 三方已核，见本地笔记）。
- 第 6 页：缩放函数 λ(t) 可取常数或随时间变化；脚注：通常由交叉验证确定。
- 第 8 页（3 Parity）：`λ(t)=1/i`，原文明确 "where i is the ith network"——**按成员序号，不是按样本或 epoch**。
- 第 8 页（noisy sine）：88 个均匀分布模式（N=88），`λ(t)=100/(N*t)`，"where t is the number of training epochs"——**按 epoch 衰减**，等价于随累计已见样本数约 1/t 衰减。
- 第 8 页（分类域）：0–1 分类域中网络输出被限制在目标范围，式 (8) 的去相关惩罚**恒非负**，只能压低正相关，不能制造负相关。
- 方向：原文主张「先用较强惩罚迫使新网络形成不同映射，再逐步把重点移回模式误差」——**先强后弱的退火**，与本设计的「先关后开」方向相反。
- 对本设计：可引作「λ 可随时间变化」的正源，**但不能引作预热/延迟激活的支持**；若照搬其方向，会加重初始化期病理。

### (2) Harangi et al. 2023 — 固定 λ，无调度

- 题录：Balázs Harangi, Ágnes Baran, Marcell Beregi-Kovács, András Hajdu, *Composing Diverse Ensembles of Convolutional Neural Networks by Penalization*, Mathematics 11(23):4730, 2023, DOI `10.3390/math11234730`（Crossref 已核；前一日全文笔记）。
- 原文：`L_f = L + λE`，λ 在 {0, 0.5, 1, 5} 中扫描，λ≈1 最稳、λ=5 普遍过强；**没有 λ(t) 或 warm-up**。
- 对本设计：无调度先例，中性。

### (3) Takama & Hasegawa 2026 — Dynamic NCL（摘要级）

- 题录：Hiromu Takama, Tatsuhito Hasegawa, *Dynamic Negative Correlation Learning in Deep Ensemble Learning*, ICIAE 2026, pp. 81–88, DOI `10.12792/iciae2026.015`（Crossref 已核）。
- 可得性：出版社页面仅有摘要；摘要称 "dynamically adjusts the balance between diversity and accuracy during learning" / "dynamically adjusting parameters as learning progresses"；**未给出 λ 的更新方向、触发条件或公式**。全文未取得。
- 对本设计：只能登记为「确有人做训练中动态 λ」的待核候选，不能判断其是否支持预热。

## 3. 全负预测/输出常数鞍点

- 本轮未找到专门命名「全负预测」或「分类器输出常数化鞍点」的论文；arXiv 与 Crossref 的标题检索均为空，WebSearch 只返回工程报告/问答。
- 最接近的通论：Dauphin et al. 2014, *Identifying and attacking the saddle point problem in high-dimensional non-convex optimization*, NeurIPS 2014, arXiv:1406.2572（arXiv API 已核）。其摘要只讨论「高误差平台包围的鞍点会拖慢学习」，**不涉及分类器全负输出**。
- 结构类比：VAE 的 posterior collapse——辅助 KL 项在训练初期压过主重建项，模型退化为忽略潜变量的平凡解，Bowman 的 KL annealing 正是针对此。这可作为「辅助项早期激活→退化→缓启修复」的机制类比，但不是同名现象。
- 警示：neural collapse / minority collapse 是特征与类均值结构现象，不是「输出常数化」，不得混引。

## 4. 对「BCE<0.5 后激活惩罚」的裁决输入

- **支持**：辅助/正则项在初始化期关闭或缓启，是有全文先例的标准做法（Bowman 2016；Ganin & Lempitsky 2016；Fu 2019）。
- **不支持**：本轮未找到以主损失阈值（如 BCE<0.5）作为硬触发条件的已发表先例；所有先例都是按训练进度/迭代数的连续或分段调度。Kendall 2018 不是门控；Rosen 1996 的调度方向相反；Harangi 2023 无调度。
- **建议表述**：可写「延迟激活/缓启去相关惩罚」有先例；「BCE<0.5 硬阈值」只能标为本任务设计选择，需登记为任务化设定并做触发前后对照，不能写成文献结论。
