# 双侧组相对对抗训练统一框架：理论对抗审查与反例推演

**状态：外部候选，待本地全文和实验复核；本报告不验证实验有效性、不裁决方案存废、不修改冻结合同。**

| 返回字段 | 本次执行 |
|---|---|
| `actual_model` | GPT-5.5 Thinking |
| `actual_effort` | high |
| `actual_mode` | deep-research；纯数学机制审查，不做外部文献检索 |
| `used_apps` | GitHub：仅尝试读取两个白名单文件；在指定 commit/branch 下均返回 404，故未获得仓库正文。未访问白名单外路径；未运行项目代码；未使用 Web |
| `source_scope` | 用户本轮给出的框架描述与数学推演 |
| `verification_status` | 数学推演可独立检查；实现细节因白名单文件未成功读取而未核验 |

## 总结判断

这个框架真正需要警惕的，**不是“双内层 max 一定不收敛”**，而是三个更精确的问题：

第一，恶意侧与良性 CVaR 如果在同一个 \(\theta\) 快照上分别求近似内层解、再一次性合并梯度，那么两个内层变量在数学上其实可以分解，**不要求一个所谓“共享内层解”**。真正危险的是把两侧做成顺序式、边更新 \(\theta\) 边重新求另一侧 hard set；那样每一步已经不是同一个目标的梯度，存在明确的顺序偏差和振荡构造。

第二，目前“**留一均值优势 + 正优势 + top-\(q\)**”有一个比通常所说“截断产生偏差”更致命的数学事实：

\[
A_i
=
u_i-\frac{1}{K-1}\sum_{j\ne i}u_j
=
\frac K{K-1}(u_i-\bar u).
\]

所以对于同一组 \(K\) 个扰动，**优势的排序和原始违规量 \(u_i\) 的排序完全相同**。如果最终只是取 top-\(q\)，留一基线根本不会改变 top-\(q\) 成员；它只在“必须 \(A_i>0\)”时额外施加“高于组均值”的门。

因此审稿人最可能直接攻击：

> “你的 detector-side group-relative top-\(q\) 是否只是 per-clean-example top-\(q\) hard example mining 换了一个 GRPO 术语？”

这个问题必须正面回答。尤其 \(q=1\) 时，只要没有完全并列，**选中的就是原始 \(u\) 最大的样本**。

第三，batch 内最坏 5% CE 的 hard top-\(k\) 不是总体 CVaR 的无偏 mini-batch 梯度。\(n_b\approx512,\alpha=0.05\) 时，有效尾部只有约 \(25.6\) 个样本，统计有效样本量确实只有二十多个量级；而且“每批 CVaR 再平均”一般不等于“全训练集 CVaR”。若论文把它直接写成 population CVaR 的无偏估计，会留下很明显的理论漏洞。

最建议的表述修正是把总体框架写成：

\[
\min_\theta
\left[
\mathbb E_{x\sim D_{\rm mal}}
\rho_{K,q}^{\rm mal}(\theta;x)
+
\lambda
\rho_\alpha^{\rm ben}(\theta)
\right],
\]

其中恶意侧诚实称作 **\(K\)-sample group hard-risk surrogate**，而不是宣称有限 \(K\) 的 top-\(q\) 是“无偏内层 max”；良性侧若坚持 batch top-\(k\)，则称作 **mini-batch empirical CVaR surrogate**。这样反而更难被攻击。

## 对 Q1 的审查：两个内层 max 会不会振荡，何时需要共享求解

### 形式上先把问题拆清楚

把恶意侧写成

\[
A(\theta)
=
\max_{\phi\in\Phi}
L_{\rm mal}(\theta,\phi),
\]

把良性尾部风险写成 CVaR 的对偶形式

\[
B(\theta)
=
\max_{w\in\mathcal W_\alpha}
L_{\rm ben}(\theta,w),
\]

其中经验 CVaR 的权重集合可以写成

\[
\mathcal W_\alpha
=
\left\{
w_i\ge0,\;
\sum_iw_i=1,\;
w_i\le \frac1{\alpha n_b}
\right\}.
\]

总目标是

\[
F(\theta)
=
A(\theta)+\lambda B(\theta)
=
\max_{\phi}L_{\rm mal}(\theta,\phi)
+
\lambda\max_wL_{\rm ben}(\theta,w).
\]

只要 \(\phi\) 与 \(w\) 的约束互不耦合，就有

\[
\max_{\phi,w}
\left[
L_{\rm mal}(\theta,\phi)
+
\lambda L_{\rm ben}(\theta,w)
\right]
=
\max_\phi L_{\rm mal}(\theta,\phi)
+
\lambda\max_wL_{\rm ben}(\theta,w).
\]

**因此：从数学目标本身看，没有必要让两个内层 max 共用一个“inner solution”。**

需要共享的是另一件事：

> **两边应该在同一个 \(\theta_t\) 快照上决定各自的 hard set／inner response，然后合并成一次 outer update。**

这与“共享一个内层玩家”完全不同。

### 一个最小振荡反例

考虑最简单的双内层双线性问题：

\[
\min_\theta\max_{a,b}
L(\theta,a,b)
=
\theta a+\theta b.
\]

忽略投影，普通同时梯度下降—上升为：

\[
\theta_{t+1}
=
\theta_t-\eta(a_t+b_t),
\]

\[
a_{t+1}=a_t+\eta\theta_t,
\qquad
b_{t+1}=b_t+\eta\theta_t.
\]

令

\[
c_t=a_t+b_t,
\]

得到

\[
\begin{pmatrix}
\theta_{t+1}\\
c_{t+1}
\end{pmatrix}
=
\begin{pmatrix}
1&-\eta\\
2\eta&1
\end{pmatrix}
\begin{pmatrix}
\theta_t\\
c_t
\end{pmatrix}.
\]

该矩阵特征值为

\[
1\pm i\sqrt2\,\eta,
\]

模长

\[
\sqrt{1+2\eta^2}>1.
\]

所以普通同步 GDA 不是收敛，而是向外螺旋。

但如果每个 \(\theta\) 下先精确求内层：

\[
a^\star=b^\star=\operatorname{sign}(\theta),
\]

那么外层目标只是

\[
F(\theta)=2|\theta|,
\]

最优点清楚地在 \(\theta=0\)。

**这说明“原问题有明确 minimax 解”不等于“同时训练两个玩家会收敛”。**

若给 \(a,b,\theta\) 加有界投影，发散会变成边界附近的周期追逐或反复翻转，并没有自动变成稳定收敛。

### 你们当前框架更现实的风险反而是顺序更新偏差

假设恶意风险梯度为

\[
g_m(\theta)=\nabla_\theta A(\theta),
\]

良性风险梯度为

\[
g_b(\theta)=\nabla_\theta B(\theta).
\]

理想的一次总更新是

\[
\theta^+
=
\theta-\eta
\left[
g_m(\theta)+\lambda g_b(\theta)
\right].
\]

但若程序实际做：

1. 在 \(\theta\) 上求恶意 hard set；
2. 更新一次 \(\theta'=\theta-\eta g_m(\theta)\)；
3. 再在 \(\theta'\) 上求良性 top-tail；
4. 再做良性更新，

则

\[
\theta''
=
\theta
-\eta g_m(\theta)
-\eta\lambda g_b(\theta-\eta g_m(\theta)).
\]

Taylor 展开：

\[
g_b(\theta-\eta g_m)
=
g_b(\theta)
-\eta H_b(\theta)g_m(\theta)
+
O(\eta^2),
\]

因此

\[
\theta''
=
\theta
-\eta(g_m+\lambda g_b)
+
\eta^2\lambda H_b g_m
+
O(\eta^3).
\]

如果把顺序反过来，则多出来的是

\[
\eta^2\lambda H_m g_b.
\]

二者差值：

\[
\Delta_{\rm order}
=
\eta^2\lambda
\left(
H_b g_m-H_m g_b
\right)
+
O(\eta^3).
\]

所以即使两个 branch 本身完全独立，**mal-first 与 benign-first 也不是同一个算法**。

这会成为非常合理的审稿问题：

> “为什么 adversarial branch 先更新，而 CVaR branch 后更新？交换顺序是否改变结论？”

### 最稳的实现建议

同一步内：

\[
\theta_t
\longrightarrow
\begin{cases}
S_t^{\rm mal}=\operatorname{SelectMal}(\theta_t),\\
S_t^{\rm ben}=\operatorname{SelectTail}(\theta_t),
\end{cases}
\]

然后只计算

\[
g_t
=
g_{\rm mal}
+
\lambda g_{\rm ben},
\]

最终一次：

\[
\theta_{t+1}
=
\theta_t-\eta g_t.
\]

这样论文中可以明确说：

> 两侧风险集合均由同一 detector snapshot 构造；不存在一侧更新后再重新定义另一侧风险集的 sequential best-response bias。

### 什么时候真的需要联合 inner solve

只有出现以下耦合时，两个内层才不能简单分开：

\[
\max_{\phi,w}
L(\theta,\phi,w)
\neq
\max_\phi L_1+\max_wL_2.
\]

典型情况包括：

共同攻击预算：

\[
c_{\rm mal}(\phi)+c_{\rm ben}(w)\le C;
\]

共同样本配额；

一个 branch 的权重取决于另一个 branch 的输出；

\(\lambda\) 本身由当前 attacker 强度自适应；

或者存在交叉项：

\[
C(\theta,\phi,w).
\]

此时独立把两边各自做到 max 可能实际上**重复消费同一个预算**。

你们目前描述中没有这种约束，所以没有理论必要引入“共享 inner solver”。

### 需要非常谨慎的一点：P3 与 P4 不能用同一套“minimax 收敛”语言

若当前 P3 的“攻击者”只是：

- 固定字符扰动算子；
- 每次从算子随机生成 \(K=4\) 个候选；
- 然后 hard-select；

那其实**没有持久化的攻击者参数 \(\phi_t\)**。

这时所谓内层不是一个通过梯度上升不断学习的玩家，而是一个 Monte Carlo hard-mining operator。

因此 P3 的主要数学问题是：

\[
\text{有限样本 max 的统计逼近误差}
\]

而不是

\[
\text{minimax GDA 的动态收敛}.
\]

真正到了 P4，即攻击策略参数 \(\phi_t\) 同时更新，才出现标准的双侧非平稳追逐问题。

把二者分开写，会明显减少审稿人抓概念混用的空间。

### Q1 最可能的审稿攻击线

> “你的两个 inner maximization 究竟是否真的都在学习？良性 CVaR 的 top-k 是闭式排序，不是玩家；恶意侧如果只是采样也不是 gradient-ascent inner optimization。为什么把它写成双内层博弈？”

这是合理攻击。

建议改成：

> 恶意侧采用有限候选集上的 sample robust-risk approximation；良性侧采用 empirical upper-tail risk。两侧在统一参数快照上确定 active set，然后联合更新 detector。

等真正加入可学习 attacker 时，再写 minimax game。

### Q1 结论

**不需要共享内层解；需要共享 detector snapshot。**

可分离条件下的两个 exact maxima 本身没有矛盾。

真正危险的是：

- persistent attacker 与 detector 同时学习导致的旋转动力学；
- sequential two-side update 的二阶顺序偏差；
- hard-set 在 \(\theta\) 附近频繁切换形成非光滑震荡。

对于当前神经网络、离散字符扰动和 hard selection，**没有合理依据声称全局 minimax 收敛**。最安全措辞是：

> 优化采用 stochastic alternating approximation；理论分析仅用于说明风险目标与梯度构造，不主张一般非凸—非凹条件下的全局收敛。

## 对 Q2 的审查：留一基线无偏性会被 top-q 破坏吗

### 先给结论

**会。**

更严格地说：

1. 留一均值作为 REINFORCE control variate，在满足独立条件时可以保持原始 policy-gradient 期望；
2. 一旦再乘一个“正优势且 top-\(q\)”选择指示器，通常就不再是原始 REINFORCE 梯度的无偏估计；
3. 若这个优势根本不用于攻击者 policy gradient，而只是拿来选 detector 的训练样本，那么“REINFORCE 无偏性”本来就不是正确的理论对象；
4. 更严重的是，在你们定义下，LOO advantage 对组内排序没有任何新信息。

### 留一均值什么时候确实是无偏 baseline

设对于固定 clean sample \(x\)，独立采样

\[
a_1,\ldots,a_K
\stackrel{i.i.d.}{\sim}
\pi_\phi(\cdot|x),
\]

每个攻击动作奖励

\[
R_i=R(x,a_i;\theta).
\]

定义：

\[
b_{-i}
=
\frac1{K-1}
\sum_{j\ne i}R_j,
\]

以及

\[
A_i=R_i-b_{-i}.
\]

标准 score-function 项：

\[
g_i
=
A_i
\nabla_\phi\log\pi_\phi(a_i|x).
\]

若 \(b_{-i}\) 在给定 \(x\) 后与 \(a_i\) 独立，则

\[
\mathbb E
\left[
b_{-i}
\nabla_\phi\log\pi_\phi(a_i|x)
\right]
=
\mathbb E[b_{-i}]
\mathbb E
\left[
\nabla_\phi\log\pi_\phi(a_i|x)
\right].
\]

而 score expectation 为

\[
\mathbb E[\nabla_\phi\log\pi_\phi(a_i|x)]
=
\nabla_\phi
\int\pi_\phi(a|x)\,da
=
0.
\]

所以

\[
\mathbb E[g_i]
=
\mathbb E
\left[
R_i
\nabla_\phi\log\pi_\phi(a_i|x)
\right].
\]

这就是你们可以声称的“LOO baseline 不改变期望”的条件版本。

但要注意条件：

- \(a_j\) 需要与 \(a_i\) 条件独立；
- 若候选是 without-replacement；
- 或后一个扰动依赖前一个；
- 或整组满足共同约束；
- 或共享一个会诱发强相关的随机变量，

上述简单因子分解就不再成立。

因此不要写成无条件命题。

### 但你们的优势还有一个代数恒等式

令

\[
\bar R
=
\frac1K\sum_{j=1}^K R_j.
\]

因为

\[
\sum_{j\ne i}R_j
=
K\bar R-R_i,
\]

所以

\[
A_i
=
R_i-\frac{K\bar R-R_i}{K-1}
\]

\[
=
\frac{K}{K-1}(R_i-\bar R).
\]

于是：

\[
A_i>A_j
\iff
R_i>R_j.
\]

并且：

\[
A_i>0
\iff
R_i>\bar R.
\]

还有：

\[
\sum_iA_i=0.
\]

这是当前机制最应该提前防守的数学事实。

### 它对 top-q 意味着什么

如果你们做的是：

> 对同一域名 \(K=4\) 个候选，按 \(A_i\) 排序，取最大的 \(q\) 个。

那么：

\[
\operatorname{TopQ}(A_1,\dots,A_K)
=
\operatorname{TopQ}(R_1,\dots,R_K).
\]

**LOO group-relative baseline 对 top-q 排名没有任何作用。**

若还要求：

\[
A_i>0,
\]

它的唯一新增作用是：

> 只允许高于本组均值的候选进入候选集。

所以 detector-side 机制严格说不是：

> “group-relative advantage creates a new ranking”。

而是：

> “per-clean-sample hard ranking + above-group-mean admission criterion”。

这个区别必须讲清楚。

### \(q=1\) 时问题尤其尖锐

只要四个 \(R_i\) 不完全相同：

\[
\arg\max_iA_i
=
\arg\max_iR_i.
\]

所以若 \(q=1\)，所谓 group-relative top-1 和直接：

\[
\max_{i=1,\ldots,4} R_i
\]

完全相同。

审稿人非常可能直接说：

> “This is best-of-4 adversarial hard mining, not a group-relative optimization mechanism.”

这不是措辞问题，而是代数等价。

### 更严重的反例：组内全都很难时，relative advantage 反而消失

设 \(K=4\)，一个 clean malicious domain 的四个扰动全部极强：

\[
u=(0.99,0.99,0.99,0.99).
\]

则：

\[
A=(0,0,0,0).
\]

如果规则要求“正优势才入批”，那么这个**绝对最危险的组可能一个也不选**。

反过来，另一个总体并不危险的组：

\[
u=(0.10,0.11,0.12,0.13)
\]

则最高两个样本有正 advantage。

于是 relative-only admission 可能出现：

> 弱组有样本入选，极强但组内齐平的组反而被清空。

这与“近似内层 max”的语义直接冲突。

这很可能是 Q2 中最强的机制反例。

### 对 binary bypass reward 更直观

假设奖励只有：

\[
R_i\in\{0,1\},
\]

1 表示骗过 detector。

若一个组有 \(m\) 个成功攻击，则成功样本：

\[
A_i
=
1-\frac{m-1}{K-1}
=
\frac{K-m}{K-1},
\]

失败样本：

\[
A_i
=
0-\frac{m}{K-1}
=
-\frac m{K-1}.
\]

当 \(K=4\)：

| 成功数 \(m\) | 成功样本优势 | 失败样本优势 |
|---:|---:|---:|
| 0 | — | 0 |
| 1 | 1 | \(-1/3\) |
| 2 | \(2/3\) | \(-2/3\) |
| 3 | \(1/3\) | \(-1\) |
| 4 | 0 | — |

所以最荒谬的极端是：

\[
m=4.
\]

四个攻击全部成功，反而

\[
A_i=0.
\]

若正优势 hard gate 是 detector adversarial-training 的唯一入选条件，那么“攻击全面得手”会被判为没有值得训练的样本。

这不能靠调 \(q\) 修复；是中心化本身导致的。

### top-q 对 REINFORCE 无偏性的破坏

原始无偏估计器写成：

\[
g
=
\mathbb E[A_iS_i],
\qquad
S_i=
\nabla_\phi\log\pi_\phi(a_i|x).
\]

加入选择变量：

\[
M_i
=
\mathbf1
\{
A_i>0,\;
i\in \operatorname{TopQ}(A)
\},
\]

得到：

\[
g_{\rm trunc}
=
\mathbb E[M_iA_iS_i].
\]

于是偏差：

\[
\operatorname{Bias}
=
g_{\rm trunc}-g
\]

\[
=
-\mathbb E[(1-M_i)A_iS_i].
\]

除非恰好：

\[
\mathbb E[(1-M_i)A_iS_i]=0,
\]

否则就是有偏的。

通常没有理由该项为零。

而且 negative-advantage action 并不是无用的：在 policy gradient 里，它们负责**降低坏动作概率**。全部删掉，已经改变了优化目标。

### 一个可写进附录的偏差范数上界

由 Cauchy–Schwarz：

\[
\|\operatorname{Bias}\|
\le
\sqrt{
\mathbb E[(1-M_i)A_i^2]
}
\sqrt{
\mathbb E[(1-M_i)\|S_i\|^2]
}.
\]

若进一步假设：

\[
|A_i|\le A_{\max},
\qquad
\|S_i\|\le G,
\]

则粗略有：

\[
\|\operatorname{Bias}\|
\le
A_{\max}G
\Pr(M_i=0).
\]

这个界很松，但足以说明一件事：

> hard truncation 不是“baseline 仍然无偏，所以整个算法仍然无偏”。

前一个命题不能推出后一个命题。

### deterministic top-q 也很难靠 importance correction 修回无偏

如果某些样本条件选中概率就是零：

\[
P(M_i=1\mid A_{1:K})=0,
\]

则不能用普通 Horvitz–Thompson/importance weighting 对这些被完全排除的项进行恢复，因为分母为零。

因此所谓：

> “我们给 top-q 样本乘一个修正权重，就重新无偏”

通常站不住。

若确实希望可校正，需要让所有样本具有非零选择概率，例如 soft/randomized selection。

### 最干净的规避方式：把 attacker update 与 detector hard mining 分离

这是本报告最推荐的理论拆法。

攻击者参数 \(\phi\) 更新：

\[
\hat g_\phi
=
\frac1K
\sum_{i=1}^K
A_i
\nabla_\phi\log\pi_\phi(a_i|x),
\]

**使用全部 \(K\) 个候选。**

LOO baseline 此时可以继续作为 control variate。

detector 参数 \(\theta\) 更新则使用：

\[
S_q(x)
=
\operatorname{TopQ}_{i}
\{u_i\},
\]

或者一个明确命名的 hard-risk：

\[
\rho_{K,q}(\theta;x)
=
\frac1q
\sum_{i\in S_q(x)}
\ell_\theta(\tilde x_i,y).
\]

这样两个数学目标不混：

- group-relative advantage：攻击者策略学习；
- top-\(q\)：检测器 hard adversarial training。

这是比声称“top-q group-relative gradient remains unbiased”稳健得多的结构。

### 如果一定要保留 relative gate

至少不要仅用 \(A_i>0\)。

可以采用绝对危险度保护：

\[
M_i
=
\mathbf1
\left[
i\in\operatorname{TopQ}(u)
\right]
\vee
\mathbf1[u_i\ge\tau_{\rm abs}].
\]

这样“组内全部很难”不会因为中心化而消失。

但这已经是机制改造，需要本地独立裁决，并且 \(\tau_{\rm abs}\) 不能由目标测试数据事后选择。

### 另一个可行方向：soft max-risk

例如：

\[
w_i(\tau)
=
\frac{\exp(u_i/\tau)}
{\sum_j\exp(u_j/\tau)},
\]

\[
\rho_\tau
=
\sum_iw_i(\tau)\ell_i.
\]

它避免 hard top-q 的集合跳变。

不过这优化的是平滑的 entropic/log-sum-exp 型风险，不应宣称等于原始 max。

### Q2 建议删除的说法

不建议写：

> “由于使用 leave-one-out baseline，我们的 top-q group-relative estimator 是内层 max 的无偏 Monte Carlo estimator。”

这里至少混了三件不同的事：

- REINFORCE 期望梯度；
- finite-\(K\) max approximation；
- hard top-q risk。

三者都不是一回事。

### 更稳的说法

可以写：

> 留一均值仅作为攻击策略 score-function gradient 的 control variate；对于 detector，top-\(q\) 操作被明确视为有限候选集上的有意 hard-risk truncation，因此不声称其为原始期望风险的无偏估计。

如果当前根本没有 learned attacker，则再进一步：

> group-relative quantity only defines within-group admission; detector optimization itself is a deterministic hard-mining surrogate over sampled perturbations.

## 对 Q3 的审查：batch CVaR 的偏差、方差和全数据 CVaR 的关系

### 首先统一 CVaR 记号

这里 \(\alpha=0.05\) 指“**最坏 5%**”，即 upper-tail mass，而不是有些文献中把 \(\alpha=0.95\) 写成 confidence level 的另一套记法。

对于良性损失随机变量 \(L\)，设

\[
q_\alpha
=
\operatorname{VaR}_{1-\alpha}(L).
\]

upper-tail CVaR 可写成：

\[
\operatorname{CVaR}_\alpha(L)
=
q_\alpha
+
\frac1\alpha
\mathbb E[(L-q_\alpha)_+].
\]

也可以写成优化形式：

\[
\operatorname{CVaR}_\alpha(L)
=
\min_\tau
\left[
\tau+
\frac1\alpha
\mathbb E(L-\tau)_+
\right].
\]

这一形式对 mini-batch 讨论尤其有用。

### 512 个良性、5% 尾部并不是“正好 25 个”

若恰有：

\[
n_b=512,
\qquad
\alpha=0.05,
\]

那么：

\[
\alpha n_b=25.6.
\]

所以：

- top-25 实际对应

\[
25/512
=
0.048828125,
\]

即约 **4.883%**；

- top-26 对应

\[
26/512
=
0.05078125,
\]

即约 **5.078%**。

若要严格表示经验分布的 5% CVaR，并假设损失从大到小排列：

\[
L_{[1]}\ge L_{[2]}\ge\cdots,
\]

则正确的 fractional boundary 是：

\[
\widehat{\operatorname{CVaR}}_{0.05}
=
\frac{
\sum_{j=1}^{25}L_{[j]}
+
0.6L_{[26]}
}{25.6}.
\]

所以“worst 5% = top 25 mean”本身已经存在一个小的定义误差。

如果每批良性数量只是“约 512”，问题更明显。应使用该批实际：

\[
n_b^{(t)}
\]

来计算 tail mass，而不是永远固定 \(k=25\)。

### CVaR 的有效尾部样本量确实只有约 26

一般而言，在连续分布和足够正则的条件下，经验 CVaR 的一阶 influence term 可以写成：

\[
IF(L)
=
\frac1\alpha
\left[
(L-q_\alpha)_+
-
\mathbb E(L-q_\alpha)_+
\right].
\]

因此渐近方差：

\[
\operatorname{Var}(\widehat C_\alpha)
\approx
\frac1{n_b\alpha^2}
\operatorname{Var}\left[(L-q_\alpha)_+\right].
\]

令尾部 excess：

\[
Z=L-q_\alpha\mid L>q_\alpha,
\]

其条件均值和方差分别是：

\[
\mu_+=\mathbb E[Z\mid L>q_\alpha],
\]

\[
\sigma_+^2=\operatorname{Var}(Z\mid L>q_\alpha).
\]

则

\[
\operatorname{Var}\left[(L-q_\alpha)_+\right]
=
\alpha\sigma_+^2
+
\alpha(1-\alpha)\mu_+^2.
\]

所以：

\[
\operatorname{Var}(\widehat C_\alpha)
\approx
\frac{
\sigma_+^2+(1-\alpha)\mu_+^2
}{
n_b\alpha
}.
\]

代入：

\[
n_b=512,\qquad\alpha=0.05,
\]

有：

\[
n_b\alpha=25.6.
\]

标准误量级：

\[
SE
\approx
\frac1{\sqrt{25.6}}
\sqrt{
\sigma_+^2+0.95\mu_+^2
}.
\]

而：

\[
\frac1{\sqrt{25.6}}
\approx0.198.
\]

所以可以非常直观地说：

> 对尾部尺度而言，单批 CVaR 的采样噪声是“二十几个有效尾部样本”的量级，而不是“512 个样本均值”的量级。

这是合理且重要的预期。

但不能给出一个具体的 CVaR 数值误差百分比，因为那还取决于你们实际 CE 尾部分布的 \(\mu_+\)、\(\sigma_+\) 和尾厚度。

### CE 尾部还存在理论上的重尾问题

交叉熵对极端错误概率并没有有限上界。

例如二分类真良性 \(y=0\)，预测 DGA 概率 \(p\) 时：

\[
\ell_{\rm CE}
=
-\log(1-p).
\]

当

\[
p\rightarrow1,
\]

有：

\[
\ell_{\rm CE}\rightarrow\infty.
\]

所以不能在不加条件的情况下使用“损失有界，因此 concentration 为……”这类证明。

如果实际程序进行了 logit clipping／probability clipping，可以基于该实际边界分析；否则最好只声称有限样本经验风险，不给 distribution-free bounded-loss guarantee。

### 经验 CVaR 还有有限样本乐观偏差

定义：

\[
\hat C_n
=
\min_\tau
\left[
\tau+
\frac1{\alpha n}
\sum_{i=1}^n(L_i-\tau)_+
\right].
\]

因为对任意随机函数 \(f_n(\tau)\)：

\[
\mathbb E[\min_\tau f_n(\tau)]
\le
\min_\tau\mathbb E[f_n(\tau)],
\]

所以在相应正则条件下，empirical optimized CVaR 存在典型的有限样本向下／乐观偏差：

\[
\mathbb E[\hat C_n]
\le
C.
\]

直观上：

> 同一批样本既决定“哪里是尾部阈值”，又用于估计该尾部的平均损失，有限样本下会有 optimization bias。

在光滑密度、有限矩条件下，这类 plug-in 偏差通常随 \(n\) 消失；但不要在没有附加条件时宣称精确 \(O(1/n)\) 对所有分布成立。VaR 附近有原子、平坦区或重尾时行为会变差。

### 最重要的事实：batch CVaR 的平均不等于 full-data CVaR

给一个完全离散的反例。

有四个良性损失：

\[
100,\ 99,\ 98,\ 0.
\]

分两个 batch：

\[
B_1=(100,99),
\qquad
B_2=(98,0).
\]

取最坏 50%，即每批 top-1。

batch CVaR 平均：

\[
\frac{100+98}{2}
=
99.
\]

但把四个样本放一起，最坏 50% 是：

\[
100,\ 99,
\]

所以 full-data CVaR：

\[
\frac{100+99}{2}
=
99.5.
\]

因此：

\[
\frac1M\sum_b
\operatorname{CVaR}_\alpha(B_b)
\neq
\operatorname{CVaR}_\alpha
\left(
\bigcup_bB_b
\right).
\]

原因不是代码误差，而是：

\[
\operatorname{TopTail}
\]

是非线性算子。

### 所以 batch top-k SGD 在优化什么

如果每批独立随机抽样，那么它更准确对应：

\[
J_{\rm batch}(\theta)
=
\mathbb E_B
\left[
\widehat{\operatorname{CVaR}}_\alpha(B;\theta)
\right].
\]

而不是有限训练集上的精确：

\[
J_{\rm full}(\theta)
=
\operatorname{CVaR}_\alpha
\left(
\{\ell_i(\theta)\}_{i=1}^N
\right).
\]

随着 batch 中良性样本数：

\[
n_b\rightarrow\infty,
\]

并在常规 i.i.d.／正则条件下，二者才逐渐逼近同一个 population tail risk。

所以论文不要写：

> “每个 batch 的 top 5% 给出了全数据 CVaR 的无偏 stochastic gradient。”

这句话一般不成立。

### hard top-k 还有一个优化层面的不光滑问题

设排序中的第 25 和第 26 个损失非常接近：

\[
L_{[25]}\approx L_{[26]}.
\]

参数微小变化就可能交换两者：

\[
S_{\rm tail}(\theta^-)
\neq
S_{\rm tail}(\theta^+).
\]

因此 hard CVaR 对 \(\theta\) 是分段光滑的，但在排名交换边界处非光滑。

如果边界附近聚集大量良性样本，batch-to-batch 梯度会明显抖动。

这不是错误，但应该避免声称：

> “CVaR branch provides a smooth safety constraint.”

它不是。

### 一个比 batch top-k 更干净的实现形式

若希望论文里的目标真的是 population CVaR，更理论一致的办法是保留辅助阈值：

\[
J_{\rm ben}(\theta,\tau)
=
\tau
+
\frac1\alpha
\mathbb E_{\rm ben}
[
(\ell_\theta(x)-\tau)_+
].
\]

mini-batch 估计：

\[
\hat J_{\rm ben}
=
\tau+
\frac1{\alpha n_b}
\sum_{i=1}^{n_b}
(\ell_i-\tau)_+.
\]

对于**固定的 \((\theta,\tau)\)**，样本平均项是总体期望的标准无偏 Monte Carlo 估计：

\[
\mathbb E_B[\hat J_{\rm ben}(\theta,\tau)]
=
J_{\rm ben}(\theta,\tau).
\]

然后联合更新：

\[
\theta,\tau.
\]

这与：

> 每批先自己算一个 top-5% 阈值，再只反传这 25 个样本

有本质区别。

前者的 stochastic objective 更容易理论描述。

当然，它的 \(\tau\) 学习本身仍有随机优化问题，但至少不会产生“每个 mini-batch 自己重新定义一个经验分位点”的 nested plug-in bias。

### CVaR 还有一个与最终 FPR 门完全不同的问题

这是审稿人很可能追问、而且相当有力的一点：

> **降低良性 CE 的 CVaR，并不数学上保证 FPR 不增。**

假设判恶意阈值是 0.5。

初始有 100 个良性样本：

- 4 个预测 DGA 概率 0.99；
- 其余很低。

则：

\[
FPR=4\%.
\]

更新后：

- 5 个样本都变成 0.60；
- 原来 0.99 的几个下降很多。

这时尾部平均 CE 完全可能下降，但：

\[
FPR=5\%.
\]

即：

\[
\Delta CVaR_{\rm CE}<0
\]

不推出：

\[
\Delta FPR\le0.
\]

CVaR CE 控制的是“高损失 benign score 的平均严重程度”，而 FPR 是：

\[
P(s(x)>\tau_{\rm cls}\mid Y=0),
\]

是越阈概率。

所以良性 CVaR 可以被称为：

> FPR-oriented differentiable tail surrogate，

但不要称：

> FPR safety guarantee。

最终 FPR 仍必须作为独立实证门。

## 跨三个问题最容易被审稿人抓住的结构性漏洞

### “group-relative”可能退化成普通 group hard mining

这是目前第一优先级攻击。

因为：

\[
A_i
=
\frac K{K-1}(u_i-\bar u),
\]

所以：

\[
\operatorname{rank}(A)
=
\operatorname{rank}(u).
\]

如果算法作用只是：

\[
A_i\rightarrow\text{top-q 入批},
\]

没有使用 advantage magnitude 做梯度权重，也没有用于 learned attacker 的 policy gradient，那么 reviewer 有充分理由认为核心运算只是：

\[
\text{same-clean-example group top-q mining}.
\]

这不是说机制一定没有价值，而是说**理论 novelty 不能建立在“组相对优势产生了新的组内排序”上**。

### group-relative centering 会把“绝对全难”误判为“没有优势”

例：

\[
u=(0.95,0.96,0.94,0.95).
\]

虽然全部很危险，但：

\[
A
\]

只表示它们彼此差多少。

这说明相对信号适合回答：

> 哪一个候选比自己的兄弟更强？

不适合单独回答：

> 这一组本身是否值得对抗训练？

两者需要两级信号：

\[
\text{group hardness}
\quad+\quad
\text{within-group relative hardness}.
\]

否则存在信息丢失。

### \(K=4\) 对真正的 max 是很弱的 Monte Carlo 覆盖

令真实扰动空间：

\[
\mathcal A(x).
\]

你们看到的只是：

\[
a_1,\ldots,a_4\sim\pi(\cdot|x).
\]

有限样本 max：

\[
\max_{i\le4}u(a_i)
\]

总有：

\[
\mathbb E\left[\max_{i\le4}u(a_i)\right]
\le
\sup_{a\in\mathcal A(x)}u(a).
\]

除非攻击分布几乎总能命中强扰动，否则不能把 best-of-4 写成真实 inner max。

更稳的称呼是：

> four-sample approximation to local adversarial risk。

### 两侧 tail emphasis 可能导致梯度尺度不对称

良性 CVaR 中每个 tail sample 的梯度权重约为：

\[
\frac1{\alpha n_b}.
\]

普通全体良性 CE 每个样本则是：

\[
\frac1{n_b}.
\]

所以单个尾部样本相对被放大：

\[
\frac1\alpha=20
\]

倍。

当然只有约 5% 样本非零，因此整体 CVaR 仍是“尾均值”，不是损失整体放大 20 倍。

但恶意侧如果每个 clean group 只保留 1 或 2 个候选，它的 per-selected-sample normalization 可能完全不同。

因此 \(\lambda\) 的含义必须基于**两个风险项最终如何归一化**定义，而不能只是沿用一个任意 scalar。

审稿人会合理地问：

> “你的 λ 在改变 K、q、α 或 batch class ratio 后还是同一个含义吗？”

### \(u=|s-y|\) 必须明确 \(s\) 是什么

若：

\[
s\in[0,1]
\]

是 DGA 概率，则：

对于恶意：

\[
y=1,\qquad u=1-s.
\]

这很好理解。

而 CE 为：

\[
-\log s.
\]

两者对 \(s\) 的排序完全一致，所以 hard-selection ranking 没问题。

但若 \(s\) 是 raw logit，则：

\[
|s-y|
\]

没有清晰概率语义，并且不再天然对应 misclassification severity。

所以方法正文必须明确：

\[
s=f_\theta(x)\in[0,1]
\]

还是 logit。

## 建议的统一数学重写

与其写成模糊的：

\[
\min_\theta
[
\max_{G_i^{mal}}E\ell
+
\lambda CVaR
],
\]

更推荐分开定义两个风险泛函。

### 恶意侧

对 clean malicious sample \(x_i\)，采样：

\[
\tilde x_{i1},\ldots,\tilde x_{iK}
\sim Q(\cdot|x_i).
\]

定义违规量：

\[
u_{ik}
=
u(\theta,\tilde x_{ik}).
\]

定义 top-\(q\) 索引：

\[
S_{i,q}
=
\operatorname{TopQ}
\{u_{i1},\ldots,u_{iK}\}.
\]

detector robust risk：

\[
\rho^{mal}_{K,q}(\theta;x_i)
=
\frac1q
\sum_{k\in S_{i,q}}
\ell_\theta(\tilde x_{ik},1).
\]

这样严格说明：

- 是 finite-\(K\) sample risk；
- 是 order-statistic hard mining；
- 不声称是 exact max；
- 不需要借 REINFORCE 无偏性来解释 detector gradient。

若有 learned attacker，再另外定义：

\[
A_{ik}
=
R_{ik}
-
\frac1{K-1}
\sum_{j\ne k}R_{ij},
\]

并让它**只服务于 \(\phi\) 的 policy update**。

### 良性侧

严格 population 形式：

\[
\rho_\alpha^{ben}(\theta)
=
\min_\tau
\left[
\tau+
\frac1\alpha
\mathbb E_{x\sim D_{ben}}
(\ell_\theta(x,0)-\tau)_+
\right].
\]

总目标：

\[
J(\theta)
=
\mathbb E_{x\sim D_{mal}}
[
\rho^{mal}_{K,q}(\theta;x)
]
+
\lambda
\rho_\alpha^{ben}(\theta).
\]

这比把两者都叫“内层玩家”更准确。

## 三个问题的审稿人攻击线与建议回应

| 问题 | 最强攻击线 | 不建议回应 | 建议回应 |
|---|---|---|---|
| Q1 | “两个 adversary 同时学会循环，凭什么收敛？” | “实验能收敛所以理论上没问题” | 明确当前非凸离散设置不主张全局 minimax 收敛；两侧基于同一 \(\theta\) 快照构造 active set、一次聚合更新；P3 与 learned-attacker P4 分开描述 |
| Q1 | “为什么先更新攻击侧再更新良性侧？” | “顺序无所谓” | 顺序有 \(O(\eta^2)\) 偏差；预注册 simultaneous gradient aggregation |
| Q2 | “LOO advantage 排名不是和 raw reward 一样吗？” | “但它来自 GRPO，所以不同” | 直接承认排序等价；将创新点放在 group-conditioned hard risk／absolute+relative two-level signal，而非声称新排序 |
| Q2 | “top-q 后怎么还能说 policy gradient 无偏？” | “baseline 无偏，所以整体无偏” | 明确 top-q 是 intentional biased truncation；若需要无偏 attacker PG，全 \(K\) 样本更新 \(\phi\)，top-q 只更新 detector |
| Q2 | “全组攻击都成功时 advantage 为零怎么办？” | “实际很少发生” | 这是结构反例，必须用 absolute hardness fallback 或把 relative advantage 限于 attacker control variate |
| Q3 | “batch CVaR 为什么等于 dataset CVaR？” | “batch 足够大” | 不相等；承认是 stochastic empirical surrogate，或使用共享 \(\tau\) 的 RU 形式逼近 population CVaR |
| Q3 | “25 个尾部样本够稳定吗？” | “batch 是 1024，很大” | 真正 tail effective count 约 25.6；报告源期稳定性／batch-size sensitivity，不把 1024 当有效尾部样本量 |
| Q3 | “CVaR 下降怎么保证 FPR 不升？” | “都是良性损失，所以能保证” | 不能保证；CVaR 是 tail surrogate，FPR 必须单独作为硬评价门 |

## 最值得优先做的三个低成本理论/实现核查

第一优先级不是训练，而是确认 detector-side selection 到底有没有真正使用 advantage magnitude。

若当前代码只是：

\[
A_i>0
\quad+\quad
\operatorname{TopQ}(A),
\]

那么应先与：

\[
u_i>\bar u
\quad+\quad
\operatorname{TopQ}(u)
\]

逐样本核对。按上述代数，两者理论上应完全相同，除非实现里还有别的权重或 tie-breaking 规则。

如果完全相同，则不能把 detector 这一侧的排序增量归因于 GRPO 风格 advantage。

第二优先级是构造三个手工 group：

\[
G_A=(0.99,0.99,0.99,0.99),
\]

\[
G_B=(0.10,0.11,0.12,0.13),
\]

\[
G_C=(0,0,0,0).
\]

只检查 selector 输出。

若规则是“positive advantage 才可入批”，应特别确认 \(G_A\) 是否被全部丢弃。这个反例不需要训练，就能判断机制语义是否和“inner max”矛盾。

第三优先级是 CVaR batch/full discrepancy 检查。无需模型，只使用抽象损失：

\[
(100,99)
\quad\text{与}\quad
(98,0)
\]

验证 per-batch top-tail 平均与 merged-data top-tail 不一致。

这样可以迫使论文在实现前就决定：

> 我们到底声称优化 population CVaR，还是 expected mini-batch tail risk？

## 最终建议表述

当前最容易防守的总方法定义，不应是：

> “两个内层 maximizer 的无偏 Monte Carlo minimax 求解。”

而应是：

> **双侧尾风险驱动的对抗训练 surrogate。** 恶意侧对每个原始域名构造有限扰动组，并优化组内 order-statistic hard risk；良性侧显式优化高损失尾部风险。两侧 active set 均在同一 detector snapshot 上构造并联合更新。若额外引入可学习攻击策略，组相对 leave-one-out advantage 仅作为攻击策略梯度的 control variate，其无偏性声明不延伸至 detector 的 hard top-\(q\) truncation。

这个版本牺牲了一些“GRPO 风格统一公式”的表面漂亮度，但数学上明显更稳。

## 来源、精确位置与核验状态

本轮按交接要求**未进行外部文献检索**。两个指定 GitHub 白名单文件：

- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/task_plan.md`
- `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/h-arm-research-question-card.md`

均分别尝试在 commit `e335c20ccf957e4a86b500a3982ea8ff68cbc1d0` 读取；其中首个路径又尝试了 branch `exp/ch3-drift-20260908`，GitHub 接口均返回 `404 Not Found`。为遵守白名单约束，没有搜索或访问其他仓库路径。

因此本报告的数学对象以用户消息中“框架表述”及 Q1–Q3 为准。上述反例、恒等式、Taylor 展开、REINFORCE 截断偏差和 CVaR 方差表达均为本轮直接数学推演，并非对仓库实现的核验结果。

## 不确定性与未回答问题

目前有几项实现细节会直接影响上述结论，但本轮不能从白名单正文核验：

**其一，top-\(q\) 是否只是 selector，还是 advantage magnitude 还继续乘进 detector loss。** 若存在连续权重：

\[
w_i=f(A_i),
\]

则“排序等价于 raw \(u\)”仍成立，但 advantage magnitude 可能产生额外更新差异；需要重新分析具体 \(f\)。

**其二，攻击候选是否条件独立。** 若四个 perturbation 是有关联的联合采样，LOO baseline 的简单无偏证明不成立。

**其三，\(q\) 是固定数量还是比例，以及 positive-advantage 条件在不足 \(q\) 个候选时如何补位。** 这决定“全组高难度但齐平”反例的实际后果。

**其四，良性 CVaR 是 top-25、top-26、fractional boundary，还是阈值形式。** 三者并非完全相同。

**其五，恶意侧是否已经存在可学习攻击参数。** 若没有，当前 P3 不应承担双玩家 minimax 的收敛主张；若有，则还需要额外审查 attacker–detector 两时间尺度、策略熵塌缩和 best-response lag。

**最重要的外部候选结论是：当前数学上最大的风险并非“双侧优化一定振荡”，而是 detector-side 的 leave-one-out group-relative top-\(q\) 在代数上很可能退化为普通组内 hard mining，同时 positive-relative gate 会丢失绝对组难度。这个点应在任何进一步机制包装之前由本地实现独立核对。**