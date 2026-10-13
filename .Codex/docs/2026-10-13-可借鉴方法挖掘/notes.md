# 检索笔记（滚动更新）

> 证据等级标记：〔本地全文·已核页码〕〔在线摘要〕〔仅题录〕。

## 难点 2 已核实材料

### SAAT（2022-SAAT-预算自适应对抗训练.pdf，arXiv:2210.01288）〔本地全文·已核页码〕
- 式(5)（p.5）：`δ_i = argmin_δ ℓ(f_θ(x_i+δ),y_i)  s.t. ℓ(f_θ(x_i+δ),y_i) ≥ ρ`。
  **去掉预算约束**，改用「最小对抗损失 ≥ ρ」约束对抗样本生成；预算只作搜索上限。
- 算法 1 SA-PGD（p.6）：**渐进搜索**——初始 ε=0；若该预算下最优攻击损失 < ρ 则 ε←ε+r 继续攻击；
  若 ε=0 已满足 ℓ≥ρ 则保留干净样本。⇒ **逐样本预算 = 使最优攻击达到最低对抗损失 ρ 的最小预算**，
  即预算是「模型状态（当前攻击可达损失）」的函数。
- Algorithm 2（p.6）SAAT 训练循环。
- ρ 语义（p.7 §4.2）：ρ 控制「鲁棒差异度」（RD），ρ=0 退化为自然训练、ρ→∞ 退化为标准 AT；
  CIFAR 上 ρ∈[0,2.2] 有效，ρ>2.2 不收敛（PreAct ResNet-18）。ε_max 防 死循环（离群样本）。
- 对我们的可迁移点：把 q 的调度从「预设时间表」改成「q_i(θ)=min{q: 核在预算 q 的最优攻击损失 ≥ ρ}」，
  ρ 为标定参数；成本=逐样本多预算扫描（预算枚举 × 每预算 K 次核调用）。

### SAAT 相关工作清单（p.3–4 提及，按名登记待查）
FAT（Zhang 2020a）、IAAT（Balaji 2019，本地已有）、ATES（Sitawarin 2020）、Customized AT（Cheng 2020）、
curriculum（Cai 2018）、FOSC（Wang 2019a）、geometry reweighting（Zhang 2020b = GAIRAT）、
MMA（Ding 2018）、 stopping criterion＝误分类即停（PGD-AT 变体）。

### BETA（2023-BETA-黑箱双层优化.pdf，ICLR 2024，arXiv:2306.11035）〔本地全文·已核页码〕
- 定位：指出「surrogate 零和 min-max」两大缺陷（弱攻击者、无效防御者，§3 式(9) 上界论证），
  改为**非零和双层**：防御者最小化 CE（式 16），攻击者最大化**负边际**（式 13–15，Proposition 1）。
- Proposition 1（p.5）：0-1 错误约束（式 12）⇔ 每个错误类 j 上最大化负边际（式 15），
  **不是松弛，是等价重写**；下层因此变成一阶可解的光滑问题（Algorithm 1 BETA，p.6）。
- Algorithm 2 BETA-AT（p.6）：把下层最优攻击 `η_j*` 作为训练样本，上层只优化 CE。
- 二分类特例（K=2）：负边际 = logit 差；下层 = 「找最小预算 q 使 margin>0」⇒ 与我们的 q*(θ)
  同构（margin 是 q 的函数，q* = 首过点）。**margin 代替 0-1 错误作为反应变量**是可直接借的形态。

## 难点 1 已核实材料

### BiGrad（2023-BiGrad-离散双层对抗梯度估计.pdf，arXiv:2302.14473）
- 既有核查（第三章-离散反应项文献核查.md）已核 Thm 3 式(6)–(9)、§5.2 式(13)（经 ar5iv 全文）。
- 待办：对本地 PDF 复核式(6)(7)(8)(9) 页码。

### 本地检索补充（混合索引本轮可用）
- GRANDE/GradTree（wiki/papers/methodology/tree-inspired/2024-Marton-GRANDE-全文.md）：
  不可微决策树用 straight-through 算子反传——表格模型侧同型技术（对难点 1 属「ST 的另一实例」，非新路线）。

## 难点 2 已核实（续）

### IAAT / Balaji 2019（raw/papers/attack-detection/2019-Balaji-Instance-Adaptive-Adversarial-Training.pdf）〔本地全文，结构化笔记已核页码〕
- 笔记：`wiki/papers/attack-detection/dga/2019-Balaji-逐样本半径对抗训练.md`。
- 式(2)（p.3）：逐样本半径 min-max 目标；算法 1 统一半径预热＋逐样本选半径（p.3）；
  算法 2 **三点半径试探**（p.3–4）：对上一轮半径做 +γ/原值/−γ 三点试探，
  取「PGD 样本仍被预测为原标签」的最大试探值，再以 β 平滑更新。
- ⇒ **逐样本预算 = 模型状态（当前是否仍判对）驱动**，与 SAAT 的「损失约束」互补。
- 负证据（表 1–2，p.6）：部分骨干上攻击鲁棒性略降——不是统一提升。

### 课程式对抗训练的调度判据（Shi & Liu, AAAI-24）〔本地全文笔记〕
- `wiki/papers/attack-detection/课程式对抗训练-在线视角.md`（原件 `raw/papers/attack-detection/课程式学习.pdf`）。
- 调度判据：把各轮对抗样本视为不同分布，**调度扰动半径 δ_t 使相邻分布的 Wasserstein 漂移 J 最小**
  （Prop 4.1/4.2 + 主定理 4.5）——「预算调度 = 最小化分布漂移」的理论形态。

## 难点 3 已核实

### HotFlip（Ebrahimi et al., ACL 2018，arXiv:1712.06751）〔本地全文·已核页码，/tmp 副本〕
- §3.2 式(1)（p.2）：翻转字符 (a→b) 的方向导数
  `max ∇_x ℓ(x,y)^T·ṽ_{i,j,b} = max_{i,j,b}(∂ℓ/∂x_{i,j}^{(b)} − ∂ℓ/∂x_{i,j}^{(a)})`
  ——**一次反传得全部位置×字母的替换得分**。
- §3.3（p.3）：贪心/束搜索组合 r 步；`score([c1,c2,c3]) = Σ_t ∂ℓ(x_t)/∂c_t`；
  O(br) 前反传 vs 朴素 O(brL|V|)。插入/删除需 shift 项与 L2 归一化（p.3）。
- p.1 §1 原文明说该方法可用于对抗训练。
- DGA 域先例：Drichel 2024 把 HotFlip 作为离散白盒攻击用于 DGA 对抗训练
  （`wiki/papers/attack-detection/dga/2024-Drichel-DGA检测鲁棒分类.md` §4.3.3 p.7）。
- 黑盒对位：DeepWordBug 家族（评分函数驱动 + 贪心 swap/replace/delete）——EACL 2023 NMT 版
  （arXiv:2301.11122）已核题录；**Gao 2019 分类版（arXiv:1901.10633）未核原件，标候选**。

## 难点 4 已核实（本地库）

### pAUC 低误报区目标（LibAUC, KDD 2023）〔本地全文·已核页码〕
- `wiki/papers/methodology/training-efficiency/2023-Yuan-LibAUC库与X风险优化.md`（结构化笔记）+
  同名 KDD-全文（MinerU 全文）。
- one-way pAUC（FPR≤β）优化（式(2)(3) p.3）：`min (1/n_+)(1/k) Σ Σ ℓ(h_w(x_j)−h_w(x_i))`，`k=⌊n_-β⌋`；
  FCCO/移动平均估计器（SOPAs，算法 1 p.5；引用 Zhu et al. 2022）。表 2（p.6–7）低不平衡数据上优于 CE/Focal。
- 适用性注意：β=0.001 ⇒ k=⌊n_-·0.001⌋，minibatch 内需负样本池≥1000 才有可比对；库内以跨批移动平均处理。

### Neyman-Pearson 分类范式（本地库）
- `wiki/papers/methodology/2024-Wang-Hierarchical-Neyman-Pearson-Classification-全文.md`（MinerU 全文）：
  二元 NP 范式（Cannon 2002/Scott-Nowak 2005/Rigollet-Tong 2011/Tong et al. 2018 umbrella 算法）——
  **以次序统计量在验证折上选阈值，高概率控制 I 类错误 ≤ α**（§1.1，p.1–2）。
- 对位：**0.1%/1% FPR 阈值的高概率控制**可用次序统计量标定（与保形预测同族）。

### RS-Del 的可调判定阈值（已在库，角度未被吸收）
- `wiki/papers/attack-detection/2023-Huang-RS-Del编辑距离认证鲁棒性.md`；原件式(2) p.3：
  平滑分类器带**逐类判定阈值 η_y**；Remark 1（p.4）：η 是 FPR 与证书半径的调节旋钮；
  Table 1（p.5）：仅删除平滑即可证 del+ins+sub 全编辑集半径。
- 训练时用平滑分布增强（p.5「Training」段）——与本课题「训练核随机编辑」同构，
  ⇒ **RS-Del 的训练-证书同分布结构可直接搬**。

## 难点 1 已核实（续，/tmp 原件）

### 扰动优化器 / Perturbed Optimizers（Berthet et al., NeurIPS 2020）〔在线全文·已核页码，/tmp 副本 cand_2002.08676.pdf〕
- **Def 2.1（p.3）**：扰动最大化器 `y*_ε(θ) = E_{p_θ}[Y] = E[argmax_{y∈C}⟨y, θ+εZ⟩] = ∇F_ε(θ)`；
  **Jacobian 处处良定义且非零**（p.2 贡献条目原文）。
- 式(1)（p.3）`F(θ)=max⟨y,θ⟩`；式(2)（p.4）Fenchel 对偶形式 `y*_ε(θ)=argmax⟨y,θ⟩−εΩ(y)`。
- p.2 相关工作自述：Agrawal 2019 隐式微分在 polytope 上 Jacobian 几乎处处为零；Vlastelica 2019 分段线性插值；
  「perturbation techniques to differentiate through an argmax」为其首引。
- 对位：给「反应项 = 解映射」提供**随机平滑可微化**，黑箱可用、MC 估计、σ 控偏差-方差。
- 题录核验：arXiv **2002.08676**（WebSearch 给的 2006.16219 是物理论文，已证伪）。

### 其余题录核验（arXiv API）
- Vlastelica/Pogančić 黑箱组合求解器差分 = arXiv **1912.02175**（ICLR 2020）。
- I-MLE（Niepert et al.）= arXiv **2106.01798**（NeurIPS 2021）。
- Gumbel-Softmax = **1611.01144**；Bengio STE = **1305.2982**。
- GAIRAT = **2010.01736**（ICLR 2021）；FAT 式(3) p.3、GAIRAT 式(5) p.5 已读原件（/tmp cand_2010.01736.pdf）。
- top-K 校准铰链随机平滑（Garcin et al.）= arXiv **2202.02193**，**ICML 2022**（PMLR 162，非 WebSearch 所称 2023）；
  式(1)–(5) p.2–3 已读（/tmp cand_topk.pdf）；其平滑基建即 Berthet 扰动优化器。
- RCPS（Bates et al.）= arXiv **2101.02703**；Jia et al. 词替换证书 = **1909.00986**；
  Kang et al. 鲁棒性迁移 = **1905.01034**。
- **ID 证伪记录**：Maini「L0-Robustness via L∞-constrained AT」（ICML 2021）——WebSearch 先后给出
  2006.16219（物理）、2007.11427（EDHOC）、2010.15268（策略评估）三个 ID 全部错误；
  题名检索 arXiv API 无命中 ⇒ **ID 未核验，仅题录候选**。

### 本地已入库（本次新读）
- `wiki/papers/methodology/2018-Tong-纽曼皮尔逊分类.md`：次序统计量阈值，
  `v(k)=Σ_{j=k}^n C(n,j)(1−α)^j α^(n−j)` 控 P(第一类错误>α)——难点 4 阈值标定的核心先例。
- `wiki/papers/attack-detection/2022-Barbero-Transcendent逐类保形拒识阈值.md`：逐类拒识阈值
  随机搜索（p.14），**无 δ、无有限样本上界**（原文自陈）；Tong 2018 为其反对的经验选阈的修正方案。

## 待补下载（报主代理）
- **DES（arXiv:2506.04263）**：`raw/papers/attack-detection/2025-DES-自适应扰动预算.pdf` 实为 HTML 页（7.7KB），
  下载失败，需 curl `https://arxiv.org/pdf/2506.04263` 重下。
- Gao 2019 DeepWordBug 分类版（arXiv:1901.10633）、Zhu et al. 2022（pAUC FCCO 原文）、
  Tong et al. 2018 NP umbrella（JMLR 19(55)）——标候选，未取全文。
