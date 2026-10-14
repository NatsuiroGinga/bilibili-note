---
title: "Boyd & Vandenberghe《Convex Optimization》§5.5.3 水填充（water-filling）与 KKT 条件 — 节选笔记"
authors: [Stephen Boyd, Lieven Vandenberghe]
year: 2004
date: 2026-10-14
journal: "Cambridge University Press（教材；本笔记只覆盖 §5.5.3，印刷 pp.243–246 / 物理 PDF pp.257–260）"
source_pdf: "[[raw/papers/methodology/2004-Boyd-Vandenberghe-Convex-Optimization.pdf]]"
tags:
  - 凸优化
  - KKT条件
  - 水填充
  - 拉格朗日对偶
  - 类型/论文
key_finding: "§5.5.3 中的 water-filling（Example 5.2）是一个「线性等式 + 非负锥约束 + 可分离凹目标」的连续凸问题，解为 x_i*=max{0,1/ν*−α_i}，水位参数是等式乘子 ν*（不是不等式乘子 λ*）；该节未涉及整数分配。因此把它当作「存储预算 B 下分配比特」的依据，只有在分配变量连续可除、边际效用单调递减、预算约束为仿射时才成立。"
method: "写出 KKT 条件（5.49）并逐项求解 Example 5.2 的连续 water-filling 闭式解"
baseline: "—（教材章节，非实验论文）"
aliases: [Boyd-water-filling, Boyd §5.5.3, 水填充法, KKT conditions 5.49]
related:
  - "[[2017-Achiam-约束策略优化]]"
  - "[[2019-Cotter-Proxy-Lagrangian约束优化]]"
---

# Boyd《Convex Optimization》§5.5.3 节选：水填充与 KKT 条件

> 证据等级：**本地全文**（原件 `raw/papers/methodology/2004-Boyd-Vandenberghe-Convex-Optimization.pdf`，714 页）
> 覆盖范围：**仅 §5.5.3**（印刷 pp.243–246；物理 PDF pp.257–260）。页脚印刷页码 = 物理 PDF 页码 − 14。
> 抽取工具：`pdf-converter`（MinerU，`mineru-open-api extract --pages 257-266`）；页码定位用 `pdftotext` 逐页扫描，未用其读取公式。

## 0 先说结论（供方案裁决）

**主代理方案里写的「率失真／KKT／water-filling」作为理论依据，其参照对象（§5.5.3 Example 5.2）是一个具体的、可写出闭式解的连续凸问题；它成立的前提有三条，方案必须逐条自查。** 三条前提中任一条不满足，该节就不能被直接引用为「我们问题的解的形式」：

1. 分配变量**连续可除**（Boyd 的 x ∈ Rⁿ，非整数/非离散）；
2. 目标对每个实体的**边际效用单调递减**（可分离且每个分量严格凸），这正是「水位」唯一的来源；
3. 预算约束是**仿射等式**（1ᵀx = 1），不是不等式、也不是非仿射预算。

此外一个命名纠错：**「水位」参数在 Boyd 里是等式乘子 ν\*，不是不等式乘子 λ\***；λ\* 在这里只是逐坐标的非负性乘子并当场被当作松弛变量消掉。方案若把 `λ` 写成水位，与原文不符。

---

## 1 原始问题形式（Example 5.2 Water-filling，印刷 p.245 / PDF 259）

Boyd 以小化形式给出（原文逐条）：

$$
\begin{array}{ll}
\text{minimize} & -\sum_{i=1}^{n}\log(\alpha_i + x_i)\\
\text{subject to} & x \succeq 0,\quad \mathbf{1}^Tx = 1,
\end{array}
\qquad \alpha_i > 0.
$$

- **变量**：$x \in \mathbf{R}^n$。原文语境为「给 n 条通信信道分配功率」，$x_i$ = 第 i 条信道分配到的发射功率，$\log(\alpha_i+x_i)$ = 该信道的容量/通信速率；问题即「把总量为 1 的功率分给各信道以最大化总速率」。
- **目标**：$-\sum_i \log(\alpha_i+x_i)$，即等价于 **maximize $\sum_i \log(\alpha_i+x_i)$**。注意这是 **可分离**的（separable）：$f_0(x)=\sum_i f_i(x_i)$，$f_i(x_i)=-\log(\alpha_i+x_i)$。
- **约束**：一条**线性等式** $\mathbf{1}^Tx=1$；一组**线性不等式** $x \succeq 0$（坐标非负锥）。
- **凸性**：$-\log(\alpha_i+x_i)$ 在 $\alpha_i+x_i>0$ 上是凸函数，$\alpha_i+x_i$ 是仿射映射，故目标凸；约束仿射。**这是标准凸问题**，满足 Slater（取 $x\succ 0,\ \mathbf{1}^Tx=1$ 即可，因为 $\alpha_i>0$ 使域开）。

**结构判定（对应任务第 4 问的第一半）：是的，这一节的问题就是「线性（仿射）约束 + 可分离目标」。**
更直白地说，Example 5.2 是 §5.5.5 中 Example 5.4「minimize $\sum_i f_i(x_i)$ subject to $a^Tx=b$」（印刷 p.248）的一个特例；Ed.5.4 明说该目标「is called separable since it is a sum of functions of the individual variables」，因此拉格朗日函数可分离、对偶问题分解成 n 个一维标量问题。

---

## 2 解的形式：水位（level）结构与闭式解（印刷 pp.245–246 / PDF 259–260）

### 2.1 KKT 条件（原文对 Example 5.2 逐条写出，印刷 p.245）

对不等式约束 $x^\star \succeq 0$ 引入乘子 $\lambda^\star \in \mathbf{R}^n$，对等式约束 $\mathbf{1}^Tx=1$ 引入标量乘子 $\nu^\star \in \mathbf{R}$：

$$
x^\star \succeq 0,\qquad \mathbf{1}^{T}x^\star = 1,\qquad \lambda^\star \succeq 0,\qquad \lambda_i^\star x_i^\star = 0,\ i=1,\dots,n,
$$
$$
-1/(\alpha_i + x_i^\star) - \lambda_i^\star + \nu^\star = 0,\quad i=1,\dots,n.
$$

（第 4 式是**互补松弛**，第 5 式是**平稳性/梯度为零**。）

### 2.2 消去 $\lambda^\star$ 后的等价形式

原文指出 $\lambda^\star$ 在最后一式中「acts as a slack variable」，可直接消掉，得

$$
x_i^\star\bigl(\nu^\star - 1/(\alpha_i + x_i^\star)\bigr) = 0,\quad i=1,\dots,n,
\qquad
\nu^\star \ge 1/(\alpha_i + x_i^\star),\quad i=1,\dots,n.
$$

### 2.3 显式最优解（分层结构）

原文推导：若 $\nu^\star < 1/\alpha_i$，则只能 $x_i^\star>0$，由互补松弛得 $\nu^\star = 1/(\alpha_i+x_i^\star)$，解出 $x_i^\star = 1/\nu^\star - \alpha_i$；若 $\nu^\star \ge 1/\alpha_i$，则 $x_i^\star>0$ 会违反互补松弛，故 $x_i^\star=0$。因此

$$
x_i^\star =
\begin{cases}
1/\nu^\star - \alpha_i, & \nu^\star < 1/\alpha_i,\\[2pt]
0, & \nu^\star \ge 1/\alpha_i,
\end{cases}
\qquad\text{等价地}\qquad x_i^\star = \max\{\,0,\ 1/\nu^\star - \alpha_i\,\}.
$$

水位由总量约束确定：

$$
\sum_{i=1}^{n}\max\{0,\ 1/\nu^\star - \alpha_i\} = 1 .
$$

原文强调：左端是 $1/\nu^\star$ 的**分段线性递增函数**（breakpoints 在 $\alpha_i$ 处），**故该方程有唯一解**。

**分层结构的准确表述**：原文把 $\alpha_i$ 称为 patch i 的「ground level」，把 $1/\nu$ 称为「flood level（水位）」，注水深度（阴影高度）即 $x_i^\star$；「把水面抬高到恰好用掉总量为 1 的水」即为解。

> **命名纠错（重要）**：**水位参数是 $\nu^\star$（等式约束 $\mathbf{1}^Tx=1$ 的乘子），不是 $\lambda^\star$。** $\lambda^\star$ 是 $x\succeq 0$ 的逐坐标乘子，在解的过程中被当作松弛变量消掉。方案文档若写「拉格朗日乘子 λ 即水位」，与本节原文不符。
>
> **另注**：$x_i^\star$ 与 $1/\nu^\star$ 是**线性**关系（不是对数关系）。「分层」来自 $1/\nu^\star$ 这个公共水平线，而不是来自对目标取对数。

---

## 3 本节中 KKT 条件是怎么用的（印刷 pp.243–244 / PDF 257–258）

### 3.1 一般 KKT 条件（式 (5.49)，印刷 p.243）

在 $f_0,\dots,f_m,h_1,\dots,h_p$ **可微**（因此定义域开）的假设下，原文先声明「**we make no assumptions yet about convexity**」（不加凸性假设），给出

$$
\begin{array}{rcl}
f_i(x^\star) \le 0, & i=1,\dots,m & \text{(primal 可行性)}\\
h_i(x^\star) = 0, & i=1,\dots,p & \text{(primal 可行性)}\\
\lambda_i^\star \ge 0, & i=1,\dots,m & \text{(对偶可行性)}\\
\lambda_i^\star f_i(x^\star) = 0, & i=1,\dots,m & \text{(complementary slackness)}\\
\nabla f_0(x^\star) + \sum_{i=1}^{m}\lambda_i^\star \nabla f_i(x^\star) + \sum_{i=1}^{p}\nu_i^\star \nabla h_i(x^\star) = 0 & & \text{(stationarity)}
\end{array}
\tag{5.49}
$$

**必要性**（原文）：「for any optimization problem with differentiable objective and constraint functions for which strong duality obtains, any pair of primal and dual optimal points must satisfy the KKT conditions (5.49).」——注意仍要求**强对偶**。

### 3.2 凸问题下 KKT 变成充分条件

原文（印刷 p.244）：当 $f_i$ 凸、$h_i$ 仿射时，**满足 (5.49) 的点即最优**，且对偶间隙为零。原文证明的路径值得记下：前两条 ⇒ 原可行；$\lambda\succeq 0$ ⇒ $L(x,\lambda,\nu)$ 关于 $x$ 凸；末条 ⇒ 其在 $\tilde x$ 处梯度为零 ⇒ $\tilde x$ 是 $L$ 的最小点 ⇒ $g(\tilde\lambda,\tilde\nu)=L(\tilde x,\tilde\lambda,\tilde\nu)=f_0(\tilde x)$。

再叠加 **Slater 条件**时，KKT 成为**充要**：「x is optimal if and only if there are $(\lambda,\nu)$ that, together with $x$, satisfy the KKT conditions.」

### 3.3 前缀：互补松弛（式 (5.48)，印刷 p.243）

§5.5.3 之前（属 §5.5.2）已给出：在强对偶下，任何原最优 $x^\star$ 与对偶最优 $(\lambda^\star,\nu^\star)$ 满足

$$
\lambda_i^\star f_i(x^\star) = 0,\quad i=1,\dots,m, \tag{5.48}
$$

即「$\lambda_i^\star>0 \Rightarrow f_i(x^\star)=0$」/「$f_i(x^\star)<0 \Rightarrow \lambda_i^\star=0$」。

### 3.4 本节还给了什么

- **Example 5.1**（印刷 p.244）：等式约束凸二次小化，KKT 化为一个 $(m+n)$ 元线性方程组 $\begin{bmatrix}P&A^T\\A&0\end{bmatrix}\begin{bmatrix}x^\star\\\nu^\star\end{bmatrix}=\begin{bmatrix}-q\\b\end{bmatrix}$。
- **§5.5.4 Mechanics interpretation**（印刷 pp.245–246）：用弹簧-滑块系统把 KKT 的平稳性解释为**力平衡**，乘子解释为**接触力**（$\lambda_i\ge 0$ 即接触力远离接触面；互补松弛即「只有接触时才有接触力」）。
- **§5.5.5 Solving the primal problem via the dual**（印刷 pp.247–248）：**Example 5.3 熵最大化**、**Example 5.4 可分离函数 + 单个等式约束**（$f_0=\sum_i f_i(x_i)$，$a^Tx=b$；由 $\nabla_x L=0$ 得 $f_i'(x_i^\star)=-\nu^\star a_i$）。**注意 Example 5.3/5.4 属于 §5.5.5 而非 §5.5.3**——若方案要引「可分离」，引的应是 §5.5.5 Example 5.4。
- **§5.6 Perturbation and sensitivity analysis**（印刷 p.249 起）：$\lambda_i^\star = -\partial p^\star(0,0)/\partial u_i$，$\nu_i^\star=-\partial p^\star/\partial v_i$（式 (5.58)）——**这是「预算/约束的边际价值 = 乘子」这句话在本教材中的唯一出处，且要求 $p^\star$ 可微 + 强对偶。**

---

## 4 我们的问题与本节结构差在哪（任务第 4 问）

### 4.1 本节问题满足的前提（逐条）

| 前提 | §5.5.3 Example 5.2 是否满足 | 出处 |
|---|---|---|
| 变量连续可除 | 满足（$x\in\mathbf{R}^n$） | 印刷 p.245 |
| 约束为仿射（1 个等式 + 非负锥） | 满足 | 印刷 p.245 |
| 目标可分离 | 满足（$\sum_i \log(\alpha_i+x_i)$） | 印刷 p.245、p.248 |
| 每个分量边际效用单调递减（严格凹） | 满足（$\mathrm{d}/\mathrm{d}x_i \log(\alpha_i+x_i)=1/(\alpha_i+x_i)$ 严格递减） | 由闭式解反推，印刷 p.245 |
| 可微 | 满足（$\alpha_i>0$，域开） | 印刷 p.243 |
| 强对偶 / Slater | 满足 | 印刷 p.244 |

### 4.2 **哪些前提我们的问题不满足**（直接回答）

方案表述是「存储预算 $B$ 下分配比特，目标与分配量之间是凹关系」。对照上表，**下列任一条不成立，§5.5.3 的结论就不能照搬**：

1. **整数/离散分配**（最可能踩的一条）。
   若「分配比特」指每个实体分配**整数** bit-width、**整数**条回放样本、或按固定粒度（如每实体只能取 $b\in\{0,8,16,32\}$）分配，则可行集是格点而非欧氏空间：目标不可微，「$\nabla f_0+\sum\lambda_i\nabla f_i=0$」**没有意义**，KKT 平稳性条件根本无法写出。此时强对偶一般**不成立**，$\nu^\star$ 不再精确等于预算的边际价值。**整型可分凹资源分配有它自己的一套结论（按边际增益贪心最优），但那不在 §5.5.3 里**，不能引本节当依据。

2. **预算约束不是仿射等式**。
   Boyd 用的是**必须用完**的等式 $\mathbf{1}^Tx=1$。若我们的预算是**不等式** $\le B$，则最优解存在两种情形：预算**用满**（此时才有水位结构）或**不用满**（此时水位为 $0$、各实体取无约束最优）。§5.5.3 不含「预算不激活」这一支。
   若预算是**存储字节数**而每个实体的存储代价**不是分配量的线性函数**（例如代价随样本数/量化位宽非线性增长），则约束集非多面体，§3.2 的「$h_i$ 仿射 ⇒ KKT 充分」那一支**不再成立**，KKT 退回为「仅必要（且仍需强对偶）」。

3. **效用不凹**（例如存在最小可用样本量、或有「分配太少反而有害」的区间）。
   水位的**唯一性**依赖原文那句「左端是 $1/\nu^\star$ 的分段线性**递增**函数」。若某个实体的边际效用不是单调递减，聚合函数不再单调，水位可能不唯一，$\max\{0,1/\nu^\star-\alpha_i\}$ 形式的解**不再是最优**，KKT 点可能只是驻点（saddle / local）。

4. **多约束**。
   Boyd 只有**一个**等式约束，因此水位是一个标量 $\nu$。若我们的预算不止一条（例如同时限制总存储与原子的最大重放次数），水位变成向量，本节的标量注水图示与「唯一解」论证都要重做。

### 4.3 明确结论

- **若**方案中的分配变量连续可除、效用对每个实体的边际贡献单调递减、且预算写成单一的仿射约束，**那么该问题确实落在 §5.5.3 的适用范围**，water-filling 的 level 解与「预算乘子 = 边际价值」（式 (5.58)）可以引用，但必须逐条列出上面 6 条前提。
- **若**存在整数 bit-width / 整数样本数，或预算为不等式且可能不激活，或存储代价非线性，**则该节不适用**：§5.5.3 只提供了连续凸情形下的必要充分条件，跨到整型或非凸情形时它给不出最优性保证。此时应改引「可分凹整型资源分配的贪心最优性」或「连续松弛 + 取整的间隙分析」——**这两样都不在本节内，需要另找文献**。

---

## 5 该节有没有提到「整数分配」或「非凸」的情形？（任务第 5 问）

- **非凸：有，而且是专门一小节。** §5.5.3 开头即写「we make no assumptions yet about convexity」，并设小标题 **"KKT conditions for nonconvex problems"**（印刷 p.243 / PDF 257）。结论是：不加凸性时 KKT 仍是**必要**条件（前提仍是可微 + 强对偶 + 零对偶间隙），但**不再充分**。
- **整数 / 离散分配：原文未述。** 对 §5.5.3 正文区间逐词检索 `integer|discrete|boolean|combinatorial`，**零命中**（唯一命中是 `nonconvex`）。Example 5.2 全篇是连续变量；本节没有任何「整数规划」「取整」「格点」讨论。
- 该节也没有出现 rate–distortion（率失真）。**「率失真」不是 §5.5.3 的内容**；本节把 $\log(\alpha_i+x_i)$ 解释为信道容量/速率，属于功率分配语境。

---

## 6 我的理解

- 本节真正的「可迁移资产」其实只有三件：**(a) KKT 五条 (5.49) 及其凸情形下的充要性；(b) 可分离结构使对偶分解为 n 个一维问题；(c) 乘子 = 约束的边际价值 (5.58)（且要求可微）**。water-filling 只是 (a)+(b) 的一个漂亮例子。
- 因此方案若只是想说「我们用一个预算乘子去给不同实体定价、按边际收益均等的原则分配」，那这个**直觉**没问题，但它对应的严格结论在 §5.5.5/§5.6（可分离 + 边际价值）而非 §5.5.3；而一旦落到整数分配，**这两处的结论都不再是充要的**。

## 7 疑问 / 待验证

1. 方案里所谓「目标与分配量之间是凹关系」——**具体是哪个量对哪个量的凹关系**？是「效用 × 存储预算」的连续凹函数，还是「效用 × 样本条数」的整值函数？这决定了 4.2 的第 1 条是否触发。**在拿到方案原文的公式前，本笔记只判定「结构条件需逐条自查」，不判定方案成立或不成立。**
2. 预算 $B$ 的**单位**是什么（bit / byte / 样本条数 / 实体条数）？每实体的代价对分配量是否线性？这决定 4.2 第 2 条。
3. 方案若要引「水位」，需先把乘子记号统一：**水位 = 等式/预算乘子 $\nu^\star$**，$\lambda$ 是逐坐标非负乘子。

## 8 文献信息

- 原件：`raw/papers/methodology/2004-Boyd-Vandenberghe-Convex-Optimization.pdf`（714 页；LaTeX with hyperref，GPL Ghostscript 10.00.0 生成，Letter 612×792 pt）
- 章节：§5.5.3 KKT optimality conditions（印刷 pp.243–246 / PDF pp.257–260），含 Example 5.1（p.244）、**Example 5.2 Water-filling（p.245）**、Figure 5.7（p.246）、§5.5.4 Mechanics（pp.245–246）
- 相邻章节：§5.5.2 互补松弛 (5.48)（p.243）；§5.5.5 求解原问题（含 Example 5.4 可分离，p.248）；§5.6 灵敏度分析 (5.58)（p.249 起）
- 抽取记录：`mineru-open-api extract --pages 257-266 -o /tmp/boyd_p257-266.md`（中间产物在 `/tmp`，未落库）
