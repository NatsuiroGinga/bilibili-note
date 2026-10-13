# 工作笔记：形式化草案（2026-10-13）

## 一、原件核对记录（逐条，回原 PDF）

### Shi & Liu, AAAI-24，`raw/papers/attack-detection/课程式学习.pdf`

- **物理页 14978（第 4.3 节）**：
  - J 定义：`J := (1/T) Σ_{t=1}^{T} t·W_q(P̂^adv_{δ_{t-1}}(h_{t-1}), P̂^adv_{δ_t}(h_t))`
  - 关键假设原文：「we observe in the experiments that the adversarial examples are generated
    very close to the border of the perturbation set, i.e. **||x − x^adv||_p ≈ δ**. According to
    the definition of Wasserstein distance, the following formula holds for any h ∈ H:
    `W_q(P̂^adv_{δ_t}(h), P̂) ≈ δ_t` (**Lemma 2 of (Tu, Zhang, and Tao 2019)**).」
  - 式 (16)：`J ≈ δ_T + (1/T)Σ_{t=1}^{T-1}((t+1)k_t + t)δ_t + (1/T)k_0 δ_0`
  - 控制律 1)：`k_t > −t/(t+1)` ⇒ `(t+1)k_t+t > 0` ⇒ 减小 `δ_t` 减小 J；
    2)：`k_t < −t/(t+1)` ⇒ 增大 `δ_t`。
  - **注意**：控制律是「根据 k_t 的**经验轨迹**自适应调半径」，不是预设的「早小后大」；
    「早小后大」是 k_t 轨迹（早大后小）的**结果**。
- **物理页 14979（§5.2，Calculation of Wasserstein Distance）**——**本次最关键的核对**：
  「we can calculate the Wasserstein distance directly, since the mapping T_h defined in
  Section 3.2 is indeed the optimal transport between distributions P̂ and P̂^adv(h).
  Hence, we obtain **W_1(P̂^adv(h), P̂) = (1/n) Σ_{i=1}^n ||x_i^adv − x_i||**, where x_i^adv is
  the adversarial example of x_i according to h.」
  ⇒ **原文的 W_1 就是「输入空间平均扰动范数」**，不是特征空间量。这是距离-预算对应的桥。

### RS-Del, NeurIPS 2023，`raw/papers/attack-detection/2023-Huang-RS-Del序列分类器编辑距离证书.pdf`

- **物理页 6**：式 (7) `F(x,μ_y)={h: μ_y=p_y(x;h)}`；式 (8) 邻域充分条件；
  **Proposition 3**：`ρ(x,μ_y) := min_{x̄∈N_r(x)} min_{h∈F(x,μ_y)} p_y(x̄;h) ≥ ν_y(η)`（式 9）；
  式 (10) 阈值分三支；**Lemma 4**（等价编辑，双射 `m: 2^{ε̄*}→2^{ε*}`，
  `s(ε̄,x̄;h) = p_del^{|x̄|−|x|} s(ε,x;h)`）；式 (13) 重排。
- **物理页 7**：**Theorem 5** 式 (14)：`ρ(x̄,x,μ_y) ≥ ρ̃ = p_del^{|x̄|−|x|}(μ_y − 1 + p_del^{½(dist_LCS(x̄,x)+|x|−|x̄|)})`；
  **§4.3 式 (15)**：`ρ̄(x;μ_y) = min_{x̄∈N_r(x)} ρ̃(x̄,x,μ_y)`；
  **Corollary 6**（**关键**）：存在 `n_sub, n_ins, n_del ≥ 0` 使
  `dist_O(x̄,x)=n_sub+n_ins+n_del` 时 `ρ̃(x̄,x,μ_y) = p_del^{n_del−n_ins}(μ_y − 1 + p_del^{n_sub+n_ins})`
  ⇒ **下界已经是「编辑操作计数」的函数**；
  **式 (16)**：`ρ̄(x;μ_y) = min_{n_sub,n_ins,n_del ∈ C_r} p_del^{n_del−n_ins}(μ_y − 1 + p_del^{n_sub+n_ins})`
  ⇒ **在计数集合 `C_r` 上取 min**（`C_r` = 和等于 r 的计数组合）；
  **Theorem 7**：`O={del,ins,sub}` 时 `ρ̃(x;μ_y) = μ_y − 1 + p_del^r`，
  `r* = ⌊log(1+ν_y(η)−μ_y)/log p_del⌋`；「对任意 O 的适配是直接的，全部组合见 Table 1」。
  脚注 2：LCS 距离 ≡ `O={del,ins}` 的广义编辑距离。
- **物理页 9**：Table 2（Sleipnir2/VTFeed 数字）、Figure 2、§6 Related work。
  §6 提及 **Liu et al. [33]**：对**点云**（无序集合）用子采样平滑做编辑距离证书，
  因集合无序，编辑距离化为「集合基数」的简单形式 ⇒ 用 Neyman-Pearson 得到紧证书。
  **Table 1 本体未见**（PDF 抽取中 Table 1 在正文 §4.3 内，但抽取页未见独立表格页；
  按 Theorem 7 与评估报告的 `{del,ins}` 行歧义登记，本草案只引 Theorem 7 的 Levenshtein 式与
  `含 sub 的组合` 结论，不逐行引用 Table 1 数值）。

### Shin & Alvarez-Melis, COLM 2026，`raw/papers/attack-detection/2026-Shin-课程学习作为传输.pdf`

- 按评估报告：**全文无 Theorem/Proposition**（检索零命中），结论来自校准合成套件实验。
  本草案引用其边界（Appendix D：预训练/真实数据 SFT 上效应减弱）——**沿用评估报告结论**，
  未逐页复核（该文只作边界引用，不作承重证据）。

## 二、本地检索（Zotero 语义）

- `zotero_semantic_search`「certified robustness under constrained or structured perturbation
  sets, non-ball neighborhoods, discrete sequence edit distance」→ **前 10 条相似度全为负**
  （最高 −0.176），无相关命中。⇒ 本地 Zotero 未收录「非球状受限邻域的认证」专门工作。
- 本地混合索引查询（后台）见 `search-local-constrained.json`（若完成则记；否则不作结论）。

## 三、关键判定（写入草案）

1. N'(x;q) ⊆ B_H(x,q) ⊆ N_q(x)，严格且指数级更小（链 vs 球）。
2. 原文 W_1 = 平均输入空间扰动范数 ⇒ 我们的 Hamming 度量下 `W_1 = E[q_actual]`（精确，非 c·q）。
3. 「特征空间 c·q」是机制方案的**误述**：原文量在输入空间；特征空间需另行假设。
4. 控制律形式保留，但依赖「经验 k_t 轨迹」，且整数 q、下限 1、实体依赖 q、难度非单调
   四条边界效应。
5. **最大缺口**：D-7 训练用的是 `perturb2`（随机位置），理论对象是 §十二的共享前缀算子 `N'`
   —— 二者不是同一算子。
