# DRIFT 双侧组相对对抗训练的优化问题形式化链条

**状态：外部候选，待本地全文与实验复核；本地保留全部裁决权。以下不验证实验有效性，不改变冻结合同，也不将任何未来目标期信息纳入设计。**

| 返回字段 | 实际情况 |
|---|---|
| `actual_model` | GPT-5.5 Thinking |
| `actual_effort` | high |
| `actual_mode` | deep-research |
| `used_apps` | GitHub、Web |
| GitHub 读取状态 | 在指定 commit `962a6aa089e99e2b41d6397841e0e647de47e08a` 下对两条白名单路径进行只读 `fetch_file`，均返回 404；因此本文不声称独立核对了仓库实现，所有实现事实均以本交接包锁定定义为准 |
| 文献核验 | Madry et al.、Sinha et al.、Drichel et al.、CharBot、Shin & Alvarez-Melis 原文/原始预印本 |
| 核心裁决 | **可以形成与参照论文同层级的“优化问题→实现近似→误差分解→课程路径”形式化链条，但不能按原任务中的三处强说法直接写：①所给支持集分布族并不产生真正区别于点级攻击的“分布级 follower”；②当前 benign×3 不是良性侧内层 max 的估计器；③当前 binary-centering + global top-\(q\) 不是 \(\max_Q\mathbb E\ell\) 的序统计估计器。把这三处改正后，链条反而与实现更严密。** |

## 核心结论与形式化总图

参照 Madry 式鲁棒优化，攻击模型首先由允许扰动集合定义，随后形成“外层模型最小化、内层攻击最大化”的鞍点问题；Madry et al. 在 §2、式 (2.1) 正是以 \(\mathbb E[\max_{\delta\in S}L]\) 作为核心对象，在 §3.3 再讨论在内层损失最大化器处计算外层梯度的合法性。citeturn28view0turn29view2turn28view1 DGA 场景确实有离散输入与有效域名约束：Drichel et al. 指出梯度型攻击不能直接作用于 DGA 的离散输入，embedding-space 对抗向量还需离散化为有效域名；他们同时强调 DGA 的威胁模型不能机械照搬图像中的“小不可感知扰动”假设。citeturn29view0turn29view1

但从数学上，本方法最稳妥的链条应写成：

\[
\boxed{
\text{允许编辑集合}
\rightarrow
\text{理想鲁棒母目标}
\rightarrow
\text{随机候选生成}
\rightarrow
\text{binary-centered 配额 follower}
\rightarrow
\text{条件 CE 外层更新}
\rightarrow
\text{覆盖/搜索/保留/重加权误差}
\rightarrow
\text{预算分布课程路径}
}
\]

而不是：

\[
\text{分布级攻击者}
\overset{\text{当前实现}}{\Longrightarrow}
\max_Q\mathbb E\ell
\overset{\text{top-}q}{\Longrightarrow}
\text{无偏/一致估计}
\]

后面这条链在当前定义下是假的。

更具体地，本章可同时保留两个层次：

\[
\boxed{
\textbf{理想母问题：}
\quad
\min_\theta
\{\text{malicious robust risk}
+
\lambda\text{ benign robust/pressure risk}\}
}
\]

用于说明“希望防什么”；

以及

\[
\boxed{
\textbf{实现问题：}
\quad
\theta_{t+1}
=
\theta_t-
\eta_t
\nabla_\theta
\widehat{\mathcal R}
(\theta\mid\bar\theta_t)
\big|_{\theta=\theta_t}
}
\]

用于准确说明“代码实际上优化什么”。

这一“双层表述”比强行把实现说成精确求解理想 min–max 更安全，也更接近成熟鲁棒优化论文区分**目标问题**与**可计算近似**的写法。Sinha et al. 的 DRO 也是先定义分布不确定集上的 worst-case population risk，再通过结构化 Wasserstein 不确定集与对偶形式得到可计算训练目标。citeturn24view1

---

## 威胁建模与双侧母问题

### 编辑预算与合法扰动集合

设有效域名字符串空间为 \(\mathcal X\)，模型输出

\[
s_\theta(x)\in(0,1),
\]

其中 \(1\) 表示 DGA，二分类 CE 为

\[
\ell_1(x;\theta)=-\log s_\theta(x),
\qquad
\ell_0(x;\theta)=-\log(1-s_\theta(x)).
\]

对干净恶意域名 \(x\)，令 \(\mathcal V(x)\subseteq\mathcal X\) 表示冻结威胁合同所允许的合法结果；令

\[
d_{\rm edit}(x,\widetilde x)
\]

表示与实际字符操作一致的编辑代价。预算 \(B\) 下的攻击集合定义为

\[
\boxed{
\Delta_B(x)
=
\left\{
\widetilde x\in\mathcal V(x):
d_{\rm edit}(x,\widetilde x)\le B
\right\}.
}
\tag{F1}
\]

这里把“RFC/语法有效性、长度边界、允许字符以及本地威胁合同的其他合法性条件”统一封装进 \(\mathcal V(x)\)，避免把没有实现的恶意语义条件偷偷写进数学定义。Drichel et al. 的 DGA 鲁棒性研究同样明确要求连续空间产生的攻击最终必须离散化为有效域名，并指出 DGA 威胁模型与图像感知相似性不同。citeturn29view0turn28view3

接着定义用户提出的支持约束概率族：

\[
\boxed{
\mathcal Q_B(x)
=
\left\{
Q\in\mathcal P(\mathcal X):
Q(\Delta_B(x))=1
\right\}.
}
\tag{F2}
\]

理想的单样本恶意鲁棒风险可以写成

\[
\boxed{
\rho_B^{\rm mal}(\theta;x)
=
\sup_{Q\in\mathcal Q_B(x)}
\mathbb E_{\widetilde x\sim Q}
[\ell_1(\widetilde x;\theta)].
}
\tag{F3}
\]

### 关键定理：这里的“分布级 follower”实际上坍缩为点级 follower

**定理 A（Dirac 坍缩）。** 对任意非空 \(\Delta_B(x)\)，

\[
\boxed{
\sup_{Q\in\mathcal Q_B(x)}
\mathbb E_Q[\ell_1(\widetilde x;\theta)]
=
\sup_{\widetilde x\in\Delta_B(x)}
\ell_1(\widetilde x;\theta).
}
\tag{T1}
\]

若 \(\Delta_B(x)\) 有限，则右边是最大值而非仅 supremum。

**证明。** 对任意 \(Q\in\mathcal Q_B(x)\)，

\[
\mathbb E_Q[\ell_1]
\le
\sup_{\widetilde x\in\Delta_B(x)}\ell_1.
\]

反向，任取 \(\varepsilon>0\)，取一个

\[
\widetilde x_\varepsilon
\]

满足

\[
\ell_1(\widetilde x_\varepsilon;\theta)
>
\sup_{\Delta_B}\ell_1-\varepsilon.
\]

令 \(Q=\delta_{\widetilde x_\varepsilon}\)，它显然属于 \(\mathcal Q_B(x)\)，故

\[
\sup_Q\mathbb E_Q\ell_1
\ge
\ell_1(\widetilde x_\varepsilon)
>
\sup_{\Delta_B}\ell_1-\varepsilon.
\]

令 \(\varepsilon\to0\) 即得等号。证毕。

这意味着，**按当前 \(\mathcal Q_B(x)=\{Q:\operatorname{supp}Q\subseteq\Delta_B(x)\}\) 的定义，不能把方法的理论差量写成“我们从样本级攻击升级到了分布级攻击”。两者数学上完全等价。**

这也说明“黑盒＋离散，所以攻击者只能表达为分布”不是成立的推论。DGA 的离散性确实削弱了直接连续梯度攻击的自然性，但 CharBot 本身就是一个无需目标分类器知识的具体黑盒域名扰动算法，MaskDGA 也以不知道目标架构和参数为黑盒条件；黑盒攻击仍可由点级或随机算法产生。citeturn25view6turn23academia1

因此，推荐的论文措辞应是：

> 分布符号用于统一表示**随机扰动提议核、有限候选采样以及后续课程分布路径**；在允许所有 Dirac 质量的纯支持约束族上，理想 worst-case distributional risk 与 pointwise robust risk 等价。

若未来真正要引入**非退化的分布级 follower**，必须额外限制 \(Q\)，例如生成器族 \(Q_\phi\)、熵/覆盖约束、密度比限制，或围绕参考分布的 Wasserstein 球。Sinha et al. 的真正 DRO 正是以围绕原始数据分布的 Wasserstein ambiguity set 来限制对抗分布，而不只是要求支持落在某个集合中。citeturn24view1 **这些约束目前没有出现在锁定实现中，因此不应加入当前方法定义。**

### 恶意侧鲁棒总体风险

设恶意干净分布为 \(P_{\rm mal}\)。理想母风险为

\[
\boxed{
\mathcal R_{\rm mal}^{\rm rob}(\theta;B)
=
\mathbb E_{x\sim P_{\rm mal}}
\left[
\sup_{\widetilde x\in\Delta_B(x)}
\ell_1(\widetilde x;\theta)
\right].
}
\tag{F4}
\]

它正是 Madry 型 \(\mathbb E[\max]\) 在离散字符域中的任务化版本；区别只在允许集合不再是连续 \(L_p\) 球，而是合法字符编辑集合。Madry et al. §2 明确把 attack model 定义为每个输入允许的 perturbation set，再形成外层 expectation、内层 maximum 的 saddle-point objective。citeturn28view0turn29view2

### 概念性的双侧母问题

若同样为真良性 \(x_b\sim P_{\rm ben}\) 定义允许的 FP-pressure 编辑集合

\[
\Delta_B^{\rm ben}(x_b),
\]

则可以定义**概念母问题**

\[
\boxed{
\begin{aligned}
\min_\theta\quad
\mathcal J_{\rm sym}(\theta)
={}&
\underbrace{
\mathbb E_{x_m\sim P_{\rm mal}}
\sup_{Q_m\in\mathcal Q_B^{\rm mal}(x_m)}
\mathbb E_{Q_m}\ell_1
}_{F_{\rm mal}(\theta)}
\\
&+
\lambda
\underbrace{
\mathbb E_{x_b\sim P_{\rm ben}}
\sup_{Q_b\in\mathcal Q_B^{\rm ben}(x_b)}
\mathbb E_{Q_b}\ell_0
}_{F_{\rm ben}(\theta)} .
\end{aligned}}
\tag{F5}
\]

其中良性侧最大化 \(\ell_0=-\log(1-s)\)，等价于把良性样本向更大的 DGA score 推，即 FP-pressure。

若两个内层的可行集是笛卡尔积、没有共享攻击预算或耦合约束，且 \(\lambda\ge0\)，则：

\[
\boxed{
\sup_{Q_m,Q_b}
\left[
F(Q_m)+\lambda G(Q_b)
\right]
=
\sup_{Q_m}F(Q_m)
+
\lambda\sup_{Q_b}G(Q_b).
}
\tag{T2}
\]

**证明。** 任意 \(Q_m,Q_b\) 都满足左式不超过右式，得“\(\le\)”；反向各取 \(\varepsilon\)-最优的 \(Q_m^\varepsilon,Q_b^\varepsilon\)，左式至少为右式减去 \((1+\lambda)\varepsilon\)，令 \(\varepsilon\to0\) 即得。有限集合下直接取两个最大化器即可。

所以两个内层在理想母问题上是可分离的。**但如果未来加入“恶意与良性共享总攻击预算”“同一个生成器参数必须同时服务两侧”等耦合约束，可分离性立即失效。**

### 当前组件二不是良性侧内层 max

这是本轮第二个必须纠正的形式化点。

当前代码没有从

\[
\Delta_B^{\rm ben}(x_b)
\]

生成良性扰动并求内层最大值；锁定实现是在**原始真良性样本**中，用当前模型的误报状态做三倍 CE 权重。因此，式 (F5) 可以作为“对称威胁母问题”，却**不能声称当前方法同时数值求解了两个内层 max**。

令

\[
h_{\bar\theta}(x)
=
\mathbf1[s_{\bar\theta}(x)\ge1/2],
\qquad
c_t=-\log(1-\tfrac12)=\log2.
\]

当前良性连续超额损失可写为

\[
\boxed{
\psi_b(\ell)
=
\ell+2(\ell-c_t)_+ .
}
\tag{F6}
\]

在不恰落在阈值上的样本，对当前快照有

\[
\nabla_\theta
\psi_b(\ell_0(x;\theta))
\big|_{\theta=\bar\theta}
=
[1+2h_{\bar\theta}(x)]
\nabla_\theta\ell_0(x;\bar\theta).
\tag{F7}
\]

因此组件二真正对应的是**固定决策阈值诱导的状态依赖良性尾部压力风险**，而不是另一个攻击生成器。

还可以将它解释为一种状态依赖分布重加权。若

\[
Z(\bar\theta)
=
\mathbb E_{P_{\rm ben}}
[1+2h_{\bar\theta}(X)]
\]

且定义

\[
\frac{dQ_{\rm FP,\bar\theta}}{dP_{\rm ben}}(x)
=
\frac{1+2h_{\bar\theta}(x)}
{Z(\bar\theta)},
\]

则

\[
\mathbb E_{P_{\rm ben}}
[(1+2h_{\bar\theta})\ell_0]
=
Z(\bar\theta)
\mathbb E_{Q_{\rm FP,\bar\theta}}\ell_0.
\tag{F8}
\]

这给组件二一个干净的“distribution pressure”解释，但 \(Q_{\rm FP,\bar\theta}\) 是由当前误报掩码**确定出来的 reweighting distribution**，不是一个被 \(\max_Q\) 优化出来的 adversarial distribution。

---

## 实现一致的离散双层优化

这部分是整个形式化链条最重要的“落地层”。建议在论文里把它作为真正对应代码的主优化问题，而把前面的 robust objective 称为“理想威胁目标”。

### 随机候选生成层

对主批中的第 \(i\) 个恶意干净域名 \(x_i\)，实际扰动器定义一个提议核

\[
P_B(\cdot\mid x_i),
\qquad
\operatorname{supp}P_B(\cdot\mid x_i)
\subseteq
\Delta_B(x_i).
\]

每批采样：

\[
\boxed{
\widetilde x_{ij}
\overset{\rm approx.\ iid}{\sim}
P_B(\cdot\mid x_i),
\qquad
j=1,\ldots,K,
\quad K=4.
}
\tag{F9}
\]

这里的“近似 iid”必须继续标为实现理想化，因为交接包说明 `perturb2` 使用共享随机流顺序采样、无去重，并未提供独立性的数学保证。

### binary violation 与组内中心化

在当前参数快照 \(\bar\theta_t=\theta_t\) 下：

\[
\boxed{
u_{ij}(\bar\theta_t)
=
\mathbf1
\left[
s_{\bar\theta_t}(\widetilde x_{ij})<\frac12
\right].
}
\tag{F10}
\]

组均值为

\[
\bar u_i=\frac1K\sum_{r=1}^K u_{ir},
\]

留一中心化优势：

\[
\boxed{
A_{ij}
=
u_{ij}
-
\frac1{K-1}\sum_{r\ne j}u_{ir}
=
\frac{K}{K-1}(u_{ij}-\bar u_i).
}
\tag{F11}
\]

注意，式 (F11) 在**同一组内部**与 \(u_{ij}\) 排序完全一致，但在**跨组比较**时，\(\bar u_i\) 改变了组与组之间的相对尺度。这正是上一轮分配律分析真正有意义的地方。

### 全局配额选择是一个精确的离散 follower

设候选总数为 \(nK\)，实际入选数量

\[
q=\min(Q,nK),\qquad Q=64.
\]

将选择写成二值变量：

\[
w_{ij}\in\{0,1\}.
\]

当前 global top-\(q\) 等价于求解：

\[
\boxed{
w_t^*
\in
\arg\max_{w}
\sum_{i,j}w_{ij}A_{ij}(\theta_t)
\quad
\text{s.t.}\quad
\sum_{i,j}w_{ij}=q,\quad
w_{ij}\in\{0,1\}.
}
\tag{F12}
\]

**命题 B（top-\(q\) 最优性）。** 按 \(A_{ij}\) 降序选前 \(q\) 个是式 (F12) 的精确解。

**证明。** 若一个可行解中存在已选 \(a\) 与未选 \(b\)，且 \(A_b>A_a\)，交换二者使目标增加 \(A_b-A_a>0\)。因此任何最优解均不能包含这样的逆序对，故必须由前 \(q\) 个最大 \(A\) 构成；同值并列时存在多个最优解。证毕。

这一步给你一个真正干净的“**内层优化问题**”：

> 当前攻击 follower 不是在域名空间直接最大化 CE，而是在随机候选池上最大化**组内中心化 binary violation 的固定总配额得分**。

这比把它硬写成 GRPO 或 \(\max_Q E\ell\) 更准确。

### 外层使用的是 CE，不是内层目标 \(A\)

设

\[
S_t
=
\{(i,j):w_{t,ij}^*=1\}.
\]

主批大小 \(B_0=128\)，且

\[
D_t=B_0+q.
\]

与锁定实现完全对齐的条件代理为

\[
\boxed{
\begin{aligned}
\widehat{\mathcal R}_t(\theta\mid\theta_t)
=
\frac1{D_t}
\Big[
&
\sum_{x\in\mathcal B_t^{\rm mal}}
\ell_1(x;\theta)
+
\sum_{x\in\mathcal B_t^{\rm ben}}
\ell_0(x;\theta)
\\
&
+
\sum_{(i,j)\in S_t}
\ell_1(\widetilde x_{ij};\theta)
+
2\sum_{x\in\mathcal B_t^{\rm ben}}
h_{\theta_t}(x)\ell_0(x;\theta)
\Big].
\end{aligned}}
\tag{F13}
\]

实际一步更新可抽象为

\[
\boxed{
\theta_{t+1}
=
\theta_t
-
\eta_t
\nabla_\theta
\widehat{\mathcal R}_t
(\theta\mid\theta_t)
\Big|_{\theta=\theta_t}.
}
\tag{F14}
\]

若实现使用带动量或自适应优化器，则式 (F14) 是“有效的一阶梯度输入”而非完整优化器状态递推；论文算法框应按真实优化器补齐状态变量。

### 这里没有朱式“反应梯度”

这是与参照论文最重要、也最值得明确写出的**负对应**。

由于

\[
u_{ij}(\theta)
=
\mathbf1[s_\theta(\widetilde x_{ij})<1/2]
\]

是阶跃函数，只要所有候选没有跨过分类阈值，\(u_{ij}\)、\(A_{ij}\) 和 \(w^*\) 在参数的一个局部邻域内都是常数。因此定义 selector value：

\[
V_A(\theta)
=
\max_{\substack{w\in\{0,1\}^{nK}\\
\mathbf1^\top w=q}}
\sum_{ij}w_{ij}A_{ij}(\theta),
\]

则除阈值切换和排序切换边界外，

\[
\boxed{
\nabla_\theta V_A(\theta)=0
\quad\text{a.e.}
}
\tag{F15}
\]

而入选样本的 CE 梯度一般满足

\[
\sum_{(i,j)\in S}
\nabla_\theta\ell_1(\widetilde x_{ij};\theta)
\ne0.
\]

所以：

\[
\boxed{
\nabla_\theta V_A
\ne
\nabla_\theta
\left[
\sum_{(i,j)\in S(\theta)}
\ell_1(\widetilde x_{ij};\theta)
\right]
}
\]

一般成立。

Madry §3.3 中利用的思路，是在**内层最大化的正是外层 adversarial loss**时，在该 maximizer 上计算 loss 对模型参数的梯度；论文还明确讨论了 Danskin 条件在深网中的近似适用问题。citeturn28view1 本方法的 inner objective 是 \(A\)，outer evaluation 是 CE，因此**不能借 Madry/Danskin 来声称式 (F14) 是 \(V_A\) 的梯度，更不能构造不存在的 \(\partial w^*/\partial\theta\) 二阶反应项。**

实现的准确定位应是：

\[
\boxed{
\textbf{离散状态选择}
\;+\;
\textbf{stop-gradient 条件代理下降}.
}
\]

这不是形式化“少一层”，而是算法结构本来就不同。

---

## 估计误差链：什么能证明，什么不能叫 robust-max 估计器

### 当前 top-\(q\) 不是 \(\max_Q\mathbb E\ell\) 的序统计量估计器

原任务要求“证明 K=4 采样＋中心化＋top-\(q\) 是 \(\max_Q E\ell\) 的序统计估计器”。**这个命题在锁定实现下不可证明，因为存在直接反例。**

取 \(K=4,q=1\)。

第一组：

\[
s(G_1)=(0.01,0.01,0.01,0.01).
\]

四个候选全部被骗过：

\[
u=(1,1,1,1),\quad \bar u=1,
\]

所以

\[
A=(0,0,0,0).
\]

其中任一候选恶意 CE：

\[
\ell_1=-\log0.01\approx4.605.
\]

第二组：

\[
s(G_2)=(0.49,0.9,0.9,0.9).
\]

于是

\[
u=(1,0,0,0),
\]

唯一成功候选具有

\[
A=1,
\]

但其 CE 仅为

\[
-\log0.49\approx0.713.
\]

global top-1 按 \(A\) 会选择第二组的 \(0.49\)，而候选池中真正最大 CE 是第一组的 \(0.01\)。

因此：

\[
\boxed{
\operatorname{TopQ}_A
\ne
\operatorname{TopQ}_{\ell}
}
\tag{F16}
\]

一般成立。

最严谨的统计表述应是：

> \(w^*\) 是 \(A\) 的 top-\(q\) 次序统计选择器，而最终训练量是“**按 \(A\) 排名、以 CE 评价**”的伴随统计量（rank-by-\(A\), evaluate-by-\(\ell\)）。

也就是说，当前实现不是 robust max 的 Monte Carlo 一致求解器；它是对理想 robust risk 的一个**有偏、预算受限、异质组竞争代理**。

### 理想最坏风险到实际保留风险的三缺口

尽管不能证明“一致估计”，仍然可以精确刻画“偏了多少以及偏在哪里”。

对第 \(i\) 个恶意干净样本定义：

\[
L_{i,\Delta}^*
=
\sup_{\widetilde x\in\Delta_B(x_i)}
\ell_1(\widetilde x;\theta),
\]

实际随机扰动核的支持最坏值：

\[
L_{i,P}^*
=
\operatorname*{ess\,sup}_{\widetilde x\sim P_B(\cdot|x_i)}
\ell_1(\widetilde x;\theta),
\]

有限 \(K\) 候选池最大值：

\[
M_{i,K}
=
\max_{j\le K}
\ell_1(\widetilde x_{ij};\theta).
\]

令

\[
N_i=|\{j:(i,j)\in S_t\}|
\]

为该组获得的全局配额。定义组内实际保留均值

\[
\widehat L_i
=
\begin{cases}
\dfrac1{N_i}
\sum_{j:(i,j)\in S_t}
\ell_1(\widetilde x_{ij};\theta),&N_i>0,\\[7pt]
0,&N_i=0.
\end{cases}
\]

则有**精确恒等式**

\[
\boxed{
L_{i,\Delta}^*-\widehat L_i
=
\underbrace{L_{i,\Delta}^*-L_{i,P}^*}_{\text{coverage gap}}
+
\underbrace{L_{i,P}^*-M_{i,K}}_{\text{search gap}}
+
\underbrace{M_{i,K}-\widehat L_i}_{\text{retention gap}}.
}
\tag{F17}
\]

证明只需加减 \(L_{i,P}^*,M_{i,K}\)。

三项含义分别是：

**覆盖缺口**：当前固定字符算子根本不会产生的攻击区域，增加 \(K\) 也救不了；

**搜索缺口**：提议核支持内存在强攻击，但 \(K\) 个随机样本没搜到；

**保留缺口**：已经搜到了高 CE 候选，但 binary-centered \(A\) 与 global quota 没保留它。

上面的反例正说明第三项可以在 \(K\) 搜索很充分时仍然很大。

### 全局还存在第四个组重加权项

理想等组 robust risk：

\[
R_\Delta^*
=
\frac1n\sum_iL_{i,\Delta}^*.
\]

实际入选变体均值：

\[
R_S
=
\frac1q
\sum_iN_i\widehat L_i.
\]

则：

\[
\boxed{
\begin{aligned}
R_\Delta^*-R_S
={}&
\frac1n
\sum_i
\left[
C_i+E_{i,K}+T_{i,K,Q}
\right]
\\
&+
\sum_i
\left(
\frac1n-\frac{N_i}{q}
\right)\widehat L_i .
\end{aligned}}
\tag{F18}
\]

最后一项是**有符号的 group-reweighting difference**，不是自动非负的“误差界”。

这点很重要：跨组 quota 本来就有意改变组权重，因此实际目标甚至不必是“等权平均每组最坏风险”的下逼近。论文应把这种偏置作为机制本身，而不是把它藏在“Monte Carlo max approximation”一句话里。

### \(K\) 的正确搜索预算语义

令

\[
\xi_i(\varepsilon)
=
\Pr_{\widetilde x\sim P_B(\cdot|x_i)}
\left[
\ell_1(\widetilde x)
\ge
L_{i,P}^*-\varepsilon
\right].
\]

若 \(K\) 个候选条件 iid，则

\[
\boxed{
\Pr
\left(
L_{i,P}^*-M_{i,K}>\varepsilon
\right)
=
[1-\xi_i(\varepsilon)]^K
\le
e^{-K\xi_i(\varepsilon)}.
}
\tag{F19}
\]

因此 \(K\) 具有很清楚的“**提议分布内搜索预算**”含义。

若仅有下界

\[
\xi_i(\varepsilon)\ge c\varepsilon^\tau,
\]

则可推出期望搜索缺口

\[
\mathbb E[E_{i,K}]
=
O(K^{-1/\tau})
\]

（需相应有界/可积条件）。

只有在近端点还具有相匹配的两侧条件，例如

\[
c_1\varepsilon^\tau
\le
\xi_i(\varepsilon)
\le
c_2\varepsilon^\tau,
\]

并补足必要正则条件，才适合写成

\[
\boxed{
\mathbb E[E_{i,K}]
=
\Theta(K^{-1/\tau}).
}
\]

所以交接包中的“\(\Theta(K^{-1/\tau})\)”应把两侧尾质量假设一并写出来，否则理论上最多支持 \(O(\cdot)\)。

### 与 V1–V3 的直接接口

| 核查 | 应验证的形式化命题 | 结果能说明什么 |
|---|---|---|
| **V1** | \(A\) 的七值层级、global top-\(q\) 与式 (F12) 一致；记录 \(N_i\)、零优势并列簇 | 实现是否确实在优化定义的 discrete follower |
| **V1-反例审计** | 同候选池比较 `top-A`、`top-CE`、uniform；记录真实最大 CE 被保留率 | 量化 retention gap，而非证明 top-A≈max-CE |
| **V2** | 三倍 FP 权重与式 (F7) 的梯度逐项一致；阈值点单独审计 | 证明 benign 组件是 excess-risk pressure，而不是 benign attack max |
| **V3** | 对每组数值验证式 (F17)，全局验证式 (F18) | 把性能差异拆到 coverage/search/retention/reweighting |
| **V3-K** | 固定提议核改变 \(K\)，估计 \(\xi_i(\varepsilon)\) 与 search gap | 判断幂律尾假设是否有经验支持 |
| **V3-Q** | 改变 \(Q\)，重放 \(N_i/q\) 与 retention/reweighting | 验证跨组预算竞争的真实作用 |

这些验证均可在源期、冻结已有候选/模型条件下完成，不需要把未来目标年份引入任何设计。

---

## 课程路径：从编辑预算到训练分布的几何轨迹

### 文献锚点先纠正作者归属

本轮公开原文检索**未核到与交接包所述 Wasserstein curriculum framework 相匹配的 “Shi & Liu” 论文**。可核验且与描述高度一致的是 **Changho Shin 与 David Alvarez-Melis，COLM 2026，*Curriculum Learning as Transport: Understanding Curricula with Wasserstein Geodesics***。该文 §3.1 将 curriculum 明确定义为离散难度层上的训练采样分布序列，并进一步表示成连续分布路径 \(\{P_t\}_{t\in[0,1]}\) 与独立 schedule \(t_k\)；§3.2 默认使用 \(t_k=k/T\)。citeturn27view0turn28view4turn28view5

检索到的 Lin Shi、Qiyuan Liu、Bei Peng 的 CURO 是 MARL 中为 relative overgeneralization 设计的 curriculum，并非上述 Wasserstein transport framework。citeturn30academia1 因此在本地全文核清之前，建议不要写“Shi & Liu 框架”；可暂记“**Shin & Alvarez-Melis transport view，来源待本地最终题录确认**”。

### 预算层不是单个 \(B(t)\)，而可以提升为预算分布

令离散攻击难度层为

\[
\mathcal M
=
\{m_1,\ldots,m_L\}.
\]

例如与当前算子对应的层可以表示为“1 位、2 位、半替换”，但具体 \(m_\ell(x)\) 应由真实长度及攻击算子定义，而不是强行用统一整数表示。

每个层对应提议核：

\[
P_m(d\widetilde x\mid x),
\qquad
\operatorname{supp}P_m
\subseteq
\Delta_m(x).
\]

在训练进度 \(t\) 上令

\[
\pi_t\in\Delta^{L-1}
\]

为预算/难度层分布。由此得到真实的恶意增广联合分布：

\[
\boxed{
G_{\pi_t}(dx,d\widetilde x)
=
P_{\rm mal}(dx)
\sum_{m\in\mathcal M}
\pi_t(m)
P_m(d\widetilde x\mid x).
}
\tag{F20}
\]

单一调度

\[
B(t)=m_t
\]

只是退化情形：

\[
\boxed{
\pi_t=\delta_{m_t}.
}
\tag{F21}
\]

这与 Shin & Alvarez-Melis 的“训练时刻由难度层采样分布决定、课程是这些分布的路径与遍历 schedule”完全同构，但这里的 difficulty level 被任务化为**域名字符扰动预算**。citeturn28view4turn28view5

### Hamming 嵌套耦合下的相邻预算漂移界

对固定域名 \(x\)，长度为 \(\ell_x\)，定义归一化 Hamming cost：

\[
c_x(z,z')
=
\frac{d_H(z,z')}{\ell_x}.
\]

假设两个预算 \(m\le m'\) 可以由同一个随机编辑序列耦合：\(X_m\) 使用前 \(m\) 次字符操作，\(X_{m'}\) 在同一前缀基础上再执行 \(m'-m\) 次操作。

每个附加字符操作至多改变一个位置，因此逐样本：

\[
d_H(X_m,X_{m'})
\le
m'-m.
\]

于是该具体 coupling 给出：

\[
\boxed{
W_1
\left(
P_m(\cdot\mid x),
P_{m'}(\cdot\mid x)
\right)
\le
\frac{|m-m'|}{\ell_x}.
}
\tag{T3}
\]

**证明。** Wasserstein 距离是所有耦合的最小期望代价。上述共享随机编辑流已经构造出一个合法 coupling \(\gamma\)，且

\[
\mathbb E_\gamma[c_x(X_m,X_{m'})]
\le
|m-m'|/\ell_x.
\]

对所有 coupling 取 infimum 即得。

这里必须加上一个很重要的边界：

\[
\boxed{
\operatorname{supp}P_m\subseteq\Delta_m,\ 
\operatorname{supp}P_{m'}\subseteq\Delta_{m'}
\quad
\text{本身并不推出 }
W_1\le|m-m'|/\ell.
}
\]

若没有共享前缀/嵌套生成机制，一般只能通过三角关系得到更松的量级，例如在都围绕 \(x\) 的 Hamming 球中：

\[
d_H(X_m,X_{m'})
\le m+m'.
\]

所以交接包中的

\[
W_1(Q_m,Q_{m'})
\le|m-m'|/\ell
\]

必须把**nested/shared-randomness coupling**写进假设，不能作为所有支持约束分布族的无条件结论。

### 从预算空间漂移传到真实增广分布

定义预算层之间的成本

\[
\bar c(m,m')
=
\mathbb E_{x\sim P_{\rm mal}}
\left[
\frac{|m(x)-m'(x)|}{\ell_x}
\right],
\tag{F22}
\]

或者在所有域名定长时退化为 \(|m-m'|/\ell\)。

设 \(W_{1,\bar c}(\pi,\pi')\) 是预算层空间上的 Wasserstein 距离。若每对 \(m,m'\) 都存在满足式 (T3) 的条件 coupling，则：

\[
\boxed{
W_1(G_\pi,G_{\pi'})
\le
W_{1,\bar c}(\pi,\pi').
}
\tag{T4}
\]

**证明。** 取 \(\pi,\pi'\) 间一个最优层级 coupling \(\Gamma(m,m')\)。先采样 \((m,m')\sim\Gamma\)，再共享同一个 \(x\sim P_{\rm mal}\)，最后采用对应的嵌套字符编辑 coupling 产生 \((\widetilde X_m,\widetilde X_{m'})\)。这构成 \(G_\pi,G_{\pi'}\) 的一个合法联合分布，且条件期望代价不超过 \(\bar c(m,m')\)。积分后总成本不超过

\[
\mathbb E_\Gamma[\bar c(m,m')]
=
W_{1,\bar c}(\pi,\pi').
\]

真实 Wasserstein 距离是所有联合分布成本的 infimum，故成立。证毕。

这条式子的意义很强：

> **课程层不需要直接在 24M 参数模型空间里讨论“难度连续性”；只要预算层的分布路径足够平滑，就能在上述耦合条件下控制输入增广分布相邻阶段的漂移上界。**

### “最小相邻漂移”可以正式写成一个课程优化问题

Shin & Alvarez-Melis 提供的是“curriculum = difficulty-distribution path + schedule”的运输几何框架；把“最小化相邻漂移”写成显式最优化目标，是本方法的进一步构造，而不是他们原文已经替你证明的 DGA 定理。其 §3.1 确实将课程写成分布路径，并用 Wasserstein geometry 控制难度层之间的移动。citeturn28view4

设共有 \(T\) 个训练阶段，固定起点 \(\pi_0\) 与终点 \(\pi_T\)。可以定义：

\[
\boxed{
\begin{aligned}
\min_{\pi_1,\ldots,\pi_{T-1}}
\quad&
\sum_{t=0}^{T-1}
W_{1,\bar c}^2(\pi_t,\pi_{t+1})
\\
\text{s.t.}\quad&
\pi_t\in\Delta^{L-1},
\\
&
\mathbb E_{\pi_{t+1}}[m]
\ge
\mathbb E_{\pi_t}[m],
\\
&
\text{预注册的 exposure / endpoint 约束}.
\end{aligned}}
\tag{F23}
\]

如果记

\[
d_t=W_{1,\bar c}(\pi_t,\pi_{t+1}),
\]

由 Cauchy–Schwarz 与 Wasserstein 三角不等式：

\[
\sum_{t=0}^{T-1}d_t^2
\ge
\frac1T
\left(\sum_td_t\right)^2
\ge
\boxed{
\frac1T
W_{1,\bar c}^2(\pi_0,\pi_T).
}
\tag{T5}
\]

在存在 constant-speed geodesic 且各阶段取等距离点时，该下界可以达到。

结合式 (T4)：

\[
W_1(G_{\pi_t},G_{\pi_{t+1}})
\le d_t,
\]

所以式 (F23) 具有一个非常明确的任务语义：

\[
\boxed{
\text{在固定起终攻击难度与暴露预算下，
让相邻阶段的增广输入分布变化尽可能平滑。}
}
\]

这比仅写一个手工 \(B(t)\) 有更完整的优化对象。

**但当前交接包只说明已有 1 位／2 位／半替换攻击层，并没有说明代码已经实现动态课程调度。** 因此式 (F20)–(F23) 如果尚未存在于实际训练中，应明确标为“第二阶段课程扩展/待实现组件”，不能写成已经实现的方法机制。

---

## 与参照论文的逐层对位

| 参照论文链条 | 本方法最合适的对应 | 数学地位 | 关键差异 |
|---|---|---|---|
| 式 3.3：\(\min_\theta\) 外层＋\(\delta^*(\theta)=\arg\max\) 内层 | 式 (F1)–(F5)：编辑集合与理想鲁棒母问题；式 (F12)–(F14)：实际 discrete follower＋conditional outer surrogate | 前者是定义/理想目标；后者与锁定实现一致 | **实际 follower 最大化 \(A\)，不是 CE** |
| 式 3.7–3.8：课程可行域 \(S_t\) | 式 (F20)–(F23)：预算层核 \(P_m\)、层分布 \(\pi_t\)、增广分布 \(G_{\pi_t}\)、平滑课程路径 | 课程扩展构造；若代码未实现则不能称现有组件 | 可行域从“样本约束集”变成“扰动预算分布路径” |
| 式 3.11–3.12：全导数 = 直接项＋反应项 | 式 (F15)：binary selector 局部常值，selector reaction derivative 为 0 a.e.、切换面不可微；实际采用式 (F14) stop-gradient 条件代理 | **严格负对应** | 不应仿造二阶反应梯度 |
| 式 3.13–3.14：展开内层优化递推 | 式 (F9)–(F12) 的有限随机搜索＋精确 top-\(q\)，再由 (F17)–(F19) 分解近似缺口 | 严格离散求解＋概率近似分析 | 没有可微 inner trajectory 可展开 |
| 式 3.15：混合二阶更新 | 本方法无对应二阶项；以 (F17)–(F23) 的“误差链＋运输课程”提供理论密度 | 明确无此组件 | **不能为对齐章节形态凭空创造二阶更新** |

这张表体现了最重要的写作原则：

> **对标的是“优化问题被逐层拆开”的论证密度，而不是把参照论文的每一种数学工具复制过来。**

你的链条同样可以从母问题一路落到算法更新，而且多了一层“理想 robust target 与实际 selector surrogate 之间的可量化缺口”。这比写一个形式上漂亮但代码根本没有计算的 reaction term 更经得住审查。

从方法节叙事上，建议形成以下连续公式链：

\[
(F1)\to(F4)
\quad
\text{威胁集合与理想鲁棒风险}
\]

\[
\Downarrow
\]

\[
(F9)\to(F12)
\quad
\text{有限候选与离散内层 follower}
\]

\[
\Downarrow
\]

\[
(F13)\to(F15)
\quad
\text{条件代理外层更新及不可微边界}
\]

\[
\Downarrow
\]

\[
(F17)\to(F19)
\quad
\text{理想 max 与实现之间的近似误差}
\]

\[
\Downarrow
\]

\[
(F20)\to(F23)
\quad
\text{攻击预算的分布课程路径}.
\]

这就是当前方法最自然的“优化问题形式化链”。

---

## 证据等级、可核验推论与理论边界

### 哪些是严格证明

| 结果 | 状态 | 所需假设 |
|---|---|---|
| 支持约束分布族的 Dirac 坍缩，式 (T1) | **严格证明** | \(\Delta_B(x)\ne\varnothing\)；有限时 max 可达 |
| 双侧独立内层的可分离性，式 (T2) | **严格证明** | 可行集 Cartesian、\(\lambda\ge0\)、无共享耦合约束 |
| global top-\(q\) 是 \(A\)-score 离散内层的精确解 | **严格证明** | 固定候选池与分数；并列允许多解 |
| top-\(A\) 并非 top-CE / robust-max estimator | **严格反例** | 当前二值 \(u\)、当前中心化定义 |
| benign ×3 与 excess-loss 梯度等价 | **严格局部结果** | 当前参数掩码；阈值外；阈值点取与 `>=` 一致的上端次梯度 |
| selector value gradient = 0 a.e. 而 CE gradient 可非零 | **严格局部结果** | 分类状态与 top-\(q\) 排序在局部不切换 |
| 三缺口式 (F17) | **严格恒等式** | 变量按定义 |
| 全局四项式 (F18) | **严格恒等式** | \(\widehat L_i\) 按定义 |
| iid 搜索尾概率式 (F19) | **条件严格证明** | 候选条件 iid |
| nested Hamming coupling 的 \(W_1\) 上界，式 (T3) | **条件严格证明** | 两预算来自同一编辑序列的嵌套耦合 |
| level-distribution 到 augmentation-distribution 的 contraction，式 (T4) | **条件严格证明** | 每对层存在上述条件 coupling |
| 相邻平方漂移下界，式 (T5) | **严格证明** | Wasserstein 为度量；等号另需 geodesic 条件 |

### 哪些只是定义或构造

\(\mathcal Q_B(x)\) 是威胁模型定义；式 (F5) 的良恶对称双内层是**理想母问题**；式 (F8) 的 \(Q_{\rm FP,\bar\theta}\) 是对三倍良性权重的**分布重解释**；式 (F23) 是基于 transport view 提出的**课程设计问题**，不是已有实现事实。

Sinha et al. 提供了真正 DRO ambiguity set 的成熟参考，而 Shin & Alvarez-Melis 提供了“课程作为离散难度层训练分布路径＋schedule”的公开原始依据；两者支持这里的建模语言，但不替代本方法自身的实现证明。citeturn24view1turn28view4turn28view5

### 哪些必须后续数值核查

候选“近似 iid”是否足够；实际 top-\(A\) 对最大 CE 的 retention rate；\(\xi_i(\varepsilon)\) 是否真的服从足以支撑 \(\Theta(K^{-1/\tau})\) 的两侧幂律；不同 \(Q\) 下组配额 \(N_i\) 如何变化；三倍良性项与恶意项在实际参数空间是否存在共同下降方向；以及 1 位→2 位→半替换能否由真实 `perturb2` 构造成式 (T3) 所需的嵌套共享随机流。以上都属于 V1–V3 或新增 V4 的源期核查对象，不属于本轮已证明事实。

建议新增：

\[
\boxed{\text{V4：预算课程耦合核查}}
\]

在同一合法源期域名上，以相同随机编辑流同时构造两个预算结果，直接检查

\[
\frac{d_H(\widetilde x_m,\widetilde x_{m'})}{\ell_x}
\le
\frac{|m-m'|}{\ell_x}
\]

是否逐样本成立；若现有 1 位、2 位、半替换操作不是同一随机过程的嵌套前缀，则不能使用式 (T3)，课程层需换成实际可建立的 transport cost。

### 明确不能写进论文的四个强断言

**不能写：**“由于 DGA 是离散黑盒问题，因此攻击者必须建模为分布级 follower。”  
应写：随机分布表示是便于表达 proposal 与 curriculum 的建模选择；纯支持约束下它与 pointwise max 等价。CharBot 与 MaskDGA 本身也说明黑盒离散攻击完全可以由具体扰动算法定义。citeturn25view6turn23academia1

**不能写：**“当前双侧方法在两侧都求解最坏扰动分布。”  
应写：恶意侧有扰动候选与离散 follower；良性侧当前是决策阈值诱导的 state-dependent excess-risk reweighting。

**不能写：**“K=4＋group-relative top-\(q\) 是 \(\max_QE\ell\) 的 Monte Carlo estimator。”  
应写：它是 \(A\)-score 的有限样本预算优化器，CE 是 selector 的伴随评价量；式 (F17)–(F19) 刻画它与理想 max 的差距。

**不能写：**“像参照论文一样存在 reaction gradient / second-order unrolling。”  
应写：binary follower 的响应映射分段常值，反应导数 a.e. 为零、边界不可微；当前算法明确采用条件代理的一阶更新。Madry 型内层-loss/外层-loss 同目标的 Danskin 论证也不能直接迁移到“内层 \(A\)、外层 CE”的本方法。citeturn28view1

---

## 来源、精确位置与未决问题

| 原始来源 | 核验位置 | 本报告使用点 | 核验状态 |
|---|---|---|---|
| Aleksander Madry, Aleksandar Makelov, Ludwig Schmidt, Dimitris Tsipras, Adrian Vladu, *Towards Deep Learning Models Resistant to Adversarial Attacks*, ICLR 2018 | §2 “An Optimization View on Adversarial Robustness”，论文 p.3，式 (2.1)；§3.3，p.8 | attack set → inner max → outer min；内层 maximizer 上外层梯度/Danskin 讨论 | **全文核验** citeturn28view0turn28view1 |
| Aman Sinha, Hongseok Namkoong, Riccardo Volpi, John Duchi, *Certifying Some Distributional Robustness with Principled Adversarial Training*, ICLR 2018 | §1，式 (1)、(2a–b)；§2 Proposition 1，式 (5)–(7) | 真正 DRO 需要结构化 ambiguity set；Wasserstein 分布鲁棒与点级 robust surrogate 的关系 | **全文核验** citeturn24view1 |
| Arthur Drichel, Marc Meyer, Ulrike Meyer, *Towards Robust Domain Generation Algorithm Classification*, ASIA CCS 2024 | §1，论文 pp.1–2；§2.4，pp.3–4；§3 Threat Model 起始处 | DGA 离散输入、embedding 攻击离散化与合法域名约束；DGA threat model 与图像小扰动模型不能机械等同 | **全文核验** citeturn29view0turn29view1turn28view3 |
| Jonathan Peck et al., *CharBot: A Simple and Effective Method for Evading DGA Classifiers*, 2019 | Abstract | 无需目标分类器知识的黑盒 DGA attack，反驳“黑盒必然只能分布化”的强论断 | **原始摘要核验** citeturn25view6 |
| Lior Sidi, Asaf Nadler, Asaf Shabtai, *MaskDGA: A Black-box Evasion Technique Against DGA Classifiers and Adversarial Defenses*, 2019 | Abstract | 无目标架构/参数知识的字符级 DGA 黑盒扰动 | **原始摘要核验** citeturn23academia1 |
| Changho Shin, David Alvarez-Melis, *Curriculum Learning as Transport: Understanding Curricula with Wasserstein Geodesics*, COLM 2026 | §3.1，论文 p.3；§3.2，p.4 | curriculum = difficulty-level sampling-distribution path + schedule；Wasserstein path与 pacing | **全文核验** citeturn28view4turn28view5 |

关于“Shi & Liu 框架”，本轮截至 **2026-09-11** 的公开检索没有核实到与交接包描述相符的该作者组合。可核验的 transport curriculum 来源是 **Shin & Alvarez-Melis, COLM 2026**；搜索到的 Shi–Liu curriculum 工作 CURO 属于 MARL relative overgeneralization，主题不同。citeturn25view4turn30academia1 这一题录归属应在本地最终全文复核时确认，当前不能自行改写冻结文献合同。

**最终推荐的章节形式化主线**可压缩成一句：

\[
\boxed{
\underbrace{\Delta_B\ \&\ \mathcal R_{\rm rob}}_{\text{理想威胁目标}}
\;\Rightarrow\;
\underbrace{P_B,\ u,\ A,\ w^*}_{\text{随机搜索与离散 follower}}
\;\Rightarrow\;
\underbrace{\widehat{\mathcal R}(\theta\mid\bar\theta)}_{\text{实际条件代理}}
\;\Rightarrow\;
\underbrace{C+E+T+\text{reweight}}_{\text{理想—实现缺口}}
\;\Rightarrow\;
\underbrace{\pi_t,\ G_{\pi_t},W_1}_{\text{预算课程路径}}
}
\]

它与参照论文同样具有从“训练方法是什么优化问题”一路推到“实际算法如何近似该问题”的完整链条，但没有伪造不存在的二阶反应项。当前最强的理论价值恰恰在于：**明确区分理想 robust max、binary-centered 配额 follower 和实际 CE 更新，并给出它们之间可以逐项核验的误差与运输关系。**

以上全部为**外部候选形式化**；Dirac 坍缩、可分离性、top-\(q\) 最优性、反例、缺口恒等式及条件 Wasserstein 界可独立数学复核，但方法原创性、实现逐行对应、iid/尾部/嵌套耦合假设以及任何性能解释，仍须由发起方在本地全文和源期实验中独立复核后方可进入台账。