# 门控组合方案实证审核 · 检索笔记

> 逐条落盘。每条结论标注证据等级：`本地全文` / `在线全文已下载` / `在线摘要` / `仅题录`。
> 零命中也是结论。

## 来源可用性（先记，影响后续判读）

| 来源 | 状态 | 证据 |
| --- | --- | --- |
| 本地混合索引 | **可用** | `status --json`：`built_at 2026-09-04T05:51Z`，`note_count 1897`，`papers 860`，`chunk_count 140500` |
| Zotero MCP | **不可用** | `zotero_semantic_search` 与 `zotero_search_items` 均返回 `[Errno 61] Connection refused`（本机 Zotero 未运行）。**本轮无法执行「避免重复入库」的去重检查** |
| Elicit（`990aea2c…search_papers`） | **不可用** | `api_access_denied`：该账号套餐不含 API |
| Scholar Gateway（`50ccb3c5…semanticSearch`） | 可用但**偏 Wiley 期刊**（数值代数 / 控制论），ML 会议论文覆盖弱 |
| alphaXiv（`4cfe5157…`） | 可用，arXiv 覆盖好；`get_paper_content` 默认返回 **AI 生成的中间报告**，非原文 |
| WebSearch / WebFetch | 可用 |

---

## 线 2 交替优化：收敛保证要求什么条件？（**本轮最重要**）

### 检索式与命中

| 检索式 | 来源 | 命中 |
| --- | --- | --- |
| `alternating minimization block coordinate descent convergence` | 本地混合索引 `--scope local --mode hybrid` | 10（无一是交替优化理论论文；Top1 是 TPAUC 多示例，属主题漂移）→ **本地库无交替优化收敛理论原件** |
| 「BCD/交替极小化的块选择规则需要什么条件？迭代依赖的块选择是否破坏保证？」 | Scholar Gateway `semanticSearch` | 15 passages / 12 articles（2013–2026） |
| `Powell 1973 cyclic coordinate descent fails to converge counterexample` | WebSearch | 9 links |
| `incremental gradient convergence cyclic or randomized selection … Bertsekas Nedic` | WebSearch | 9 links |

### 核心发现

**(2-A) 收敛证明依赖的块选择条件是「本质循环」（essentially cyclic），不是任意规则。**

Scholar Gateway 命中 DOI `10.1002/mma.10098`，章节 `THE PROPOSED METHOD` 原文段落：

> "The rule for selecting the blocks states that each of the d blocks must be included in any consecutive T iterations of the scheme. The paper considers a general approach known as the essentially cyclic regime..."

证据等级：**在线全文（passage 级摘录，非整篇）**。这条直接给出条件：**存在有限 T，使任意连续 T 次迭代中每个块都被访问至少一次**。

对本机制的意义：门控依据是「上一步活动集是否为空」。文档自身实测（`.Codex/docs/RWKV/2026-09-04-EAS方案对抗性审核.md:608`）记录过「六档活动率全 0」的空活动集状态，且该状态可持续多步。**只要空活动集连续持续，`maximum` 分支就连续 T 步不被访问，本质循环条件不成立**——不存在能事先给出的有限 T。这不是「保证变弱」，是「保证的前提直接不满足」。

**(2-B) 循环 BCD 在非凸情形有经典不收敛反例（Powell 1973）。**

M.J.D. Powell, *On search directions for minimization algorithms*, Mathematical Programming 4:193–201, 1973。
反例函数 `f(x1,x2,x3) = -(x1x2 + x2x3 + x1x3) + Σ(|xi|-1)_+^2`，逐分量凸但非严格拟凸，3 块循环精确极小化会在 6 个非最优顶点邻域**无限循环**，迭代序列有多个极限点，相邻迭代差不趋于 0。

证据等级：**在线摘要级综述转述**（来自 Wright *Coordinate Descent Algorithms* arXiv:1502.04759 §3.1 与 Shi et al. *A Primer on Coordinate Descent Algorithms* arXiv:1610.00040 的 WebSearch 摘要，**Powell 1973 原件未取得**）。按证据纪律，这条只能作候选，不能单独支撑「本机制必然震荡」的论断。

配套的正面条件（同来源，同等级）：
- Bertsekas Prop. 2.7.1：非凸下循环 BCD 收敛需假设**沿任一坐标方向的极小点唯一**
- 两块分解（two-block）是特殊情形，可在较弱条件下保证全局收敛
- 近端点／prox-linear 修正可救 Powell 反例

**(2-C) 增量梯度法的经典证明假设「指标序列事先固定或与迭代点无关」——这正是状态门控违反的假设。**

WebSearch 综述给出的结构性结论：

> "The classical proofs assume the index sequence is fixed in advance (cyclic) or independent of the iterate (randomized) — precisely the assumption an order chosen as a function of $x_k$ violates."

对应主源：Nedić & Bertsekas, *Incremental subgradient methods for nondifferentiable optimization*, SIAM J. Optim. 12(1):109–138, 2001；Bertsekas, *Incremental gradient, subgradient, and proximal methods for convex optimization: a survey*, arXiv:1507.01030。

证据等级：**在线摘要**（综述转述，主源全文未取得，待核）。同一综述明确指出**未检索到「构造性的、状态依赖顺序导致发散」的论文**——即这是理论空白，不是已证事实。

### 线 2 判读

**存在反证（条件级），但反证本身尚未达到全文证据等级。**

- 「有下界论证」这一主张若借用 BCD/交替极小化理论，则前提「本质循环」在本机制下**不成立**——空活动集可持续多步，`maximum` 分支无有限访问周期上界。
- 更根本的**结构错配**（我的推论，非文献）：BCD 交替的是**变量块**、目标固定；本机制交替的是**目标形式**、变量固定。二者不同构，BCD 的下界论证不能直接迁移。这条须由方案作者给出对应关系才成立。
- 未找到「状态依赖顺序导致发散」的构造性论文（WebSearch 综述明确说没检索到）——所以也**不能断言必然发散**。

---

## 线 3 多任务梯度冲突消解：「取消同时性」有没有先例？

### 检索式与命中

| 检索式 | 来源 | 命中 |
| --- | --- | --- |
| `gradient conflict multi-task learning conflicting gradients projection surgery` | 本地索引 | 10，全部相关：Recon(ICLR2023)、ConFIG、Nash-MTL(Navon 2022)、AuxiNash(Shamsian 2023)、ForkMerge(Jiang 2023)、Gradient Pathologies(Wang 2021) |
| `rg -il "PCGrad\|CAGrad\|GradNorm\|Nash-MTL\|gradient vaccine\|uncertainty weighting"` | 本地 `wiki/papers/` `raw/papers/` | 18 文件 |
| MTL / 梯度冲突 / 交替 / 任务调度 / 时间分离 | alphaXiv `discover_papers`（difficulty 8） | 10 |

### 核心发现（**推翻被审文档的新颖性主张**）

被审文档称：「三者共同的失败模式是让两机制同时作用再设法调和，本方案取消同时性本身」。
**「取消同时性」不是新构造，它是 MTL 里一条已成形的独立路线——task grouping and scheduling。**

**(3-A) SON-GOKU：每步只激活一个非冲突任务组，序贯更新。**

- 题录：Santosh Patapati, Ian Noronha, *Graph Coloring for Multi-Task Learning*, arXiv:2509.16959（v1 2025-09-21，v5 2026-06-29）
- 证据等级：**在线摘要（原文核验）+ 在线全文（AI 中间报告，非原始 PDF）**。摘要经 WebFetch 从 arXiv 页面逐字取得。
- 摘要原文关键句：「At each training step, only one group (color class) of tasks are activated, and the grouping partition is constantly recomputed as task relationships evolve throughout training.」以及「We provide extensive theory showing why grouping and sequential updates improve multi-task learning, with guarantees on descent, convergence...」

方法：EMA 平滑各任务梯度 → 负余弦相似度作干涉系数 → 阈值 `τ` 建冲突图 → Welsh-Powell 贪心染色 → **每步激活一个色类，按固定顺序轮转**，每 `R` 步重算划分。（该段来自 AI 中间报告，非原始 PDF，标为待核。）

**(3-B) 同族先行工作（构成一条路线，不是孤例）。**

- Jeong & Yoon, *Selective Task Group Updates for Multi-Task Optimization*, arXiv:2502.11986（2025-02-17，KAIST）——**仅题录 + 在线摘要**
- Task Affinity Groupings (TAG)、Towards Principled Task Grouping (PTG)、Scalable Task Grouping via Training Dynamics (STG-MLT)——**仅题录**（来自 SON-GOKU 相关工作节的转述，未独立核验）
- 本地全文可用的近邻：`wiki/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移-全文.md`（**本地全文**）、`wiki/papers/manifold/Recon-ICLR2023-全文.md`（**本地全文**）

**(3-C) 反证：最接近的已发表工作明确消融了「单步未平滑状态」，结论是显著更差。**

SON-GOKU 消融（来自 AI 中间报告，**待原始 PDF 核验**）：

> "Single-Step Conflict Estimation" 变体（仅用最近一个 mini-batch 的梯度估计干涉，H=1）**在所有数据集上都明显更差**；这验证了用 EMA 平滑梯度信号的设计选择。
> "Static One-Shot Coloring"（冻结分组）也显著逊于动态重算。

这条对本机制是**直接反证方向**：被审机制的门控信号是**上一步的原始运行时状态**（活动集空/非空），无 EMA 平滑、无 warm-up、无最小更新频率保底。而同路线里唯一给出消融的工作恰好测了这个设计点，结论是更差。

### 线 3 三处结构差异（决定「先例是否可迁移」）

| 维度 | SON-GOKU（已发表） | 被审机制 |
| --- | --- | --- |
| 门控信号 | 多步 EMA 平滑的梯度余弦 | 上一步**原始**活动集空/非空，无平滑 |
| 调度结构 | 划分确定后**按固定顺序循环**色类 | 无循环结构，纯状态触发 |
| 饥饿保护 | 有界陈旧性（每任务 ≤ `Δ+1` 步必更新一次）+ 最小更新频率 `f_min` 补槽 | **无**任何最小访问频率保证 |
| 刷新频率 | 每 `R` 步重算一次划分（低频） | 每步都可能翻转（高频） |
| 被切换对象 | 哪些**任务**参与本步 | 同一损失项的**聚合算子**（tail mean vs max） |

**最后一行是关键**：SON-GOKU 切的是任务集合（各任务损失本身不变），本机制切的是**目标函数的形式**。前者仍在优化同一个总目标的不同分量，后者每步在**两个不同的目标函数**间跳。SON-GOKU 的下界／收敛论证不能直接搬给后者。

### 线 3 判读

**「取消同时性」= 支持先例（已有成形路线）；但被审机制的具体形态 = 存在反证。**
被审文档把「取消同时性」当作对 PCGrad/CAGrad/ConFIG 路线的新颖突破，这一新颖性主张**不成立**——它是 task grouping/scheduling 路线的既有主张（SON-GOKU 摘要逐字可证）。而本机制相对该路线的三处偏离（无平滑、无循环、无饥饿保护），正好落在该路线消融为「明显更差」的一侧。

---

## 线 1 课程学习与损失调度：切换依据是运行时状态还是预设 schedule？

### 检索式与命中

| 检索式 | 来源 | 命中 |
| --- | --- | --- |
| `curriculum learning loss scheduling dynamic loss weighting training stage` | 本地索引 | 10；含 `2009_Bengio_Curriculum_Learning-全文.md`（**本地全文**） |
| `rg -il "self-paced\|自步\|self paced"` | 本地 `wiki/papers/` | 8 文件 |
| 「课程学习／损失调度用预定 schedule 还是响应模型运行时状态？自步方法的失败模式？」 | Scholar Gateway | 12 passages / 9 articles |

### 核心发现

**(1-A) Bengio 2009 的课程 = 预设的、单调的连续化序列，不是状态反馈门控。**

`wiki/papers/methodology/2009_Bengio_Curriculum_Learning-全文.md`（**本地全文**）第 48–75 行，原文：

- 连续化方法（continuation method）框架：单参数族 `C_λ(θ)`，`C_0` 易优化、`C_1` 是真正目标，「One first minimizes `C_0(θ)` and then **gradually increases λ** while keeping θ at a local minimum of `C_λ(θ)`」。
- 课程的**形式定义**（式 3、4）要求两条**单调性**：分布熵单调增 `H(Q_λ) < H(Q_{λ+ε}) ∀ε>0`；样本权重单调不减 `W_{λ+ε}(z) ≥ W_λ(z) ∀z, ∀ε>0`。
- 「Consider a **monotonically increasing sequence of λ values**, starting from `λ=0` and ending at `λ=1`」。

**关键点：课程学习的定义里内置了单调性与终点。** 被审机制的门控**没有单调性、没有终点、可反复来回翻转**——它不满足 Bengio 定义下的「课程」，不能借课程学习的合法性。

**(1-B) 自步／自动课程确实按运行时状态选，但选的是「任务/样本」，且带信任域与调度参数。**

`wiki/papers/methodology/2020_Klink_Self-Paced_Deep_Reinforcement_Learning-全文.md`（**本地全文**）第 26 行：「specify how it is generated, i.e. **how a task is selected given the current performance of the agent**」；第 86 行显示仍存在 `α` 的 **schedule**（「for a given schedule of α, we simply need to scale every value in this schedule by 1/η」）。

即：state-dependent 选择在课程学习里**存在先例**，但形态是「在参数化任务连续统上按当前表现移动一个连续变量，且受 KL 信任域与 α 调度约束」，不是「在两个离散目标形式间按布尔状态每步翻转」。

- 同族：`UASPL: Uncertainty-Aware Self-Paced Learning with Evidential Neural Networks`, arXiv:2607.06638（**仅题录 + 在线摘要**）——SPL「progressing from easy to difficult samples **based on the value of the loss function** during learning」，同样是按运行时损失值选**样本**。
- Scholar Gateway 命中 DOI `10.1111/exsy.12961`（CL 综述，**在线全文 passage 级**）：「In the curriculum (CURR), the learner follows a **predetermined curriculum**」——主流 CL 实现是预定的。

### 线 1 判读

**部分先例，但不可直接迁移。**
「按运行时状态调整训练目标」有先例（自步学习／自动课程）；但所有先例都满足至少一条本机制不满足的约束：**(i) 单调性**（Bengio 的定义性要求）、**(ii) 连续参数而非离散翻转**、**(iii) 被调整的是样本/任务权重而非损失的聚合算子形式**。**未检索到任何按运行时布尔状态在两个损失聚合形式间逐步来回翻转的课程学习工作。**

---

## 线 4 运行时状态触发的损失形式切换

### 检索式与命中

| 检索式 | 来源 | 命中 |
| --- | --- | --- |
| `switch loss function during training based on runtime state adaptive loss selection` | 本地索引 | 10，**无一命中该主题**（Top1 是 PINN 论文，属主题漂移）→ **本地库零命中** |
| 自适应损失选择／loss switching／bandit／RL／self-paced／dynamic loss（difficulty 9） | alphaXiv `discover_papers` | 12 |
| `"switching the loss function" during training … objective switching non-stationary` | WebSearch | 19 links（两组） |
| `switching between max pooling and mean pooling during training … oscillation` | WebSearch | 19 links（两组） |

### 核心发现

**(4-A) 有「按运行时状态换优化器／换算法」的先例，没有「按运行时状态换损失聚合形式」的先例。**

alphaXiv 返回的最接近工作（均为**仅题录 + 在线摘要**）：

- `PILOT: Policy-Informed Learned Optimization for Adaptive Deep Network Training`, arXiv:2605.24570
- `Reinforcement learning to choose optimizers`, arXiv:2609.01811
- `A Reinforcement Learning Inspired Latent Yield Based Adaptive Algorithm Switching Mechanism`, arXiv:2605.24436
- `Interactive Training: Feedback-Driven Neural Network Optimization`, arXiv:2510.02297

这些换的是**优化器／算法／超参**，目标函数不变。**换目标函数本身的没有检索到。**

WebSearch 的合成结论明确记录了这一空白（**在线摘要级**）：
> "I did not find a paper specifically studying *state-conditional loss switching* (i.e., switching objectives based on a model-state trigger) as its own instability phenomenon."

**(4-B) 关键结构事实：`tail mean(α=0.5)` 与 `maximum` 不是两个「形式」，是同一族的两个参数点。**

`wiki/papers/methodology/ranking/2021-Hu-SoRR-Sum-of-Ranked-Range.md`（**本地全文笔记，源 PDF `raw/papers/methodology/ranking/2021-Hu-SoRR-Sum-of-Ranked-Range-arXiv.pdf`，sha256 `37e1dc5e…`**）：

> Hu, Ying, Wang, Lyu, *Sum of Ranked Range Loss for Supervised Learning*, JMLR（NeurIPS 2020 扩展），arXiv:2106.03300。
> SoRR「把 **max、average、top-k 均值（AT_k）、CVaR 统一为『排序后取连续值域区间求和/均值』的特例**」。

所以被审机制做的事，用文献语言说是：**把 SoRR 族的参数 `k` 在两个值之间每步跳变**（`maximum` = `k=1`，`tail mean α=0.5` = `k=⌈0.5N⌉`）。既然存在统一参数化，「必须离散翻转」这一前提本身需要论证。

**(4-C) 反证：同一问题（max vs mean 聚合）文献给出的解法是连续可学参数 + 单调退火 + 抑制漂移的约束，恰好是离散翻转的反面。**

McFee, Salamon, Bello, *Adaptive pooling operators for weakly labeled sound event detection*, **IEEE TASLP, in press, 2018**, arXiv:1804.10070。
证据等级：**在线全文已下载并逐字读取**（缓存于 `…/tool-results/mcp-4cfe5157-…-get_paper_content-1788508737639.txt`，2068 行；已核验第 468–482、520–730、795–845、1284–1298、1648–1695 行）。

逐字要点：

1. **max 聚合本身被判定为不稳定**（行 476–477）：
   > "the sub-gradient of the objective function with respect to non-maximizing instances is 0, and those instances therefore do not contribute when updating the parameters θ. This is particularly problematic early in training... Parameter updates then depend entirely upon single, randomly selected instances. As a result, **max-pooling for MIL can be sensitive to initialization, generally unstable, and difficult to deploy.**"

2. **解法是单个连续可学参数 α**（式 8，行 620–645）：`α=0` → 非加权均值；`α=1` → soft-max pooling；`α→∞` → max；`α≤0` → min。「Treating α as a free parameter **to be learned along-side the model parameters θ**」。

3. **推荐的运动方向是单调的 mean → max**（行 1288–1294）：
   > "max-pooling produces extremely sparse gradients during training, which **impedes the model's ability to learn stable representations**. By contrast, initializing the auto-pool model with α = 1 (softmax-like behavior) produces dense gradients early in training, which **become sparser as the model converges toward max-like behavior**."
   
   行 1675–1677：「we generally recommend to **initialize α with small values (either 0 or 1)** to ensure sufficient gradient propagation early in training」。

4. **论文额外引入两种机制专门抑制参数滑向 max 侧**：
   - **CAP（constrained auto-pool，行 702–795）**：由「单个实例允许占的最大聚合权重 `φ⁺`」反解出 `α` 的上界；实验用 `φ⁺ = 0.5`。
   - **RAP（regularized auto-pool，行 798–812）**：`min_{θ,α} f(θ) + λ|α|²`，「a penalty is applied to α **to prevent it from placing too much weight on individual instances**... This promotes mean-like behavior, but still provides flexibility to learn max-pooling behavior if necessary」。
   - 结论节（行 1678）：「In all datasets, **the regularized auto-pool models are among**〔最优之列〕」；行 1548：「the unconstrained, unregularized auto-pool method consistently〔仅在静态预测上最高〕」。

**四条对照下来，被审机制在每一条上都取了文献相反的一侧**：离散而非连续、每步翻转而非单调退火、无约束/无惩罚而非 CAP/RAP、由外部布尔状态驱动而非由梯度学习。

### 线 4 判读

**无先例（就「按运行时状态切换损失聚合形式」这一具体构造而言），且同一聚合问题上存在方向明确的反证。**
本地索引零命中；在线检索只找到「换优化器/换算法」的先例，未找到「换损失形式」的；而针对 max-vs-mean 这个**完全相同的聚合选择问题**，已发表工作（IEEE TASLP 2018，全文核验）的解法是连续可学参数 + 单调退火 + 显式抑制向 max 漂移。

---

## 线 5 非平稳目标 SGD 与反馈切换稳定性

### 检索式与命中

| 检索式 | 来源 | 命中 |
| --- | --- | --- |
| 「状态依赖切换的目标函数下 SGD 是否震荡/不收敛？」（difficulty 9） | alphaXiv `discover_papers` | 10 |
| `switched systems individually stable subsystems unstable under arbitrary switching … dwell time … chattering` | WebSearch | 9 links |
| `"hysteresis" AND "switching" AND ("chattering" OR "Zeno") AND "state-dependent"` | scite `search_literature`（keyword 模式） | **corpus 内 183 篇匹配**，取回 6 |

### 核心发现

**(5-A) 切换系统的基本结论：子系统各自稳定 ≠ 切换后稳定。**

WebSearch 综述（**在线摘要级**，主源 Liberzon & Morse 1999 / Liberzon 2003 专著未取得全文）：

> "If all the subsystems are individually stable and the switching signal is not restricted in any way, the stability of the switched system still needs to be verified... Relying solely on the stability of individual subsystems is therefore insufficient to guarantee overall stability under arbitrary switching."

要拿到稳定性，必须补三者之一：**共同 Lyapunov 函数**（任意切换下）、**驻留时间／平均驻留时间**（Hespanha & Morse 1999，切换足够慢）、或**受限切换**。

**(5-B) 状态依赖切换是独立研究领域，其稳定性要单独构造证书，不能继承。**

scite 关键词检索（`total = 183`）取回的代表：

- Katsanikakis, Bekiaris-Liberis, Bresch-Pietri, *Predictor-Feedback Stabilization of Linear Switched Systems with State-Dependent Switching and Input Delay*, 2026, arXiv:2603.20027（**在线摘要**）——为状态依赖切换建立指数稳定性，靠的是「**a novel construction of multiple Lyapunov functionals**」。
- *Stabilization for Switched Stochastic Systems With Adjustable Convergence Rate: A State-Dependent Switching Control Strategy*, 2025, DOI `10.1002/rnc.70054`（**在线摘要**）
- *Hysteresis-Based Switching Design for Stabilization of Switched Linear Neutral Systems*, 2016, DOI `10.1007/s00034-016-0294-7`（**在线摘要**）——**基于迟滞的切换策略**是该领域标准的抖振抑制设计。
- *State-dependent intermittent control of non-linear systems*, 2017, DOI `10.1049/iet-cta.2016.1385`（**在线摘要**）
- *Some experiments on chattering suppression in power converters*, 2009, DOI `10.1109/cca.2009.5281139`（**在线摘要**）

**(5-C) ML 侧：切换/非平稳目标的分析工作存在，但都假设切换与迭代点无关。**

alphaXiv 命中（均**仅题录 + 在线摘要**）：

- `Analysis and Synthesis of Switched Optimization Algorithms`, arXiv:2510.21490
- `Learning switched non-linear dynamical systems from a single trajectory`, arXiv:2607.23502——摘要明写保证条件是「**i.i.d switching over a set of K modes**」，即**切换独立于状态**
- `Stochastic Approximation with Two Time Scales: The General Case`, arXiv:2412.19872
- `Non-normal spectral signatures of instability in neural network training dynamics`, arXiv:2605.23476
- `SGD at the Edge of Stability`, arXiv:2606.30930

Lyle, Zheng, Nikishin, Avila Pires, Pascanu, Dabney, *Understanding plasticity in neural networks*, **ICML 2023**, arXiv:2303.01486（**在线摘要**，全文未取得）：摘要确认「Deep neural networks are known to **lose plasticity over the course of training** even in relatively simple learning problems」，且该现象「often occurs **in the absence of saturated units**」。

**(5-D) 一条必须撤回的候选证据（负面记录）。**

WebSearch 合成曾给出「AdamW 二阶矩估计过时（stale second moment）导致 loss spike，与 β₂ 有关」的机制，并挂到 `Small-scale proxies for large-scale Transformer training instabilities`（Wortsman et al., 2023, arXiv:2309.14322）名下。
**WebFetch 核对该文摘要：不成立。** 该摘要讲的是「the growth of logits in attention layers」与「divergence of the output logits from the log probabilities」，**未提 AdamW ε、二阶矩过时或 β₂**。
**该机制标为「未验证、来源错配」，不得引用。** 若要用「优化器状态与新目标不匹配」这条论证，须另找并核验主源。

### 线 5 判读

**存在条件级反证，但没有直接针对本机制的构造性发散结果。**

- 「两个分支各自能收敛 ⟹ 切换后能收敛」在切换系统理论下**明确不成立**；要成立须补共同 Lyapunov 函数、驻留时间下界或切换受限之一。被审机制**三者都没有**。
- 状态依赖切换的稳定性证书需**单独构造**（多 Lyapunov 泛函），不能从子系统继承。
- 该领域抑制抖振的标准装置是**迟滞（hysteresis）**。被审机制的门是「上一步活动集是否为空」的**裸阈值，无迟滞、无最小驻留步数**。结合本仓库自身实测记录的 `ξ` bang-bang 追踪动力学（`.Codex/docs/RWKV/2026-09-04-EAS方案对抗性审核.md:543,549,624`：`ξ` 被活动对猛推高、空步缓慢衰减，空活动集是暂态），门控信号本身就是高频抖动量——这正是抖振的构成条件。**（此段的因果连接是我的推论，不是文献结论；文献只给出「无迟滞的状态依赖切换需单独证明稳定性」。）**
- **未找到**「状态反馈切换必然导致 SGD 发散」的构造性论文。所以只能说**保证缺失**，不能说**必然失败**。

---

## 待办 / 未关闭疑点

1. Powell 1973 原件（Math. Programming 4:193–201）未取得，反例细节仅经 Wright / Shi 综述转述。
2. Nedić & Bertsekas 2001（SIAM J. Optim. 12(1):109–138）与 Bertsekas 综述 arXiv:1507.01030 全文未取得，「经典证明假设指标序列与迭代点无关」仅为综述转述。
3. SON-GOKU（arXiv:2509.16959）的**原始 PDF 未下载**；摘要已 WebFetch 逐字核验，但方法细节与「Single-Step Conflict Estimation 消融明显更差」出自 alphaXiv 的 **AI 中间报告**，须取原始 PDF 复核后才能作为定论引用。
4. Zotero 本轮不可用（`Errno 61`），**未执行重复入库检查**；AutoPool、SoRR 之外的候选是否已在 Zotero 库中未知。
5. Liberzon 2003 专著与 Liberzon & Morse 1999 未取得全文，切换系统基本结论为综述转述。
6. 若要正式引用，建议优先入库两篇：**AutoPool（arXiv:1804.10070，已有全文文本）** 与 **SON-GOKU（arXiv:2509.16959，需下载 PDF）**。本轮按边界**未执行入库**。
