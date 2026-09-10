# DRIFT 第三章机制候选深度研究：反事实优势路由

**状态：外部候选，待本地全文与实验复核；不构成候选存废裁决，不进入冻结台账。**

| 执行字段 | 实际值 |
|---|---|
| `actual_model` | **GPT-5.5 Thinking** |
| `actual_effort` | **high** |
| `actual_mode` | **deep-research** |
| `used_apps` | **github**：尝试按给定快照读取白名单内容，但连接返回 `404 Not Found`，未取得仓库正文；另使用公开 Web 检索一手论文 |
| `repository_snapshot` | 按发起方给定：`NatsuiroGinga/bilibili-note` / `exp/ch3-lamda-20260908` / `947551cb5a6ac9858c26495f927237b7e70bb060`；**本次未能通过 GitHub 连接独立验证** |
| `evidence_status` | 内部实验事实仅使用本消息的脱敏摘要；公开文献用于机制边界与近邻核查 |
| `temporal_contract` | **T17–T19 可用于设计、训练、校准；T20–T25 只作最终评价，不参与训练、调参、归一化统计、阈值选择、模型选择或适应** |

下文把发起方本消息中的脱敏实测记为 **[E-LOCAL]**。其中包括：T17/T18/T19 三路判定不一致率分别为 35.5%/34.4%/35.0%，静态融合错误中至少一个反事实支路可纠正分别有 6,823/10,356/11,499 个；朴素置信选择器劣于静态融合；以及 M1-v1、M1-v2、M2/J06、硬近邻、R02/R07、固定全局更新混合、N12 的止损结果。**这些内部数字本次均未重新验证。**

## 研究结论与立项边界

**主推外部候选：CARS — Counterfactual Advantage Routing with Safeguard，反事实优势路由与保护。**

这里最重要的限定是：**“可学习门控”“从多个专家里选一个”“预测哪个专家更可靠”本身绝不能作为创新点。** 稀疏 MoE 至少在 Shazeer 等人的 2017 工作中已经用可训练 gate 按样本选择专家；多专家 Learning-to-Defer 已直接研究如何估计 \(P(m_j=y\mid x)\)，即“第 \(j\) 个专家在这个样本上会不会正确”；2026 年的新工作甚至把“多专家下到底信谁”的 expert identifiability 作为核心难点来分析。citeturn39view1turn36view3turn41academia2

因此，CARS 候选的**可辩护差量必须收窄**为：

> **不重新学习“谁是专家”，也不更新 DRIFT 主干；把现有静态融合 C00 明确设成受保护的默认动作，以 T17–T19 上“支路相对 C00 的样本级反事实增益/伤害”作为监督目标，只在三路发生实际决策冲突且预测增益超过源期校准门时覆盖 C00，否则严格回退 C00。**

这使研究问题从“学一个更好的融合器”变成一个更窄、与 [E-LOCAL] 直接同构的问题：

\[
\text{何时存在可利用的 branch-over-fusion advantage，且能否在不制造更多错误的前提下识别它？}
\]

这个定位有三点好处。第一，它正打唯一已经充分量化的病灶：约三分之一源期样本存在反事实分歧，而 C00 的相当一批错误具有现成的可纠正动作 [E-LOCAL]。第二，它不要求再次改 DRIFT 表示学习，因此避免把此前 M1-v2 的基模型目标梯度与保护约束梯度直接塞进同一个参数更新。第三，它天然允许“什么都不做”：若支路优势不可识别，保护门可以退回 C00，而零训练正锚点应在真正训练 gate 之前就暴露这种退化。

但这一方案的**创新风险仍为中高**。多专家 L2D 已经直接学习专家正确率，2026 年 PiCCE 还依据经验正确性选择可靠专家；所以将来论文中不能写成“提出一种根据可靠性动态选择字符/子词专家的方法”。Verma 等在 AISTATS 2023 已明确研究多专家正确率估计；Liu 等 2026 的 PiCCE 又进一步表明多专家选择中的正确性监督与 identifiability 都已有直接先例。citeturn36view3turn42view0 **能否形成第三章级创新，必须由本地全文检索进一步核定“相对受保护融合基准的 counterfactual incremental utility + temporal no-target protected routing”这一组合是否仍有实质差量。**

公开的 DRIFT 论文与本课题的大方向是吻合的：Lee、Jung、Jeong 的 2026 论文研究 2017–2025 的纵向 DGA 漂移，并明确采用字符级与子词级混合表示以及三个自监督预训练任务；但本消息给出的具体三路反事实统计和 2025 指标属于本地脱敏证据，不能从公开摘要反推为已独立复现。citeturn32academia3

## 主推方案：CARS 反事实优势路由与保护

### 病灶到干预点的动机链

CARS 的动机不应从“动态融合通常比静态融合好”开始，而应严格从 [E-LOCAL] 的四步证据链开始。

**第一步：存在可利用的条件互补性。** T17–T19 的三路不一致率稳定在约 35%，说明静态融合、字符支路和子词支路并没有退化成几乎相同的分类器。[E-LOCAL]

**第二步：互补性与真实错误相交。** 在 C00 静态融合犯错的样本中，大量样本至少存在一个已经训练好的反事实支路能够给出正确决策。[E-LOCAL] 这比单纯的“支路 diversity”更有价值，因为它证明了动作集合中存在真实的纠错余量。

**第三步：但“有正确专家”不等于“能知道该信谁”。** 已做的启发式置信选择器 AUROC/AP 低于静态融合，说明单独拿 confidence/margin 当可靠性代理不够。[E-LOCAL] 这与多专家 L2D 文献揭示的 identifiability 风险方向一致：多一个专家并不自动使系统变好，因为系统还必须识别哪个专家在当前输入上可靠。citeturn36view3turn41academia2

**第四步：因此干预点不应再是全局权重，也不应继续改表示。** [E-LOCAL] 已显示固定全局更新专家混合即使存在瞬时三风险共同下降方向，也在短程优化后触发良性 BCE 止损；M1-v2 则出现近乎反向的目标/约束梯度。主推方向于是转为**冻结三个现有动作，学习“相对 C00 的局部动作价值”，并允许零覆盖回退**。这一点也与 DWM 的问题设定不同：DWM 是随概念漂移根据在线错误动态调整专家权重、删除低权重专家并加入新专家，而不是在固定源期学一个输入条件化的、未来不更新的 C00-relative router。Kolter 与 Maloof 的原始算法见 JMLR 2007 §3 和 Figure 1。citeturn31search5turn8view0

### 问题形式化

按脱敏摘要最自然的解释，令动作集合为

\[
\mathcal A=\{0,c,s\},
\]

其中 \(0\) 表示原 DRIFT 静态融合 C00，\(c\) 为字符支路，\(s\) 为子词支路。若本地实现实际还有不同定义的第三反事实动作，应只扩展动作索引 \(k\)，不改变下面的基本形式；这一点需本地白名单文件复核。

对输入 \(x\)，冻结后的三个动作分别输出 logit

\[
a_k(x), \qquad
p_k(x)=\sigma(a_k(x)),
\]

并按照 **C00 原有冻结分类阈值** \(\tau_0\) 得到

\[
\hat y_k(x)=
\mathbb I[p_k(x)\ge \tau_0],
\qquad y\in\{0,1\},
\]

其中约定 \(y=1\) 为 DGA，\(y=0\) 为良性。这里不建议因为 CARS 重新定义主分类阈值；否则“路由增益”会和普通 threshold tuning 混在一起。

每个动作的连续分类损失写为

\[
\ell_k(x,y)
=
-y\log p_k(x)
-(1-y)\log [1-p_k(x)] .
\]

真正与病灶直接对应的不是 \(\ell_k\) 本身，而是“相对 C00 的反事实变化”。对 \(k\in\{c,s\}\) 定义：

\[
R_k
=
\mathbb I[
\hat y_0\neq y,\,
\hat y_k=y
],
\]

即支路**救回一个 C00 错误**；

\[
H^{FP}_k
=
\mathbb I[
y=0,\,
\hat y_0=0,\,
\hat y_k=1
],
\]

即覆盖 C00 后**新制造一个良性误报**；

\[
H^{FN}_k
=
\mathbb I[
y=1,\,
\hat y_0=1,\,
\hat y_k=0
],
\]

即覆盖后**新制造一个 DGA 漏报**。

再定义连续的相对损失增益：

\[
\Delta_k
=
\ell_0-\ell_k.
\]

于是一个候选性的源期动作价值可写为

\[
u_k
=
\lambda_R R_k
-\lambda_{FP}H^{FP}_k
-\lambda_{FN}H^{FN}_k
+
\lambda_\Delta
\operatorname{clip}(\Delta_k,-b,b),
\]

并令

\[
u_0\equiv0.
\]

这里真正重要的是**结构**而不是当前系数数值：\(R_k\) 奖励真实纠错，\(H_k^{FP}\) 和 \(H_k^{FN}\) 显式刻画“为了救一边伤另一边”，\(\Delta_k\) 只提供决策边界附近的连续排序信息。鉴于最终硬门明确要求未来 FPR 不增加，候选上可以让 \(\lambda_{FP}\) 至少不小于普通错误代价，但具体比值绝不能从未来 T20–T25 反推，必须只在源期协议内冻结。

这也刻意区别于“预测每个专家是否正确”。AISTATS 2023 的多专家 L2D 已经研究 \(P(m_j=y\mid x)\)，所以若 CARS 只训练

\[
g_k(x)\approx P(\hat y_k=y\mid x)
\]

再选最大者，几乎就是直接近邻，而非有力创新。citeturn36view3 CARS 候选真正要检验的是

\[
g_{\phi,k}(z(x))
\approx
u_k(x,y),
\]

即**支路相对于受保护动作 C00 的增量效用**，而不是支路的绝对正确率。

### 高阶键与优势学习

路由器输入 \(z(x)\) 应只包含**推理时本来就能得到、且其处理参数在 T17–T19 冻结**的信息。基础版本可由：

\[
z_{\mathrm{pred}}
=
[
a_0,a_c,a_s,\,
|a_c-a_s|,\,
|a_c-a_0|,\,
|a_s-a_0|,\,
H(p_0),H(p_c),H(p_s),\,
\hat y_0,\hat y_c,\hat y_s
]
\]

构成。

这里 \(H(p)\) 是二分类预测熵。N14 所谓“高阶键”真正值得核查的，是**联合关系**而非再加一个单路 confidence，例如字符/子词表示间的差异、相似度或逐元素交互：

\[
z_{\mathrm{joint}}
=
[
|h_c-h_s|,
\,
h_c\odot h_s,
\,
\cos(h_c,h_s)
],
\]

但是否能直接使用这些中间表示、维数如何压缩，都必须以后由本地结构与预算复核。任何压缩器若需要训练，就已经不属于“零训练正锚点”；正锚点阶段只能使用已有表示的固定统计量。

候选优势头输出两个分数：

\[
g_\phi(z)
=
[g_{\phi,c}(z),g_{\phi,s}(z)].
\]

为防止仅拟合 utility 绝对尺度而不会排序，可采用“优势回归 + 动作排序”：

\[
\mathcal L_{\mathrm{adv}}
=
\frac1N
\sum_i
\sum_{k\in\{c,s\}}
\rho_\delta
\left(
g_{\phi,k}(z_i)-u_{ik}
\right)
+
\lambda_{\mathrm{rank}}
\sum_i
\sum_{j<k}
\log\left[
1+
e^{-(u_{ij}-u_{ik})(g_{ij}-g_{ik})}
\right],
\]

其中 \(\rho_\delta\) 为 Huber 型稳健损失；比较集合中可把 C00 看成固定的

\[
g_{\phi,0}=u_0=0.
\]

这样模型必须回答两个问题：“字符还是子词更值得用？”以及更关键的“**它真的比什么都不改的 C00 好吗？**”

这仍然是一种监督路由，因此论文写作中必须主动承认 MoE/L2D 邻域。Shazeer 等的经典 MoE 在 §1.2、§2、§2.1 已经给出可训练 gate、专家加权

\[
y=\sum_iG_i(x)E_i(x)
\]

以及联合反向传播训练；CARS 的差异不能写成“首次动态选专家”，而只能落在其受保护默认动作、relative counterfactual target、冻结专家和 temporal protocol 上。citeturn39view1

### 保护路由

定义三路硬判定存在分歧：

\[
D(x)=
\mathbb I[
|\{\hat y_0,\hat y_c,\hat y_s\}|>1
].
\]

候选支路为

\[
k^\star
=
\arg\max_{k\in\{c,s\}}
g_{\phi,k}(z).
\]

只有它与 C00 的最终类别不同，覆盖才有实质意义。令转换方向

\[
d(x)=
\hat y_0\rightarrow\hat y_{k^\star}
\in\{0\!\to\!1,1\!\to\!0\}.
\]

建议不用一个全局门 \(\delta\)，而使用两个**完全由源期校准的方向门**：

\[
\delta_{0\to1},\qquad
\delta_{1\to0}.
\]

原因是两个动作的风险并不对称：\(0\to1\) 可能新增良性 FPR，\(1\to0\) 可能新增恶意 FNR。最终覆盖指示量为

\[
m(x)=
\mathbb I[D(x)=1]\,
\mathbb I[
\hat y_{k^\star}\neq\hat y_0
]\,
\mathbb I[
g_{\phi,k^\star}(z)>\delta_{d(x)}
].
\]

最终输出为

\[
p_{\mathrm{CARS}}(x)
=
m(x)p_{k^\star}(x)
+
[1-m(x)]p_0(x).
\]

即：

\[
m=0 \Rightarrow \text{严格返回原 C00};
\qquad
m=1 \Rightarrow \text{只覆盖到一个既有支路}.
\]

这比连续 weighted fusion 更容易解释，也更适合做 rescue/harm 审计，因为每一个性能变化都能定位到“哪一条覆盖决策”。

### 为什么暂不拆成两个组件

**本候选不建议硬凑 \(2\times2\)。**

“优势预测”和“保护回退”表面看似两个模块，但后者的门值本身就是“相对于 C00 的预测优势”，二者不是像参照论文中“难度调度”和“展开优化”那样可分别关闭而仍保持同一语义的问题。强行写：

\[
\text{Advantage On/Off}
\times
\text{Safeguard On/Off}
\]

会遇到一个不可避免的问题：Advantage Off 时 Safeguard 根据什么分数决定是否覆盖？一旦换成 confidence、MoE gate 或固定最好支路，已经换了路由问题，而不是单纯关闭一个组件。

而且近期 L2D 理论也提醒，对复杂路由问题随意把耦合决策拆成独立 heads 可能引入一致性问题；2026 年 Montreuil 等针对“routing + advice”的扩展问题给出了 separated surrogates 可能不一致的反例。该论文场景并不等同于 DRIFT，但它足以说明“不为了漂亮的消融表而人为解耦”是更稳妥的研究习惯。citeturn41academia3

因此，**CARS 应按“一个不可约机制 + 直接近邻消融”组织**。若本地后续能证明某两个子机制真的具有独立语义和可单独运行的干预对象，再升级成 \(2\times2\)；当前阶段不先写结论再倒推结构。

### 与近邻方法的逐一边界

| 近邻 | 原方法真正做什么 | CARS 候选与它的必要区别 |
|---|---|---|
| **DRIFT 原静态融合** | 公开论文的核心是字符级与子词级混合 tokenization 和多任务自监督学习，以提升长期 DGA 漂移鲁棒性。citeturn32academia3 本消息进一步给出本地静态融合实现与反事实支路 [E-LOCAL]。 | 不改 tokenization、SSL 或主干参数；把已有字符支、子词支、静态融合视作三个冻结动作，只改变**发生分歧时的最终决策聚合**。 |
| **MoE** | Shazeer et al., ICLR 2017，§1.2、§2、§2.1：trainable gating network 选择 sparse expert combination，专家和 gate 可联合反向传播；Eq. (1) 是 \(y=\sum_iG_i(x)E_i(x)\)。citeturn39view1 | CARS 不是条件计算/扩大模型容量；专家已存在并冻结，不按 load balancing 培养专家；C00 本身是受保护动作，监督量是 **branch-vs-C00 incremental utility**。 |
| **多专家 L2D** | Verma, Barrejón, Nalisnick, AISTATS 2023：研究多专家 deferral 的一致 surrogate、校准，并估计 \(P(m_j=y\mid x)\)。citeturn36view3 | 因此“学习哪个支路会正确”不是创新。CARS 若成立，只能靠“**相对融合反事实增益 + protected no-override action + temporal source-only protocol**”形成差量。 |
| **PiCCE / 多专家 identifiability** | Liu et al., 2026，§3 分析 multi-expert underfitting / expert aggregation 与 identifiability；§4 提出 PiCCE，利用经验正确性做 data-dependent expert selection。论文第 2 页贡献概述明确标出 §§3–6。citeturn42view0turn41academia2 | 它进一步压缩了“correct expert selection”的新颖空间。CARS 不应宣称解决一般 multi-expert identifiability；只针对现有 DRIFT 三动作相对 C00 的局部覆盖问题。 |
| **SERAC** | Mitchell et al., ICML 2022，§3.1：SERAC 在 base model 外包一层，由显式 edit memory、scope classifier 和 counterfactual model 组成；in-scope 输入交给 counterfactual model，否则保留 base。论文总体目标是 model editing。citeturn11view1turn37view0 | CARS 没有 edit memory，不训练一个承接编辑的新 counterfactual predictor；“反事实”只是源期用真值问“若这次改走已有字符/子词支会怎样”。其 scope 不是 edit scope，而是相对 C00 的可纠错动作区域。 |
| **CADE** | Yang et al., USENIX Security 2021，§3.1–§3.2：用对比学习形成低维空间，并依据表示距离识别 drift samples，同时支持漂移解释。citeturn12view2 | CADE 回答“这个样本是否发生漂移/远离已有类结构”；CARS 回答“在已有三个预测动作中，哪个相对 C00 有正增益”。**漂移程度不等价于支路可靠性。** |
| **DWM** | Kolter & Maloof, JMLR 2007，§3 / Fig. 1：随在线错误降低专家权重、删除低权专家，并在整体犯错时增加专家，属于概念漂移下的动态集成。citeturn31search5turn8view0 | CARS 不读未来标签、不在线改权、不增加/删除专家；所有 route 参数和阈值在 T17–T19 冻结，T20–T25 完全静态执行。 |
| **PCT** | Yan et al., CVPR 2021，§4：Positive-Congruent Training 关注 model update 中旧模型原本正确、更新后变错的 negative flip；Focal Distillation 对旧模型正确样本加强 congruence。citeturn36view1 | CARS 不训练“新版本模型去模仿旧版本”；C00 参数本身完全不变，保护发生在**决策覆盖层**。因此思想上都含“别破坏原本正确的东西”，机制上不是 PCT。且 PCT 已被后续安全领域工作直接适配到 Android malware continual learning，不能把这种保护原则重新命名成创新。citeturn33academia3 |

其中 **SERAC 和 PCT 是必须主动讨论的两个“审稿人一眼会想到”的邻居**：CARS 的“默认保留 base、只在某种 scope 覆盖”形态和 SERAC 有外观相似性；“不要把 C00 原本正确样本改错”又和 PCT 的 positive congruence 有目标相似性。必须靠“无 edit memory/无 counterfactual model、无 model update/无 distillation、固定三动作上的 relative utility routing”把边界写死。citeturn37view0turn36view1

### 训练与推理协议

训练必须是**源期封闭的四阶段流程**。

**源期反事实构造。** 保留原 DRIFT C00、字符支、子词支，先冻结所有主干参数。用于生成 CARS 监督目标的预测最好来自源期 held-out/cross-fitted 预测，而不是用每个样本参与训练后的 in-sample correctness 直接教 gate，否则会把训练集记忆误当成“支路可靠性规律”。

**源期优势学习。** 只用 T17–T19 的 \(z(x)\)、三个冻结输出和标签构造 \(u_k\)，训练小型 \(g_\phi\)。不得将年份本身、未来家族身份、未来统计量作为 route key。年份可以用于 source validation 划分，但不建议成为推理特征。

**源期保护校准。** 在完全独立于 gate 拟合的 source validation 上选择

\[
\delta_{0\to1},\delta_{1\to0},
\]

目标不是追求最大 source F1，而是寻找满足本地“源年不塌”规定、且 source FPR 安全的非零覆盖点。**这一步是 post-hoc route calibration，不把 FPR 约束梯度回传到 DRIFT 或 gate objective。**

**未来只推理。** CARS、所有 normalization statistic、gate、阈值、特征定义在进入 T20 前全部冻结。T20–T25 每年只执行：

\[
x
\rightarrow
(p_0,p_c,p_s,z)
\rightarrow
g_\phi(z)
\rightarrow
m(x)
\rightarrow
p_{\mathrm{CARS}}.
\]

不能根据未来某一年的无标签分布重新做 temperature scaling、batch normalization statistic、分位点、阈值、路由覆盖率控制，更不能用 T20 结果决定 T21–T25 的设置。公开 DRIFT 工作本身采用多年纵向/forward-chaining 评估；本课题更严格的 T17–T19 / T20–T25 冻结合同以 [E-LOCAL] 为准。citeturn32academia3

### 消融矩阵

由于当前不把 CARS 假装拆成两个独立组件，建议消融不是 \(2\times2\)，而是用**“从 C00 到成熟直接近邻再到 CARS”**的证据链：

| 臂 | 定义 | 回答的问题 |
|---|---|---|
| **C00** | 原静态融合，完全不加 gate | 章内唯一主锚点；所有增量都相对它解释 |
| **C-H** | 已有 heuristic confidence selector | “仅凭置信度”是否已经足够；[E-LOCAL] 已给出负锚点，正式表需按最终同协议复核 |
| **C-STACK** | 仅用源期重新做简单 logistic/linear stacking 或同复杂度静态再融合 | CARS 的收益是不是普通静态重校准就能取得 |
| **C-MOE** | 冻结三个现有动作，用普通 softmax gating/weighted CE 学输入条件化组合 | “动态 gate”本身是否已经解释全部收益；MoE 是成熟直接邻居。citeturn39view1 |
| **C-L2D** | 预测 \(P(\hat y_k=y\mid x)\)，直接选择估计正确率最高动作 | relative-to-C00 advantage target 是否真的比成熟的 expert-correctness 思路有额外作用。citeturn36view3 |
| **C-A** | 用同一 CARS advantage head，但取消 safeguard，凡有分歧就 route 到预测优势最大的支路 | “C00 保护回退”是不是避免新伤害的关键 |
| **C-K** | 保留完整 CARS objective/safeguard，但 \(z\) 只允许 confidence/margin 等低阶键 | N14 的“高阶联合可靠性键”究竟是否提供超过朴素 confidence 的信息 |
| **CARS** | 相对 C00 advantage + joint keys + protected routing | 完整候选 |

还应加入一个**诊断性非部署上界**，但不要把它列成方法成绩：在源期 held-out 样本上，使用真值事后选择 \(\{0,c,s\}\) 中正确动作，计算可纠错 ceiling。它只回答“动作集合有多少理论空间”，绝不能进入最终部署对比，更不能用 T20–T25 oracle 结果反向决定 CARS 设计。

### 通过门、失败门与最小证伪

正式门仍应以发起方冻结合同为最高优先，本文不替本地改写。按用户给定要求，CARS 至少必须相对 C00 满足：

\[
\Delta FPR_{\text{future}}\le0,
\]

且

\[
\Delta FNR_{\text{unseen}}<0
\quad
\text{或}
\quad
\Delta TPR_{\text{family-macro}}>0,
\]

同时 source validation 不塌。[E-LOCAL]

作为**额外压力测试而非合同改写**，建议把“未来 FPR 不增”同时报告为 T20–T25 每年逐年的

\[
FPR^{\mathrm{CARS}}_t-FPR^{C00}_t,\quad
t=20,\ldots,25,
\]

而不是只报告六年平均，因为平均值可能用某些年份的改善掩掉另一些年份的误报恶化。正式是否要求“逐年都不增”仍由本地冻结协议裁决。

失败形态也应预先写明，而不是等结果后解释：

\[
\delta\rightarrow+\infty
\quad\Longrightarrow\quad
m(x)\equiv0
\quad\Longrightarrow\quad
\mathrm{CARS}=C00.
\]

这种情况虽然“安全”，但不是成功；它说明所有可利用的 rescue 区域在可观测 key 下都与 harm 区域纠缠，保护条件一加就不存在非零可行覆盖。

**预算最小的第一个实验不是训练 CARS，而是下文的零训练正锚点。** 只用已有 T17–T19 冻结输出/允许的已有表示统计，做 leave-one-source-year-out 的非参数 reliability table。若连这个表都无法在 held-out source year 上找到“可迁移的哪个支路更可靠”信号，同时满足非零覆盖、净 rescue 为正和良性安全，那么没有理由立即投入神经 gate；这会在一轮 optimizer 都不开的情况下证伪 N14/CARS 的核心前提。

## 备选机制

**备选一：BGO — Benign-Guarded Override，良性保护覆盖；针对“未来良性误报”。** 核心不是预测“哪个支路最好”，而只训练一个极窄的 source-only harm model，估计某个候选 \(0\to1\) 覆盖是否可能把 C00 原本正确的良性样本变成 FP；对 \(0\to1\) 采用严格 veto，对 \(1\to0\) 走独立门，其他情况保持 C00。它的优点是直接对准 2025 FPR 仍不饱和这一分面 [E-LOCAL]，且可把安全问题变成单向错误检测；但它排名低于 CARS，因为它只会告诉系统“别做危险覆盖”，没有完整利用 6,823/10,356/11,499 个可纠错机会，而且方法邻域非常靠近 cost-sensitive selective classification、PCT 式旧正确决策保护和 L2D，章级新颖度更危险。PCT 的核心就是对旧模型原本正确的样本施加更强 congruence，因此 BGO 若写成“保护正确旧决策”本身不具新颖性。citeturn36view1

**备选二：DCR — Drift-Conditioned Routing，漂移条件路由；针对“未见家族”。** 在冻结 DRIFT 支路之外，用**严格源期训练**的 CADE-style contrastive drift score 或 source-centroid distance 只作为一个额外 route key，问“远离源期已知结构的样本上，字符/子词哪一支的条件优势是否发生系统性变化”，最终仍不在未来更新。它针对未见家族 FNR 的直觉比 BGO 强；但排名更低，因为当前 [E-LOCAL] 只完整量化了“支路分歧→可纠错”，并没有量化“representation drift score→哪个支路正确”的链条。更重要的是，CADE 本身已经是 USENIX Security 2021 的成熟安全概念漂移方法，其 §3.1–§3.2 就通过 contrastive representation 和距离刻画 drift，因此“加一个 CADE 漂移分数”绝不能独立充当创新；它只能作为 CARS 的候选特征/公开基线，除非本地进一步发现新的、稳定的 route-conditioning 机制。citeturn12view2

没有把 family-specific 长尾方案排入前二，是因为 [E-LOCAL] 中 N12 的六个单任务臂已没有支持“family-specific 局部伤害”这一解释；在该证据状态下再把 source family reweighting 或 Group-DRO 类方案升为主备选，会绕开已有负证据而不是回应它。若将来只是采用成熟 family-balanced/group-robust weighting，也必须按原方法名称作为基线或组件，不应重新命名为章级创新。

## 反方视角与可证伪攻击

### 反驳：是不是只把 M1-v2 的梯度冲突搬到了决策层

这是最强反驳。

M1-v2 的表面失败是：

\[
\cos(\nabla L_{\mathrm{objective}},
\nabla L_{\mathrm{constraint}})
\approx -1,
\]

于是投影后无法离开 P0。[E-LOCAL]

CARS 通过冻结主模型并把 safety 从“同时反传的约束梯度”移到 post-hoc route threshold，确实消除了**同一参数空间内的直接梯度相撞**；但它完全可能只是把冲突改写成：

\[
\text{允许更多 override}
\Rightarrow
\text{救回更多 C00 错误}
\Rightarrow
\text{同时制造更多 FP/FN},
\]

从而一旦要求

\[
\Delta FPR\le0,
\]

唯一可行解仍是

\[
\mathrm{coverage}=0.
\]

也就是说，**优化死锁可能变成统计决策死锁。**

证伪方法应是训练任何大 gate 前就画 source held-out 的 route Pareto：

\[
(\text{override coverage},
\Delta FPR,
N_{\mathrm{rescued}},
N_{\mathrm{induced}})
\]

随 \(\delta\) 的曲线。必须寻找一个

\[
\text{coverage}>0,\quad
\Delta FPR\le0,\quad
N_{\mathrm{rescued}}>N_{\mathrm{induced}}
\]

的区域。如果零训练 lookup 或最小线性 gate 都没有任何这样的非零点，那么“搬位置”的反驳成立，CARS 的保护门最终只会把系统推回 C00。这个检验比看 gate AUROC 更重要。

### 反驳：35% 分歧只是 oracle headroom，不代表 selector 可识别

这是第二个根本问题。

[E-LOCAL] 已经证明“答案集合里经常有一个正确选项”，却还没有证明：

\[
P(k^\star=c\mid z)
\quad\text{或}\quad
P(k^\star=s\mid z)
\]

能够由推理时可见的 \(z\) 跨年份稳定预测。启发式 confidence selector 已经给过一个负结果，因此不能用“branch confidence 有差异”当正证据。[E-LOCAL]

多专家 L2D 文献恰好把这件事视为实质问题，而不是工程细节。Verma 等直接研究各专家正确率估计；Liu 等 2026 更指出多专家场景存在 intrinsic expert-identifiability 问题，并在 §3 分析其来源、§4 才提出 PiCCE。citeturn36view3turn42view0

**证伪检验：source-year transport，而不是随机 train/test split。** 在 T17/T18 上形成一个不训练梯度的 key→preferred-action 表，直接放到 T19；再循环三个 leave-one-year-out 方向。只关注字符与子词“恰有一个正确”的 exclusive-correct 子集。若 preferred-branch 的 held-out balanced accuracy 不能稳定超过 0.5，或者 train-year 的条件可靠性差异在 held-out year 大面积反号，则 learnable selector 的因果前提不存在。此时更大的 MLP 只会提高记住源期偶然相关性的能力。

### 反驳：它可能只是重新校准或 stacking，而不是新机制

第三个强反驳来自静态融合本身。

既然 C00 已经把字符和子词表示输入 MLP，审稿人可以非常合理地问：

> “为什么另加 router？也许你只是第二次利用同一组 logits/representation 做了 calibration；普通 stacking 或 source threshold retuning 会不会得到一样的改善？”

如果答案是“会”，那 35% 分歧仍是有趣诊断，但 CARS 不再是必要机制。

**证伪检验必须给 CARS 设置三个公平控制：**

\[
\text{C00 + source-only threshold retune},
\]

\[
\text{static logistic/linear stacking}(p_0,p_c,p_s),
\]

以及

\[
\text{generic frozen-expert MoE/L2D gate}.
\]

其中 generic MoE 与 L2D 都有直接成熟文献依据。citeturn39view1turn36view3 在同样的 T17–T19 参数选择协议、同样的输入信息预算下，如果这些控制已经达到 CARS 的 rescue/harm、FPR 和 future facet 改善，那么“反事实增益监督 + protected routing”没有证明其独立必要性。

同时结果表应把总性能拆成：

\[
\begin{aligned}
&\text{rescued benign FP},\\
&\text{rescued DGA FN},\\
&\text{induced benign FP},\\
&\text{induced DGA FN}.
\end{aligned}
\]

这样才能证明变化来自“选择对了已有支路”，而不是普通分数重标定。

## 可学习门控的正锚点资格核查

这里建议把 N14 的资格核查设计成一个**零梯度、两问式正锚点**。核心原则是：在训练可学习 selector 之前，必须分别证明“知道何时值得覆盖”和“知道覆盖时该选谁”都存在推理可观测信号。

### 固定诊断键

不拟合任何神经参数，只从已有源期输出定义少量预注册离散键：

\[
K_1=(\hat y_0,\hat y_c,\hat y_s),
\]

即三路决策模式；

\[
K_2=
\operatorname{rank}
(
|a_0|,
|a_c|,
|a_s|
),
\]

即 margin 的**相对顺序**，而不是“最高 confidence 自动赢”；

\[
K_3=
\operatorname{bin}
(
|a_c-a_s|
),
\]

表示字符/子词冲突强度；

若已有支路表示可以合法读取，则再考虑一个无需训练的

\[
K_4=
\operatorname{bin}
[
\cos(h_c,h_s)
].
\]

bin 边界只从用于构造 table 的 T17–T19 source 子集得到，并在 held-out source year 上固定。不得用 T20–T25 分位数。

### 正锚点一：branch-choice signal

只取

\[
\mathcal E
=
\{
x:
\hat y_c=y,\hat y_s\neq y
\}
\cup
\{
x:
\hat y_s=y,\hat y_c\neq y
\},
\]

即“字符和子词恰有一个正确”的样本。这是最纯粹的 **which-branch** 诊断。

对每个 source-training cell \(B(K)\)，计算

\[
\Delta_B
=
P(\hat y_c=y\mid B,\mathcal E)
-
P(\hat y_s=y\mid B,\mathcal E).
\]

只记录符号：

\[
\pi_B=
\begin{cases}
c,&\Delta_B>0\\
s,&\Delta_B<0.
\end{cases}
\]

随后**不再训练**，把这个 lookup rule 直接用于 held-out source year。

资格判据建议至少是：

\[
BA_{\mathrm{choice}}>0.5
\]

在每个 held-out source year 上方向一致，并且 pooled uncertainty interval 的下界也应排除纯随机选择；更重要的是，不能出现“大量高覆盖 cell 在 held-out 年可靠性符号反转”。这里 balanced accuracy 是为了避免某一个支路在 \(\mathcal E\) 中天然占多数造成伪成功。

这比“某个 key 与 correctness 的相关系数显著”更严格，因为它直接问**上一源年的 branch preference 能不能迁移到另一个源年**。

### 正锚点二：override signal

第二问是：即使知道字符/子词谁更可靠，什么时候应保持 C00？

定义 source-training cell 中三动作的经验价值：

\[
\bar u_k(B)
=
E[u_k\mid x\in B].
\]

无参数 lookup 决策为

\[
\pi(B)
=
\begin{cases}
\arg\max_{k\in\{c,s\}}\bar u_k(B),
&
\max_k\bar u_k(B)>0,\\
0,&\text{otherwise}.
\end{cases}
\]

把这个表冻结后放到 held-out year。资格不是“accuracy 比 0.5 高”，而必须同时出现：

\[
\mathrm{coverage}>0,
\]

\[
N_{\mathrm{rescued}}
>
N_{\mathrm{induced}},
\]

以及按本地源期安全定义

\[
\Delta FPR_{\mathrm{source}}\le0
\]

或至少落入本地已经冻结的允许范围。

换言之，零训练诊断必须找到一个**既可识别、又值得执行的非零决策区域**。

### 三种核查结果的解释

| 结果 | 解释 | 对 CARS 的含义 |
|---|---|---|
| which-branch 不过 | 三路有 oracle complementarity，但推理 key 不能识别该信谁 | **最直接否定 learnable gate 的前提**；不能拿更大网络“赌”未来 |
| which-branch 过、override 不过 | 知道哪个支路更可能好，但任何非零覆盖都会伤 C00 | 高度支持“把 M1-v2 冲突搬到 route layer”的反方解释 |
| 两者都过 | 至少存在无需神经训练即可跨 source-year 转移的条件可靠性结构 | 才有资格训练 CARS，并要求可学习 gate **超过这个 lookup 正锚点** |

这里还有一个关键的防自欺要求：**置信度 heuristic 必须保留为负锚点。** 如果所谓“高阶键”最终的 lookup 决策和“选 confidence 最大支路”几乎完全一致，那么 N14 没有发现新的 selector signal，只是在重新表达已失败的 heuristic。[E-LOCAL]

这种资格设计也正好回应了成熟 L2D 文献：专家正确率预测并不是新问题，而 multi-expert expert identification 本身可能失败；因此先证明 DRIFT 的两个反事实支路在 source temporal shift 下具有可识别的可靠性结构，比直接搭一个 gate 更有说服力。citeturn36view3turn42view0

## 成章后的章节骨架预判

若 CARS 最终通过本地资格核查、全文新颖性审核和正式实验门，建议按发起方给出的朱焱雷论文第三章组织逻辑成章，但**不要机械模仿其“两独立组件”形式**。当前 CARS 应围绕“一条病灶—机制—反证—增量”主线展开。

| 章节位置 | 建议内容 |
|---|---|
| **3.1 引言** | 先立 DRIFT 的强基线：整体 F1 已很高，因此本章不是“再做一个更大模型”。随后给三个未饱和分面：未来良性 FPR、未见家族 FNR、family-macro TPR [E-LOCAL]。真正引出机制的核心图应是 T17–T19 约 35% 三路分歧 + C00 错误中大量存在可纠正支路；紧接着给 heuristic confidence selector 负结果，形成“**有 oracle opportunity，但 naive chooser 失败**”的研究问题。 |
| **3.2 相关工作** | 四条线足够：DRIFT/DGA temporal drift；MoE 与 multi-expert Learning-to-Defer；CADE/DWM 等 drift-aware detection/ensemble；SERAC/PCT 等 scope/protection 思想。重点不是罗列，而是明确排除“动态门控就是创新”“保护旧预测就是创新”“counterfactual 这个词就是 SERAC 类方法”等错误表述。MoE 已有 trainable sparse routing；AISTATS 2023 已有 multi-expert correctness estimation。citeturn39view1turn36view3 |
| **3.3 方法** | 先形式化 \(\{C00,c,s\}\) 三动作和 disagreement set；再定义 rescue、induced FP、induced FN、\(\Delta_k\)、\(u_k\)；说明为何预测的是 branch-over-C00 advantage 而不是 expert correctness；定义 joint reliability keys、advantage learning objective、directional safeguard、最终 hard fallback；最后给完整算法伪代码和“source fit → source calibrate → freeze → future evaluate”时间边界。 |
| **3.4 实验设置** | 数据和 DRIFT 主模型沿冻结协议；T17–T19 只用于 base/gate/cross-fit/calibration，T20–T25 只评价。基线至少包括 C00、confidence selector、static stacking、generic MoE-style gate、multi-expert-correctness/L2D-style selector。指标沿既有协议报告，并特别增加 route coverage 与 rescue/harm decomposition。有关 MoE/L2D 的成熟形式必须按原名引用。citeturn39view1turn36view3 |
| **3.5 实验结果与分析** | 第一张表先复现 C00 锚点，再与已发表/直接近邻同协议重跑；第二张表放 C-H/C-STACK/C-MOE/C-L2D/C-A/C-K/CARS 消融，不做虚假的 \(2\times2\)。随后给 \(\delta_{0\to1},\delta_{1\to0}\) 的 coverage–FPR–rescue 敏感性；尤其报告是否出现 \(\delta\to\infty\)、coverage→0 的“安全但无效”退化。单次运行沿原课题报告风格，不额外伪造多种子结果。 |
| **3.6 案例与进一步分析** | 不应只挑几个成功域名讲故事。主分析应是 key-cell reliability map、字符/子词 preference 在 T17→T18→T19 的符号稳定性、四类 rescue/harm 计数、route coverage 分层，以及 simple stacking 与 CARS 的差异。若正式未来评估完成，可只作**冻结后的事后解释**讨论 unseen/seen family、长尾 family 的 route 分布，绝不能据此再改 gate。 |
| **3.7 本章小结** | 回答三个问题：静态融合错误是否有可执行而非仅 oracle 的支路互补性；relative advantage + safeguard 是否比 confidence/MoE/L2D 直接近邻更有效；严格 source-only 冻结后是否满足原通过门。若任一问题失败，按真实结果总结，不把回退到 C00 包装成成功。 |

这种写法仍保留参照章节最有价值的论证结构：**先把基线数字立锚，再对机制做直接近邻/去机制消融，每个声称的增益都有对应反证臂。** 不同点只是 CARS 当前没有被证实具有两个真正可独立开关的机制，所以不应为了形式对称照搬参照论文的双组件结构。

## 来源、精确位置、不确定性与未回答问题

### 原始文献与位置

| 文献 | 本报告使用的精确位置 | 支撑点 |
|---|---|---|
| **Lee, Chaeyoung; Jung, Chaeri; Jeong, Seonghoon. _DRIFT: Drift-Resilient Invariant-Feature Transformer for DGA Detection_. 2026；发起方标注 DSN 2026。** | arXiv:2605.10436，**Abstract** | 2017–2025 纵向 DGA 漂移；character/subword hybrid；三项 self-supervised pretraining；forward-looking temporal robustness。公开摘要支持这些总体事实，具体内部指标仍来自 [E-LOCAL]。citeturn32academia3 |
| **Mitchell, Eric; Lin, Charles; Bosselut, Antoine; Manning, Christopher D.; Finn, Chelsea. _Memory-Based Model Editing at Scale_. ICML 2022.** | **§3.1 SERAC Architecture**；论文摘要亦说明 explicit memory + counterfactual modulation | SERAC 的 base + edit memory/scope classifier/counterfactual model 边界；不能把“有 fallback 的 route”笼统称作 SERAC 式创新。citeturn11view1turn37view0 |
| **Shazeer, Noam et al. _Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer_. ICLR 2017.** | **§1.2**, **§2**, **§2.1**；Eq. (1)–(5)；ar5iv lines 32–70 | 可训练 gate、稀疏专家组合、\(y=\sum_iG_iE_i\)、softmax/noisy-top-k 和联合反向传播都已有成熟先例。citeturn39view1 |
| **Yang, Limin; Guo, Wenbo; Hao, Qingying; Ciptadi, Arridhana; Ahmadzadeh, Ali; Xing, Xinyu; Wang, Gang. _CADE: Detecting and Explaining Concept Drift Samples for Security Applications_. USENIX Security 2021.** | **§3.1–§3.2**；漂移表示与检测设计 | CADE 用 contrastive representation / distance 刻画 drift，而不是在 DRIFT 已有支路中预测 branch-over-fusion advantage。citeturn12view2 |
| **Kolter, J. Zico; Maloof, Marcus A. _Dynamic Weighted Majority: An Ensemble Method for Drifting Concepts_. JMLR 8, 2007, pp. 2755–2790.** | **§3**, 尤其 pp. 2763–2764、**Figure 1** | 根据在线预测错误动态降低权重、删专家、加专家；与 CARS 的 frozen source-only instance routing 区别明确。citeturn31search5turn8view0 |
| **Yan, Sijie; Xiong, Yuanjun; Kundu, Kaustav; Yang, Shuo; Deng, Siqi; Wang, Meng; Xia, Wei; Soatto, Stefano. _Positive-Congruent Training: Towards Regression-Free Model Updates_. CVPR 2021 Oral.** | **§4 Positive Congruent Training**；公开摘要 lines 16–19 | negative flip、只对旧模型正确样本加强 congruence、Focal Distillation。citeturn36view1 |
| **Verma, Rajeev; Barrejón, Daniel; Nalisnick, Eric. _Learning to Defer to Multiple Experts: Consistent Surrogate Losses, Confidence Calibration, and Conformal Ensembles_. AISTATS 2023.** | arXiv abstract **lines 16–19**；全文为 multi-expert L2D | 已明确研究 \(P(m_j=y\mid x)\)；故“学习哪个专家正确”不能作为 CARS 新意。citeturn36view3 |
| **Liu, Shuqi; Cao, Yuzhou; Feng, Lei; An, Bo; Ong, Luke. _When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer_. 2026 preprint.** | **§3** multi-expert underfitting/aggregation；**§4** PiCCE；第 2 页 contribution summary | 多专家下“该信谁”的 identifiability 不是平凡问题；PiCCE 已利用 empirical correctness 做 data-dependent expert choice。citeturn42view0turn41academia2 |
| **Ghiani, Daniele et al. _Regression-aware Continual Learning for Android Malware Detection_. 2025 preprint.** | **Abstract** | PCT 思想已经被直接移植到 malware continual learning；安全领域不能把“保护旧正确判断”当成无人涉足的新点。citeturn33academia3 |
| **Montreuil, Yannis; Carlier, Axel; Ng, Lai Xing; Ooi, Wei Tsang. _Beyond Augmented-Action Surrogates for Multi-Expert Learning-to-Defer_. 2026 preprint.** | **Abstract / theoretical result on separated routing–advice surrogates** | 仅作为“不应为漂亮消融强行拆耦合机制”的辅助警示；其 advice setting 与 DRIFT 并不相同，不能直接当 CARS 理论依据。citeturn41academia3 |

### 本次能够确定的逐项证据

| 判断 | 证据强度 | 来源 |
|---|---|---|
| DRIFT 的字符/子词组合确实天然形成可研究的互补动作空间 | **中等偏强** | DRIFT 公开论文确认 hybrid character/subword 架构；具体 35% 分歧和 rescue 计数来自 [E-LOCAL]。citeturn32academia3 |
| 静态融合错误存在显著 oracle-correctable headroom | **强，但仅限本消息内部实测** | [E-LOCAL]：6,823 / 10,356 / 11,499 |
| “最大 confidence 选支路”不足以利用该 headroom | **强，但仅限本消息内部实测** | [E-LOCAL]：heuristic selector AUROC/AP 均低于静态融合 |
| “可学习 gate”本身没有新颖性 | **很强** | MoE、multi-expert L2D 已成熟。citeturn39view1turn36view3 |
| “根据专家正确性选专家”也不能作为新颖性 | **很强** | Verma et al. AISTATS 2023；Liu et al. 2026 PiCCE。citeturn36view3turn42view0 |
| CARS 与 SERAC 不是同一机制 | **较强** | SERAC 有 explicit edit memory、scope classifier 和新的 counterfactual model；CARS 候选只有冻结既有动作上的 relative routing。citeturn11view1turn37view0 |
| CARS 与 DWM 不是同一机制 | **强** | DWM 是有反馈的在线权重/专家池更新，CARS 明确禁止未来更新。citeturn31search5turn8view0 |
| CARS 与 PCT 不是同一实现机制，但有“保护旧正确决策”的概念邻近 | **强** | PCT 是 model-update congruence/Focal Distillation；CARS 是 frozen-model routing。citeturn36view1 |
| CARS 是否足够构成硕士论文第三章级创新 | **未确定** | L2D/PiCCE 已大幅压缩新颖空间，必须本地全文复筛后裁决。citeturn36view3turn42view0 |

### 仍未回答且必须保留的不确定性

**最重要的未回答问题不是“gate 要几层”，而是 selector identifiability。** [E-LOCAL] 只证明“至少有一个支路能纠错”，尚未证明“无需标签时可以知道是哪一个”。这就是为什么零训练正锚点应置于所有实现之前。多专家 L2D 的最新理论恰好表明，专家更多并不自动带来更好的最终系统。citeturn42view0

**第二个未回答问题是 CARS 的新颖性差量是否足够厚。** “counterfactual advantage relative to protected fusion”目前是一个合理的 task-specific formulation，但很可能被审稿人解释为 two-stage L2D、post-hoc routing、selective ensemble 或 PCT-like protection 的组合。公开文献已经表明多专家正确率估计、两阶段路由和安全保护各自都很成熟。citeturn36view3turn41academia2turn36view1 因而本地全文复筛必须特别检索“post-hoc model routing / classifier routing / multi-expert deferral / complementarity / negative flip / protected ensemble / counterfactual expert selection”等交叉邻域，而不能只查 DGA 文献。

**第三个未回答问题是本地“三支路”的精确定义和可提取 feature contract。** 本报告按摘要将三动作形式化为 C00 static fusion、character-only、subword-only；GitHub connector 未能取得白名单正文，因此没有独立确认支路 logit、阈值、representation API、cross-fit 现状或本地臂命名。故所有 \(a_0,a_c,a_s\) 和 \(h_c,h_s\) 的设计都属于外部候选数学接口，而不是对现有代码的断言。

**第四个未回答问题是“源年验证不塌”的冻结数值定义。** 本消息只给出原则，没有给容忍区间。本报告故意没有新增诸如“F1 不下降 0.2 个百分点”之类阈值，以免私自改写冻结合同。[E-LOCAL]

**第五个未回答问题是未来 FPR 门究竟按逐年还是聚合判定。** 本报告建议将 T20–T25 逐年差值作为额外压力分析，但不把它升级为本地正式裁决规则；正式门仍以发起方冻结合同为准。无论采用何种呈现，T20–T25 均必须保持**纯评价**，不得反向参与 CARS 的 utility、feature、gate、阈值、超参数或模型选择。[E-LOCAL]

**最终结论：** 在当前只读证据状态下，**CARS 是最值得先做“零训练正锚点资格核查”的外部主候选**，因为它直接对准当前唯一完整量化的失败机制，而不是重新追逐已被多次源期止损否定的表示更新、全局权重或 family-local 优化方向。[E-LOCAL] 但它目前**不是已经确立的创新方法**：MoE、multi-expert L2D、PiCCE、SERAC、PCT、CADE、DWM 都形成了必须正面跨越的成熟邻域。citeturn39view1turn36view3turn42view0turn37view0turn36view1turn12view2turn31search5 因此正确的第一步不是实现完整 CARS，更不是看 T20–T25，而是仅用 T17–T19 做 **which-branch signal + override signal** 的零梯度跨源年正锚点；只有这个前提成立，训练可学习路由器才具有实验上的立项资格。**本报告全部结论仍为外部候选，必须由发起方在本地全文与实验条件下独立复核后再决定是否进入台账。**