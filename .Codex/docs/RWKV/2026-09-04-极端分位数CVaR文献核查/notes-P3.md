# P3 · 在线全文 · 滚动笔记 第三批

<!-- RESEARCH_ROUTE=RWKV -->

日期 2026-09-04。

---

## P3-1 · ADA-CVAR（Curi, Levy, Jegelka, Krause; NeurIPS 2020）· 证据等级 `L2`

- arXiv:1910.12511v3（2020-11-06），NeurIPS 33: 1036–1047
- 全文 PDF 已取得并逐页读取（本代理会话缓存
  `~/.claude/projects/.../tool-results/webfetch-1788507653466-twh0p0.pdf`，
  **该缓存不是仓库原件**；若要正式引用须按 `raw/AGENTS.md` 入库）
- 代码：`https://github.com/sebascuri/adacvar`

### **Q3 的直接答案（原文明确报告了 bang-bang 及其处置）**

第 8 页 "Gradient Magnitude and Training Time" 原文：

> "The gradients of TRUNC-CVAR are **either 0 or 1/α times larger** than the gradients of the
> same point using MEAN. A similar but smoothed phenomenon arises with SOFT-CVAR.
> This makes training these losses considerably harder due to **exploding gradients and noisier
> gradient estimates**. With the same learning rates, these algorithms usually produce
> **numerical overflows** and, to stabilize learning, we used **considerably smaller learning rates**.
> In turn, this **increased the number of iterations required for convergence**. ADA-CVAR does not
> suffer from this as the gradients have the same magnitude as in MEAN. For example, to reach
> 85% train accuracy ADA-CVAR requires 7 epochs, MEAN 9, SOFT-CVAR 21, and
> **TRUNC-CVAR never surpassed 70% train accuracy**."

- 「要么 0、要么 `1/α` 倍」**就是本课题实测的 `14.7`–`1002` 倍不对称**。
  最低档 `1/β = 1/0.000997 = 1003`，实测全活动时的比值 `1002` —— **与原文机制数值吻合**。
  故 Q3 的答案是：**该现象已被报告，且被判定为该 formulation（truncated / Rockafellar-Uryasev
  截断形式）的固有性质，不是实现缺陷。**
- 原文给出的三条处置，按其自身评价排序：
  1. **调小学习率**（原文实际采用；代价是迭代数上升）——与 SOPA 的 $\eta_1=O(\beta\epsilon^2)$ 同向；
  2. **平滑化**（SOFT-CVAR，用 Nemirovski & Shapiro 的 $T\log\sum_i e^{x_i/T}$ 松弛
     替代 $\sum_i[x_i]_+$）——原文评价「a similar but smoothed phenomenon arises」，
     即**缓解但未消除**，收敛仍慢（21 epoch vs 9）；
  3. **自适应采样**（ADA-CVAR，本文方法）——梯度量级与 MEAN 相同，7 epoch 达标。
- **TRUNC-CVAR 在其非凸实验中 `never surpassed 70% train accuracy`** —— 这是「原始截断形式
  在深度模型上直接失败」的公开负面结果。BER 现用实现属同一族。

### Q2 的答案（罕见事件重要性抽样这条线，且是 ML 侧）

第 3 页 "Challenges for Stochastic Optimization" 原文：

> "when this batch is sampled uniformly at random from the data, **only a fraction α of points will
> contain gradient information. The gradient of the remaining points gets truncated to zero by the
> max{·} non-linearity. Furthermore, the gradient of the examples that do contain information is
> scaled by 1/α, leading to exploding gradients.**"

> "Our key observation is that the root of the problem lies in the **mismatch between the sampling
> distribution P and the unknown distribution Q\***... Problem (3) can be interpreted as a form of
> **rejection sampling** – samples with losses smaller than ℓ are rejected. It is well known that
> **Monte Carlo estimation of rare events suffers from high variance** (Rubino and Tuffin, 2009).
> To address this issue, we propose a novel sampling algorithm that **adaptively learns to sample
> events from the distribution Q\*** while optimizing the model parameters θ."

- 即：**低 α 的 CVaR 训练被明确归类为罕见事件蒙特卡洛问题**，处置是自适应重要性抽样。
- ADA-CVAR 机制（第 3–5 页）：把 DRO 内层
  $\mathcal{Q}^\alpha=\{q\mid 0\le q_i\le 1/k,\ \sum_i q_i=1\}$，$k=\lfloor\alpha N\rfloor$，
  写成 θ-玩家与 q-玩家的零和博弈，q-玩家用 k-DPP（对角核）的边缘分布作决策变量，
  按 $w_{t+1,i_t}=w_{t,i_t}e^{\eta_s k L_{t,i_t}/q_{t,i_t}}$ 乘性更新（EXP3 型）。
  **每步只采一个点（或一个小批），由采样器保证采到的就是尾部点。**
  脚注 1（第 4 页）："Note that we do **not** use any importance sampling correction."
- **关键结构差异**：`k = ⌊αN⌋` 里的 `N` 是**数据集规模**，`k` 是**全局尾部计数**；
  批量只决定每步取几个点，**不承担表示 α 尾部的责任**。本课题 `k = K = 121`（正整数，合法）。
- Lemma 1 采样器后悔 $O(\sqrt{TN\log N})$；Theorem 1 博弈后悔
  $O(\sqrt{TN\log N}+\epsilon_{\text{oracle}}T)$；Corollary 1/2 给出超额 CVaR 界。

### **Q1 的答案（统计侧）：Proposition 1 的 `1/α` 一致收敛界**

第 3 页 Proposition 1（有限函数类 $|\mathcal{H}|$，损失取值 `[0,1]`）：

$$\mathbb{E}\left[\sup_{h\in\mathcal{H}}\left|\widehat{\mathbb{C}}^\alpha[L(h)]-\mathbb{C}^\alpha[L(h)]\right|\right]\le \frac{1}{\alpha}\sqrt{\frac{\log(2|\mathcal{H}|/\delta)}{N}}$$

- **`N` 是数据集规模，不是批量。** 这是**统计**可行性关系式，不是批量下界。
- 代入本课题（`N = N_pop = 121336`，损失已归一到 `[0,1]` 的前提下，取 `log(2|H|/δ) = 10`
  这一乐观值）：$\sqrt{10/121336}=0.00908$。
  - 最低档 `α = 0.000997`：界 $= 1003\times0.00908 = 9.11$ **> 1，界失效（vacuous）**。
  - 最高档 `α = 0.079993`：界 $= 12.5\times0.00908 = 0.113$，有意义。
  - 界跨过 `1` 的临界 `α ≈ 0.00908`，**恰在第三档 `α = 0.009997` 附近**。
  - ⚠ 这是**充分条件型的最坏情况界**，`log(2|H|/δ)=10` 是本笔记的乐观代入而非实测；
    界失效**不证明**低档一定学不到东西，只说明**该界不能为低档提供保证**。
    标为「推论」，不得当作实验结论。

### 实验设置（用于标定文献走过多远）

- 5.1 节：凸设定评价 **`α = 0.01`**；5.2 节：**`α = 0.1`**；5.4 节：**固定 `α = 0.1`**。
- 即 Curi 等实测最小 `α = 0.01`，正好是本课题第三档（`β = 0.009997`）。
  **本课题最低两档（`0.000997`、`0.004994`）低于该文实测范围。**
- 特例说明（第 7 页）："It is instructive to consider the special cases k = 1 and k = N.
  For k = N, q_t remains uniform and ADA-CVAR reduces to SGD. **For k = 1, the sampler simply
  plays standard EXP3 over data points and ADA-CVAR reduces to the algorithm of
  Shalev-Shwartz and Wexler (2016) for the max loss.**"
  → **`k = 1`（最极端，等价 `β = 1/N`）在该框架里是良定义的合法端点**，不是禁区。
  这与 SOPA「`β = 1/n₋` 即 infinite-push」的说法相互独立地指向同一结论。

---

## P3-2 · CVaR 估计的样本复杂度（`n = Ω(1/α)`）· 证据等级 `L3`（检索综合，未逐篇取全文）

检索式：`CVaR estimation sample complexity concentration bound requires n = Omega(1/alpha)
samples tail quantile`

- 核心事实：**插件式（plug-in / SAA）CVaR 估计量**
  $\hat v_{n,\alpha}=X_{[\lfloor n(1-\alpha)\rfloor]}$、
  $\hat c_{n,\alpha}=\frac{1}{n(1-\alpha)}\sum_i X_i\mathbb{I}\{X_i\ge \hat v_{n,\alpha}\}$
  要良定义，**必须** $\lfloor n(1-\alpha)\rfloor\ge 1$，即 `n = Ω(1/α)`；
  达到 `ε` 精度一般需 `n = Ω(1/(α²ε²))`。
- 主要来源（**均只见检索层面，未取全文**）：
  - Kolla, Prashanth, Bhat, Jagannathan, *Concentration bounds for empirical CVaR: the unbounded
    case*, Operations Research Letters, 2019（arXiv:1808.01739）
  - Prashanth L.A., Jagannathan, Kolla, *Concentration bounds for CVaR estimation: light-tailed
    and heavy-tailed*, ICML 2020（PMLR v119；arXiv:1901.00997）
  - Bhat & Prashanth, *A Wasserstein distance approach for concentration of empirical risk
    estimates*（arXiv:1902.10709）
  - Thomas & Learned-Miller, *Concentration Inequalities for CVaR*
- **对本课题的关键区分（这是 Q1 的核心结论）**：
  `n = Ω(1/α)` 约束的是**在一个样本集内直接算分位数的插件估计量**，
  **不**约束「RU 对偶 + 跨步持久阈值 + 随机逼近」这条路径。
  - 本仓库 2026-08-31 试的**跨步水库分位数**正是插件估计量：`reservoir_size = 4096`，
    最低档期望尾部样本 `4096 × 0.000997 = 4.08` 个 —— **勉强良定义、方差极大**，
    且水库在非平稳损失下还有陈旧性。**其失败与该理论预测一致。**
  - 当前回退到的**子梯度 SGD** 属另一条路径，`n = Ω(1/α)` 不适用于它。
- ⚠ 本节为 `L3`，只用于说明「两类估计量的可行性条件不同」这一定性区分；
  具体常数与定理条件**须取全文后方可写入正文**。

---
