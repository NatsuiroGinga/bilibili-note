# Notes: 预算课程调度候选复活审核（文献分支）

证据等级标记规则：`本地全文`／`在线全文已下载`／`在线摘要`／`仅题录`。
**未取得全文者不得支撑「有先例」或「无先例」裁断**，只能列为待核候选。

## 已确认在库的原件与笔记

| 论文 | 原件路径 | 全文笔记 | 结构化笔记 |
| --- | --- | --- | --- |
| Bardou/Frikha/Pagès 2008 VaR/CVaR SA | `raw/papers/methodology/ranking/2008-Bardou-VaR-CVaR-Stochastic-Approximation-arXiv.pdf` | `wiki/papers/methodology/ranking/2008-Bardou-VaR-CVaR-Stochastic-Approximation-arXiv-全文.md`（1169 行） | `…/2008-Bardou-VaR-CVaR随机逼近与移动风险水平.md`（54 行） |
| Kawaguchi & Lu 2019 Ordered SGD | `raw/papers/methodology/ranking/2019-Kawaguchi-Ordered-SGD-arXiv.pdf` | `…/2019-Kawaguchi-Ordered-SGD-arXiv-全文.md`（638 行） | `…/2019-Kawaguchi-OrderedSGD批内top-q选择.md`（59 行） |

同目录其他在库原件（可能与判三相关）：Curi 2019 ADA-CVaR、Prashanth 2019 CVaR 集中不等式、
Levy 2020 Large-Scale DRO、Hu 2021 SoRR、Nguyen 2021 Extreme-FPR、Yao 2022 Large-Scale pAUC、
Zhu 2022 pAUC-DRO、Shi 2023 HNS-OPAUC、Jiang 2025 pAUC Two Formulations、Asness 2026 Exp-Smoothing CVaR。

## 检索日志

（每组查询后立即追加：查询式、来源、命中、证据等级、与三条判据的关系）

## 判一证据

### A. Bardou/Frikha/Pagès 2008（`本地全文`，`raw/papers/methodology/ranking/2008-Bardou-VaR-CVaR-Stochastic-Approximation-arXiv.pdf`）

行号指全文笔记 `wiki/papers/…/2008-Bardou-…-arXiv-全文.md` 的行号（MinerU 转换稿），
对应 arXiv:0812.3381 的 §3.2–3.3 与结论节。

**A1. `(α_n)` 是「一个 α 沿时间移动」，不是算法内部并列多个水平——但它移动的对象不是主估计量。**

- 行 `800`（§3.2 末）：`we propose to introduce companion VaR procedure (without IS, i.e., based on
  H₁ from Section 2.2) that will lead the IS parameters into the critical risk area during a first
  phase`；`introducing a non-decreasing sequence α_n slowly converging to α during the first phase`。
- 式 `(42)`：`ξ̂_n = ξ̂_{n−1} − γ_n Ĥ₁(ξ̂_{n−1}, X_n, α_n)`，其中
  `Ĥ₁(ξ, x, α̂) = 1 − (1/(1−α̂))·1_{φ(x)≥ξ}`。**每步只有一个 `α_n` 出现在 `Ĥ₁` 里。**
- 式 `(43)`：Phase I 的三元组 `(ξ̂_n, θ̂_n, μ̂_n)`，**没有 `C` 分量**。

**A2.（本次核验的关键发现，主代理转述中缺失）该退火序列被作者明确声明「不是目标的估计量」。**

- 行 `810` 前后（式 `(43)` 之后）原文：`The sequence (ξ̂_n)_{n>0} is only designed to drive "smoothly"
  the IS procedures toward the "critical area" at the beginning of the procedure, say during the
  first M iterations and **in no case to approximate ξ*_α or C*_α**.`
- 紧接一句：`Although, we are not really interested in the asymptotic of this procedure (ξ̂_n)…`
- 结论节（行 `1092`）：`the risk level α can be **temporarily** replaced by a slowly increasing level
  α_n (stepwise constant in practice) converging to α. **This produces a VaR companion procedure
  (ξ̂_n) that controls the IS change of measure parameters (θ̂_n, μ̂_n)**.`

**A3. 三段式调度只存在于 Phase I；最终估计由 Phase II 在固定目标 `α` 上重新产生。**

- §3.3 行 `844–852`：Phase I `α_n = 50%`（`1≤n≤M/3`）→ `80%`（`M/3<n≤2M/3`）→ `α`（`2M/3<n≤M`），
  `M ≈ 15000 ≈ N/100`。**Phase I 的职责被明写为 `devoted to the estimation of the variance reducers
  (θ*_α, μ*_α)`。**
- Phase II 伪代码（行 `857–870`）：`Set ξ_0 = ξ̂_M, C_0 = 0, θ_0 = θ̂_M, μ_0 = μ̂_M`，
  随后 `N` 步全部在**固定 `α`** 上跑 `(ξ_n, C_n, θ_n, μ_n)`，
  最终估计 `(ξ*_α, C*_α)` 由 **Phase II 的 Cesàro 均值 `(ξ̄_N, C̄_N)`** 给出。
  **Phase I 的整条轨迹只以初值形式进入 Phase II，不进入最终估计。**

**A4. 收敛性定理的内容是「退火渐近无害」，不是「退火改进解」。**

- 式 `(44)` 把退火写成扰动 `r_n := Ĥ₁(·,α_n) − H₁(·)`，界为 `|r_n| ≤ |α_n − α|/(1−α)²`；
  定理 2.2 的假设 (9) 成立的条件是 `Σ_{n≥1} γ_n (α − α_n)² < +∞`。
  **即：`α_n` 必须收敛到 `α` 快到使扰动平方可和，退火才不破坏 CLT。**
- 摘要（行 `20`）与结论（行 `1092`）宣称的收益是**方差削减 / IS 初始化提速**，
  不是「最终估计量更优」——最终估计量的渐近分布被证明**与不退火时相同**（minimal-variance CLT）。

**A5. 一处措辞与定义的出入（如实登记，不改变结论）。**

行 `800` 写 `Since the algorithm for the CVaR component C_n is free of α`，
但式 `(3)` 定义 `w(ξ,x) := ξ + (1/(1−α))(Ψ(φ(x)) − ξ)·1_{φ(x)≥ξ}`，
`H₂(ξ,c,x) := c − w(ξ,x)`（行 `246`）——`w` 显含 `1/(1−α)`，故该句字面不严格。
**但操作层面结论不受影响**：Phase I 伪代码根本不更新 `C`，移动水平确实从未进入 CVaR 估计。

**A6. 溯源到的更上游先例（判三线索）**：行 `48`、`794` 均注明
`This kind of incremental threshold increase has been already proposed in [22] in a different
framework (use of cross entropy in rare event simulation)`；
参考文献 `[22]`（行 `1140`）= Kroese & Rubinstein (2004), *The Cross-Entropy Method*, Springer。
**即 Bardou 自认此法不是其原创，源头是交叉熵法的自适应「中间水平序列」。**

### A 小结（对判一第 1 问的回答）

Bardou 的 `(α_n)` 是**单水平沿时间移动**，算法内部**没有并列多个 VaR/CVaR 水平**。
但主代理「单水平退火」的转述**遗漏了三件决定性的事**：
移动的是**一条被明确声明不估计目标的伴随过程**（A2）；
它只活在**一个其输出被丢弃、只留初值的预热相**（A3）；
定理证明的是**退火渐近无害**而非有益（A4）。

### B. Kawaguchi & Lu, Ordered SGD（`本地全文`，`raw/papers/methodology/ranking/2019-Kawaguchi-Ordered-SGD-arXiv.pdf`）

行号指全文笔记 `wiki/papers/…/2019-Kawaguchi-Ordered-SGD-arXiv-全文.md`。

**B1. `q` 确实是风险水平类量，但退火时旧 `q` 不留在损失中。**

- Theorem 1（行 `94`）：批内 top-`q` 的梯度是 `L_q(θ) = (1/q)Σ_j γ_j L_(j)(θ) + R(θ)` 的无偏次梯度。
- Proposition 1（行 `112`）：`1 − (1/s)γ(z)` 是 `Beta(z; q, s−q)` 的 CDF，「悬崖」位置由 `q/s` 决定——
  故 `q/s` 是一个尾部比例，与 `β` 同型。
- §6（行 `190`）：`The value of q was **automatically updated at the end of each epoch** based on this
  simple rule.` **每个时刻恰有一个 `q` 生效，`L_q` 整体被替换**；不存在「旧 `q` 项仍在损失里」的写法。

**B2.（本次核验的关键发现）该退火表的自述目的是「消掉一个超参数自由度」，不是一个被主张的机制。**

- §6 原句（行 `190`）：`**To avoid an extra freedom due to the hyper-parameter q**, we introduce a
  single fixed setup of the adaptive values of q as the default setting…`
  紧接：`This rule was derived based on the **intuition** that in the early stage of training, all
  samples are informative…`
  **即：这是为公平基准而固定的默认设置，作者未把它作为贡献主张，也未给出任何论证。**

**B3. 全部定理都只覆盖固定 `q`，退火过程无理论覆盖。**

- Theorem 2（行 `134`）显式假设 `there exists a finite θ* ∈ argmin_θ L_q(θ)`——**单一固定目标 `L_q`**。
- Theorem 3（行 `164`）的泛化界依赖固定的 `(q, s)`。
- **全文没有对「`q` 随轮次变化」这一非平稳目标序列的收敛性或泛化性作任何陈述。**

**B4. 论文自身的消融不支持「退火优于固定 `q`」。**

- 行 `536`（Figure 8 讨论）：`ordered SGD generally improved the test errors of mini-batch SGD,
  **even with fixed q values**.` 随后只定性说小 `q` 在后期有效、初期低效。
  **未给出「自适应规则优于最佳固定 `q`」的结论。**

**B5. 无「多个 `q` 并列」的讨论。**

全文检索 `multiple q`／`set of q`／`values of q` 只命中 Figure 8 的**跨运行**对比
（不同固定 `q` 各跑一次），不是同一损失内并列。
相关工作节（行 `254`）把 Fan et al. (2017) 的 average top-`k` 明确区分为**不同目标**。

### 判一小结（三问逐条）

1. **Bardou 的 `(α_n)`：单水平沿时间移动**，算法内部不并列多个 VaR/CVaR 水平。
   但它移动的是一条**被作者明确声明「in no case to approximate ξ*_α or C*_α」的伴随过程**，
   活在一个输出被丢弃、只留初值的预热相；定理证的是**渐近无害**（`Σγ_n(α−α_n)² < ∞`），不是有益。
2. **Ordered SGD 的 `q`：等价于一个尾部比例水平**；退火时**旧 `q` 不留在损失中**（逐轮整体替换）；
   全文**无任何「多个 `q` 并列」或「`q` 的集合」讨论**；且该退火表自述目的是**消超参自由度**，
   全部定理只覆盖固定 `q`，论文自身消融也未证明退火优于固定 `q`。
3. **没有任何一篇实际上是多水平的。** 主代理「多档 staging 无先例」的结论**不被这两篇推翻**；
   但「单水平退火有成熟先例」这句话**须大幅限定**——见判二。

## 判二证据

（待填）

## 判三证据

（待填）
