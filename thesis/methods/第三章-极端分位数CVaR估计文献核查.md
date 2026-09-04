# 第三章 · 极端分位数 CVaR 阈值估计的文献核查

<!-- RESEARCH_ROUTE=RWKV -->

- 日期：2026-09-04
- 唯一问题：**当 CVaR 的预算水平细到小批量在统计上分辨不出来时，文献里是怎么估这个阈值的？**
- 性质：**纯文献核查，未执行任何实验计算**（本机与服务器均未占用）
- 过程记录：`.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/`
  （`task_plan.md`、`notes.md`、`notes-P2.md`、`notes-P3.md`、`notes-P4.md`、`notes-P5.md`）
- 冻结前提（直接沿用，未重新推导）：`N_pop = 121336`、`n_neg = 64`、`n_pos = 2`、
  `K = [121, 606, 1213, 2426, 4853, 9706]`、
  `β = K/N_pop = [0.000997, 0.004994, 0.009997, 0.019994, 0.039996, 0.079993]`、
  `K_eff = β·n_neg = [0.0638, 0.3196, 0.6398, 1.2796, 2.5598, 5.1195]`

## 证据等级图例

| 级别 | 含义 |
| --- | --- |
| `L1` | 本地全文（`wiki/papers/**` 全文笔记，原件在 `raw/papers/**`） |
| `L2` | 在线全文已取得并逐页读取（**原件尚未按 `raw/AGENTS.md` 入库**） |
| `L3` | 在线摘要或定向抽取，未通读全文 |
| `L4` | 仅题录 |

**本文件中标 `L3`／`L4` 的条目一律不得单独支撑正文论断或候选存废裁决。**

---

## 零、必须先处理的一条更正（阻断项）

### 现有裁决文件对 SOPA 的引用是误读

`.Codex/docs/RWKV/2026-09-01-BER水库分位数修法裁决.md` 第四节写道：

> 「该结论与 SOPA 原文一致：Zhu 2022 的 p.3 式(6) 要求 `nγ` 为整数、p.4 式(7) 下方假设
> `n₋β` 为正整数。**本课题的低预算档违反该前提**，属于超出方法适用范围，不是实现缺陷。」

并据此在第五节给出正文处置：

> 「六档中低三档标注为**超出方法适用范围，依据 SOPA 原文的整数假设**。」

**核查结论：该前提本课题六档全部满足，不存在「违反」。**（证据 `L1`）

- SOPA 原文式 (7) 的求和域是 $\mathcal{S}_-^{\downarrow}[1,\,n_-\beta]$，
  即**全体负样本集合 $\mathcal{S}_-$** 排序后的前 `n₋β` 个。
  紧随其后的原文是 "where we assume $n_-\beta$ is a positive integer for simplicity of
  presentation"——**`n₋` 是训练集负样本总数，不是批量 `|B₋|`**。
- 本课题 `n₋ = N_pop = 121336`，`n₋β = K = 121, 606, 1213, 2426, 4853, 9706`，
  **六档全部是正整数。**
- 式 (6) 上方的 "for some γ such that `nγ` is an integer" 中的 `n` 同样是式 (4) 里
  $\ell_1,\dots,\ell_n$ 的个数（全体），不是批量。
- 另有旁证：SOPA 的 TPAUC 估计量用 $k_2=\lfloor n_-\beta\rfloor$（**取下整**），
  本身就允许 `n₋β` 非整数；HNS-OPAUC（Shi et al., WWW 2023）式 (8) 下方
  "we assume $n_-\cdot\beta$ is a positive integer" 中的 `n₋` 也同样是全体负样本数。

**处置要求**：

1. **正文不得写「依据 SOPA 原文的整数假设，低三档超出方法适用范围」**——该引用不成立，
   写进论文即为错误引用，会在引用核验与答辩中被击穿。
2. 低三档确实困难，但**正确的文献依据是另外三条**（见本文第一节），
   且其**适用范围只到「批内估计量」，不及于整个方法**。
3. 裁决文件第四节的另一句「**换任何估计器都修不好**」，
   与本核查取得的多条已发表工作**方向相反**（见第二节）。该句在科学主张层面不成立。
   ⚠ 但该裁决**关闭「榨干 C01」这条线的工程决定**另有独立理由
   （C01 已过目标年正增益门、第三章不受影响），**该工程决定不因本核查而自动推翻**，
   是否重开由用户裁决。

---

## 一、Q1：有没有已发表的「批量下界 vs 目标分位数水平」的可行性关系式？

**答：有，而且不止一条。核心结论是——关系式存在，但它约束的是「批内估计量」，
不约束「RU 对偶 + 跨步持久阈值 + 随机逼近」这条路径；后者把代价转移到步长与迭代数上。**

### 1.1 最直接的一条：Levy, Carmon, Duchi, Sidford (NeurIPS 2020) Proposition 1 · `L2`

《Large-Scale Methods for Distributionally Robust Optimization》，arXiv:2010.05893，
NeurIPS 33: 8847–8860。代码 `https://github.com/daniellevy/fast-dro`。

对任意 `x` 与批量 `n`，批目标 $\overline{\mathcal{L}}(x;n)=\mathbb{E}_{S_1^n}\mathcal{L}(x;S_1^n)$ 的偏差满足

$$0 \le \mathcal{L}(x;P_0) - \overline{\mathcal{L}}(x;n) \;\lesssim\; B\,\min\left\{1,\;(\alpha n)^{-1/2}\right\}
\qquad (\mathcal{L}=\mathcal{L}_{\text{CVaR}})$$

`B` 为损失上界。原文明确：该界在损失服从 Bernoulli 分布时
「tight up to constant or logarithmic factors ... and so are **unimprovable without further
assumptions**」——**最坏情况下不可改进**。

**`αn` 恰好就是本课题一直在用的 `K_eff`。** 代入六档：

| 档 | `β` | `K_eff = αn` | `(αn)^{-1/2}` | 偏差界 `B·min{1,·}` |
| ---: | ---: | ---: | ---: | :--- |
| 1 | 0.000997 | 0.0638 | 3.958 | `B`（**平凡**） |
| 2 | 0.004994 | 0.3196 | 1.769 | `B`（**平凡**） |
| 3 | 0.009997 | 0.6398 | 1.250 | `B`（**平凡**） |
| 4 | 0.019994 | 1.2796 | 0.884 | `0.884B` |
| 5 | 0.039996 | 2.5598 | 0.625 | `0.625B` |
| 6 | 0.079993 | 5.1195 | 0.442 | `0.442B` |

**界失效的恰好是低三档，与 2026-09-01 实测活动率恒为 `0` 的恰好是同一组档位。**
这是本核查最有判别力的一处吻合，且它来自一条与本课题无关的独立文献。

**反解所需批量**（`n ≳ B²/(αε²)`，取 `B = 1`）：

| 档 | `ε = 0.25B` 所需 `n` | `ε = 0.10B` 所需 `n` |
| ---: | ---: | ---: |
| 1 | 16 048 | 100 301 |
| 2 | 3 204 | 20 024 |
| 3 | 1 601 | 10 003 |
| 4 | 800 | 5 002 |
| 5 | 400 | 2 500 |
| 6 | 200 | 1 250 |

- **这独立支持了本仓库对 `n_neg → 256` 的既有否决，并给出了量级**：
  最低档即使只要求 `ε = 0.25B` 的宽松精度，也需要 `n ≈ 16000`，`256` 差 `60` 倍以上。
- **但同一命题的另一分支给出转机**：在附加假设 A2（`ℓ(x;S)` 的**逆 CDF 在目标分位邻域
  是 `G_icdf`-Lipschitz**）下，偏差界变为 $G_{\text{icdf}}\,n^{-1}$，
  原文写明该界「**independent of the uncertainty set size**」，
  且「for CVaR at level α, we **only need the inverse cdf `F⁻¹(β)` to be Lipschitz around
  `β = α`**, a common assumption in the risk estimation literature」。
- **因此严格的答案是：批量下界不是 `α` 的普适函数，而取决于损失分布在目标分位处的正则性。**
  - 分布退化／离散（大量并列值、hinge 把大批成对损失压成 `0` 质点）：`n ≳ 1/(αε²)`，无解。
  - 分布在目标分位邻域有不退化密度：`n ≳ G_icdf/ε`，**与 `α` 无关**，`n = 64` 可能已够。

### 1.2 方差侧：同文 Proposition 2 · `L2`

$$\mathrm{Var}\left[\nabla\mathcal{L}_{\text{kl-CVaR}}(x;S_1^n)\right] \lesssim \frac{G^2}{\alpha n}$$

（`L_CVaR` 是 `λ=0` 的特例，界同样成立。）梯度方差因子 `1/K_eff`：

`[15.67, 3.13, 1.56, 0.78, 0.39, 0.20]`，**最低档比最高档高 `80.2` 倍**。

**这给本仓库自定的诊断量 `K_eff` 提供了正式文献地位**——`K_eff = αn` 正是已发表方差界
分母上的那个量。但请注意结论是**方差**，不是**不可表示**：方差可以用步长、迭代数、
多层估计或平滑来交换。

### 1.3 总预算的信息论下界：同文 Theorem 3 · `L2`

> 对任意算法，存在分布 `P₀` 与凸 `G`-Lipschitz 损失 `ℓ: X×S → [0, GR]`，使得
> $T \le c\,(GR)^2/(\alpha\varepsilon^2)$ 蕴含
> $\mathbb{E}[\mathcal{L}_{\text{CVaR}}(x_T;P_0)] - \inf > \varepsilon$。

- **总梯度调用数 `Ω(1/(αε²))` 躲不掉**，且该下界在 `d = 1` 且预言机返回整个函数 `ℓ(·;S)`
  的更强模型下仍成立。
- **但它作用于总预算 `nT`，不作用于批量 `n`。可以用迭代数换批量。**
  这与 SOPA 的 `T = O(1/(βε⁴))` 是同一事实的两种表述。

### 1.4 统计侧：低档在**总体层面**是良定的 · `L3`

《Closing the Approximation Gap of PAUC Optimization: A Tale of Two Formulations》
（arXiv:2512.01213）给出紧泛化界 $\tilde{O}\left(\alpha^{-1}n_+^{-1} + \beta^{-1}n_-^{-1}\right)$。
负样本项即 $\tilde{O}(1/(\beta n_-)) = \tilde{O}(1/K)$：

`1/K = [0.00826, 0.00165, 0.000824, 0.000412, 0.000206, 0.000103]`——**六档全部很小**。

对照 Curi et al. (NeurIPS 2020) Proposition 1 的较松界
$\frac{1}{\alpha}\sqrt{\log(2|\mathcal{H}|/\delta)/N}$（`L2`）：取 `N = 121336`、
`log(2|H|/δ) = 10` 的乐观代入，最低档为 `9.11`（大于 `1`，界失效），
最高档为 `0.113`（有效），临界 `α ≈ 0.0091` 正好落在第三档附近。
**两条界取更紧的一条**，结论是：**低档的困难不在总体统计，在批内估计。**

### 1.5 「批量下界」问题的最精确形式：Ordered SGD 的 `γ_j` 刻画 · `L2`

Kawaguchi & Lu，《Ordered SGD》，AISTATS 2020（arXiv:1907.04371）。

**Theorem 1**：批内取 top-`q`（批量 `s`、总量 `n`）的随机方法，其梯度是下述目标的
**无偏**（次）梯度：

$$L_q(\theta) = \frac{1}{q}\sum_{j=1}^{n}\gamma_j L_{(j)}(\theta) + R(\theta),
\qquad
\gamma_j = \frac{\sum_{l=0}^{q-1}\binom{j-1}{l}\binom{n-j}{s-l-1}}{\binom{n}{s}}$$

**Proposition 1**：令 `z = j/n`，则 $\lim n\gamma_j = \gamma(z)$，
且 $1-\frac{1}{s}\gamma(z)$ 是 **Beta(`z`; `q`, `s−q`)** 的累积分布函数。

**这是「批内硬选择到底在优化什么」的闭式答案**：它不是总体的硬 top-`k`，
而是一条以 `Beta(q, s−q)` 为形状的**平滑权重**曲线；曲线的「悬崖」位置由 `q/s` 决定，
陡峭程度由 `s` 决定（原文 Figure 2：固定 `s,q` 增大 `n` 则悬崖变平滑；`n,q` 固定增大 `q`
则悬崖右移）。

**代入本课题**：`s = n_neg = 64`。批内可取的 `q` 是整数，故**该族方法能表达的最细预算是
`q/s = 1/64 = 0.015625`**。六档中 `β₁ = 0.000997`、`β₂ = 0.004994`、`β₃ = 0.009997`
**全部小于 `1/64`**，`β₄ = 0.019994` 大于 `1/64`。

**三条独立刻画在同一处分界**：

| 刻画 | 判为不可分辨的档位 |
| --- | --- |
| Levy Prop 1 偏差界取平凡值 `B` | 1, 2, 3 |
| Ordered SGD 的 `q/s = 1/64 = 0.0156` 分辨率地板 | 1, 2, 3（`β < 0.0156`） |
| 2026-09-01 实测活动率轮均值恒为 `0` | 1, 2, 3 |

⚠ **适用范围声明**：Ordered SGD 是**无跨步状态**的纯批内 top-`q`。
BER／SOPA 属**有跨步持久阈值**的 RU 对偶族，`γ_j` 刻画**不直接适用**。
它给出的是「无状态批内选择」这一族的确切分辨率地板，不是对 BER 的判决。

### 1.6 SOPA 自身对 Q1 的回答：**没有批量条件，只有步长与迭代数条件** · `L1`

SOPA（Zhu et al., ICML 2022）Theorem 3 与其附录 B.6：

| 量 | 取值 |
| --- | --- |
| `w` 随机梯度二阶矩 `G²` | $C^2/\beta^2$ |
| **阈值 `s` 的随机梯度二阶矩 `C₂²`** | $\frac{1}{n_+^2}\left(1+\frac{1}{\beta}\right)^2$ |
| 步长条件 | $\eta_2 B_+/n_+ = \eta_1$，$\eta_1 = O(\beta\varepsilon^2)$ |
| 迭代复杂度 | $T = O\!\left(1/(\beta\varepsilon^4)\right)$ |

- **Theorem 3 全文没有任何关于 `|B₋|` 的下界条件。**
  原文行文明确写出该 formulation 的目的就是绕开批内不可表示：
  "It is **impossible** to compute an unbiased stochastic gradient of the objective in (7) based on
  a mini-batch ... that include only a part of negative examples"，
  而改写后 "an **unbiased** stochastic subgradient can be computed in terms of (w, s)"。
- **`η₁ = O(βε²)`：阈值步长必须正比于 `β`。**
  本课题 `xi_learning_rate = 1e-4` 对六档取同一常数，而六档 `β` 跨 `80` 倍。
  按 SOPA 的定理条件，最低档步长应比最高档小 `80` 倍。
  **这是一条有全文出处、与已否决两条修法都不同、且可直接检验的第三条路径。**
- **`T = O(1/(βε⁴))`：最低档达到同精度需要比最高档多 `80` 倍迭代。**
  这解释了「六轮平均仍压不住」——不是量化噪声不可克服，是**该档的迭代预算少了近两个数量级**。

### Q1 小结

| 子问题 | 答案 |
| --- | --- |
| 有没有关系式？ | **有。** 偏差 `B·min{1,(αn)^{-1/2}}`；方差 `G²/(αn)`；总预算下界 `Ω(1/(αε²))`；无状态批内选择的分辨率地板 `q/s` |
| `β = 0.001` 对应多大批量？ | 无正则性假设时 `n ≳ 1/(αε²)`：`ε=0.25B` 需 `≈16 000`，`ε=0.1B` 需 `≈100 000`。**有逆 CDF 利普希茨时与 `α` 无关**，`n ≳ G_icdf/ε` |
| 能否验证／推翻本仓库根因判定？ | **部分支持、部分推翻。** 支持：`K_eff` 确是控制批内偏差与方差的正确量，低三档批内不可表示，`n_neg = 256` 远不够。推翻：（一）SOPA 整数假设并未被违反；（二）「换任何估计器都修不好」不成立——批量下界只约束批内估计量，不约束跨步随机逼近、MLMC、自适应抽样与软化 |

---

## 二、Q2：`β` 细于批量分辨率时别人怎么做？

**答：六条已发表路线。按与本课题的可移植性排序。**

### 2.1 调小阈值步长（代价：迭代数）· `L1` + `L2`

- SOPA 附录 B.6：$\eta_1 = O(\beta\varepsilon^2)$，`T = O(1/(βε⁴))`。
- Curi et al. 第 8 页原文："to stabilize learning, we used **considerably smaller learning rates**.
  In turn, this **increased the number of iterations required for convergence**."
- **可移植性最高**：只改 `xi_learning_rate` 的按档标定，不动算子、不动数据合同。

### 2.2 软化：把硬阈值换成连续温度／平滑参数 · `L1` + `L2` + `L3`

**这是覆盖面最广的一条，且四篇独立工作给出同一数学结构——对 `β` 的依赖是对数的。**

| 工作 | 机制 | `β` 依赖 | 本课题六档跨度 |
| --- | --- | --- | ---: |
| HNS-OPAUC（Shi et al., WWW 2023）`L1` | softmax 负采样，温度 $\tau=\sqrt{\dfrac{\mathrm{Var}_j(L)}{-2\log\beta}}$ | $1/\sqrt{-2\log\beta}$ | **1.65 倍** |
| Levy et al. Claim 1 `L2` | KL 正则 CVaR，$0\le\mathcal{L}_{\text{CVaR}}-\mathcal{L}_{\text{kl-CVaR}}\le\lambda\log(1/\alpha)$，取 $\lambda\asymp\varepsilon/\log(1/\alpha)$ | $1/\log(1/\alpha)$ | **2.74 倍** |
| SOPA-s（Zhu et al. Alg. 2）`L1` | 移动平均 `u_i` 追踪 $\mathrm{E}\exp(L/\lambda)$，软权重 $p_{ij}=\exp(L/\lambda)/u_i$，**无阈值变量** | λ 连续 | 连续 |
| PAUC「两种表述」（arXiv:2512.01213）`L3` | 可学习阈值 + softplus $r_\kappa(x)=\log(1+e^{\kappa x})/\kappa$ 光滑 $[x]_+$ | κ 连续 | 连续 |

**关键数学事实**：硬计数路线对 `β` 是**线性**依赖（`αn`，跨 `80` 倍），
软化路线对 `β` 是**对数**依赖（跨 `1.65`–`2.74` 倍）。
**这就是极端 `β` 下软化可行、硬计数不可行的统一解释。**

HNS-OPAUC 的六档温度代入（$\tau_k=\sqrt{\mathrm{Var}_j(L)}/c_k$，$c_k=\sqrt{-2\ln\beta_k}$）：

| 档 | `β` | `−2 ln β` | `c_k` | `τ_k` 相对最高档 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.000997 | 13.822 | 3.718 | 0.605 |
| 2 | 0.004994 | 10.599 | 3.256 | 0.690 |
| 3 | 0.009997 | 9.211 | 3.035 | 0.741 |
| 4 | 0.019994 | 7.825 | 2.797 | 0.804 |
| 5 | 0.039996 | 6.438 | 2.537 | 0.886 |
| 6 | 0.079993 | 5.052 | 2.248 | 1.000 |

（**算术代入，非实验**；`Var_j(L)` 需实测，未测。）

SOPA-s 的 Theorem 4 复杂度
$T=O\!\left(\frac{1}{\min(B_+,B_-)\varepsilon^4}+\frac{n_+}{B_+B_-\varepsilon^4}\right)$
**不含 `1/β`**；SOPA 自己的 Table 3 显示在两个最不平衡数据集上 SOPA-s 优于 SOPA
（molmuv(t1) FPR≤0.3：`0.8449` vs `0.8187`）。

### 2.3 罕见事件重要性抽样 · `L2` + `L3`

**（a）ADA-CVAR（Curi, Levy, Jegelka, Krause; NeurIPS 2020）`L2`**

原文第 3 页把低 `α` 的 CVaR 训练**明确归类为罕见事件蒙特卡洛问题**：

> "Problem (3) can be interpreted as a form of **rejection sampling** – samples with losses smaller
> than ℓ are rejected. It is well known that **Monte Carlo estimation of rare events suffers from
> high variance** ... we propose a novel sampling algorithm that **adaptively learns to sample
> events from the distribution Q\*** while optimizing the model parameters θ."

机制：把 DRO 内层 $\mathcal{Q}^\alpha=\{q\mid 0\le q_i\le 1/k,\ \sum q_i=1\}$、$k=\lfloor\alpha N\rfloor$
写成零和博弈，`q`-玩家用对角核 k-DPP 的边缘分布作决策变量，
按 $w_{t+1,i_t}=w_{t,i_t}e^{\eta_s kL_{t,i_t}/q_{t,i_t}}$ 做 EXP3 型乘性更新，
**每步只采一个点（或一个小批），由采样器保证采到的就是尾部点**。
脚注明确 "we do **not** use any importance sampling correction"。
`k = ⌊αN⌋` 中的 `N` 是**数据集规模**——本课题 `k = K = 121`，合法。

**（b）Bardou, Frikha, Pagès (2009)`L3`**
《Computing VaR and CVaR using stochastic approximation and adaptive unconstrained importance
sampling》，Monte Carlo Methods and Applications 15(3): 173–210，arXiv:0812.3381。
基于 Rockafellar-Uryasev 恒等式的 Robbins-Monro 过程 + 递归自适应重要性抽样。原文：

> "the bottleneck of this algorithm is that it is **only updated on rare events** since it tries to
> measure the tail distribution of φ(X): ℙ(φ(X)>VaR_α)=1−α≈0"

**（c）Exponential Adaptive Smoothing and IS for CVaR（arXiv:2606.11515，2026）`L3`**
Bregman 邻近点算法，用广义 Fermi-Dirac 熵作正则（同样是 `ln(1+exp(·))` 家族），
对偶分布同时提供**自适应平滑**与**内建重要性抽样**。原文对小 `α` 问题的表述：

> "an increasing fraction of samples ... neither contribute to the objective nor to its gradient,
> yet they still incur computational cost ... limits the efficiency of both sample-average
> approximation and stochastic approximation schemes in high-confidence CVaR optimization."

### 2.4 **预算水平退火（moving risk level）** · `L3`

Bardou, Frikha, Pagès (2009) 原文：

> "we make the confidence level **slowly increase from a low level (say 50%) to α** by introducing
> a **deterministic sequence $(\alpha_n)_{n\ge0}$ of confidence level that converges toward α**"

（该文只作定性描述，抓取到的正文**未给出 $\alpha_n$ 的解析式**，须取全文核。）

**独立的第二处证据（且在深度学习侧）**：Ordered SGD 的默认设置就是一条退火表——
`q = s` 起步，`train_acc ≥ 80%` 后 `q = ⌊s/2⌋`，`≥ 90%` 后 `⌊s/4⌋`，
`≥ 95%` 后 `⌊s/8⌋`，`≥ 99.5%` 后 `⌊s/16⌋`（`s = 64`）。
**两条互不相关的文献在同一件事上收敛：不要从第一步就用极端预算，从宽到窄退火。**

### 2.5 多层蒙特卡洛（MLMC）：**不常驻加批量而获得大批量统计效力** · `L2`

Levy et al. 2020 第 4 节。取截断几何变量 $J\sim\min\{\mathrm{Geo}(1/2),j_{\max}\}$，
$q(j)=\mathbb{P}(J=j)$，偏差增量

$$\widehat{\mathcal{D}}_k := \nabla\mathcal{L}(x;S_1^k) - \frac{\nabla\mathcal{L}(x;S_1^{k/2})+\nabla\mathcal{L}(x;S_{k/2+1}^{k})}{2},
\qquad
\widehat{\mathcal{M}}[\nabla\mathcal{L}] := \nabla\mathcal{L}(x;S_1^{n_0}) + \frac{1}{q(J)}\widehat{\mathcal{D}}_{2^Jn_0}$$

- **Claim 2**：$\mathbb{E}\widehat{\mathcal{M}}[\nabla L]=\nabla\overline{\mathcal{L}}(x;n)$，
  **期望样本量只有 $n_0(1+\log_2(n/n_0))$**（对数于 `n`）。
- **Proposition 4**：$\mathbb{E}\|\widehat{\mathcal{M}}[\nabla\mathcal{L}_{\text{CVaR}}]\|^2
  \lesssim\left(1+\frac{\log(n/n_0)}{\alpha n_0}\right)G^2$。
- **Theorem 2**：取 $n\asymp B^2/(\alpha\varepsilon^2)$、$1\lesssim n_0\lesssim \log n/\alpha$、
  $T\asymp\frac{(GR)^2}{n_0\alpha\varepsilon^2}\log^2 n$，总复杂度
  $\lesssim\frac{(GR+B)^2}{\alpha\varepsilon^2}\log^2\frac{B^2}{\alpha\varepsilon^2}$，与下界匹配。

**本课题换算（算术代入，非实验）**：最低档 `α = 0.000997`，取 `B = 1`、`ε = 0.25`
→ 目标等效批量 `n ≈ 16 048`，取 `n = 2⁸·64 = 16 384`，以 `n₀ = 64` 为最小层：
期望样本量 $=64\times(1+8)=576$，即**平均每步 `576` 个负样本（约 `9×` 现有代价），
换取等效批量 `16 384` 的无偏梯度**；`P(J=1)=1/2`，**绝大多数步骤仍只用小批**，
峰值 `16 384` 的概率为 `2⁻⁸`。

**与已否决的 `n_neg → 256` 是不同性质的做法**：后者是恒定 `4×` 提升，仍比所需低 `60` 倍；
MLMC 是**指数覆盖 + 对数期望代价**。
⚠ **峰值显存是主要工程风险**，须先核 CVaR hinge 在负样本维度可分块累积后的峰值占用。
本条整体标为**待验证**。

### 2.6 极值理论（POT/GPD）从小样本外推尾部分位数 · `L1` + `L3`

- 本地已核验：SPOT（Siffer et al., KDD 2017）`L1`，
  外推式 $z_q = u + \frac{\sigma}{\xi}\left[\left(\frac{qN}{N_u}\right)^{-\xi}-1\right]$。
  **关键性质：`q` 可以远小于 `1/N`**——GPD 不要求样本里真的出现过 `q` 分位。
- **但与本课题的落差不可忽略**：SPOT 是**部署期**对**冻结分数**的阈值估计，
  不在训练循环内、不需要梯度、拟合样本量是数千级初始批而非 `64`。
- 训练循环内使用 EVT 的公开做法主要是「GPD 偏差损失作为可微目标」
  （Pasche & Engelke，arXiv:2208.07590，`L3`）与两阶段残差 POT（`L3`）。
  已知阻碍：GPD 负对数似然在 `ξ ≈ 0` 与支撑边界附近病态；POT 假设平稳与独立，
  而训练中损失分布每步都在漂移。
- **结论：这条线在本课题可移植性最低**，除非用于部署期阈值而非训练期预算。
  本仓库 SPOT 笔记既有边界（不得把 `q` 写成假阳性率、不得声称 EVT 提高平均精确率）继续有效。

### 2.7 对任务简报中一条具体询问的回答（负面结果）

**「LibAUC 的 `DualSampler`/`TriSampler` 对 `β` 与批量的处理」——答案是这两个采样器不处理 `β`。**（`L1`）

- `DualSampler` 的超参是 `batch_size` 与 `sampling_rate`，`# positives = batch_size × sampling_rate`，
  控制的是**批内正样本比例**，面向类别不平衡。
- `TriSampler` 的 `sampled_tasks`／`batch_size_per_task`／`sampling_rate_per_task`
  同样是「每 query 的正样本占比」，面向 LTR 多 query 结构。
- LibAUC 对小批量的真实答案是 **SOPAs（软版）+ 移动平均超参随批量重标定**：
  4.4.3 节原文 "For each batch size, **we tune γ correspondingly as theories indicate its best
  value depends on batch size**"，批量取 `{512, 256, 128, 64}`。

### 2.8 文献实际走到过多细的 `β`（用于标定「本课题在地图上的位置」）

| 工作 | 批量 | 实测最小 `β`／`α` | `β·批内负样本` |
| --- | ---: | ---: | ---: |
| SOPA（ICML 2022）`L1` | 64 | `β = 0.1` | `≈ 3.2–6.4` |
| ADA-CVAR（NeurIPS 2020）`L2` | 每步 1 点或小批 | `α = 0.01` | 不适用（自适应采样器） |
| PAUC 两种表述（2025-12）`L3` | 1024 | `β = 0.3` | `≈ 154` |
| Ordered SGD（AISTATS 2020）`L2` | 64 | `q/s = 1/16 = 0.0625` | `4` |
| **本课题最低档** | **64** | **`β = 0.000997`** | **`0.0638`** |

**本课题最低档比上表任何一项实测过的水平都低至少一个数量级。**
`α = 0.01`（ADA-CVAR）对应本课题第三档；**第一、二档在已核查的实验文献里没有先例。**

---

## 三、Q3：有没有工作报告过阈值追踪的 bang-bang／振荡现象及其处置？

**答：有，而且是逐字命中，并给出了三条处置。同时在另一支文献里是零结果。**

### 3.1 正面命中：Curi et al. (NeurIPS 2020) 第 8 页 · `L2`

> "The gradients of TRUNC-CVAR are **either 0 or 1/α times larger** than the gradients of the same
> point using MEAN. A similar but smoothed phenomenon arises with SOFT-CVAR. This makes training
> these losses considerably harder due to **exploding gradients and noisier gradient estimates**.
> With the same learning rates, these algorithms usually produce **numerical overflows** and, to
> stabilize learning, we used **considerably smaller learning rates**. In turn, this **increased the
> number of iterations required for convergence**. ADA-CVAR does not suffer from this as the
> gradients have the same magnitude as in MEAN. For example, to reach 85 % train accuracy ADA-CVAR
> requires 7 epochs, MEAN 9, SOFT-CVAR 21, and **TRUNC-CVAR never surpassed 70 % train accuracy**."

**数值吻合**：本课题最低档 `1/β = 1/0.000997 = 1003`，实测全活动时的不对称比 `1002`。
「要么 `0`、要么 `1/α` 倍」正是实测的 `14.7`–`1002` 倍。

**因此 Q3 的结论是**：该现象**已被公开报告**，且被判定为
**截断型（Rockafellar-Uryasev）formulation 的固有性质，不是实现缺陷**。
BER 现用实现属同一族，出现该现象是**预期行为**。

原文给出的三条处置（按其自评效果排序）：

| 处置 | 原文评价 | 与本课题的关系 |
| --- | --- | --- |
| 调小学习率 | 实际采用；代价是迭代数上升 | 与 SOPA `η₁=O(βε²)` 同向，**可直接执行** |
| 平滑化（SOFT-CVAR，Nemirovski-Shapiro 的 $T\log\sum e^{x_i/T}$ 松弛） | 「a similar but **smoothed** phenomenon arises」，缓解但未消除，21 epoch vs 9 | 与 §2.2 软化路线同族 |
| 自适应采样（ADA-CVAR） | 梯度量级与 MEAN 相同，7 epoch 达标 | 需换采样器，改动最大 |

### 3.2 SOPA 的结构性解释 · `L1`

BER 现用的 `ξ` 更新式**逐字**就是 SOPA Algorithm 1 第 5 行：

$$s_i^{t+1}=s_i^t-\frac{\eta_2}{n_+}\left(1-\frac{\sum_j p_{ij}}{\beta|\mathcal{B}_-|}\right)
\qquad\longleftrightarrow\qquad
\frac{\partial L}{\partial\xi}=\frac{1}{N_p|K|}\left(1-\frac{n_{\text{active}}}{K_{\text{eff}}}\right)$$

（`K_eff = β|B₋|`。）不对称比恒为 `1/β`，**与估计器实现无关，是该更新式的代数性质**。
附录 B.6 的 $C_2^2=\frac{1}{n_+^2}(1+1/\beta)^2$ 是该不对称的方差表述。

**SOPA 原文全文检索 `oscillat`／`unstable`／`instabilit`／`fluctuat`／`vanish` 零命中**——
SOPA 提出了这个更新式，但**没有报告或讨论它的振荡**。

### 3.3 通用分位数追踪文献：**零结果（如实记录）** · `L3`

- Robbins-Monro 分位数递推的驱动项 $(\tau-\mathbb{1}\{X_t\le q_t\})$ 天然不对称：
  多数步下降 $\alpha_t\tau$，罕见越界上跳 $\alpha_t(1-\tau)$，比值 $(1-\tau)/\tau$。
- 步长两难：经典收敛要求 $\sum\alpha_t=\infty$、$\sum\alpha_t^2<\infty$；
  **追踪非平稳目标时必须放弃后者**，改用常数或缓慢衰减步长，**这就保证了持续振荡而非收敛**。
  → 本课题 `xi_learning_rate = 1e-4` 恒定不衰减，属「追踪」配置，振荡是配置的预期后果。
- 稳定化方向：proximal Robbins-Monro（Toulis & Horel，arXiv:1510.00967），
  作者以 Robbins & Monro (1951) 原始分位数回归例子演示数值稳定性改善。
- **零结果声明**：检索式
  `Robbins-Monro stochastic approximation extreme quantile tracking instability oscillation
  asymmetric update rare exceedance step size`
  **未命中**专门研究「极端分位（`τ→1`）下 RM 追踪振荡幅度及其处置」的工作。
  该子问题在通用随机逼近文献中**看起来是空白**。
  ⚠ 但这是**一轮检索的零结果**，不是穷尽性否定；且它不影响 Q3 的整体结论——
  在「CVaR 深度学习」这一支里现象与处置都有明确出处。

### 3.4 反向标定：批量足够时不出现该现象

`arXiv:2512.01213`（batch 1024，`β ∈ {0.3, 0.5}`，即 `β·n₋^B ≈ 154`）**未报告任何阈值不稳定
或梯度爆炸**（`L3`）。这与 `1/β` 不对称度随 `β` 增大而急剧减小的代数事实一致。

---

## 四、Q4：有没有先例是「直接放弃不可表示的档位」？

**答：有一条明确的、可量化的先例，但它在评价侧；把它的判据代入本课题，
六档全部通过，即该先例不支持砍掉任何一档。此外还有两条「不砍档而改做法」的先例。**

### 4.1 明确的先例：评价侧的 `N × FPR ≥ 100` 判据 · `L2`

《Leveraging Uncertainty for Improved Static Malware Detection Under Extreme False Positive
Constraints》，arXiv:2108.04081（作者与发表载体**未核**，只核了正文内容）。第 5 页原文：

> "One can clearly see that as the validation set size decreases, the ability to estimate the FPR
> decreases. This causes more errors and a **"shortening" of the curves as it becomes impossible to
> estimate lower desired FPR rates**. This last point is important as **some prior works have
> reported FPRs lower than what their dataset could accurately estimate. If the test set size times
> the desired FPR is less than 100 samples, it is unlikely the TPR@FPR reported will be an accurate
> estimate** (e.g., as done in [Anderson et al., 2016])."

同页另有更严的示例性说法：

> "low FPRs naturally require more data to estimate: if you want an FPR of 1:1,000 and you want
> 1,000 FPRs to estimate the threshold from you would expect to need `1,000² = 1 million` examples."

**代入本课题（`N_pop × β = K`）**：

| 档 | `K = N_pop·β` | `≥ 100`？ | 相对标准误 `1/√K` |
| ---: | ---: | :---: | ---: |
| 1 | 121 | **通过**（临界） | 9.09 % |
| 2 | 606 | 通过 | 4.06 % |
| 3 | 1213 | 通过 | 2.87 % |
| 4 | 2426 | 通过 | 2.03 % |
| 5 | 4853 | 通过 | 1.44 % |
| 6 | 9706 | 通过 | 1.02 % |

**六档全部通过该判据**，最低档 `121` 刚过门槛 `100`，相对标准误 `9.1 %`。
（假阳数近似 `Poisson(N·β)`，相对标准误 `1/√K`；`K = 100` 对应 `10 %`，
即该 `×100` 启发式的统计等价形式。）

**结论**：**已发表的「砍档」判据不支持砍掉本课题任何一档。**
若要砍档，需要另找依据，且不能援引本判据。

⚠ 边界：该判据针对**评价集上估计 TPR@FPR 的可靠性**，
不直接等价于**训练期批内预算档的可优化性**。二者不可混用。

### 4.2 「不砍档，改做法」的先例（两条）· `L2`

**（a）Ordered SGD：把批量能表达的东西定义为目标。**
不宣称批内 top-`q` 等于总体 top-`k`，而是给出批内过程**真正**在优化的目标
$L_q(\theta)=\frac{1}{q}\sum_j\gamma_jL_{(j)}(\theta)+R(\theta)$（`Beta(q,s−q)` 型权重），
并论证该目标本身在泛化上可取（Theorem 3）。
**这是「承认分辨率上限、改写目标口径」而非「删掉档位」。**

**（b）Ordered SGD 的 `q` 退火在 `⌊s/16⌋` 处停止，不下探到 `q = 1`。**
`s = 64` 时最细只到 `q = 4`（`q/s = 0.0625`）。这**接近**「主动不使用最极端档位」，
但原文将其表述为超参默认设置的经验规则，**未给出「因为不可表示所以停在这里」的论证**。
故只能作为**弱先例**，不足以单独支撑砍档裁决。

### 4.3 一处需要澄清的非先例 · `L3`

《Large-scale Optimization of Partial AUC in a Range of False Positive Rates》
（arXiv:2203.01505，NeurIPS 2022）确实把 FPR 限定在 `[α, β]`（`α > 0`），
但其摘要给出的动机是 **「低 FPR 段无实际相关性」**
（"may include the FPRs with **no practical relevance** in some applications"），
**不是「低 FPR 段估不准」**。
**该文不能被引用为「因不可表示而放弃档位」的先例。**
（该判断基于摘要；正文是否另有论述**未核**。）

### 4.4 关于本机模拟

任务简报指出「本机模拟显示只留后三档反而更差，但模拟复现不了真实基线，不可采信」。
**本核查支持维持该不可采信判定**，并补充：即使模拟可信，
按 §4.1 的已发表判据也没有砍档的依据。

---

## 五、零结果声明（明确哪一问文献没有答案）

| 编号 | 零结果内容 | 检索范围 | 严格性 |
| --- | --- | --- | --- |
| Z1 | **没有**任何工作报告过在 `K_eff < 1` 的深度学习 CVaR/pAUC 训练中的**实验**结果 | 本核查覆盖的 SOPA、SOPA-s、SOTA-s、LibAUC、HNS-OPAUC、ADA-CVAR、Levy et al.、Ordered SGD、arXiv:2512.01213 | 强。已核工作中实测最小 `α/β` 为 `0.01`（ADA-CVAR），对应本课题第三档；**第一、二档无实验先例** |
| Z2 | **没有**专门研究极端分位（`τ→1`）下 Robbins-Monro 阈值追踪**振荡幅度及其处置**的工作 | 一轮定向检索（检索式见 §3.3） | 中。一轮零命中，非穷尽；但 Q3 在 CVaR 深度学习一支有明确出处，故该空白不阻断结论 |
| Z3 | **没有**「因批内不可表示而主动删除预算档位」的直接先例 | pAUC/CVaR/低 FPR 评价三支 | 中。最接近的是评价侧 `N×FPR ≥ 100` 判据（§4.1，代入后六档全过）与 Ordered SGD 的 `q ≥ s/16` 经验停点（§4.2b，未给论证） |
| Z4 | **没有**在训练循环内用 EVT/POT 外推 CVaR 阈值、且报告了极端 `β` 下有效性的工作 | EVT-in-training 一轮检索 | 中。现有 EVT×深度学习工作是 GPD 偏差损失或两阶段残差 POT，**不是训练期 CVaR 阈值外推** |
| Z5 | **没有**给出「批量下界」的单一普适公式 | 全部 | 强，且是**实质性发现**：Levy et al. 证明该关系式**必然依赖损失分布在目标分位处的正则性**（无正则性 `n≳1/(αε²)`，逆 CDF 利普希茨则与 `α` 无关） |
| Z6 | Bardou et al. 的 moving risk level **解析调度式**未从抓取正文中取得 | arXiv:0812.3381 HTML 定向抽取 | 需取全文补 |

---

## 六、由本核查引出的可执行动作（全部标为「待验证」，**不构成开工授权**）

按「改动成本 / 判别力」排序。**下列均未经本课题任何实验证实。**

| 编号 | 动作 | 文献依据 | 是否触及冻结合同 |
| --- | --- | --- | --- |
| A1 | **测本课题成对损失分布在六档目标分位邻域的逆 CDF 局部斜率**（等价于密度是否退化、是否有并列质点）。这是判定「批量是否真是硬约束」的**决定性且最便宜**的测量，不接触最终目标标签，可在源年训练数据上做 | Levy et al. Prop 1 式 (8) vs (11)，假设 A2 | 否，纯诊断 |
| A2 | 把 `xi_learning_rate` 由六档同值改为**按档正比于 `β`** 标定 | SOPA 附录 B.6 `η₁=O(βε²)`；Curi et al. 第 8 页「considerably smaller learning rates」 | 是（改超参，需重跑） |
| A3 | 用 softplus $r_\kappa$ 光滑 BER 的 hinge `[·]₊`，`κ` 按档标定 | arXiv:2512.01213；Curi et al. SOFT-CVAR；Nemirovski & Shapiro 松弛 | 是（改算子） |
| A4 | **预算档退火**：由宽到窄（如 `q/s` 由 `1` 降到目标档）而非从第一步就用极端档 | Bardou et al. moving risk level；Ordered SGD 的 `q` 退火表 | 是（改训练协议） |
| A5 | 对低三档改用 SOPA-s 型软权重（移动平均 `u_i`，**去掉 ξ 变量**）或 HNS 型 softmax 温度采样（`τ` 按 §2.2 表标定） | SOPA Thm 2/Alg 2；HNS-OPAUC Thm 2 | 是（换机制，等于新候选） |
| A6 | MLMC 梯度估计器（`n₀ = 64`，`j_max` 由目标 `ε` 定） | Levy et al. §4，Claim 2 / Prop 4 / Thm 2 | 是；**峰值显存须先核** |

**先做 A1。** 它单独就能验证或推翻「批内采样规模是根因」这一判定，
成本远低于 A2–A6 中任何一项，且不需要改任何冻结配置。

---

## 七、不可声称清单

1. **不得**写「依据 SOPA 原文的整数假设，低三档超出方法适用范围」——该引用不成立（§零）。
2. **不得**把「`K_eff < 1` 所以数学上无法表示」写成对整个方法的判决；
   其成立范围是**无跨步状态的批内估计量**（Levy Prop 1、Ordered SGD `γ_j`），
   不及于 RU 对偶 + 跨步随机逼近（SOPA Thm 3 无批量条件）。
3. **不得**声称「换任何估计器都修不好」——与 §2 的六条已发表路线方向相反。
4. **不得**把 §1、§2 中任何代入本课题常数的表格当作实验结果；它们全部是**算术代入**，
   `B`、`G`、`R`、`Var_j(L)`、`G_icdf` 均**未测**。
5. **不得**用 §4.1 的 `N×FPR ≥ 100` 判据论证训练期档位的可优化性——该判据只针对评价侧。
6. **不得**依据本文件启动实现。所有动作须先过 `writing-plans`，
   且机制候选须先过实验判据（本仓库规则：未通过实验判据的机制候选不进入实现）。
7. 标 `L3`／`L4` 的条目（arXiv:2512.01213、2203.01505、0812.3381、2606.11515、
   CVaR 集中不等式一族、RM 分位数追踪一族）**必须先取全文入库**才能进入正文引用。

---

## 八、证据台账

| 出处 | 等级 | 位置 | 支撑的问题 |
| --- | :---: | --- | --- |
| Zhu et al., *When AUC meets DRO*, ICML 2022（SOPA） | `L1` | `wiki/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO-ICML-全文.md`：式(6)(7)、Alg.1 第 5 行、Thm 2 Remark、Thm 3、附录 B.6、§6 参数表 | §零、Q1.6、Q2.1/2.2、Q3.2 |
| Shi et al., *Theories Behind Hard Negative Sampling*, WWW 2023 | `L1` | `wiki/papers/methodology/ranking/2023-Shi-HNS-OPAUC-arXiv2302.03472-全文.md`：式(8)(14)(17)(19)(20)、Thm 1/2 | Q2.2 |
| Yuan et al., *LibAUC*, KDD 2023 | `L1` | `wiki/papers/methodology/training-efficiency/2023-Yuan-LibAUC-X-Risk-Optimization-KDD-全文.md`：§3.2、§4.4.2、§4.4.3 | Q2.7 |
| Siffer et al., *SPOT*, KDD 2017 | `L1` | `wiki/papers/methodology/2017-Siffer-SPOT极值流阈值.md`（原件 `raw/papers/methodology/2017-Siffer-SPOT-EVT-Anomaly-Streams.pdf`） | Q2.6 |
| Levy, Carmon, Duchi, Sidford, NeurIPS 2020 | `L2` | arXiv:2010.05893，PDF 第 4、6–11 页：Prop 1/2/4、Claim 1/2、Thm 1/2/3、§4 | **Q1 主体**、Q2.2/2.5 |
| Curi, Levy, Jegelka, Krause, NeurIPS 2020（ADA-CVAR） | `L2` | arXiv:1910.12511v3，PDF 第 3、4、7–9 页 | **Q3 主体**、Q1.4、Q2.1/2.3 |
| Kawaguchi & Lu, *Ordered SGD*, AISTATS 2020 | `L2` | arXiv:1907.04371，PDF 第 3–5 页：Thm 1、Prop 1、Fig 2、§6 超参表 | Q1.5、Q4.2 |
| *Leveraging Uncertainty ... Extreme FP Constraints* | `L2` | arXiv:2108.04081，PDF 第 5 页 §4.1 | **Q4 主体** |
| *Closing the Approximation Gap of PAUC* | `L3` | arXiv:2512.01213：摘要 + Thm 5 + 实验设置 | Q1.4、Q2.2、Q3.4 |
| *Large-scale Optimization of pAUC in a Range of FPRs* | `L3` | arXiv:2203.01505：仅摘要 | Q4.3（非先例） |
| Bardou, Frikha, Pagès, MCMA 2009 | `L3` | arXiv:0812.3381：定向抽取 | Q2.3b、Q2.4 |
| *Exponential Adaptive Smoothing and IS for CVaR* | `L3` | arXiv:2606.11515：摘要 + 定向抽取 | Q2.3c |
| CVaR 集中不等式一族（Kolla et al. 2019；Prashanth et al. ICML 2020；Bhat & Prashanth；Thomas & Learned-Miller） | `L3` | 检索层综合，未取全文 | Q1（`n=Ω(1/α)` 对插件估计量） |
| Toulis & Horel, *Proximal Robbins-Monro* | `L4` | arXiv:1510.00967 | Q3.3 |

### 未入库提示

标 `L2` 的四份 PDF 目前只存在于本会话工具缓存，**不是仓库原件**。
若要正式引用，须按 `raw/AGENTS.md` 下载入 `raw/papers/methodology/`，
按 `wiki/AGENTS.md` 建结构化全文笔记（frontmatter 八字段、`source_pdf` 指向原件），
并更新 `wiki/papers/methodology/INDEX.md`。

---

## 九、本次核查的工具实况（影响可复现性，如实登记）

本代理会话**没有** `Bash`、`Skill`、`ToolSearch` 工具，导致规定检索链未能按原样执行：

| 规定路径 | 实际执行 | 影响 |
| --- | --- | --- |
| `uv run --project scripts/literature_search ... query --mode hybrid` | **无法执行**（无 `Bash`）。改用内置 `Grep`/`Glob` 直接检索 `wiki/papers/**` | 语料同一批，但**向量通道未运行**，只等价于 lexical 检索；可能漏掉语义近邻 |
| `Skill` 调用 `planning-with-files`／`literature-reviewer`／`citation-verification`／`pdf-converter` | **无法调用**。按其工作流手工执行；`task_plan.md` 与 `notes*.md` 即 `planning-with-files` 的产物形态 | `citation-verification` 未运行，**题录（作者、卷期页）未逐条核**；本文件只核了**正文内容**出处 |
| `pdf-converter`（MinerU）读 PDF | 用 `Read` 的原生 PDF 通道（**不是 `pdftotext`**，未违反禁令） | 公式为图像识读，保真度低于 MinerU。本文件所引公式均来自可清晰辨认的排版，但**正式引用前建议用 MinerU 复核** |
| `ToolSearch` 加载五个 MCP 检索服务 + `zotero_semantic_search` | **均不在本代理可用工具表内**；Zotero 只有 `search_items`/`get_item_fulltext` 等基础工具 | 在线检索改用 `WebSearch` + `WebFetch`；**Zotero 去重检查未执行** |
| 分阶段 `git commit` | **无法执行**（无 `Bash`）。已分六次落盘文件 | 需由主代理补提交 |

**已落盘但未提交的文件**（需主代理执行 Conventional Commits 提交，禁止 Co-Authored-By）：

- `thesis/methods/第三章-极端分位数CVaR估计文献核查.md`（本文件）
- `.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/task_plan.md`
- `.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/notes.md`
- `.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/notes-P2.md`
- `.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/notes-P3.md`
- `.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/notes-P4.md`
- `.Codex/docs/RWKV/2026-09-04-极端分位数CVaR文献核查/notes-P5.md`
