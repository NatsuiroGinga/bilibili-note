# 文献审核 notes（滚动落盘）

<!-- RESEARCH_ROUTE=RWKV -->

**最终交付件是同目录 `文献核查.md`；本文件是过程记录，冲突时以 `文献核查.md` 为准。**

证据等级：`L1` 本地全文 / `L2` 在线全文已下载并逐页读 / `L3` 在线摘要或定向抽取 / `L4` 仅题录

---

## 阶段 0：读仓库已有核查（2026-09-04）

已读两份，**四问全部未被覆盖**，不构成重复劳动：

1. `thesis/methods/第三章-极端分位数CVaR估计文献核查.md`
   覆盖 CVaR 批量下界、软化路线、阈值追踪振荡、砍档先例；**没有**讨论
   「插值式软 top-k 算子本身是否已有定义」，也**没有** Hyndman-Fan／Acerbi-Tasche／
   NeuralSort／SoftSort／OT 排序／AutoPool。
   可复用：§3.1 Curi et al. 报告的梯度「要么 `0` 要么 `1/α` 倍」——本次 Q2 引用。
2. `thesis/methods/实体分数聚合一致性的文献核查.md`
   问的是「同一实体分数被两个可加损失各自聚合」，**与 Q3 的「两级嵌套」不同**。
   可复用：SoRR（Hu et al. 2021）已入库 `L1`，其 §6 用 `k′` 与 `k` 区分两级参数。

## 阶段 0b：待审算子的确切形式（读方案原文后厘清）

方案 `thesis/methods/第三章-两级风险聚合框架.md:54-58` 的 `Σ_{i<k}` **只能读作 0-indexed**。
若按 1-indexed 读，权重和为 `(k−1+f)/t ≠ 1`，与方案 `:66-68` 自报的
「整数点上与硬 top-k 逐位相同」矛盾。故核对用式（1-indexed）：

```
S_e = ( Σ_{i=1}^{⌊t⌋} s_i + (t − ⌊t⌋)·s_{⌊t⌋+1} ) / t，  t = α·m_e
```

⚠ 方案文本的索引写法本身是阻断项，须改写。

---

## 阶段 1：Q1 —— 决定性证据（`L2`，逐页读原件）✅

**Rockafellar & Uryasev (2002), JBF 26: 1443–1471，Proposition 8 式 (25)（预印本 p.13）
在等概率 `p_k = 1/m` 下逐项等于待审算子。**
RU 预印本 p.12 把分数权重称为「劈开概率原子」；
**Proposition 13（预印本 p.19）已给出 `φ_α` 对 `α` 的连续性与闭式左右导数**，
即方案自称的「让 α 可微」不是新的。
完整推导、原文引文、页码见 `文献核查.md` §1.1–1.2。

交叉验证：Levy et al. NeurIPS 2020 式 (2) 的 LP（`L1`，本地笔记行 `37`）最优值即此式；
AT_k Lemma 1（`L3`）是其 RU 对偶形式；SoRR §4.2 标题即
"Connection with Conditional Value at Risk"（`L1`）。

**额外发现（写入交付件 §1.6）**：本算子**不属于** SoftSort/NeuralSort/OT 那一族。
那一族让**分数**可微；本算子只让**水平参数**可微，对分数的权重仍是
`(1/t,…,1/t, f/t, 0,…,0)` 的硬选择。**「软 top-k」这个名字名实不符。**
证据：Blondel et al. ICML 2020 摘要与 §1（`L2`，PDF p.1）
"ranks … their derivatives are null or undefined, preventing gradient backpropagation"。

## 阶段 2：Q4 —— 本地全文直接命中（`L1`）✅

AutoPool（McFee et al. 2018）
`wiki/papers/methodology/multiple-instance/2018-McFee-AutoPool-Adaptive-Pooling-arXiv-全文.md`：

- 行 `316`：`"the CAP model learns to maximize all α to the upper bound"`——**端点退化实测**。
- 两条独立处置：CAP 硬约束式 (11) `α ≤ ln(m−1)`；RAP 正则 `min f(θ) + λ|α|²`（行 `192–232`）。
- 行 `353/361/367`：不加约束会 over-fit；"regularized auto-pool models are among the best performing"。
- 行 `365`：建议 `α` 初始化取小值以保证早期梯度传播。
- 行 `330`（DCASE 2017）：**反例**——`α` 逐类分化，未一律到端点。故端点退化是数据依赖现象。

结构性理由（推论，由 RU Cor 7 + Prop 13 代入）：`∂S_e/∂α = (s_{⌊t⌋+1} − S_e)/α ≤ 0` 恒成立，
**单袋无内点驻点** ⟹ 无外部锚时 `α` 必到端点。

零结果 Z1：一轮定向检索未命中「把 CVaR 的 `α` 作为可训练参数并报告收敛到端点」的工作。
不影响结论（AutoPool 已在同型参数上给出实测）。

## 阶段 3：Q2 —— 已知问题 ✅

六条，详见 `文献核查.md` §2：

1. 不解决梯度稀疏（Blondel `L2`、Xie `L3`、AutoPool `L1`）；
2. 插值项权重 `f/t`，`f → 0` 时几乎不回传（推论）；
3. `α` 方向只有 `C⁰`，每个整数 `t` 处导数跳变（RU Prop 13 左右导数不等，`L2`）；
4. 每袋 `α`-梯度符号恒定，无内点驻点（RU Cor 7，`L2`）；
5. 截断 CVaR 梯度二值化 `0` 或 `1/α`、爆炸、需极小学习率（Curi et al.，本仓库既有核查 `L2`）；
6. 偏差 `B·min{1,(αn)^{-1/2}}`、方差 `G²/(αn)`，在 ETA 上 `n = m_e`，小袋处最差（Levy et al. `L1`）。
   **缺口：袋大小 `m_e` 分布未登记，本条无法定量。**

## 阶段 4：Q3 —— 有先例，且有强负面定理 ✅

**零结果不成立。** 详见 `文献核查.md` §3。

- **Shapiro, *Time consistency of dynamic risk measures*, ORL 2012**（`L2`，逐页读
  optimization-online 预印本 p.1–5）：其 §2 构造是 `Ω × Ω` 等概率两层树，
  内层 `ρ_i` 作用于第 `i` 行、外层 `ρ_0` 作用于内层结果向量——**与 ETA∘BER 结构逐点对应**。
  - Lemma 2.1（p.3）：复合律不变 ⟹ `ρ_0 = ρ_1 = … = ρ_n`（**两级参数必须相等**）。
  - Theorem 2.1（p.4）：且 `ρ_0` 只能是期望或 max-measure（**只能在两个端点**）。
  - §1 末与 §3：`AVaR_α`，`α ∈ (0,1)`，**不可**分解为律不变相干风险映射的复合。
  - **Remark 2（p.5）**：结论以「所有 `p_i` 相同」为前提。**本课题袋大小不等，是否咬合未核（缺口）。**
- **Hu et al., NeurIPS 2023（`L1`）**：TCCO 三级嵌套复合优化，
  应用即 **multi-instance two-way partial AUC**（袋内聚合 + 跨实体偏 AUC），已有算法与收敛分析。
  **⟹「两级风险聚合框架」本身不是新提法。**
- SoRR §6（`L1`）：两级 top-k 参数 `k` 与 `k′` 显式区分、独立取值。

---

## 完成状态

- [x] Q1 决定性一问（RU vs 算子）
- [x] Q1 其余线索（可微排序族、H&F 与 `numpy.quantile`、AT_k、SoRR）
- [x] Q2 已知问题（六条）
- [x] Q3 两级/嵌套风险（Shapiro 2012 + Hu 2023 + SoRR）
- [x] Q4 AutoPool + 结构性理由 + 零结果 Z1
- [x] 交付件 `文献核查.md` 已写出

## 遗留缺口（如实登记）

1. Shapiro 2012 的期刊卷期页未核（读的是预印本）；`citation-verification` 未运行。
2. Shapiro Remark 2 的等概率前提在本课题是否成立，未核。
3. 袋大小 `m_e` 分布未登记，Q2 第 6 条无法定量。
4. 三份 `L2` PDF（RU 2002、Shapiro 2012、Blondel 2020）**未入 `raw/papers/`**，
   也未建 `wiki/` 全文笔记；正式引用前必须补。
5. 本代理无 `Bash` ⟹ 混合索引向量通道未运行、**三个文件均未 `git commit`**，需主代理补。
