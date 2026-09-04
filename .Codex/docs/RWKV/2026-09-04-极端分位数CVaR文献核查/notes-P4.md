# P4 · Levy et al. 2020 · **Q1 的决定性答案** · 滚动笔记 第四批

<!-- RESEARCH_ROUTE=RWKV -->

日期 2026-09-04。

## 出处

Daniel Levy, Yair Carmon, John C. Duchi, Aaron Sidford.
**Large-Scale Methods for Distributionally Robust Optimization.** NeurIPS 2020, 33: 8847–8860.
arXiv:2010.05893。代码 `https://github.com/daniellevy/fast-dro`（PyTorch）。
证据等级 `L2`（全文 PDF 已取得，逐页读取第 4–11 页；页码为 arXiv 版 PDF 页码）。

---

## 一、**Proposition 1（批估计量的偏差），第 7 页** —— 这就是「批量下界 vs 目标分位数水平」的关系式

对任意 `x ∈ X`、`n ∈ ℕ`：

$$0 \le \mathcal{L}(x;P_0) - \overline{\mathcal{L}}(x;n) \lesssim
\begin{cases}
B\min\left\{1, (\alpha n)^{-1/2}\right\} & \mathcal{L}=\mathcal{L}_{\text{CVaR}} \quad (8)\\
G_{\text{icdf}}\, n^{-1} & \text{任意式 (5) 型损失，需假设 A1} \quad (11)
\end{cases}$$

其中 `B` 是损失上界（`0 ≤ ℓ ≤ B`），`n` 是**批量**，`α` 是 CVaR 水平，
$\overline{\mathcal{L}}(x;n) = \mathbb{E}_{S_1^n}\mathcal{L}(x;S_1^n)$ 是批目标的期望。

### 读法一：`αn < 1` 时该界**平凡**

- `min{1, (αn)^{-1/2}}` 在 `αn ≤ 1` 时取 `1`，界退化为 `B`——**偏差可以大到整个损失量程**。
- **`αn` 就是本课题的 `K_eff`**（`α = β`，`n = n_neg = 64`）。
  本课题六档 `αn = K_eff = [0.0638, 0.3196, 0.6398, 1.2796, 2.5598, 5.1195]`，
  **低三档 `αn < 1`，式 (8) 对它们给不出任何非平凡保证。**
- 该论文明确写道（第 7 页）：界 (8)(9)(10) 在损失服从 **Bernoulli 分布**时
  「tight up to constant or logarithmic factors ... and so are **unimprovable without further
  assumptions**」——**即这不是分析不够紧，是最坏情况下的真实行为。**
- 反解精度：要偏差 `≤ ε`，需 $n \gtrsim \dfrac{B^2}{\alpha\varepsilon^2}$。
  代入最低档 `α = 0.000997`、`B = 1`：
  - `ε = 0.5`（宽松）：`n ≳ 2007`
  - `ε = 0.1`：`n ≳ 100301`
  - `ε = 0.05`：`n ≳ 401203`
  **`n_neg = 64` 与 `n_neg = 256` 都远远不够**——这条独立证据**支持**本仓库
  「`n_neg → 256` 仍失配」的既有否决，并给出了它失配的量级原因。

### 读法二（**关键转折**）：式 (11) 的 `1/n` 界**与 `α` 无关**

- 附加假设 **A2：`ℓ(x;S)` 的逆 CDF `F⁻¹` 是 `G_icdf`-Lipschitz**（即损失分布在目标分位附近
  有不退化的密度）。原文第 7 页："it allows us to obtain a general `1/n` bias bound (11)
  **independent of the uncertainty set size**"，并且
  "for CVaR at level α, we **only need the inverse cdf `F⁻¹(β)` to be Lipschitz around `β = α`**,
  a common assumption in the risk estimation literature."
- **结论**：批量下界**不是 `α` 的普适函数，而取决于损失分布在目标分位处的正则性**。
  - 损失分布退化／离散（Bernoulli 型）：必须 `n ≳ 1/(αε²)`，`K_eff < 1` 无解。
  - 损失分布在 `β = α` 邻域逆 CDF 利普希茨：`n ≳ G_icdf/ε`，**与 `α` 无关，`n = 64` 可能足够**。
- **这条给出了本课题可独立检验、可证伪的判据**：
  「对本课题的成对损失分布，在六档目标分位邻域测 `F⁻¹` 的局部斜率（即密度倒数）」。
  该测量**不接触最终目标标签**，可在源年训练数据上做。
  测出接近平坦（密度不退化）→ 低档失败不能归因于批量；
  测出陡峭／有平台（大量并列值、损失被 hinge 压到 0 造成质点）→ 批量确实是硬约束。
  ⚠ **该判据是本笔记依据式 (8)/(11) 的推导，尚未执行任何测量**，标为「待验证」。

## 二、Proposition 2（批估计量的方差），第 8 页

$$\mathrm{Var}\left[\nabla\mathcal{L}_{\text{kl-CVaR}}(x;S_1^n)\right] \lesssim \frac{G^2}{\alpha n}$$

（原文注明 `L_CVaR` 是 `L_kl-CVaR` 在 `λ = 0` 的特例，故该界对 CVaR 同样成立。）

- **梯度方差正比于 `1/(αn) = 1/K_eff`。** 本课题六档方差因子
  `1/K_eff = [15.7, 3.13, 1.56, 0.781, 0.391, 0.195]`，最低档比最高档高 **`80` 倍**。
- **这为本仓库一直在用的诊断量 `K_eff` 提供了正式的文献地位**：
  `K_eff = αn` 正是出现在已发表方差界分母上的那个量。
- 但注意后果是**方差**而不是**不可表示**。方差可用步长、迭代数、MLMC 或平滑来交换。

## 三、Theorem 3（极小极大下界），第 11 页 —— **总预算不可绕过**

> 对每个 `d ≥ 1`、域 `X = {x : ‖x‖ ≤ R}` 与任意算法，存在分布 `P₀` 与凸 `G`-Lipschitz 损失
> `ℓ : X × S → [0, GR]`，使得 $T \le c\dfrac{(GR)^2}{\alpha\varepsilon^2}$ 蕴含
> $\mathbb{E}[\mathcal{L}_{\text{CVaR}}(x_T;P_0)] - \inf_{x'}\mathcal{L}_{\text{CVaR}}(x';P_0) > \varepsilon$。

- 即**总梯度调用数 `Ω(1/(αε²))` 是信息论下界**，任何算法都躲不掉；
  且该下界「holds for `d = 1` and extends to a global model where at every round the oracle
  provides the entire function `ℓ(·;S)`」——**比标准一阶预言机更强的预言机也躲不掉**。
- **但下界作用于总预算 `nT`，不作用于批量 `n`。**
  → **可以用迭代数换批量**，这与 SOPA 的 `T = O(1/(βε⁴))` 是同一件事的两种表述。
- Theorem 1（第 9 页）上界：`nT ≲ (GR)²/(αε²)·(1 + min{...})`，与下界匹配。

## 四、Section 4：**多层蒙特卡洛（MLMC）——「不加批量而获得大批量统计效力」的公开做法**

这是 Q2 中「多层/嵌套 CVaR 估计」这条线的直接答案，且**可直接实现**。

- 取截断几何变量 $J \sim \min\{\mathrm{Geo}(1/2), j_{\max}\}$，$q(j)=\mathbb{P}(J=j)=2^{-j+1_{(j=j_{\max})}}$。
- 偏差增量：
  $$\widehat{\mathcal{D}}_k := \nabla\mathcal{L}(x;S_1^k) - \frac{\nabla\mathcal{L}(x;S_1^{k/2}) + \nabla\mathcal{L}(x;S_{k/2+1}^k)}{2}$$
- MLMC 估计量（式 16）：
  $$\widehat{\mathcal{M}}[\nabla\mathcal{L}] := \nabla\mathcal{L}(x;S_1^{n_0}) + \frac{1}{q(J)}\widehat{\mathcal{D}}_{2^Jn_0}$$
- **Claim 2（第 10 页）**：$\mathbb{E}\widehat{\mathcal{M}}[\nabla L] = \nabla\overline{\mathcal{L}}(x;n)$，
  且**期望样本量只有 $n_0(1+\log_2(n/n_0))$**——即**对数于 `n`**。
- **Proposition 4（第 10 页）**：
  $\mathbb{E}\|\widehat{\mathcal{M}}[\nabla\mathcal{L}_{\text{CVaR}}]\|^2 \lesssim \left(1+\frac{\log(n/n_0)}{\alpha n_0}\right)G^2$
- **Theorem 2（第 11 页）**：取 $n \asymp \dfrac{B^2}{\alpha\varepsilon^2}$、$1\lesssim n_0\lesssim \dfrac{\log n}{\alpha}$、
  $T \asymp \dfrac{(GR)^2}{n_0\alpha\varepsilon^2}\log^2 n$，总复杂度
  $\lesssim \dfrac{(GR+B)^2}{\alpha\varepsilon^2}\log^2\dfrac{B^2}{\alpha\varepsilon^2}$。

### 对本课题的换算（**算术代入，非实验**）

最低档 `α = 0.000997`，取 `B = 1`、`ε = 0.1` → 目标等效批量 `n ≈ 100301`，取 `n = 2^{11}·64 = 131072`。
以 `n₀ = 64`（即当前 `n_neg`）为最小层：期望样本量 $= 64(1+\log_2(131072/64)) = 64\times12 = 768$。

- **即：用平均每步 `768` 个负样本的代价，获得等效批量 `131072` 的无偏梯度**，
  而**绝大多数步骤仍然只用 `64` 个**（`P(J=1) = 1/2`），只有罕见步骤展开到大批。
- 这与已被否决的「把 `n_neg` 固定提到 `256`」是**不同性质的做法**：
  后者是常数倍提升（`4×`），仍远低于 `1/(αε²)` 所需；
  MLMC 是**指数覆盖 + 对数代价**，且**峰值显存**由 `j_max` 层控制、可分块累积。
- ⚠ 该换算是把论文公式代入本课题冻结常数的**算术**，`B`、`G`、`R` 未测，`ε` 是假设值。
  **不构成「MLMC 在本课题会有效」的证据**，只说明这条路径的代价量级可评估。

## 五、Claim 1（第 9 页）：平滑化的代价也是**对数级**

$$0 \le \mathcal{L}_{\text{CVaR}}(x;P) - \mathcal{L}_{\text{kl-CVaR}}(x;P) \le \lambda\log(1/\alpha)$$

取 $\lambda \asymp \varepsilon/\log(1/\alpha)$ 即可把近似误差控制在 `ε`。

- 本课题六档 `log(1/α) = [6.91, 5.30, 4.61, 3.91, 3.22, 2.53]`，**全程只跨 `2.7` 倍**。
- 与 HNS-OPAUC 的 $\tau \propto 1/\sqrt{-2\log\beta}$（跨 `1.65` 倍）同一现象：
  **软化路线对 `β` 的依赖是对数的，硬计数路线是线性的（`αn`）。**
  这是「极端分位下软化可行、硬计数不可行」的统一数学解释。

## 六、旁证（第 4 页 Related work）

- 「Kawaguchi and Lu [36] propose to only use gradients from the **highest k losses in every batch**,
  which is **essentially identical to our mini-batch estimator for CVaR**; they do not, however,
  relate their algorithm to CVaR optimization.」
  → 「批内取 top-k」（Ordered SGD）与批式 CVaR 估计量等价，同受 Prop 1 的偏差界约束。
- 「Curi et al. [14] ... While the latter performs better in practice, its worst-case guarantees
  scale roughly as `Nε⁻²`, similarly to the full-batch method.」
  → 对 ADA-CVAR 的独立评价：实践更好，最坏情况保证更差（依赖 `N`）。
- 该文自评贡献：「optimal complexity bounds scaling as **`α⁻¹ε⁻²`**」，
  且「for CVaR the guarantees scale **linearly** in the uncertainty level rather than
  **quadratically** as in previous work」。

---
