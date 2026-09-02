---
title: "When AUC meets DRO: Optimizing Partial AUC for Deep Learning with Non-Convex Convergence Guarantee"
authors: [Dixian Zhu, Gang Li, Bokun Wang, Xiaodong Wu, Tianbao Yang]
year: 2022
date: 2026-09-02
journal: "Proceedings of the 39th International Conference on Machine Learning（ICML 2022），PMLR 162:27548–27573"
source_pdf: "[[raw/papers/methodology/ranking/2022-Zhu-pAUC-DRO-ICML.pdf]]"
sha256: "ce0c5e4494774de414d5844cc69f05cbf351961a11dd83460b357744a93d8b40"
tags:
  - 偏AUC优化
  - 分布鲁棒优化
  - CVaR
  - 弱凸优化
  - 类型/论文
key_finding: "把每个正样本对全体负样本的偏 AUC 目标改写为 DRO 损失，用 CVaR 散度得到非光滑但精确的估计量（SOPA，Theorem 1），用 KL 散度正则得到不精确但光滑的估计量（SOPA-s，Theorem 2）；SOPA 的核心是一个跨迭代持久、按小批随机坐标更新的阈值向量 s，把偏 AUC 原本对整个负样本集合排序选择的强耦合，降为对当前采样小批 B_+/B_- 的耦合；全文用大 O 迭代复杂度衡量效率，检索 wall clock/running time/training time/seconds/speedup/runtime/throughput/memory usage/peak memory 等词全部零命中，未报告任何实测墙钟时间或显存数字。"
method: "对每个正样本的偏 AUC 代理损失套一层 DRO（CVaR 或 KL 正则），把原本需要对负样本排序取 top-k 的非光滑选择问题，转化为弱凸优化（CVaR，SOPA）或有限和耦合复合优化（KL，SOPA-s），并复用/扩展 Wang & Yang (2022) 的 SOX 算法给出随机梯度算法与收敛率证明；两级 DRO 叠加得到 TPAUC 的 SOTA-s。"
baseline: "朴素小批量方法（Kar et al. 2014，MB）、ad-hoc 加权方法（Yang et al. 2021，AW-poly）、交叉熵、AUC 平方损失（AUC-SH）、AUC-margin（AUC-M）、p-norm push"
aliases:
  - SOPA
  - SOPA-s
  - SOTA-s
  - pAUC-DRO
  - Zhu2022-pAUC-DRO
---

# SOPA：偏 AUC 遇见分布鲁棒优化

> Zhu, Li, Wang, Wu, Yang，2022，ICML（PMLR 162:27548–27573）· PDF 共 26 物理页

**本次核验范围**：使用 `pdf-converter`（`mineru-open-api extract`，精度模式、公式识别，全文一次转换）对全文 26 页逐段精读第 1–11 页（摘要、引言、相关工作、预备知识、第 4 节 OPAUC-DRO、第 5 节 TPAUC-DRO、第 6 节实验、第 7 节结论、参考文献、附录 A 更多实验结果、附录 B 引理 4–6 及引理 6 证明开头）；第 11–26 页（引理 7 证明续、附录 C–H 定理 3–5 的完整弱凸性与收敛性证明）**仅做全文关键词检索，未逐段精读证明细节**——本笔记不对这部分数学证明的正确性作出判断，仅引用其结论陈述（定理编号与迭代复杂度阶）。页码引用均已用 `pdftotext -f <页> -l <页> -layout` 逐页核对物理页面位置（PDF 页面尺寸 letter，612×792 pts，双栏排版）。

## 一句话

SOPA 把偏 AUC（pAUC）优化中"对每个正样本需要从全体负样本里挑出排名最前的一批再算损失"这个非光滑选择问题，改写成对每个正样本维护一个持久阈值变量 `s_i` 的分布鲁棒优化问题（CVaR 散度给出精确估计量，KL 散度正则给出光滑但不精确的估计量），使得每步只需采样两个小批 `B_+⊂S_+`、`B_-⊂S_-` 并对小批内正样本做随机坐标更新 `s_i`，就能获得弱凸目标下 `O(1/(βε⁴))` 复杂度的近稳定点收敛保证；全文用迭代复杂度衡量"效率"，未报告任何实测墙钟时间或显存数字。

## 背景：问题的演进（第 1–2 页，引言与相关工作）

- 标准 AUC 优化关心整条 ROC 曲线下面积；很多应用（如医疗诊断）只关心低 FPR 或高 TPR 区域，即偏 AUC（pAUC），分单向（OPAUC，限制 FPR∈[0,β]）和双向（TPAUC，限制 FPR≤β 且 TPR≥α）两种（第 1 页，引用 Dodd & Pepe 2003；Yang et al. 2019）。
- 偏 AUC 的经验估计量（式 2/3，第 3 页）需要对负样本按预测分数排序、只取前 `k=⌊n_-β⌋` 名，这个"选择"操作本身不可微，且不能像标准 AUC 那样写成逐对样本可分解的形式——从一个小批数据算出的梯度并不是整个目标梯度的无偏估计（第 4 页，式 7 之后原文明确指出："It is impossible to compute an unbiased stochastic gradient of the objective in (7) based on a mini-batch of examples that include only a part of negative examples"）。
- 已有路线的效率批评（第 2 页，相关工作原文逐字核验）：
  - **结构化 SVM 路线（Narasimhan & Agarwal, 2013b/2013a/2017）**：原文——"their algorithms are only applicable to learning linear models and are **not efficient for big data due to per-iteration costs proportional to the size of training data**."（第 2 页）。同段引言部分（第 1 页）另有一句概括同一批评："their approach is not efficient for big data and is not applicable to deep learning, **which needs to evaluate the prediction scores of all examples and sort them at each iteration**."
  - **朴素小批量方法（Kar et al., 2014）**：原文——"this heuristic approach is **not guaranteed to converge** for minimizing the pAUC objective and its **error scales as `O(1/√B)`**, where B is the mini-batch size."（第 2 页）。
  - **ad-hoc 加权方法（Yang et al., 2021）**：为负样本和正样本设计权重函数使目标可按对分解，但"their objective function **might have a large approximation error** for the pAUC estimator"（第 2 页）。
- 本文的立场：以上三条批评都指向"效率"或"收敛性"的**理论/渐近**性质（迭代代价是否正比于数据规模、误差是否随批量收敛、是否有近似误差），不是实测运行时间的比较——这与本文自身完全不报告实测时间是一致的（见下节）。

## 方法核心

### 4.1 DRO 视角下的 OPAUC 目标（第 3–4 页，式 4、式 8–10）

- 一般 DRO 损失（第 3 页，式 4）：`L̂_φ(·) = max_{p∈Δ} Σ_j p_j ℓ_j(·) − λ D_φ(p, 1/n)`，用散度度量 `D_φ` 约束权重分布 `p`。本文取两种散度：CVaR 散度 `φ_c(t)=I(0<t≤1/γ)` 和 KL 散度 `φ_kl(t)=t log t − t + 1`（第 3 页，引理 1）。
- 对每个正样本 `x_i` 定义一个基于全体负样本的 DRO 损失 `L̂_φ(w;x_i)`（第 4 页，紧接式 7 之后），再对所有正样本取平均得到目标（式 8，第 4 页）：`min_w (1/n_+) Σ_{x_i∈S_+} L̂_φ(w;x_i)`。
- **Theorem 1（CVaR，第 4 页）**：取 `φ(·)=φ_c(·)=I(·∈(0,1/β])`，式 8 等价于 `min_{w,s∈R^{n_+}} F(w,s) = (1/n_+) Σ_{x_i∈S_+} [s_i + (1/β) ψ_i(w,s_i)]`（式 9），其中 `ψ_i(w,s_i)=(1/n_-)Σ_{x_j∈S_-} (L(w;x_i,x_j)−s_i)_+`。原文备注明确：CVaR-based OPAUC 估计量是 OPAUC 的**精确（exact）**估计量，`s_i` 可解释为为每个正样本挑选负样本 top-k 阈值的变量。
- **Theorem 2（KL，第 4 页）**：取 `φ(·)=φ_kl(·)`，式 8 变为式 10：`min_w (1/n_+) Σ_{x_i∼S_+} λ log E_{x_j∈S_-} exp(L(w;x_i,x_j)/λ)`。原文备注：KL-DRO 估计量是**软（soft）**估计量，随 `λ` 在 `OPAUC(h_w,0,1/n_-)`（infinite-push 极限）和 `OPAUC(h_w,0,1)`（标准 AUC 极限）之间插值；当 `λ→0` 与 CVaR 取 `β=1/n_-` 时都退化为 infinite-push 目标。
- **两种估计量的精确/光滑权衡（摘要与第 4–5 页明确写出，任务第 5 点核验完成）**：CVaR 给出"non-smooth but exact"估计量（`F(w,s)` 弱凸但不光滑，第 5 页引理 2）；KL 给出"inexact but smooth (soft)"估计量（式 11 的 `F(w)` 在假设 2 下光滑，第 5 页）。这一措辞在摘要中逐字出现，正文 4.2/4.3 节呼应。

### 4.2 算法 1（SOPA，第 5 页，逐行核验，任务第 1、2 点）

原文完整伪代码（第 5 页，`pdftotext -layout` 逐页核对）：

```
Algorithm 1 SOPA
1: Set s^1 = 0 and initialize w
2: for t = 1, ..., T do
3:   Sample two mini-batches B_+ ⊂ S_+, B_- ⊂ S_-
4:   Let p_ij = I(ℓ(h(w_t,x_i) − h(w_t,x_j)) − s_i^t > 0)
5:   Update s_i^{t+1} = s_i^t − (η_2/n_+)(1 − Σ_j p_ij/(β|B_-|))  for x_i ∈ B_+
6:   Compute a gradient estimator ∇_t by
     ∇_t = (1/(β|B_+||B_-|)) Σ_{x_i∈B_+} Σ_{x_j∈B_-} p_ij ∇_w L(w_t;x_i,x_j)
7:   Update w_{t+1} = w_t − η_1 ∇_t
8: end for
```

逐点核验（任务要求的算法结构五点）：

1. **`s` 是否为跨迭代持久的向量（每正样本一个分量）**：**是**。第 5 页步骤 1 只在算法开始时执行一次 `s^1=0`（`s ∈ R^{n_+}`，维度等于全体正样本数），此后不再重新初始化；每次迭代只更新当前采样到的正样本对应分量（步骤 5 的 `for x_i ∈ B_+`），未采样到的正样本的 `s_i` 分量保持上一轮的值不变，跨迭代持久累积。第 5 页正文额外说明："Another challenge for optimizing F(w,s) is that s is of high dimensionality and computing the gradient for all entries in s at each iteration is expensive."——正是因为 `s` 与全体正样本等维，才需要设计"只更新采样到的分量"的随机坐标下降。
2. **每步是否只采样两个小批 `B_+`、`B_-`**：**是**。步骤 3 明确 `Sample two mini-batches B_+ ⊂ S_+, B_- ⊂ S_-`，无第三个采样集合。
3. **`p_ij` 是否为硬 `0/1` 权重、由配对损失与 `s_i^t` 比较得到**：**是**。步骤 4 `p_ij = I(ℓ(h(w_t,x_i)−h(w_t,x_j)) − s_i^t > 0)`，`I(·)` 为指示函数，取值严格 0 或 1；第 5 页正文明确称其为"hard weights `p_ij`（either 0 or 1）… dynamically computed by step 4, which compares the pairwise loss … with the threshold variable `s_i^t`"。
4. **`s` 是否只对当前小批内的正样本做随机坐标更新**：**是**。步骤 5 的更新式仅对 `x_i ∈ B_+`（当前采样到的正样本小批）执行，且步骤 6 的说明称这是"stochastic coordinate gradient descent (SCGD) updates for updating s"——即随机坐标下降，而非对全部 `n_+` 个坐标同时更新。

5. **`s` 的更新量是否只依赖计数、不需要模型参数的梯度路径**：**是**。步骤 5 更新式为 `s_i^{t+1} = s_i^t − (η_2/n_+)(1 − Σ_j p_ij/(β|B_-|))`，右端只有常数 `η_2/n_+/β`、正样本 `i` 对应的负样本命中计数 `Σ_j p_ij`（`p_ij∈{0,1}` 的求和，即当前小批内有多少负样本使配对损失超过阈值 `s_i^t`）以及负样本批量大小 `|B_-|`——**不包含任何对 `w` 的梯度或雅可比项**。这与后面 `w` 的更新（步骤 6–7，需要对配对损失 `∇_w L` 反传）形成鲜明对比：`s` 的更新是纯计数驱动的次梯度上升（对偶变量），`w` 的更新才走标准反向传播。

### 4.2 差异对照：SOPA vs SOPA-s（第 5–6 页，任务第 5 点续）

第 5 页正文明确列出两条差异（逐字核验）：

> "There are two key differences between SOPA-s and SOPA. First, the pairwise weights `p_ij` in SOPA-s (step 5) are **soft weights between 0 and 1**, in contrast to the **hard weights `p_ij∈{0,1}`** in SOPA. Second, the update for `w_{t+1}` is a momentum-based update where `γ_1∈(0,1)`."

Algorithm 2（SOPA-s，第 6 页，完整伪代码）：

```
Algorithm 2 SOPA-s
1: Set u^1 = 0 and initialize w
2: for t = 1, ..., T do
3:   Sample two mini-batches B_+ ⊂ S_+, B_- ⊂ S_-
4:   For each x_i ∈ B_+, update u_i^{t+1} = (1−γ_0) u_i^t + γ_0 (1/|B_-|) Σ_{x_j∈B_-} exp(L(w_t;x_i,x_j)/λ)
5:   Let p_ij = exp(L(w_t;x_i,x_j)/λ) / u_i^t
6:   Compute a gradient estimator ∇_t = (1/|B_+|)(1/|B_-|) Σ_{x_i∈B_+}Σ_{x_j∈B_-} p_ij ∇L(w_t;x_i,x_j)
7:   Update v_t = (1−γ_1) v_{t-1} + γ_1 ∇_t
8:   Update w_{t+1} = w_t − η v_t（or Adam-style）
9: end for
```

SOPA-s 用移动平均 `u_i`（跨迭代持久，同样只更新当前采样到的正样本分量）代替 SOPA 的阈值 `s_i`，`p_ij` 由 `exp(·)/u_i^t` 给出、连续取值于 (0,1)（严格意义上可 >0 但受 `u_i` 归一化，原文称"soft weights between 0 and 1"）。

### 5. TPAUC 与 SOTA-s（第 6–7 页）

- 在 OPAUC-DRO 的基础上，对正样本再套一层 DRO（式，第 6 页），取 `φ=φ'=φ_kl` 得到三层复合优化（第 6–7 页，`f_1(s)=λ' log(s), f_2(g)=g^{λ/λ'}`），提出 Algorithm 3（SOTA-s，第 7 页），维护 `u_i^t`（跟踪 `g_i(w)`）与 `v_t`（跟踪外层 `f_2` 的均值）两级移动平均状态。
- CVaR 版本的精确 TPAUC 估计量（`φ_c,φ_c'`）需要用合页函数的共轭形式转成弱凸-凹极小极大问题，只给出 `O(1/ε⁶)` 复杂度算法，正文明确说"We present the algorithm and analysis in the supplement for interested readers"（第 7 页）——本笔记未核验附录中该算法的完整推导。

### 收敛结果一览（第 5–7 页，定理陈述已读，证明细节未核验）

| 算法 | 定理 | 复杂度 | 收敛测度 |
| --- | --- | --- | --- |
| SOPA（CVaR，OPAUC） | Theorem 3（第 5 页） | `O(1/(βε⁴))` | `F(w,s)` 的 Moreau 包络梯度范数（弱凸目标的标准弱测度） |
| SOPA-s（KL，OPAUC） | Theorem 4（第 5 页） | `O(1/(min(B_+,B_-)ε⁴) + n_+/(B_+B_-ε⁴))` | `F(w)` 本身的梯度范数（更强的收敛测度，因 `F(w)` 光滑） |
| SOTA-s（KL，TPAUC） | Theorem 5（第 7 页） | 与 SOPA-s 同阶 | `F(w)` 梯度范数 |
| TPAUC（CVaR，精确） | 第 7 页正文提及，无定理编号，证明见附录 | `O(1/ε⁶)` | 未展开 |

第 5 页 Remark 明确指出 SOPA-s 相对 SOPA 的两个优势："(i) 收敛测度更强（直接是目标梯度范数而非 Moreau 包络）；(ii) SOPA-s 的复杂度随小批量并行加速（parallel speed-up）"，同时也指出"SOPA 的复杂度不依赖正样本总数 `n_+`，而 SOPA-s 的复杂度依赖 `n_+`"——这是一处效率上的权衡，但依然是**迭代复杂度**层面的比较，不是实测时间。

## 效率论述的性质核验（任务第 3 点，逐词检索结果）

对提取全文（26 页、968 行 Markdown）执行大小写不敏感检索，结果如下，**全部零命中**：`wall clock`、`wall-clock`、`running time`、`training time`、`seconds`、`runtime`、`run time`、`throughput`、`memory usage`、`peak memory`、`memory`、`GPU`。

唯一命中的相关词：
- `speed-up` / `speedup`：命中 2 处，均指"SOPA-s 的**迭代复杂度**可随小批量并行加速"这一理论表述（第 2 页贡献列表、第 5 页 Remark），不涉及任何实测数字。
- `efficient` / `efficiency` / `complexity`：命中多处，全部指大 O 迭代复杂度或"per-iteration cost 是否正比于训练集规模"这类**渐近**表述（例如第 2 页对结构化 SVM 和 Kar et al. 2014 的批评），没有一处附带秒数、显存 GB 数或吞吐量数字。

**结论**：本文讨论的"效率"（efficient/efficiency）严格限定在**迭代复杂度**（数据是否需要全排序、per-iteration cost 是否随数据规模线性增长、误差是否随小批量收敛）与**收敛保证**（是否有理论 ε-稳定点收敛率）两个维度，全文没有任何实测墙钟时间、显存占用或吞吐量的报告——第 6 节实验（Figure 2，第 8 页）只画训练收敛曲线（目标值/pAUC 指标 vs 训练轮数或迭代步数），不含耗时坐标轴。

## 实验结果（第 8–9 页，Table 1–4，仅记录用于交叉核对，非本笔记重点）

- 数据集：CIFAR-10/100（构造 80% 正样本移除的不平衡版本）、Melanoma（自然不平衡医学图像）、OGB 分子图数据集 moltox21/molmuv/molpcba；模型分别用 ResNet18（图像）和 GIN（图）。
- 基线：MB（Kar et al. 2014 朴素小批量）、AW-poly（Yang et al. 2021 ad-hoc 加权）用于训练收敛对比；CE、AUC-SH、AUC-M、P-push 用于测试性能对比。
- OPAUC 测试结果（Table 1）：SOPA 在 CIFAR-10 FPR≤0.3 上取得 `0.8766±0.0034`，优于 MB 的 `0.8690±0.0016`、AW-poly 的 `0.8664±0.0052`；Melanoma FPR≤0.3 上 SOPA `0.8093±0.0248` 明显领先其余方法。
- TPAUC 测试结果（Table 2）：SOTA-s 在多数设置上领先，例如 Melanoma (0.6,0.4) 设置下 `0.4198±0.0825` vs AW-poly 的 `0.3878±0.0292`。
- 消融（附录 A.2，第 10–11 页）：`γ_0`（SOPA-s）与 `γ_0,γ_1`（SOTA-s）的移动平均系数敏感性扫描，固定值 0.9 并非全局最优，调参可进一步提升测试 pAUC。

## 与本课题的关系

**本课题背景**：第三章机制 BER 是"多预算 CVaR-pAUC 实体排序损失"，与逐流 BCE 联合训练，损失形式为 `loss = (1/6)·Σ_k (1/N_p)·Σ_p [ξ_{p,k} + (1/K_k)·Σ_n relu(L_pn − ξ_{p,k})]`，`ξ` 作为叶张量参与同一次 `backward()` 后按其梯度更新；实体是"袋"，袋内含多条流，每步 66 个实体展开成最多 4224 条序列。

- **论文原结论**：SOPA 通过"持久 `s` + 随机坐标更新"，把偏 AUC 优化中原本需要对全体负样本排序选 top-k 的目标，改写成弱凸的 DRO 目标，使得**每步只需采样两个小批 `B_+`、`B_-`** 即可计算无偏次梯度（第 5 页："A benefit for solving (9) is that an unbiased stochastic subgradient can be computed in terms of (w,s)"）。
- **可迁移机制**：`ξ` 作为跨迭代持久、按梯度更新的阈值变量，与 SOPA 中 `s_i` 的角色（每正样本一个 CVaR 分位数阈值，随机坐标更新）在数学结构上同源——都是 CVaR 估计量（式 6，本文引理 1）`L̂_cvar(·;γ) = min_s s + (1/nγ)Σ(ℓ_i(·)−s)_+` 的对偶阈值变量，只是本课题把"每个正样本一个 `s_i`"换成了"每个预算 `k` 一个 `ξ_k`"（多预算版本），把"负样本"换成了"袋内候选流"。
- **本课题推论（标注为推论，需独立核实与本课题实现的匹配度）**：SOPA 的"持久 `s` + 随机坐标更新"把 pAUC 优化中原本存在的**数据集级**耦合（需要知道全体负样本的排序）降为**小批级**耦合（只需当前采样到的 `B_+∪B_-` 内部比较）——本课题 BER 沿用了同一结构（每步 66 个实体即构成 `B_+∪B_-` 的角色，`ξ_k` 在该小批内与候选流的损失比较）。因此**不能声称**"CVaR-pAUC 要求全数据集同显存/同图"，只能说"已采样实体批内的配对耦合无法进一步分批"——这是小批内部的结构性约束，不是数据集级约束。
- **本课题推论（原论文未遇到的问题）**：SOPA 的样本是**原子的**——每个正样本 `x_i` 对应一次前向即可得一个分数，`n_+`、`n_-` 就是原始样本数；本文强调"SOPA 的复杂度不依赖正样本总数 `n_+`"（第 5 页 Remark）正是建立在"采样一个正样本只需一次前向"这个假设之上。**本课题 BER 的样本是复合的**——一个实体（袋）需要跑袋大小那么多次前向才能得到该实体的分数，因此原文"单次迭代代价与数据集规模无关"这条效率论证，在袋结构下需要重新表述为"单次迭代代价与批内袋大小之和成正比"——这是袋结构带来的、原论文完全没有遇到的问题，第三章训练开销（每步 4224 条序列展开、激活 30.97 GiB、首步 OOM）的结构性来源正在于此，不能引用本文的复杂度结论为本课题的开销规模背书。
- **不可直接声称**：不得引用本文声称"CVaR-pAUC 已被证明训练高效"或"本文报告过接近本课题规模的实测时间/显存"——本文全文对效率的讨论限于迭代复杂度阶（大 O），没有任何实测墙钟时间或显存数字（见上节逐词检索）；本文实验的批量为 64（第 8 页 Parameter Tuning），远小于本课题每步展开出的序列规模，不能作为本课题批量可行性的先例。也不得把 SOTA-s 的三层复合优化误认为已覆盖本课题"实体袋 + 序列展开"的两级采样结构——本文的两级 DRO（OPAUC→TPAUC）叠加的是"负样本排序"和"正样本排序"两个维度，而非"袋内序列展开"这一维度。
- **仍需实验验证的假设**：(1) 本课题 `ξ_{p,k}` 的更新是否严格遵循 SOPA 式 5 的"纯计数驱动、不含模型梯度"这一结构，需要核对本课题的实际反向传播实现（任务背景描述"`ξ` 作为叶张量参与同一次 `backward()` 后按其梯度更新"，这与 SOPA 原文"`s` 的更新是独立于 `w` 反传的次梯度上升，且不通过 `backward()` 得到"存在潜在差异，需要逐行核对本课题代码后确认二者是否等价，本笔记不作断言）；(2) SOPA 的收敛保证（Theorem 3）建立在假设 2（`h(·;x)` 利普希茨、光滑、有界）之上，本课题 FT-Transformer 骨干是否满足该假设需要单独核实。

## 我的理解

SOPA 系列论文的核心洞察是：偏 AUC 的"选择 top-k 负样本"这个离散、不可微操作，可以通过 DRO 的对偶变量（CVaR 阈值或 KL 温度加权）连续化，而这个对偶变量恰好可以设计成"跨迭代持久、按小批随机更新"的状态量——这与很多"有限和耦合复合优化"（FCCO，见 Wang & Yang 2022）家族方法共享同一套技巧：把"需要看到全数据集才能算准"的量，用移动平均或次梯度上升的方式，改造成"看小批就能局部更新、长期收敛到全局准确值"的量。这个技巧的代价是引入了额外的状态张量（`s` 或 `u`，维度与正样本数相当），以及额外的收敛速率损失（弱凸目标只能给 Moreau 包络意义下的收敛，比光滑目标弱）。

## 与相关工作的关系

- 本文式 11（第 5 页）明确承认 KLDRO 估计量的优化问题与 [[wiki/papers/methodology/ranking/2021-Qi-SOAP直接优化AUPRC|SOAP]]（Qi et al. 2021，优化 AUPRC 的有限和耦合复合优化）"a similar optimization problem"，并采用 [[wiki/papers/methodology/ranking/2022-Wang-FCCO与SOX|FCCO/SOX]]（Wang & Yang 2022）"derived better convergence results"的同一算法框架来求解式 10/11——SOPA-s、SOTA-s 本质上是把 SOX 算法应用到偏 AUC 场景的具体实例。
- 本文与 [[wiki/papers/multi-task-gradient/2021-Yuan-大规模鲁棒深度AUC最大化|Yuan et al. 2021（AUC-margin/DAM）]]同一课题组（Tianbao Yang 系），但 AUC-margin 处理的是标准 AUC（非偏 AUC）的极小极大代理损失设计，与本文的 DRO-偏AUC 路线是并列而非包含关系；本文第 6 节实验用 AUC-M 作为测试性能基线之一（Table 1）。
- 本文与 [[wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化|MIDAM]]同一第一作者（Dixian Zhu），MIDAM 处理的是大包多示例 AUROC 的随机池化偏差问题（不涉及偏 AUC），两文方法学谱系相邻但目标不同。

## 疑问 / 待验证

- 附录 C–H（第 11–26 页，弱凸性证明、Moreau 包络分析、Theorem 3–5 的完整推导）本次未逐段精读，若后续需要引用具体的收敛率常数或假设细节，须回到原始 PDF 核实。
- SOTA-s 的三层复合优化（第 6–7 页）与本课题多预算结构（`Σ_k`，6 个预算档位）在数学形式上是否同构，需要更细致的逐项对照，本笔记暂未展开。
- 本文实验的负样本/正样本采样批量均为 64（第 8 页），与本课题实体批量 66、展开后 4224 条序列的规模差 2 个数量级，SOPA/SOPA-s 的收敛率是否在该规模下仍成立（尤其是 SOPA-s 依赖 `n_+` 的那一项），未见文献或本课题实验支撑，需单独验证。

## 原始摘要

> In this paper, we propose systematic and efficient gradient-based methods for both one-way and two-way partial AUC (pAUC) maximization that are applicable to deep learning. We propose new formulations of pAUC surrogate objectives by using the distributionally robust optimization (DRO) to define the loss for each individual positive data. We consider two formulations of DRO, one of which is based on conditional-value-at-risk (CVaR) that yields a non-smooth but exact estimator for pAUC, and another one is based on a KL divergence regularized DRO that yields an inexact but smooth (soft) estimator for pAUC. For both one-way and two-way pAUC maximization, we propose two algorithms and prove their convergence for optimizing their two formulations, respectively. Experiments demonstrate the effectiveness of the proposed algorithms for pAUC maximization for deep learning on various datasets. The proposed methods are implemented with tutorials in our open-sourced library LibAUC (www.libauc.org).

## 文献信息

- 官方页：<https://proceedings.mlr.press/v162/zhu22g.html>（PMLR v162:27548–27573，页码经 [[wiki/papers/methodology/ranking/2023-Shi-难负采样遇见OPAUC|Shi et al. 2023 参考文献]]交叉核对为 27548–27573）
- 代码/库：本文方法已实现进 LibAUC（<https://www.libauc.org>），见 [[wiki/papers/methodology/training-efficiency/2023-Yuan-LibAUC库与X风险优化|LibAUC: A Deep Learning Library for X-Risk Optimization]]
