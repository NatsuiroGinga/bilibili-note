# P5 · pAUC 后续工作与 Q3 专项 · 滚动笔记 第五批

<!-- RESEARCH_ROUTE=RWKV -->

日期 2026-09-04。

---

## P5-1 · Closing the Approximation Gap of PAUC Optimization: A Tale of Two Formulations

- arXiv:2512.01213（2025-12），证据等级 `L3`（取得摘要逐字 + HTML 正文的定向抽取，
  **未通读全文、未入库原件**）

### 摘要逐字（关键句）

> "selecting instances within these constrained intervals during its calculation is **NP-hard**,
> and thus typically requires approximation techniques for practical resolution."
> "most existing methods still suffer from **uncontrollable approximation errors** or a limited
> scalability"
> "two simple instance-wise minimax reformulations: one with an **asymptotically vanishing gap**,
> the other with the **unbiasedness at the cost of more variables**"
> "simplify the complicated sample selection procedure by **threshold learning**, and then apply
> different **smoothing techniques**"
> "a tight generalization bound ... exhibits a sharp order of
> $\tilde{O}(\alpha^{-1}n_+^{-1} + \beta^{-1}n_-^{-1})$"

### **Q1 的第三条独立证据（统计侧，且比 Curi 的界更紧）**

- 泛化界的负样本项是 $\tilde{O}(\beta^{-1}n_-^{-1}) = \tilde{O}(1/(\beta n_-)) = \tilde{O}(1/K)$。
- **代入本课题**（`n₋ = 121336`，`K = βn₋`）：

  | 档 | `K` | `1/K` |
  | ---: | ---: | ---: |
  | 1 | 121 | 0.00826 |
  | 2 | 606 | 0.00165 |
  | 3 | 1213 | 0.000824 |
  | 4 | 2426 | 0.000412 |
  | 5 | 4853 | 0.000206 |
  | 6 | 9706 | 0.000103 |

- **六档全部很小。** 即在**总体统计层面**，`β = 0.000997` 配 `n₋ = 121336` 是**良定的**——
  有效样本量就是 `K = 121` 个负样本，泛化惩罚 `Õ(1/121)`。
- **这与 Curi Proposition 1 的 `(1/α)√(log(2|H|/δ)/N)` 在最低档失效并不矛盾**：
  后者是有限假设类的最坏情况一致收敛界（`(1/α)N^{-1/2}`），前者是针对 pAUC 结构的紧界
  （`(βn₋)^{-1}`）。**取更紧的那条**：低档的困难**不是总体统计问题**。
- **合并结论（Q1）**：本课题低档的困难被三条界共同定位到**同一处**——
  批内估计（`Var ∝ 1/(αn) = 1/K_eff`、`Bias ≲ B·min{1,(αn)^{-1/2}}`），
  **不在总体统计**（`Õ(1/K)` 很小），**也不在 SOPA 的整数假设**（`n₋β = K` 是整数）。

### 方法要点

- 阈值 `s'`（负样本侧）与 `s`（正样本侧）作为**可学习阈值**，把 top-`k` 算子改写为
  「sorting-free threshold reformulation」；
- 用 **softplus 代理** $r_\kappa(x) = \log(1+\exp(\kappa x))/\kappa$ 光滑化 $[x]_+$。
  → 即**把 hinge 的硬拐点抹平**，使阈值梯度不再是 `0/1` 指示函数。
  这是与「调步长」「换采样器」并列的第四条处置路线，**且直接作用在 BER 现有算子上**。
- 实验：**batch_size = 1024，β ∈ {0.3, 0.5}**。**未报告任何阈值不稳定或梯度爆炸。**
  （`β·n₋^B ≈ 0.3×512 = 154 ≫ 1`，处在完全可分辨区，不构成对本课题低档的证据。）

---

## P5-2 · Large-scale Optimization of Partial AUC in a Range of False Positive Rates

- arXiv:2203.01505（NeurIPS 2022），证据等级 `L3`（仅摘要逐字）
- 摘要动机逐字："it summarizes the true positive rates (TPRs) over all false positive rates (FPRs)
  in the ROC space, which **may include the FPRs with no practical relevance in some applications**.
  The partial AUC ... summarizes only the TPRs over a **specific range** of the FPRs"
- 方法：非光滑 DC 规划 + Moreau 包络光滑 + 随机块坐标更新；复杂度 $\tilde O(1/\epsilon^6)$；
  同一算法可用于 sum of ranked range（SoRR）损失。
- **对 Q4 的价值有限**：该文的「限定 FPR 区间 `[α, β]`，`α > 0`」动机写的是
  **「低 FPR 段无实际意义」**（应用相关性），**不是「低 FPR 段估不准」**（可估性）。
  抓取到的摘要中**没有**「因为估不准所以砍掉档位」的论述。
  ⚠ 该判断基于摘要；正文是否另有论述**未核**，标为待核。

---

## P5-3 · Q3 专项：Robbins-Monro 分位数追踪的不对称性 · 证据等级 `L3`（检索层）

- RM 分位数递推的驱动项是 $(\tau - \mathbb{1}\{X_t \le q_t\})$：
  绝大多数步下降 $\alpha_t\tau$，罕见越界时上跳 $\alpha_t(1-\tau)$，
  **不对称比为 $(1-\tau)/\tau$**（本课题等价形式为 `1/β`）。
  该结构性不对称在极端 `τ` 下产生锯齿／振荡，**是该算法族的已知性质**。
- 步长的两难：经典条件 $\sum\alpha_t=\infty$、$\sum\alpha_t^2<\infty$；
  但**追踪非平稳目标时必须放弃 $\sum\alpha_t^2<\infty$**，改用常数或缓慢衰减步长，
  **这就保证了持续振荡而非收敛**。
  → 本课题 `xi_learning_rate = 1e-4` 恒定不衰减，属「追踪」配置，**振荡是预期行为**。
- 稳定化方向：**proximal Robbins-Monro**（Toulis & Horel，arXiv:1510.00967），
  作者以 Robbins & Monro (1951) 原始的分位数回归例子演示数值稳定性的显著改善。
- **零结果（如实记录）**：本轮检索**未命中**专门研究「极端分位（`τ→1`）下 RM 追踪
  振荡幅度及其处置」的工作。检索式：
  `Robbins-Monro stochastic approximation extreme quantile tracking instability oscillation
  asymmetric update rare exceedance step size`。
  检索返回方自陈「did not surface work specifically on the extreme/rare-exceedance regime」。
  → **Q3 在「通用分位数追踪」文献里是零结果；但在「CVaR 深度学习」文献里不是零结果**
  （见 `notes-P3.md` 的 Curi et al. 第 8 页，已明确报告 `0 或 1/α` 的梯度与其处置）。

---
