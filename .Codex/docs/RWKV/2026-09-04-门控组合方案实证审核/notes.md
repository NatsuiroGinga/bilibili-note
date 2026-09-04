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

## 线 1 课程学习与损失调度

待填。

## 线 4 运行时状态触发的损失切换

待填。

## 线 5 非平稳目标 SGD 与反馈切换稳定性

待填。
