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

### 第 1 组：本地混合索引（`本地`）

索引 `status --json` 初次为 `stale=true`（`source_added`/`source_changed`），
已用 `build --json` 增量重建（`note_count=1960`，`papers=891`，`index_bytes=903024640`，退出码 `0`），
**向量通道正常运行**（`vector_count=142289`，`dim=384`，`device=mps:0`），未降级 lexical。

| 查询式 | scope/mode | 结论 |
| --- | --- | --- |
| `spectral risk measure Kusuoka representation weighted mixture of multiple CVaR confidence levels` | paper/hybrid | **本地无谱风险测度类论文**；top 命中是 Duchi-Namkoong DRO、Levy DRO、Bardou、Curi、Asness 等已知件 |
| `simultaneous estimation of multiple quantiles non-crossing quantile levels neural network` | paper/hybrid | **本地无多分位数/不交叉分位数论文**；命中漂移到 TAILING、conformal、PINN |
| `sum of ranked range average top-k loss combining two rank thresholds multiple budget levels in one objective` | paper/hybrid | 命中 `2021-Hu-SoRR`、`2022-Yao-Large-Scale-Partial-AUC-FPR-Range`、`2025-Jiang-Partial-AUC-Two-Formulations`（均在库） |

**本地语料在「多水平风险度量」这一支上基本是空白**——本课题此前的「无先例」结论
有很大一部分是本地语料覆盖不到，而不是文献真的没有。

### 第 2 组：Zotero 语义检索（`仅题录`）

- `spectral risk measure Kusuoka representation optimizing weighted combination of multiple CVaR confidence levels`
- `simultaneous multiple quantile regression non-crossing quantile levels curriculum from central to extreme quantiles`

两次检索 **12/12 命中相似度全为负**（最高 `−0.171`、`−0.122`），返回的是 GRPO 课程采样、FoRA、
conformal、RWKV 预测等无关条目。**Zotero 库在本主题上无任何相关条目**，
不构成「无先例」证据，只说明该库未收录该方向。

### 第 3 组：在线（来源状态如实登记）

- **Elicit（`mcp__990aea2c…__search_papers`）：不可用**——返回 `api_access_denied`，
  该账户套餐不含 API。**本次调研未能使用该来源。**
- `github`／`GitLab`／`stack-mcp-server`／`streamable-mcp-server`：本会话连接失败（未使用）。
- 可用来源：alphaXiv `discover_papers`、Consensus `search`、scite `search_literature`、
  Scholar Gateway `semanticSearch`。

**第 3 组核心发现（`在线摘要`级，除另注明外均未取得全文）：**

`【重要】`**「多个风险水平并列于同一目标」不是空白，而是有专名的成熟方向——谱风险测度
（spectral risk measure, SRM）／Kusuoka 表示／混合 CVaR（mixed-CVaR quadrangle）。**
离散谱的 SRM **就是**若干个不同水平 CVaR 的加权和，每个水平自带一个对偶阈值变量。
命中（Consensus，均 `在线摘要`）：

| 文献 | 与本课题的关系 |
| --- | --- |
| Ge et al., **SOREL: A Stochastic Algorithm for Spectral Risks Minimization**, 2024 | 自称首个带收敛保证的谱风险随机梯度算法 |
| Mehta et al., **Distributionally Robust Optimization with Bias and Variance Reduction**（Prospect）, 2023 | 谱风险不确定集 DRO；明写「includes … regularized CVaR and average top-k loss」 |
| Kim et al., **Spectral-Risk Safe RL with Convergence Guarantees**（SRCPO）, 2024 | 双层优化，**外层优化由风险测度导出的对偶变量**——与「六个 `ξ`」同构 |
| Moghimi et al., **Beyond CVaR: Static Spectral Risk Measures in Distributional RL**, 2025 | 静态 SRM 优化，泛化 CVaR 与 Mean-CVaR |
| Chu et al., **Nonasymptotic Estimation of Risk Measures via SGLD**, 2021 | 明写用 **Kusuoka 谱表示**把 AVaR 估计「bootstrap」到一般律不变风险测度 |
| Fröhlich et al., **Risk Measures and Upper Probabilities: Coherence and Stratification**, 2022 | 谱风险测度族的刻画与分层 |
| Rockafellar 学派 **mixed-quantile quadrangle**（scite 命中，`在线摘要`） | 把 CVaR quadrangle 的积分**离散化为一组水平参数**，即多水平混合 |

**对本课题的直接后果**：BER 的「六档等权平均」在数学上就是一个**离散谱风险测度**
（谱测度取六个原子、等权）。**「多档并列」本身毫无新意**，是 Kusuoka 表示的标准构造。
这**不推翻**主代理的主张（其主张是「多档**分阶段引入**无先例」），
但它**改变了论证的基线**：本课题不是在一个无人涉足的结构上做课程，
而是在一个**有成熟名字、成熟算法、成熟收敛理论**的结构上做课程——
**先例检索必须在 SRM 文献内部做，而非在「多预算 pAUC」这个自造词下做。**

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

### C. 多分位数 / 不交叉分位数（`在线摘要`＋检索返回的正文片段，**无本地原件**）

**C1. Barrera, Crépey, Gobet, Nguyen, Saadeddine, *Statistical Learning of Value-at-Risk and
Expected Shortfall*, Mathematical Finance 36(1):156–179, 2025, `doi:10.1111/mafi.70000`。**

Scholar Gateway 返回该文 §「Multi-α Learning for VaR」的正文片段（chunk 30/31/42），关键原文：

- `In this part we are interested in learning VaR(Y|X) for multiple confidence levels α ∈ (0,1)
  **using a single empirical error minimization**.`
- 明确区分两种形态：`single-α learning`（**每个水平重训一次**）vs
  `multi-α learning`（**一次训练同时学所有水平**）。
- `When several quantile levels α are considered, a flaw inherent to linear quantile regression is
  the problem of **crossing quantile curves**, i.e., the violation of the monotonicity with respect
  to α.` 综述了 He (1997)、Koenker (2004)、Takeuchi et al. (2006)、Bondell et al. (2010)、
  Moon et al. (2021)、Cannon (2018)、Gasthaus et al. (2019)、Padilla et al. (2022)。
- 该领域对「多水平互相干扰」的**两条标准解法**：
  ① 训练期显式加不交叉约束（硬约束走原对偶算法，深网走**惩罚项**）；
  ② 用**对 α 单调的假设空间**（分位数回归森林天然单调；Cannon 把置信水平当成额外协变量并强制单调；
  Gasthaus/Padilla 用多输出且**约束为正**以逼近分位数增量）。
  该文自身把 `α` 当协变量并**均匀随机采样**，再对 `∂_α ζ` 的负部加惩罚。

**C2. 同族在库外的其他证据（Consensus，`在线摘要`）**：
Moon et al. 2021 *Learning Multiple Quantiles With Neural Networks*（JCGS，45 引）；
Cannon 2018 *MCQRNN*（SERRA，155 引）；Decke et al. 2024 *SCQRNN*；
Park et al. 2021 *I(S)QF*（不交叉且可内插外推到未训练水平）；
Shen et al. 2025 *Non-crossing Quantile Network*；Hatalis et al. 2019（平滑损失＋惩罚防交叉）。

**C3.（本次最有杀伤力的发现）该领域没有一篇用「课程」解决多水平问题。**

上述全部方法都**同时训练全部水平**，用**约束或单调参数化**处理水平间干扰。
**检索未命中任何「先训宽松水平、后逐步加入严格水平」的多水平训练方案。**

`【与本课题的对位】`本候选的新动机是「第 1 轮六档活动率只差 `2.45` 倍，而设计 `β` 跨度 `80.2` 倍，
六档在此时做重复的事」。**这在数学上就是六个 `ξ_{p,k}` 之间「间距不足／接近交叉」**，
与 quantile crossing 属同一问题族。**该问题族的成熟解法是次序约束与单调参数化，不是课程调度。**

### D. 「课程」命中的实为另一类对象（`在线摘要`）

- Açıkgözoğlu, *Early-Stage DDoS Detection in IPv6 Using Curriculum Training*, Concurrency &
  Computation 38(15), 2026, `doi:10.1002/cpe.70902`：课程顺序 `15%,12%,10%,7%,5%,3%,1%`
  的**攻击强度**，每级 4 轮，级间**不重初始化**。**课程作用于数据难度，不是损失的风险档位。**
- Su et al., *CLRe*, Advanced Science, 2026, `doi:10.1002/advs.76827`：原文
  `CLRe uses a **cumulative** easy-to-hard curriculum rather than replacing easy samples with hard
  samples … newly introduced hard reactions are added together with the previously learned easier
  ones, which remain in the active subset and continue to regularize the model.`
  **「累积式课程」这一设计范式确有成熟先例，但其作用对象是训练样本，不是损失项。**
  本候选的 ep1`{K6,K5}`→ep2 加 `{K4,K3}`→ep3 六档，正是把该范式**移植到损失项**上。

## 判二证据

### 论点：把「六档并列」映射到「单水平退火」不是映射，是换损失

**E1. 冻结合同的六档不是六个任务，是**一个**风险测度。**

由第 3 组检索确认（`在线摘要`）：离散谱的谱风险测度＝若干水平 CVaR 的加权和（Kusuoka 表示，
Rockafellar 学派称 mixed-quantile quadrangle）。BER 的
`L_rank = (1/6) Σ_k mean_p[ ξ_{p,k} + (1/K_eff_k) Σ_n [L_pn − ξ_{p,k}]_+ ]`
就是**谱测度取六个等权原子**的离散谱风险测度。

**后果**：「单水平退火」不是把这个测度的调度换一下，而是**把六原子谱换成单原子谱**——
即删掉五档、改写冻结的 `L_rank`。**文献支撑（若成立）支撑的是那个替换后的损失，不是 BER。**

**E2. 冻结判据随之失效，且比 §7.4 已登记的失效更彻底。**

筛选判据的主观测 `D = (1/6) Σ_k |log10 ρ_k|` 定义在**六个** `ρ_k` 上。
单水平退火下每一时刻只有一个 `ρ`，`D` 无定义（或退化为 `|log10 ρ(t)|`）。
`【推导】`先验裁决 §7.4 只要求「加权写法后须重新论证判据适用性」；
**单水平形态下判据不是需要重新论证，而是不存在被测对象。**

**E3. 与四格协议的可比性同时消失。**

四格（C00/C01/C10/C11）比的是同一 `L_rank` 下的机制开关。把六档换成单水平后，
被测的不再是「预算课程」这一机制，而是**另一个损失函数**——
它不再是本机制的消融，无法回答「课程是否有用」。

**E4.（决定性）即便换成单水平损失，判一已证明该「文献支撑」也撑不住它要撑的事。**

主代理要用退火**改进最终模型**。但：
Bardou 退火的是一条**被声明不估计目标**的伴随过程，活在**输出被丢弃**的预热相，
定理证的是 `Σγ_n(α−α_n)² < ∞` 下**渐近无害**（判一 A2–A4）；
Ordered SGD 的退火表是**为消超参自由度**而设的默认值，无理论覆盖，
论文自身消融只说「固定 `q` 也能改进基线」，**未证明退火优于最佳固定 `q`**（判一 B2–B4）。

**两篇都不支持「退火训练目标能改进学到的模型」这一命题。**

**E5. 文献中有一处直接讨论「单水平 vs 多水平并列」的关系，方向不利于本候选。**

Barrera et al. 2025（C1，`在线摘要`＋正文片段）把二者并置为
`single-α learning`（逐水平重训）与 `multi-α learning`（一次训完所有水平），
**结论是后者更可取**（省重训、可得全分布、可内插未训练水平）。
**没有任何一处把「退火单水平」作为「多水平并列」的替代方案推荐。**

### 判二裁断

**是**——「六档并列 → 单水平退火」本身就是一次没有先例的任务化改造，
而且它改造的不是调度而是**冻结损失、冻结判据与四格可比性**三者。
**「若本候选改走单水平退火形态，文献支撑立即成立」这句话不成立**：
支撑的是别人的形态（且如 E4，连那个形态都只支撑「无害」不支撑「有益」），
不是本课题要跑的那个东西。

## 判三证据

（待填）
