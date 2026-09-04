# 极端分位数 CVaR 阈值估计 文献核查 · 滚动笔记

<!-- RESEARCH_ROUTE=RWKV -->

日期：2026-09-04。每完成一篇全文或一组查询即追加，不等任务结束补写。
（本代理无 `Edit` 工具，每次落盘为全文件重写，内容只增不删。）

## 证据等级图例

- `L1` 本地全文（`wiki/papers/**` 结构化全文笔记或 `raw/papers/**` 原件）
- `L2` 在线全文已取得（arXiv/PMLR/OpenReview 正文已读）
- `L3` 在线摘要
- `L4` 仅题录

---

## 阶段 P1：本地全文盘点（Grep/Glob，非混合索引 CLI）

命中的直接相关本地全文：

| 路径 | 与四问的关系 |
| --- | --- |
| `wiki/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO-ICML-全文.md` | SOPA，Q1/Q2/Q4 |
| `wiki/papers/methodology/ranking/2022-Zhu-pAUC-DRO-ICML-全文.md` | 同上（疑重复副本） |
| `wiki/papers/methodology/training-efficiency/2023-Yuan-LibAUC-X-Risk-Optimization-KDD-全文.md` | DualSampler/TriSampler，Q2 |
| `wiki/papers/methodology/ranking/2023-Shi-HNS-OPAUC-arXiv2302.03472-全文.md` | 难负采样×OPAUC，Q2 |
| `wiki/papers/methodology/ft-mechanisms/2023-Hu-Multi-Instance-TPAUC-NeurIPS-全文.md` | 多示例 TPAUC，Q2 |
| `wiki/papers/methodology/ranking/2021-Hu-SoRR-Sum-of-Ranked-Range.md` | SoRR/ATk，阈值变量 Q3 |
| `wiki/papers/methodology/2017-Siffer-SPOT极值流阈值.md` | EVT-POT 流式阈值，Q2 |
| `wiki/papers/methodology/2021-Duchi-Namkoong-Uniform-Performance-DRO-全文.md` | DRO 统一性能，Q1 |
| `wiki/papers/methodology/2021-Zhai-DORO-全文.md` | CVaR-DRO 小批量，Q1/Q3 |

---

## P2-1 · SOPA（Zhu et al., ICML 2022）· 证据等级 `L1`

来源：`wiki/papers/methodology/ft-mechanisms/2022-Zhu-pAUC-DRO-ICML-全文.md`
（MinerU 转换全文，行号为该文件行号）

### 结论 A（**推翻本仓库既有根因判定的一半**）：整数假设的主语是全体负样本 `n₋`，不是批量 `|B₋|`

- 行 117（式 (7) 正下方）："where we assume $n_-\beta$ is a positive integer for simplicity of presentation"。
  式 (7) 的求和域是 $\mathcal{S}_-^{\downarrow}[1, n_-\beta]$，即**全体负样本集合 $\mathcal{S}_-$ 的排序前 $n_-\beta$ 个**。
  `n₋ = |S₋|` 是**训练集负样本总数**，不是批量。
- 行 99（式 (6) 上方）："By using the CVaR divergence $\phi_c(t)$ for some γ such that **nγ is an integer**"，
  其中 `n` 是式 (4) 里 $\ell_1(\cdot),\dots,\ell_n(\cdot)$ 的个数，同样是全体。
- 行 83：TPAUC 估计量用 $k_2=\lfloor n_-\beta\rfloor$，取下整，**本身就允许 `n₋β` 非整数**。
- **代入本课题**：`n₋ = N_pop = 121336`，`n₋β = K = 121, 606, 1213, 2426, 4853, 9706`，
  **六档全部是正整数，SOPA 的整数假设六档全部满足。**
- 因此 `.Codex/docs/RWKV/2026-09-01-BER水库分位数修法裁决.md` 第四节
  「Zhu 2022 的 p.3 式(6) 要求 nγ 为整数、p.4 式(7) 下方假设 n₋β 为正整数。
  **本课题的低预算档违反该前提**」——**该引用为误读**：违反的前提并不存在。
  低档 `K_eff < 1` 是「批内期望活动数 < 1」，与原文的 `n₋β ∈ ℤ⁺` 是两件事。

### 结论 B：SOPA 的整个设计前提就是「批内不含真实前 k 负样本」

- 行 123："The challenge ... lies at tackling the selection of top ranked negative examples...
  **It is impossible to compute an unbiased stochastic gradient of the objective in (7)
  based on a mini-batch of examples that include only a part of negative examples.**"
- 行 165："A benefit for solving (9) is that **an unbiased stochastic subgradient can be computed**
  in terms of (w, s)."
- 即：RU 变分改写的**目的**就是绕开「批内无法表示尾部」。改写后的子梯度对**任意批量**无偏。
  **Theorem 3（行 226）全文没有任何关于 `|B₋|` 的下界条件。**

### 结论 C：BER 现用的 `ξ` 更新式**逐字**就是 SOPA Algorithm 1 第 5 行

- Algorithm 1 第 5 行（行 185）：
  $s_i^{t+1} = s_i^t - \frac{\eta_2}{n_+}\left(1 - \frac{\sum_j p_{ij}}{\beta|\mathcal{B}_-|}\right)$
- 本课题：$\partial L/\partial\xi = \frac{1}{N_p|K|}\left(1 - \frac{n_{\text{active}}}{K_{\text{eff}}}\right)$，
  且 `K_eff = β·n_neg = β|B₋|`。**两式同型**。
- 推论：所谓 bang-bang 不对称不是本课题实现缺陷，**是 SOPA 已发表算法在任意 β 下的固有结构**；
  不对称比恒为 `1/β`（每命中一个活动对，上跳是空集下降步的 `1/β` 倍）。
  实测 `14.7`（`1/β ≈ 1003` 时单个活动对相对 `K_eff=0.0638` 的比值）与 `1002`（全活动）
  与该结构一致，**不需要另找文献解释现象本身**。

### 结论 D（**Q1 的直接答案：可行性关系式不在批量上，在步长与迭代数上**）

SOPA 附录 B.6（行 545–587）给出三个显式的 β 依赖：

| 量 | 原文位置 | 取值 |
| --- | --- | --- |
| `w` 随机梯度二阶矩上界 `G²` | 行 545 | $C^2/\beta^2$ |
| **阈值 `s` 的随机梯度二阶矩上界 `C₂²`** | 行 563 | $\frac{1}{n_+^2}\left(1+\frac{1}{\beta}\right)^2$ |
| 步长条件 | 行 563、587 | $\eta_2 B_+/n_+ = \eta_1$，且 $\eta_1 = O(\beta\epsilon^2)$ |
| 迭代复杂度 | Theorem 3，行 226 | $T = O\!\left(1/(\beta\epsilon^4)\right)$ |

- **关键**：$\eta_1 = O(\beta\epsilon^2)$ 意味着**阈值步长必须正比于 β**。
  代入 SOPA 的 $s_i$ 更新，其等效步长为 $\eta_2/n_+ = \eta_1/B_+ = O(\beta\epsilon^2/B_+)$。
- **本课题现状对照**：`xi_learning_rate = 1e-4` 对六档**取同一常数**，而六档 β 跨 `80` 倍
  （`0.000997 → 0.079993`）。按 SOPA 的定理条件，最低档的步长应比最高档小 `80` 倍。
  **这是一个有全文出处、可直接检验、且与已否决两条修法都不同的第三条路径。**
- 代价换算：`T = O(1/(βε⁴))`。最低档 β 比最高档小 `80` 倍 → 达到同精度需 `80` 倍迭代数。
  这解释了「六轮平均仍压不住」——不是量化噪声不可克服，是**迭代预算相对该 β 少了两个数量级**。

### 结论 E（**Q2/Q4 的直接答案，且出自本课题已在用的同一篇论文**）

- 行 157–159（Theorem 2 及其 Remark）：KLDRO 估计量
  "when $\lambda = 0$, ... surrogate of $\widehat{OPAUC}(h_w, 0, \frac{1}{n_-})$;
  and when $\lambda = +\infty$, ... the AUC"，即 **λ 连续插值出任意有效 β，下限到 `1/n₋`**。
- 同段："**when $\beta = 1/n_-$ in CVaR-based estimator, the objective in (8) becomes the
  infinite-push (or top-push) objective** ... and hence **our algorithm for solving (9) can be
  also used for solving the infinite-push objective for deep learning**."
  - `β = 1/n₋ = 1/121336 ≈ 8.24e-6`，比本课题最低档 `0.000997` 还小 `121` 倍；
    此时 `K_eff = 64/121336 = 5.3e-4`，比最低档的 `0.0638` 小 `120` 倍。
  - **SOPA 作者明确声称 Algorithm 1（同一子梯度 SGD 阈值更新）可用于该极端情形。**
  - ⚠ 证据边界：这是**论文中的适用性声明，不是论文做过的实验**——SOPA 实验的 β 只取
    `{0.1, 0.3, 0.5}`（行 306）。故该条只能支撑「文献不认为 `K_eff < 1` 是禁区」，
    **不能支撑「该做法在本课题必然有效」**。
- SOPA-s（Algorithm 2，行 203–214）**根本没有阈值变量**：用移动平均 `u_i` 追踪
  $g_i(w)=\mathrm{E}\exp(L/\lambda)$，软权重 $p_{ij}=\exp(L/\lambda)/u_i^t$。
  **无 ξ、无分位数、无 bang-bang**；Theorem 4（行 230）的复杂度
  $T=O\!\left(\frac{1}{\min(B_+,B_-)\epsilon^4}+\frac{n_+}{B_+B_-\epsilon^4}\right)$ **不含 `1/β`**。
- SOPA 自己的 Table 3（行 324）：在两个最不平衡数据集上 **SOPA-s 优于 SOPA**
  （molmuv(t1) FPR≤0.3：SOPA-s `0.8449` vs SOPA `0.8187`）。

### 结论 F：SOPA 实验的 β 与批量（用于标定「文献走过多远」）

- 行 306："The mini-batch size is **64**"；"For SOPA, we tune the truncated FPR i.e. β in **{0.1, 0.3, 0.5}**"。
- 即 SOPA 自身实验的最小 `β|B₋| ≈ 0.1×64 = 6.4`（若正负各半则 `≈3.2`）。
- **本课题最低档 β 比 SOPA 实测过的最小 β 小 `100` 倍**。
  → SOPA 的**实验**证据不覆盖本课题低三档；SOPA 的**理论**覆盖（无批量下界，仅步长/迭代数代价）。

### 待办（由本篇引出）

- [x] 核 SOPA 是否报告过 `s`/阈值的振荡 → 全文检索 `oscillat`/`unstable`/`variance of s`：见 P4
- [ ] 找 SOPA 之后是否有人给出批量下界（在线检索）
- [ ] 找 infinite-push / top-push 系列（Agarwal 2011、Rakotomamonjy 2012、Rudin 2009 p-norm push）

---
