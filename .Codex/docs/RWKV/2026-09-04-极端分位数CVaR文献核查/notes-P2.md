# P2 续（本地全文）· 滚动笔记 第二批

<!-- RESEARCH_ROUTE=RWKV -->

接 `notes.md`。日期 2026-09-04。

---

## P2-2 · LibAUC（Yuan et al., KDD 2023）· 证据等级 `L1`

来源：`wiki/papers/methodology/training-efficiency/2023-Yuan-LibAUC-X-Risk-Optimization-KDD-全文.md`

### 结论（**对 Q2 是负面结果**）：DualSampler/TriSampler 与 β 无关

- 3.2 节（行 269–271）：`DualSampler` 的超参是 `batch_size` 与 `sampling_rate`，
  `# positives = batch_size * sampling_rate`——**控制的是批内正样本比例**，
  用于类别不平衡，**不控制负样本尾部分辨率 β**。
- `TriSampler` 超参 `sampled_tasks`／`batch_size_per_task`／`sampling_rate_per_task`，
  同样是「每个 query 的正样本占比」，面向 LTR 的多 query 结构。
- 4.4.2 节（行 416–418）：`sr` 调在 `{original, 10%, 30%, 50%}`；结论是
  「使用高于原始不平衡率的采样比例通常有益」，但 `sr=50%`（完全平衡）未必更好。
- **因此：任务简报中「LibAUC 的 DualSampler/TriSampler 对 β 与批量的处理」这一条，
  答案是「这两个采样器不处理 β」。** 它们解决正样本稀缺，不解决尾部预算不可表示。

### 结论（对 Q1 有间接支撑）：LibAUC 的答案是「移动平均 + 随批量调超参」

- Table 1（行 315）与 4.4.1 节：LibAUC 收录的 pAUC 算法是 **SOPAs**（软版），
  以「动态小批量损失」（moving-average `γ`）替代静态小批量损失（`γ=1` 即退化为静态）。
- 4.4.3 节（行 426）："For each batch size, **we tune γ correspondingly as theories indicate
  its best value depends on batch size**"，批量取 `{512, 256, 128, 64}`，
  图 7 结论是该设计「more robust to the mini-batch size」。
- 即 LibAUC 的工程结论：**小批量不是禁区，但移动平均超参必须随批量重标定**。
  与 SOPA 理论的 `η₁ = O(βε²)` 同型——**超参要随分辨率标定，而不是把批量堆上去**。

---

## P2-3 · HNS-OPAUC（Shi et al., WWW 2023）· 证据等级 `L1` · **Q2 的最强单条答案**

来源：`wiki/papers/methodology/ranking/2023-Shi-HNS-OPAUC-arXiv2302.03472-全文.md`
标题：On the Theories Behind Hard Negative Sampling for Recommendation

### 该文与本课题共用同一 β 定义

- 式 (8)（行 140）：$\widehat{OPAUC}(\beta)$ 的求和域为 $S^{\downarrow}[1, n_-\cdot\beta]$。
- 行 143："For simplicity, we assume $n_-\cdot\beta$ is a positive integer."
  **又一次确认整数假设的主语是全体负样本数 `n₋`，不是批量。** 本课题六档均满足。
- 式 (19)(20)（行 257–264）：给出 `OPAUC(β)` 与 `Recall@K`／`Precision@K` 的双边夹逼，
  其中 **`β = K/N₋`**——与本课题「预算档 `β = K/N_pop`」的定义完全一致，
  为六档预算的设定方式提供了独立的文献依据。

### Theorem 1（式 14）：硬计数路线，`M = n₋·β`

- DNS 采样分布（式 2，行 100）：$P^{DNS}_{ns}(j|c) = 1/M$ 当 $j$ 属于**全体负样本**的 top-`M`。
- Theorem 1：取 `M = n₋·β` 时，DNS 目标**精确等于** `OPAUC(β)`（exact but non-smooth）。
- ⚠ 该定理要求对**全体** `n₋` 排序取 top-`M`，**没有解除批内表示问题**——
  它把 β 换算成一个整数计数 `M = K`，本课题即 `M = 121, 606, …`。
  对 `n_neg = 64` 的批仍不可直接实现。**这一条不解决问题，但确立了「硬计数路线的换算关系」。**

### Theorem 2（式 17）：**软温度路线，`τ = sqrt(Var_j(L)/(−2 log β))`**

- 采样分布（式 3，行 108）：$P^{Softmax}_{ns}(j|c) = \frac{\exp(r_{cj}/\tau)}{\sum_k \exp(r_{ck}/\tau)}$。
- Theorem 2（行 224–234）：取 $\tau = \sqrt{\dfrac{\mathrm{Var}_j\left(L(c,i,j)\right)}{-2\log\beta}}$ 时，
  softmax 采样的 BPR 目标是 `OPAUC(β)` 的 **smooth but inexact surrogate**。
- 证明路线（行 236）：把 CVaR 散度换成 KL 散度、保持同一 `ρ`（`β = e^{-ρ}`，Lemma 1），
  再对精确的 `τ↔β` 关系作 Taylor 展开取近似。精确关系「complex and hard to compute」。
- **本课题的直接意义**：`τ` 对 `β` 的依赖是 **对数型** `1/sqrt(−2 ln β)`，而硬计数是**线性型** `βn`。
  这正是软路线能在极端 β 下工作、硬计数不能的数学原因。
- 代入本课题六档（`τ_k = sqrt(Var)/c_k`，`c_k = sqrt(−2 ln β_k)`）：

  | 档 | `β` | `−2 ln β` | `c_k` | `τ_k` 相对最高档 |
  | ---: | ---: | ---: | ---: | ---: |
  | 1 | 0.000997 | 13.82 | 3.718 | 0.605 |
  | 2 | 0.004994 | 10.60 | 3.256 | 0.690 |
  | 3 | 0.009997 | 9.211 | 3.035 | 0.741 |
  | 4 | 0.019994 | 7.824 | 2.797 | 0.804 |
  | 5 | 0.039996 | 6.438 | 2.537 | 0.886 |
  | 6 | 0.079993 | 5.052 | 2.248 | 1.000 |

  **六档温度全程只跨 `1.65` 倍，且全部是连续量、无整数约束、无批量下界。**
  （本表是把该文式 (17) 代入本课题冻结 `β` 的**算术代入**，不是实验结果；
  `Var_j(L)` 需按实际损失分布测得，未测。）

---

## P2-4 · SPOT / EVT（Siffer et al., KDD 2017）· 证据等级 `L1`（本地结构化全文核验笔记）

来源：`wiki/papers/methodology/2017-Siffer-SPOT极值流阈值.md`（原件
`raw/papers/methodology/2017-Siffer-SPOT-EVT-Anomaly-Streams.pdf`，证据在 PDF 第 1、3–5 页）

- 极端分位外推式：$z_q = u + \dfrac{\sigma}{\xi}\left[\left(\dfrac{qN}{N_u}\right)^{-\xi} - 1\right]$，
  `N` 为样本数、`N_u` 为超阈样本数、`(ξ,σ)` 为广义帕累托参数、`q` 为风险概率。
- **关键性质：`q` 可以远小于 `1/N`。** GPD 尾部外推不要求「样本里真的出现过 `q` 分位」，
  这正是「目标分位数细于样本分辨率」时的标准统计做法。
- 与本课题的差异（**不可忽略**）：SPOT 是**部署期**对**冻结分数**的阈值估计，
  不在训练循环内、不需要梯度、拟合样本量是数千级的初始批而非 `64`。
  把它搬进训练循环需要额外证据（见待办）。
- 本仓库既有边界（该笔记「不能直接声称」节）：不能把 `q` 写成假阳性率，
  不能声称 EVT 会提高平均精确率。

---

## P2-5 · 由本地文献引出的在线待查清单

来自 `2023-Hu-Multi-Instance-TPAUC-NeurIPS-全文.md` 参考文献：

- [4] Curi, Levy, Jegelka, Krause. **Adaptive Sampling for Stochastic Risk-Averse Learning**.
  NeurIPS 2020, vol. 33, pp. 1036–1047. → Q1/Q2 核心，必取全文
- [36] Yuan, Wu, Qiu, Du, Zhang, Zhou, Yang. **Provable stochastic optimization for global
  contrastive learning: Small batch does not harm performance**. ICML 2022, PMLR 162: 25760–25782.
  → 直接针对「小批量是否损害性能」，对 Q1 是反向证据，必取
- [46] Zhu, Gürbüzbalaban, Ruszczyński. Distributionally robust learning with weakly convex
  losses: Convergence rates and finite-sample guarantees. 2023. → Q1 有限样本保证

---
