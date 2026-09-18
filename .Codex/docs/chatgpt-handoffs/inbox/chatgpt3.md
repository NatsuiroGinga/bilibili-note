# 三条可核验的理论结果：选择收益分解、双风险共同下降与搜索预算误差

**状态：外部候选数学稿，待本地全文、实现对应关系与实验独立复核。以下给出完整陈述和证明，但不将“本次推导成立”直接等同于“已完成学术首创性核验”。**

| 返回字段        | 实际情况                                                                           |
| --------------- | ---------------------------------------------------------------------------------- |
| `actual_model`  | GPT-6 Astra Pro                                                                    |
| `actual_effort` | 后端推理档位未提供可核验值                                                         |
| `actual_mode`   | 当前对话内数学推导与公开原始文献核对                                               |
| `used_apps`     | GitHub：两个白名单文件的定点读取均返回 404；Web：核对相关原始论文                  |
| 实现与实验边界  | 未读取白名单外仓库内容，未运行代码，未独立验证实验结果；实现分析依据本轮自包含描述 |

## 一、先给结论：三条结果可以写出来，但原命题必须有三处修正

| 原计划         | 能够成立的版本                                                                               | 不能直接保留的表述                                         |
| -------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 选择算子谱系   | **跨组预算收益减去资格剔除损失、排序损失**的精确分解；二点分数模型下有闭式期望及严格优势区域 | 中心化全局 top-q 必然比逐组选择捕获更多被骗过样本          |
| 双侧梯度近正交 | 在加权 Gram 相关性、权重区间和步长条件下，**两项代理风险相对更新前共同下降**                 | 近正交足以保证联合更新在两个指标上均优于两个单独更新       |
| 预算—缺口收缩  | 有限上端点分布下的精确缺口公式、非渐近上下界及高概率预算界                                   | 把无界分布的“指数尾、重尾”直接写成对有限 supremum 的收缩率 |

**最有方法针对性的理论核心是定理 1 的收益分解。定理 2 是具有任务化系数和可测条件的共同下降命题；定理 3 属于标准次序统计理论的任务化应用，不宜再包装成一个新的极值理论。**

另有一个必须纠正的近邻对应关系：BiB 原文的 CP 每组选择一个样本，但 GS 会从整个候选批次中保留误分类样本，允许同一原样本贡献零个或多个变体。因此，下面的 per-group top-r 是一个**明确规定的分析参照算子**，不能标成“BiB 整体算法的等价形式”。BiB 的 GS 虽然没有这里规定的固定全局配额与中心化排序，但已经不是固定逐组配额。原文位置为 §4.3、式（3）—（5）。([arXiv][1])

---

# 二、定理 1：预算重分配收益与中心化选择损失的精确分解

## 2.1 数学对象与编号假设

固定检测器参数 \(\theta\)，只分析**这一次候选生成与选择**，不先推断后续训练效果。

**假设 T1.1：共同候选池。**
有 \(n\) 个干净恶意样本，每个生成 \(K\ge 2\) 个变体。违规量为

$$
u_{ik}\in[0,1],\qquad i=1,\ldots,n,\quad k=1,\ldots,K.
$$

以固定违规阈值 \(t\) 定义当前已经骗过检测器的指示量

$$
Z_{ik}=\mathbf 1\{u_{ik}>t\},\qquad
S_i=\sum_{k=1}^{K}Z_{ik},\qquad
S=\sum_{i=1}^{n}S_i.
$$

阈值上的判定按本地合同处理；下文不依赖采用哪一种固定平局规则。

**假设 T1.2：对齐选择预算。**
取整数 \(r\in\{1,\ldots,K\}\)，总预算

$$
q=nr.
$$

三个主要算子使用相同候选池：

- \(\mathsf U_r\)：每组无放回均匀选择 \(r\) 个；
- \(\mathsf P_r\)：每组按原始 \(u\) 选择最大的 \(r\) 个；
- \(\mathsf A_q\)：按中心化优势跨组排序，至多选 \(q\) 个。

为区分“预算机制”和“中心化机制”，另外引入一个必要的参照：

$$
\mathsf R_q：
\text{按原始 }u\text{ 在全部 }nK\text{ 个候选中选择 top-}q.
$$

**\(\mathsf R_q\) 不等于你们的 \(\mathsf A_q\)。** 全局大损失选择本身已有成熟的 top-k 聚合目标研究，不能仅凭出现全局排序就主张首创。([arXiv][2])

若真实 \(q\) 不能写成 \(nr\)，需要预先规定非均匀或随机化逐组配额；不能拿“每组一个、总计 \(n\) 个”直接与“全局 64 个”作未对齐比较。

**假设 T1.3：中心化规则。**

$$
A_{ik}
=
u_{ik}
-\frac{1}{K-1}\sum_{\ell\ne k}u_{i\ell}
=
\frac{K}{K-1}(u_{ik}-\bar u_i).
$$

下面首先采用此前描述中的**正优势资格条件 \(A\_{ik}>0\)**。若本地实现没有这个条件，资格集合需要相应修改，不能直接套用后面的二点分数闭式。

记

$$
H=\sum_{i,k}Z_{ik}\mathbf 1\{A_{ik}>0\},
$$

即具有选择资格的被骗过候选数。令 \(C_U,C_P,C_R,C_A\) 分别为四个算子实际捕获的被骗过候选数。

定义两个选择损失：

$$
L_{\mathrm{elig}}
=
\min(q,S)-\min(q,H),
$$

$$
L_{\mathrm{rank}}
=
\min(q,H)-C_A.
$$

前者是资格剔除造成的损失；后者是合格池内的中心化排序未优先选中被骗过候选造成的损失。二者均非负。

如果实现先过滤 \(Z=1\)，再对其中的正优势候选排序，则 \(L_{\mathrm{rank}}=0\)，但 \(L_{\mathrm{elig}}\) 仍可能非零。

---

## 2.2 定理 1A：任意候选池上的精确分解

定义逐组配额的缺额与溢出量

$$
D=\sum_{i=1}^{n}(r-S_i)_+,
\qquad
E=\sum_{i=1}^{n}(S_i-r)_+.
$$

则对任意固定候选池：

$$
\boxed{
\mathbb E[C_U\mid S_1,\ldots,S_n]
=
\frac rK S
}
\tag{1}
$$

$$
\boxed{
C_P=q-D,\qquad
C_R=C_P+\min(D,E)
}
\tag{2}
$$

并且

$$
\boxed{
C_A-C_P
=
\min(D,E)-L_{\mathrm{elig}}-L_{\mathrm{rank}}.
}
\tag{3}
$$

因此，

$$
\boxed{
\mathbb E C_A>\mathbb E C_P
\iff
\mathbb E\min(D,E)
>
\mathbb E L_{\mathrm{elig}}+\mathbb E L_{\mathrm{rank}}.
}
\tag{4}
$$

式（4）是中心化跨组配额严格优于逐组选择的**精确充要条件**，而不是无条件优势声明。

### 证明

均匀选择时，每个候选被选中的概率为 \(r/K\)。由期望线性性，

$$
\mathbb E[C_U\mid S_1,\ldots,S_n]
=
\sum_i\frac rK S_i.
$$

由于被骗过状态由原始违规量的阈值决定，逐组原始 top-r 会尽可能先选被骗过样本，因此

$$
C_P=\sum_i\min(r,S_i)
=\sum_i\bigl[r-(r-S_i)_+\bigr]
=q-D.
$$

又因为

$$
S_i=r-(r-S_i)_++(S_i-r)_+,
$$

求和得到

$$
S=q-D+E.
$$

原始全局 top-q 能捕获的被骗过样本数恰为

$$
C_R=\min(q,S)
=\min(q,q-D+E)
=q-D+\min(D,E).
$$

故

$$
C_R-C_P=\min(D,E).
$$

另一方面，按两个损失的定义，

$$
C_R-C_A
=
\bigl[\min(q,S)-\min(q,H)\bigr]
+
\bigl[\min(q,H)-C_A\bigr]
=
L_{\mathrm{elig}}+L_{\mathrm{rank}}.
$$

两式相减即得式（3）；取期望即得式（4）。证毕。

### 这一结果解释了什么

它把“跨组配额竞争”具体化为：

> 某些组没有足够的被骗过候选，留下缺额 \(D\)；另一些组具有超过逐组配额的被骗过候选，形成溢出 \(E\)。取消逐组配额最多可利用其中的 \(\min(D,E)\)。

但中心化不是免费附加项。它可能剔除有用候选，也可能将尚未骗过的“组内相对异常值”排在已经骗过的候选之前。

---

## 2.3 定理 1B：两类型模型下的闭式期望

增加以下假设。

**假设 T1.4：两类型独立候选。**
有 \(n_h=\pi n\) 个高骗过率组，\(n_l=(1-\pi)n\) 个低骗过率组，组数均为整数。条件于固定组类型，

$$
Z_{ik}\overset{\mathrm{ind}}{\sim}
\begin{cases}
\operatorname{Bernoulli}(p_h),&i\in\mathcal H,\\
\operatorname{Bernoulli}(p_l),&i\in\mathcal L.
\end{cases}
$$

其中 \(0\le p_l\le p_h\le1\)。

**假设 T1.5：用于中心化闭式的二点分数模型。**

$$
u_{ik}=a+(b-a)Z_{ik},
\qquad 0\le a<t<b\le1.
$$

这是额外的理想化假设：**只知道骗过率，不能确定连续中心化分数的排序分布。**

定义

$$
b_s(p)=\binom Ks p^s(1-p)^{K-s},
$$

$$
\beta_r(p)=\sum_{s=0}^{K}\min(r,s)b_s(p).
$$

对概率生成多项式 \(P(z)\)，定义有限和

$$
\mathcal T_q[P]
=
\sum_{s\ge0}\min(q,s)[z^s]P(z)
=
q-\sum_{s=0}^{q-1}(q-s)[z^s]P(z).
$$

再定义

$$
G_p(z)=(1-p+pz)^K,
$$

$$
H_p(z)
=
(1-p)^K+p^K
+\sum_{s=1}^{K-1}b_s(p)z^s.
$$

则有以下闭式：

$$
\boxed{
\mathbb E C_U
=
q\bigl[\pi p_h+(1-\pi)p_l\bigr]
}
\tag{5}
$$

$$
\boxed{
\mathbb E C_P
=
n\bigl[\pi\beta_r(p_h)+(1-\pi)\beta_r(p_l)\bigr]
}
\tag{6}
$$

$$
\boxed{
\mathbb E C_R
=
\mathcal T_q
\!\left[G_{p_h}(z)^{n_h}G_{p_l}(z)^{n_l}\right]
}
\tag{7}
$$

$$
\boxed{
\mathbb E C_A
=
\mathcal T_q
\!\left[H_{p_h}(z)^{n_h}H_{p_l}(z)^{n_l}\right].
}
\tag{8}
$$

这些都是有限和意义上的闭式；没有隐藏的未知分布积分。

### 证明

前两式由

$$
\mathbb E S_i=Kp_i,\qquad C_P=\sum_i\min(r,S_i)
$$

直接得到。

总被骗过候选数 \(S\) 的概率生成函数为

$$
\mathbb E z^S
=
G_{p_h}(z)^{n_h}G_{p_l}(z)^{n_l}.
$$

结合 \(C_R=\min(q,S)\)，得到式（7）。

对于中心化选择，当 \(Z_{ik}=1\) 时，

$$
A_{ik}
=
(b-a)\frac{K-S_i}{K-1};
$$

当 \(Z_{ik}=0\) 时，

$$
A_{ik}
=
-(b-a)\frac{S_i}{K-1}.
$$

所以正优势候选全部是被骗过候选，但只有

$$
1\le S_i\le K-1
$$

的组能提供正优势候选。定义

$$
T_i=S_i\mathbf 1\{S_i<K\}.
$$

则

$$
C_A=\min\left(q,\sum_iT_i\right).
$$

\(T_i=0\) 的概率为 \((1-p_i)^K+p_i^K\)，其余取值 \(s=1,\ldots,K-1\) 的概率为 \(b_s(p_i)\)，故生成函数为 \(H_{p_i}\)。独立相乘并应用 \(\mathcal T_q\)，得到式（8）。证毕。

**注意：二点模型中“全成功组被剔除”，不代表真实连续分数中所有全成功组都会被剔除。真实组内分数存在差异时，仍可能有正优势候选。**

---

## 2.4 三者严格排序的条件与明确边界

### 原始全局配额参照的排序

对 \(1\le r<K\)，

$$
\frac rK S_i\le \min(r,S_i).
$$

当 \(0<S_i<K\) 时严格。因此

$$
\mathbb E C_U<\mathbb E C_P
$$

当且仅当至少有一组满足 \(0<p_i<1\)。

由定理 1A，

$$
\mathbb E C_P<\mathbb E C_R
\iff
\Pr(D>0,E>0)>0.
$$

在独立二项模型中，其等价条件为：存在不同组 \(i\ne j\)，使得

$$
p_i<1,\qquad p_j>0.
$$

这说明：

**即使所有组具有相同的内部骗过率 \(0<p<1\)，跨组原始配额也可能严格优于逐组配额。组间异质性不是这个优势的必要条件。** 有限采样本身就会产生“有的组不足、有的组溢出”。

### 中心化配额的精确条件

在二点模型下，

$$
\mathbb E C_U<\mathbb E C_P<\mathbb E C_A
$$

当且仅当：

$$
\exists i:\ 0<p_i<1
$$

以及

$$
\boxed{
\mathcal T_q
\!\left[H_{p_h}^{n_h}H_{p_l}^{n_l}\right]
>
n\bigl[\pi\beta_r(p_h)+(1-\pi)\beta_r(p_l)\bigr].
}
\tag{9}
$$

式（9）给出完整的有限样本判定式。一般情形不应编造一个简单的单调 \(\pi\) 阈值：截断和组内零优势会使参数关系更复杂。

### 一个有限样本、显式阈值的严格优势区域

取

$$
n=2,\quad K=4,\quad r=1,\quad q=2,
$$

其中一组骗过率为 \(p\)，另一组为 \(0\)。于是

$$
\mathbb E C_U=p,
$$

$$
\mathbb E C_P=1-(1-p)^4,
$$

$$
\mathbb E C_A
=
4p(1-p)^3
+12p^2(1-p)^2
+8p^3(1-p).
$$

相减可得

$$
\boxed{
\mathbb E C_A-\mathbb E C_P
=
p^2(p^2-8p+6).
}
\tag{10}
$$

因此：

$$
\boxed{
0<p<4-\sqrt{10}
\quad\Longrightarrow\quad
\mathbb E C_U<\mathbb E C_P<\mathbb E C_A.
}
\tag{11}
$$

而

$$
4-\sqrt{10}\approx0.83772.
$$

在该边界处，中心化配额与逐组选择期望相等；超过边界后，中心化配额反而更差。

两个可直接复核的解析值如下，**不是本次运行得到的实验数值**：

| 高率组 \(p\) | Uniform | Per-group top-1 | 中心化配额 | 原始全局配额 |
| -----------: | ------: | --------------: | ---------: | -----------: |
|      \(0.5\) | \(0.5\) |      \(0.9375\) |    \(1.5\) |    \(1.625\) |
|      \(0.9\) | \(0.9\) |      \(0.9999\) | \(0.6840\) |   \(1.9962\) |

第一行给出严格优势实例；第二行给出明确失败实例。由于严格不等式对概率参数连续，第一行的优势并不只存在于 \(p_l=0\) 这一个边界点，在足够小的正 \(p_l\) 邻域内仍成立。

---

## 2.5 大组数下的显式混合比例阈值

定义每组的期望正优势成功数

$$
a(p)=K(p-p^K),
$$

以及

$$
\mu_A=\pi a(p_h)+(1-\pi)a(p_l),
$$

$$
\mu_P=\pi\beta_r(p_h)+(1-\pi)\beta_r(p_l).
$$

则

$$
\boxed{
\left|
\frac{\mathbb E C_A}{n}-\min(r,\mu_A)
\right|
\le
\frac{K-1}{2\sqrt n}.
}
\tag{12}
$$

### 证明

令 \(\bar T=n^{-1}\sum_iT_i\)。有

$$
\frac{C_A}{n}=\min(r,\bar T),
\qquad
\mathbb E\bar T=\mu_A.
$$

函数 \(x\mapsto\min(r,x)\) 为 1-Lipschitz，因此

$$
\left|\mathbb E\min(r,\bar T)-\min(r,\mu_A)\right|
\le
\mathbb E|\bar T-\mu_A|
\le
\sqrt{\operatorname{Var}(\bar T)}.
$$

由独立性及 \(0\le T_i\le K-1\)，

$$
\operatorname{Var}(\bar T)
\le\frac{(K-1)^2}{4n}.
$$

得到式（12）。证毕。

若 \(\mu_P<r\)，则大组数极限下严格优势的条件为

$$
\mu_A>\mu_P.
$$

定义

$$
d_r(p)=K(p-p^K)-\beta_r(p).
$$

于是条件化为

$$
\boxed{
\pi d_r(p_h)+(1-\pi)d_r(p_l)>0.
}
\tag{13}
$$

例如，当

$$
d_r(p_h)<0<d_r(p_l),
$$

其显式阈值为

$$
\boxed{
\pi<
\frac{d_r(p_l)}
{d_r(p_l)-d_r(p_h)}.
}
\tag{14}
$$

取 \(K=4,r=1,p_h=1,p_l=1/2\)，有

$$
d_1(1)=-1,\qquad d_1(1/2)=\frac{13}{16},
$$

故极限阈值为

$$
\boxed{\pi<\frac{13}{29}.}
$$

这是一个有解释力的反直觉结果：**当大量组已经几乎全部被骗过时，中心化正优势机制可能删除过多重要候选，因而高骗过率组比例越高，反而越容易失去捕获优势。**

有限 \(n\) 时，若

$$
\min(r,\mu_A)-\mu_P>\frac{K-1}{2\sqrt n},
$$

即可由式（12）保证严格期望优势。这个界较保守，但可核验。

---

## 2.6 真实连续评分的反例与边界

只知道 \((\pi,p_h,p_l)\)，不足以决定中心化排序。考虑同一候选池：

$$
G_1=(0.61,0.60,0.59,0.58),
$$

$$
G_2=(0.49,0.48,0,0),
$$

被骗过阈值为 \(t=0.5\)，总预算 \(q=2\)。

第一组全部被骗过，第二组全部没有被骗过。但组均值分别为

$$
\bar u_1=0.595,\qquad \bar u_2=0.2425.
$$

第二组前两个候选的中心化优势远高于第一组，因此没有额外 \(Z=1\) 预过滤时，

$$
C_A=0,\qquad C_P=1,\qquad C_R=2.
$$

这并不与二点模型定理矛盾：该候选池不满足所有组共享同一对分数水平的 T1.5。

还应注意：

$$
u_{ik}=c_i+\varepsilon_{ik}
\quad\Longrightarrow\quad
A_{ik}
=
\frac{K}{K-1}
(\varepsilon_{ik}-\bar\varepsilon_i).
$$

**加性组难度 \(c_i\) 被中心化直接消除了。** 所以不能一般性地写“中心化预算把样本集中到高平均违规组”；它更直接偏好的是组内相对突出的候选。

### 可数值验证的推论

本地源期核验最有价值的对象不是只画总收益，而是同时记录

$$
\min(D,E),\quad L_{\mathrm{elig}},\quad L_{\mathrm{rank}}.
$$

它们应逐批满足式（3）。二点合成模型则可以核验式（5）—（14）。

覆盖—强度权衡也应单列：逐组选择保证每个源样本进入训练；跨组配额允许部分组完全没有样本。**捕获更多当前误判，不等于覆盖更多家族，也不等于梯度方差更小或训练后鲁棒性更高。**

---

# 三、定理 2：加权 Gram 条件下的双风险共同下降

## 3.1 先给良性误报加权一个准确的数学对象

良性标签为 \(0\)，令

$$
\ell_b(s)=-\log(1-s),
$$

分类阈值为 \(t_0\)，相应损失阈值

$$
c_0=-\log(1-t_0).
$$

定义

$$
\boxed{
\psi_b(s)
=
\ell_b(s)+2\bigl(\ell_b(s)-c_0\bigr)_+.
}
\tag{15}
$$

在非阈值点，

$$
\nabla_\theta\psi_b(s_\theta)
=
\left[1+2\mathbf 1\{s_\theta>t_0\}\right]
\nabla_\theta\ell_b(s_\theta).
$$

因此，在固定均值归一化、权重按当前判定取值的条件下，**“误报真良性 CE×3”对应一个连续、带折点的超额 CE 风险**。

它不是 CVaR，也不是新发明的凸分析对象，但不能说它“没有数学对象”。若实现按权重和重新归一化，或在多步之间缓存旧误报标签，则需要相应修改对应关系。

---

## 3.2 编号假设

**假设 T2.1：固定一步的样本与权重。**
在 \(\theta_0\) 处固定恶意候选集合 \(\mathcal M\)、良性集合 \(\mathcal B\) 及非负权重 \(w_i,v_j\)。定义

$$
R_m(\theta)
=
\sum_{i\in\mathcal M}w_i[-\log s_\theta(x_i)],
$$

$$
R_b(\theta)
=
\sum_{j\in\mathcal B}v_j[-\log(1-s_\theta(x_j))].
$$

归一化常数并入权重。

**假设 T2.2：局部平滑。**
两风险在所考虑步长邻域内分别为 \(L_m,L_b\)-smooth，且预测概率远离导致 CE 发散的端点。

**假设 T2.3：非零梯度。**

$$
g_m=\nabla R_m(\theta_0),\qquad
g_b=\nabla R_b(\theta_0),
$$

$$
m=\|g_m\|>0,\qquad
b=\|g_b\|>0,\qquad
c=\langle g_m,g_b\rangle.
$$

**假设 T2.4：更新形式。**

$$
\theta^+=\theta_0-\eta d,\qquad
d=g_m+\lambda g_b,\quad\lambda>0.
$$

这里首先分析普通梯度步。Adam、动量、权重衰减或额外基座损失不能未经处理直接代入。

---

## 3.3 精确的特征梯度 Gram 分解

记分数特征梯度

$$
\phi(x)=\nabla_\theta s_{\theta_0}(x).
$$

将恶意与良性特征梯度按列组成矩阵

$$
\Phi_m=[\phi(x_i)]_{i\in\mathcal M},
\qquad
\Phi_b=[\phi(x_j)]_{j\in\mathcal B}.
$$

令

$$
a_i=\frac{w_i}{s_{\theta_0}(x_i)},
\qquad
b_j'=\frac{v_j}{1-s_{\theta_0}(x_j)}.
$$

为避免混淆，用向量 \(\mathbf b'\) 表示良性系数，标量 \(b\) 仍表示梯度范数。则

$$
g_m=-\Phi_m\mathbf a,\qquad
g_b=\Phi_b\mathbf b'.
$$

定义 Gram 块

$$
G_{mm}=\Phi_m^\top\Phi_m,\quad
G_{bb}=\Phi_b^\top\Phi_b,\quad
G_{mb}=\Phi_m^\top\Phi_b.
$$

得到

$$
\boxed{
m^2=\mathbf a^\top G_{mm}\mathbf a,\qquad
b^2=\mathbf b'^\top G_{bb}\mathbf b',
}
\tag{16}
$$

$$
\boxed{
c=-\mathbf a^\top G_{mb}\mathbf b'.
}
\tag{17}
$$

这是有限模型在固定参数点的精确链式求导，不需要假设网络无限宽。特征梯度构成核的对象与 NTK 文献一致，但 NTK 的无限宽恒定性结论不能自动用于这里的有限训练网络。([arXiv][3])

式（17）的负号很重要：

> 恶意 CE 希望提高恶意分数，良性 CE 希望降低良性分数。如果两类样本的分数特征梯度高度同向，两个损失梯度反而可能强烈冲突。

---

## 3.4 定理 2：共同下降的充要方向条件与有限步保证

联合方向 \(d=g_m+\lambda g_b\) 是两个风险的严格一阶共同下降方向，当且仅当

$$
\boxed{
m^2+\lambda c>0,\qquad
c+\lambda b^2>0.
}
\tag{18}
$$

具体而言：

当 \(c\ge0\) 时，任意 \(\lambda>0\) 都满足条件。

当 \(c<0\) 时，条件等价于

$$
\boxed{
\frac{-c}{b^2}<\lambda<\frac{m^2}{-c}.
}
\tag{19}
$$

该区间非空，当且仅当

$$
c>-mb.
$$

若式（18）成立，且

$$
\boxed{
0<\eta<
\frac{2}{\|d\|^2}
\min\left\{
\frac{m^2+\lambda c}{L_m},
\frac{c+\lambda b^2}{L_b}
\right\},
}
\tag{20}
$$

则

$$
\boxed{
R_m(\theta^+)<R_m(\theta_0),\qquad
R_b(\theta^+)<R_b(\theta_0).
}
\tag{21}
$$

### 证明

沿 \(-d\) 的两个方向导数分别为

$$
-\langle g_m,d\rangle
=-(m^2+\lambda c),
$$

$$
-\langle g_b,d\rangle
=-(c+\lambda b^2).
$$

两者同时为负，恰好等价于式（18）。

当 \(c<0\) 时，分别求解两个不等式，得到式（19）。该区间非空等价于

$$
\frac{-c}{b^2}<\frac{m^2}{-c}
\iff c^2<m^2b^2.
$$

结合 \(c<0\)，即 \(c>-mb\)。

由平滑性，

$$
R_m(\theta^+)
\le
R_m(\theta_0)
-\eta(m^2+\lambda c)
+\frac{L_m\eta^2}{2}\|d\|^2,
$$

$$
R_b(\theta^+)
\le
R_b(\theta_0)
-\eta(c+\lambda b^2)
+\frac{L_b\eta^2}{2}\|d\|^2.
$$

式（20）使两式右侧的变化量都严格为负，得到式（21）。证毕。

这种共同下降思想属于已有多目标优化框架；本稿的任务化内容是把两侧 CE、样本选择权重与具体 Gram 块显式对应起来，而不是重新发明 Pareto 下降。([arXiv][4])

---

## 3.5 近正交条件如何转化为可测的权重区间

若存在 \(0\le\rho<1\)，使

$$
\boxed{
\left|
\mathbf a^\top G_{mb}\mathbf b'
\right|
\le
\rho
\sqrt{
(\mathbf a^\top G_{mm}\mathbf a)
(\mathbf b'^\top G_{bb}\mathbf b')
},
}
\tag{22}
$$

则 \(|c|\le\rho mb\)。

当 \(0<\rho<1\) 时，以下区间足以保证共同下降：

$$
\boxed{
\rho\frac mb<\lambda<\frac{m}{\rho b}.
}
\tag{23}
$$

证明只需代入最坏情形 \(c=-\rho mb\)：

$$
m^2+\lambda c\ge m^2-\lambda\rho mb>0,
$$

$$
c+\lambda b^2\ge-\rho mb+\lambda b^2>0.
$$

例如取平衡两侧梯度尺度的

$$
\lambda=\frac mb,
$$

则

$$
m^2+\lambda c\ge(1-\rho)m^2,
$$

$$
c+\lambda b^2\ge(1-\rho)mb.
$$

这不是建议自动替换现有权重，而是给出可检验的充分条件。

### “块间范数小于块内范数”需要怎样准确化

一个较强但明确的充分条件是

$$
G_{mm}\succ0,\qquad G_{bb}\succ0,
$$

以及

$$
\boxed{
\|G_{mb}\|_2
\le
\rho
\sqrt{
\lambda_{\min}(G_{mm})
\lambda_{\min}(G_{bb})
}.
}
\tag{24}
$$

因为

$$
|\mathbf a^\top G_{mb}\mathbf b'|
\le
\|G_{mb}\|_2\|\mathbf a\|\|\mathbf b'\|,
$$

而

$$
m^2\ge\lambda_{\min}(G_{mm})\|\mathbf a\|^2,
\qquad
b^2\ge\lambda_{\min}(G_{bb})\|\mathbf b'\|^2.
$$

联立即得式（22）。

**不能把式（24）的最小特征值换成最大特征值。** 块内最大方向很强，并不保证实际加权梯度没有落在很弱、但跨块高度相关的方向上。实际审查更适合直接测式（22），不必强求整个 Gram 块都满足统一谱条件。

---

## 3.6 原命题“联合更新优于单独更新”的反例

令对应单臂更新为

$$
\theta_m=\theta_0-\eta g_m,\qquad
\theta_b=\theta_0-\eta\lambda g_b.
$$

一阶展开给出

$$
R_m(\theta^+)-R_m(\theta_m)
=
-\eta\lambda c+O(\eta^2),
$$

$$
R_b(\theta^+)-R_b(\theta_b)
=
-\eta c+O(\eta^2).
\tag{25}
$$

所以，只要 \(c<0\)，即使非常接近零，联合更新对每个单臂的本职目标也会有一阶损失。

### 任意接近正交仍不支配单臂

取二维局部风险

$$
R_m(x,y)=x,\qquad
R_b(x,y)=-\varepsilon x+y,
$$

其中 \(0<\varepsilon<1\)。在原点，

$$
g_m=(1,0),\qquad
g_b=(-\varepsilon,1).
$$

令 \(\lambda=1\)，则联合更新使两个风险都下降。但相对各自单臂，两个本职风险都差了

$$
\eta\varepsilon.
$$

\(\varepsilon\) 可以任意小，故“足够近正交”不能推出“联合支配单臂”。

### 即使精确正交，也不能忽略二阶项

取

$$
R_m(x,y)=x+\frac L2y^2,\qquad R_b(x,y)=y.
$$

原点处两梯度精确正交。恶意单臂与联合更新分别为

$$
(-\eta,0),\qquad(-\eta,-\eta).
$$

但

$$
R_m(-\eta,-\eta)
=
-\eta+\frac L2\eta^2
>
-\eta
=
R_m(-\eta,0).
$$

因此，精确正交只给出某些**一阶不干扰性质**，不提供无条件有限步支配。梯度冲突、尺度差异和曲率需要联合考虑，这也与 PCGrad 原文的失败分析边界一致。([arXiv][5])

### 正交性退化到完全冲突的分类器反例

设所有样本共享单个标量 logit：

$$
z_\theta(x)=\theta.
$$

恶意 CE 梯度为负，良性 CE 梯度为正，故

$$
c=-mb.
$$

此时式（19）的可行区间为空；唯一抵消点产生零方向。**样本来自不同类别或不同字符邻域，并不能自动保证特征梯度低相关。**

---

## 3.7 从代理风险下降到 FPR/FNR：还需要更强条件

在分数的仿射近似下，恶意样本分数变化为

$$
\Delta\mathbf s_m
=
\eta\left(
G_{mm}\mathbf a-\lambda G_{mb}\mathbf b'
\right),
$$

良性样本分数变化为

$$
\Delta\mathbf s_b
=
\eta\left(
G_{bm}\mathbf a-\lambda G_{bb}\mathbf b'
\right).
\tag{26}
$$

因此，若满足逐元素条件

$$
\boxed{
G_{mm}\mathbf a\ge\lambda G_{mb}\mathbf b',
\qquad
G_{bm}\mathbf a\le\lambda G_{bb}\mathbf b',
}
\tag{27}
$$

则在线性化模型中，每个恶意样本分数不降低，每个良性样本分数不升高。

在固定分类阈值下，这能推出**该固定样本集合**上的 FNR、FPR 均不增加。严格改善还需要至少一个相关样本跨越判定阈值。

证明直接由式（26）的符号及阈值判定得到。对真实非线性模型，还需要一阶变化量的安全裕度大于分数泰勒余项。

式（27）比平均风险共同下降强得多。因此不能用式（21）直接替代 FPR/FNR 的实验门。

### 可数值验证的推论与真实网络边界

本地可以检验

$$
m,\quad b,\quad c,\quad
\frac{|c|}{mb},
\quad m^2+\lambda c,
\quad c+\lambda b^2.
$$

仅核验共同下降条件时，不必构造完整 NTK；直接计算两项损失梯度的范数与内积即可。分析哪些样本造成相关性时，再抽样 Gram 块。

理论只覆盖固定参数点的一步。若加入其他基座梯度 \(g_0\)，条件应改为

$$
m^2+\lambda c+\langle g_m,g_0\rangle>0,
$$

$$
c+\lambda b^2+\langle g_b,g_0\rangle>0.
$$

若使用预条件更新，应分析实际更新方向或相应度量，不能把普通梯度的欧氏内积当成完整解释。

---

# 四、定理 3：有限上端点下的搜索预算—缺口收缩

## 4.1 编号假设

**假设 T3.1：固定问题。**
固定原样本 \(x\)、检测器参数 \(\theta\) 和扰动提议分布 \(\mu(\cdot\mid x)\)。

**假设 T3.2：独立同分布候选。**

$$
U_1,\ldots,U_K\overset{\mathrm{i.i.d.}}{\sim}F,
\qquad U_k\in[0,1].
$$

定义提议分布下的本质上确界

$$
b=\operatorname*{ess\,sup}_{\delta\sim\mu}
u_\theta(x,\delta),
$$

样本最大值及搜索缺口

$$
M_K=\max_{1\le k\le K}U_k,
\qquad
\Delta_K=b-M_K.
$$

**假设 T3.3：端点质量条件。**
对某些 \(c_->0,c_+>0,\tau>0,\varepsilon_0>0\)，在 \(0<\varepsilon\le\varepsilon_0\) 上，

$$
\boxed{
c_-\varepsilon^\tau
\le
H(\varepsilon)
:=
\Pr(U>b-\varepsilon)
\le
c_+\varepsilon^\tau.
}
\tag{28}
$$

其中 \(\varepsilon_0\le b\)。精确分布公式不需要 T3.3，收缩率上下界需要。

---

## 4.2 定理 3A：精确分布、期望与非渐近界

对任意 \(0<\varepsilon\le b\)，

$$
\boxed{
\Pr(\Delta_K\ge\varepsilon)
=
F(b-\varepsilon)^K
=
[1-H(\varepsilon)]^K.
}
\tag{29}
$$

并且

$$
\boxed{
\mathbb E\Delta_K
=
\int_0^b F(b-t)^K\,dt.
}
\tag{30}
$$

在 T3.3 下，

$$
\boxed{
\mathbb E\Delta_K
\le
\frac{\Gamma(1+1/\tau)}
{(c_-K)^{1/\tau}}
+
(b-\varepsilon_0)
e^{-Kc_-\varepsilon_0^\tau}.
}
\tag{31}
$$

对满足

$$
(2c_+K)^{-1/\tau}\le\varepsilon_0
$$

的 \(K\)，有

$$
\boxed{
\mathbb E\Delta_K
\ge
\frac12(2c_+K)^{-1/\tau}.
}
\tag{32}
$$

因此，

$$
\boxed{
\mathbb E\Delta_K=\Theta(K^{-1/\tau}).
}
\tag{33}
$$

### 证明

由独立性，

$$
\Pr(M_K\le b-\varepsilon)
=
\prod_{k=1}^{K}\Pr(U_k\le b-\varepsilon)
=
F(b-\varepsilon)^K,
$$

即式（29）。

由于 \(0\le\Delta_K\le b\)，由非负随机变量的尾积分公式，

$$
\mathbb E\Delta_K
=
\int_0^b\Pr(\Delta_K>t)\,dt.
$$

将严格与非严格不等式在积分中的零测差异略去，得到式（30）。

对上界，当 \(t\le\varepsilon_0\) 时，

$$
F(b-t)^K
=
[1-H(t)]^K
\le e^{-KH(t)}
\le e^{-Kc_-t^\tau}.
$$

当 \(t>\varepsilon_0\) 时，由单调性，

$$
F(b-t)^K
\le e^{-Kc_-\varepsilon_0^\tau}.
$$

故

$$
\mathbb E\Delta_K
\le
\int_0^\infty e^{-Kc_-t^\tau}\,dt
+
(b-\varepsilon_0)e^{-Kc_-\varepsilon_0^\tau}.
$$

作变量代换 \(z=Kc_-t^\tau\)，可得

$$
\int_0^\infty e^{-Kc_-t^\tau}\,dt
=
\frac{\Gamma(1+1/\tau)}{(Kc_-)^{1/\tau}},
$$

得到式（31）。

对下界，令

$$
a_K=(2c_+K)^{-1/\tau}.
$$

当 \(0\le t\le a_K\) 时，

$$
H(t)\le\frac1{2K}.
$$

利用 Bernoulli 不等式，

$$
[1-H(t)]^K
\ge1-KH(t)\ge\frac12.
$$

因此

$$
\mathbb E\Delta_K
\ge
\int_0^{a_K}\frac12\,dt
=
\frac12(2c_+K)^{-1/\tau}.
$$

上下界合并得到式（33）。证毕。

---

## 4.3 更精确的渐近常数与预算语义

若端点质量进一步满足

$$
H(\varepsilon)
=
c\varepsilon^\tau+o(\varepsilon^\tau),
\qquad \varepsilon\downarrow0,
$$

则

$$
\boxed{
\mathbb E\Delta_K
\sim
\Gamma(1+1/\tau)(cK)^{-1/\tau}.
}
\tag{34}
$$

### 证明要点

在式（30）中作代换

$$
t=z(cK)^{-1/\tau}.
$$

对每个固定 \(z\)，

$$
[1-H(z(cK)^{-1/\tau})]^K
\longrightarrow e^{-z^\tau}.
$$

端点邻域内，T3.3 类型的下界给出可积控制函数 \(e^{-c' z^\tau}\)；邻域外的贡献指数衰减。由控制收敛，

$$
(cK)^{1/\tau}\mathbb E\Delta_K
\longrightarrow
\int_0^\infty e^{-z^\tau}dz
=
\Gamma(1+1/\tau).
$$

证毕。

此外，由式（29）和 T3.3，

$$
\Pr(\Delta_K\ge\varepsilon)
\le e^{-Kc_-\varepsilon^\tau}.
$$

所以要使缺口以至少 \(1-\delta\) 的概率小于 \(\varepsilon\)，以下预算足够：

$$
\boxed{
K\ge
\frac{\log(1/\delta)}
{c_-\varepsilon^\tau},
\qquad 0<\varepsilon\le\varepsilon_0.
}
\tag{35}
$$

这才是 \(K\) 作为搜索预算的定量语义：**它依赖于提议分布在最坏区域附近放置了多少概率质量。**

---

## 4.4 Uniform 情形的完整闭式

若

$$
U_k\sim\operatorname{Uniform}(0,1),
$$

则

$$
\Pr(M_K\le u)=u^K.
$$

由尾积分公式，

$$
\mathbb E M_K
=
\int_0^1\Pr(M_K>u)\,du
=
\int_0^1(1-u^K)\,du
=
\frac{K}{K+1}.
$$

因此

$$
\boxed{
\mathbb E\Delta_K=\frac1{K+1}.
}
\tag{36}
$$

特别地，

$$
\boxed{
K=4:\quad
\mathbb E M_4=0.8,\qquad
\mathbb E\Delta_4=0.2.
}
$$

**0.2 是 Uniform 假设下、相对于分数上端点 1 的期望分数缺口；不是 20% 的检出缺口，不是 CE 风险差，也不是 DRIFT 实测量。**

可核验序列为

$$
K=1,2,4,8,16
\quad\Rightarrow\quad
\mathbb E\Delta_K
=
\frac12,\frac13,\frac15,\frac19,\frac1{17}.
$$

---

## 4.5 尾部类型必须重新命名

原计划中的“指数尾 \(O(1/K)\)、重尾 \(O(K^{-1/\tau})\)”不适合直接用于 \(U\in[0,1]\)。

| 情形                                               | 正确结论                                                            |
| -------------------------------------------------- | ------------------------------------------------------------------- |
| 有限端点，端点处密度 \(f(b)\in(0,\infty)\)         | \(H(\varepsilon)\sim f(b)\varepsilon\)，所以缺口为 \(O(1/K)\)       |
| 有限端点，\(H(\varepsilon)\asymp\varepsilon^\tau\) | 缺口为 \(\Theta(K^{-1/\tau})\)                                      |
| 端点存在概率原子 \(p_*=\Pr(U=b)>0\)                | \(\mathbb E\Delta_K\le b(1-p_*)^K\)，指数收缩                       |
| 无界指数分布                                       | supremum 为无穷，最大值按 \(\log K\) 尺度增长，不存在这里的有限缺口 |
| 无界 Pareto 分布                                   | supremum 为无穷，最大值按幂次尺度增长，也不是这里的缺口收缩         |

对有限离散字符扰动空间，若最优候选在提议分布下具有正概率，最终更接近第三种情形；连续端点模型可以是近似，但不能省略这一差别。

没有端点质量下界时，也不存在通用多项式收缩率。例如端点附近质量极其稀薄时，增大 \(K\) 的收益可以远慢于任何预设的 \(K^{-c}\)。

---

## 4.6 最大值收缩不等于所选训练风险收缩

### 固定比例 top-r 均值不是 maximum

Uniform 情形下，第 \(j\) 个升序次序统计量满足

$$
\mathbb E U_{(j)}=\frac{j}{K+1}.
$$

这可由其密度

$$
\frac{K!}{(j-1)!(K-j)!}
u^{j-1}(1-u)^{K-j}
$$

积分得到。因此最大的 \(r\) 个候选均值满足

$$
\boxed{
1-
\mathbb E\left[
\frac1r\sum_{j=K-r+1}^{K}U_{(j)}
\right]
=
\frac{r+1}{2(K+1)}.
}
\tag{37}
$$

固定 \(r\) 时缺口为 \(O(1/K)\)；但若 \(r/K\to\rho>0\)，缺口趋于 \(\rho/2\)，并不趋于零。

### 实际方法存在三种不同缺口

令

$$
u^*=\sup_{\delta\in\mathcal D(x)}u_\theta(x,\delta)
$$

为整个合法扰动集合中的最坏违规量，令 \(\widehat M_K\) 为该组最终入选候选中的最大违规量；该组无候选入选时约定 \(\widehat M_K=0\)。则

$$
\boxed{
u^*-\widehat M_K
=
\underbrace{u^*-b}_{\text{提议分布支持缺口}}
+
\underbrace{b-M_K}_{\text{有限搜索缺口}}
+
\underbrace{M_K-\widehat M_K}_{\text{选择缺口}}.
}
\tag{38}
$$

定理 3 只控制中间一项。

因此，增大 \(K\) 不能自动消除：

- 固定扰动算子从不访问的最坏区域；
- 全局预算竞争导致该组完全被排除；
- 中心化排序丢弃该组最大违规候选。

### 独立性失败的反例

若所有候选完全重复，

$$
U_1=\cdots=U_K=U,
$$

则

$$
M_K=U
$$

与 \(K\) 无关。Uniform 边缘分布下，缺口始终为 \(1/2\)，而不是 \(1/(K+1)\)。

所以验证预算语义时，应同时检查候选重复与相关性，不能只数生成调用次数。

---

# 五、三条结果如何成为一组，而不是三个装饰性定理

这组理论可以形成以下对应关系：

| 理论对象                    | 可核验预测                                               | 不能代替的实验结论                                     |
| --------------------------- | -------------------------------------------------------- | ------------------------------------------------------ |
| 定理 1：配额收益分解        | 捕获增量应由缺额—溢出交换解释，并扣除资格与排序损失      | 训练后检出率改善、家族覆盖改善、梯度方差降低           |
| 定理 2：Gram 结构与共同下降 | 实际两侧梯度、权重和步长满足条件时，一步代理风险共同下降 | 全训练过程支配单臂、未来年 FPR 不增                    |
| 定理 3：搜索预算误差        | 固定提议分布下，样本最大值按端点质量规律逼近支持上端点   | 中心化入选风险逼近全局最坏攻击、鲁棒准确率按同速率提高 |

## 5.1 理论所有权应怎样陈述

**定理 1：可以作为最主要的方法特定分析候选。**
真正值得保留的不是“全局选择比逐组选择好”这一口号，而是

$$
\text{净捕获收益}
=
\text{预算重分配收益}
-
\text{资格损失}
-
\text{排序损失},
$$

以及由此产生的严格优势区、失败区和混合比例阈值。本次完成了数学推导，但没有完成对这一整套组合表述的全库首创性核验。

**定理 2：应定位为条件性机制解释。**
共同下降与梯度几何已有成熟先例；贡献可以是针对两侧损失的精确系数、Gram 条件、实现诊断和反例边界，不宜称“首次证明双侧梯度正交”。([arXiv][4])

**定理 3：适合作为预算语义引理或辅助定理。**
它的主要价值是把 \(K\)、提议分布支持、端点质量和最终选择误差分开，而不是宣称重新建立了次序统计学。次序统计量的有限样本与渐近分布本身已有系统理论。([Wiley Online Library][6])

因此，最稳妥的章节定位是：

> **一个方法特定的选择收益定理，配合一个双风险局部下降命题和一个搜索预算误差引理。**

这比把三者都称为“自有新定理”更能承受审查。

## 5.2 对参照论文的理论对标

按本轮提供的参照描述，这份数学稿在**可核验性**上有明确改进：每个结果都给出了假设、证明、失效反例、可测条件，以及不允许外推的结论。

但不能据此独立断言参照论文实现错误，或证明本章学术贡献已经超过对方。尤其需要纠正一个通用理论前提：

**传统 min-max 对抗训练不对最优攻击响应反向传播，并不必然意味着遗漏了应有梯度。** 在满足条件且内层最大解唯一时，Danskin 定理给出的外层梯度正是

$$
\nabla_\theta \max_\delta L(\theta,\delta)
=
\nabla_\theta L(\theta,\delta^*),
$$

不需要额外加一个攻击响应链式项。有限步展开目标与精确内层最大值目标是不同对象。Madry 等在 §3.3 和附录 A 明确讨论了这一点。([arXiv][7])

参照方法若宣称计算有限轨迹的反应梯度，却在实现中切断轨迹，才构成其自身声明与实现的对应问题；不能进一步推导为所有 stop-gradient AT 都有同一种理论缺陷。

同样，**“检出大增但 FPR 支付可控代价”不等于 FPR—检出率两目标上的 Pareto 支配**。若 FPR 上升，应称为权衡移动；只有至少一轴严格改善、另一轴不劣，才满足支配定义。([arXiv][4])

---

## 六、来源、精确位置与核验状态

| 来源                                                                                                                                              | 精确位置                              | 本次核验状态与用途                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Fan、Lyu、Ying、Hu，_Learning with Average Top-k Loss_，NeurIPS 2017                                                                              | 引言式（1）；§2                       | **全文关键段核对**。确认平均 top-k 风险已有正式数学对象，不支持将一般全局 top-k 称为首次提出。([arXiv][2])                                     |
| Wu、Peng、Cai、Li，_Batch-in-Batch: a new adversarial training framework for initial perturbation and sample selection_，arXiv:2406.04070v1，2024 | §4.3，式（3）CP、式（4）GS、式（5）BG | **所列版本全文关键段核对**。确认 GS 允许每组零个或多个候选；未在本次另核正式发表版本。([arXiv][1])                                             |
| Jacot、Gabriel、Hongler，_Neural Tangent Kernel: Convergence and Generalization in Neural Networks_，NeurIPS 2018                                 | §3.1、§4                              | **全文关键段核对**。支持特征梯度核的对象定义；未将无限宽结论用于真实 DRIFT。([arXiv][3])                                                       |
| Sener、Koltun，_Multi-Task Learning as Multi-Objective Optimization_，NeurIPS 2018                                                                | §3 Definition 1；§3.1，式（3）        | **全文关键段核对**。区分支配、共同下降、Pareto 驻点。([arXiv][4])                                                                              |
| Yu 等，_Gradient Surgery for Multi-Task Learning_，NeurIPS 2020                                                                                   | §2.2，Definitions 1–3                 | **全文关键段核对**。支持冲突、梯度尺度、曲率必须共同考虑的边界。([arXiv][5])                                                                   |
| David、Nagaraja，_Order Statistics_，Encyclopedia of Statistical Sciences，2004 条目                                                              | 摘要与参考文献目录                    | **摘要／题录核对，未取得用于逐节引用的正文**。只用于标识既有理论谱系；定理 3 的公式由本文完整证明，不依赖未读正文。([Wiley Online Library][6]) |
| Madry 等，_Towards Deep Learning Models Resistant to Adversarial Attacks_，ICLR 2018                                                              | §3.3；Appendix A，Theorem A.1         | **全文关键段核对**。限定“忽略攻击响应导数即为理论缺陷”的表述。([arXiv][7])                                                                     |

**最终判断：这组三结果足以构成一套有明确假设、完整证明和失败边界的理论分析，但不能证明中心化选择无条件更优、联合训练无条件支配单臂，也不能把标准极值公式变成新的理论所有权。最值得作为章级理论主线的是定理 1 的净收益分解；定理 2、3 的作用是约束解释范围，而不是替实验增益作保证。**

[1]: https://arxiv.org/html/2406.04070v1 "https://arxiv.org/html/2406.04070v1"
[2]: https://arxiv.org/html/1705.08826 "https://arxiv.org/html/1705.08826"
[3]: https://arxiv.org/html/1806.07572 "https://arxiv.org/html/1806.07572"
[4]: https://arxiv.org/html/1810.04650 "https://arxiv.org/html/1810.04650"
[5]: https://arxiv.org/html/2001.06782 "https://arxiv.org/html/2001.06782"
[6]: https://onlinelibrary.wiley.com/doi/abs/10.1002/0471667196.ess6023 "https://onlinelibrary.wiley.com/doi/abs/10.1002/0471667196.ess6023"
[7]: https://arxiv.org/html/1706.06083 "https://arxiv.org/html/1706.06083"
