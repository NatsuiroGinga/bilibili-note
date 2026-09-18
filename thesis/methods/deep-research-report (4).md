# LAMDA 固定表征下的修复空间：同任务双头、部署侧组合、选择性更新与 Margin 带的文献审查

**状态：全部结论均为外部候选建议，待本地全文与实验独立复核；不构成 LAMDA 候选存废裁决，不修改既有固定阈值、数据边界、回放容量或封印合同。**

## 核心结论

基于本次对**原始论文、会议页面、arXiv 与作者/组织官方 GitHub**的检索，主问题可以给出一个相当明确的回答：

> **有成熟路线能够“不给旧全局表征继续漂移，也增加局部修复自由度”，但成熟答案不是再换一种全局正则，而是把“默认旧行为”和“局部修复行为”拆成两个预测路径，再学习何时允许修复路径接管。**

本次找到的最直接机制近邻不是传统 Task-IL 多头，而是 **SERAC 的 base model + scope classifier + counterfactual model**：基模型保持原行为，编辑模型负责修改，另一个 scope classifier 判断输入是否属于应当修改的局部区域。ICML 2022 原文明确把“**什么时候该变**”与“**该怎么变**”拆开，§3.1 Eq. (1) 规定 scope 外走 base、scope 内走 counterfactual model，§3.2 Eq. (2)–(3) 分别训练 scope 与编辑行为；其评价还显式同时看 edit success 与对其他样本的 drawdown。这个结构与“保守头 + 修复头 + 风险路由器”高度同构，只是原任务是模型编辑而非 Android 恶意软件持续检测。citeturn5search1turn12view0turn12view1turn13view2

第二个非常重要的直接近邻是 **DriftSurf**。它不是 per-sample 双头，却是在**同一监督任务、同一标签语义**下同时维护旧的长期模型与新的 reactive model；进入 reactive state 后，根据最近一个时间片的已确认性能选择哪个模型负责预测，只有新模型真正优于旧模型后才切换，从而避免一次疑似 drift 就立即抛弃旧模型。论文把这描述为 stable-state/reactive-state learning，并特别指出 reactive state 可以过滤很多 drift detector 的 false alarms。这里的 “false positive” 是**漂移告警误报**，不是 LAMDA 的 benign FPR，二者绝不能混写。citeturn17search0turn17search1turn18view0

因此，针对你给出的八连败结构，**最值得进一步筛查的文献化方向并不是“再冻结更多参数”，而是“冻结默认路径，但给极少数输入一个局部替代路径”**。这一点与 warm-start head-only 的失败并不矛盾：warm-start 仍只有**一个全局映射**；scope-routed patch 则改变了函数族。对冻结表征 \(h(x)\)，哪怕两个预测头都很小，只要 gate \(g(h)\) 能用完整冻结特征而不仅是旧标量分数，组合

\[
s(x)
=
(1-g(h(x)))\,s_{\rm conservative}(h(x))
+
g(h(x))\,s_{\rm repair}(h(x))
\]

就可以形成输入条件化的分段决策函数。换言之，**“不移动 backbone”不等于“不能增加决策局部性”**。但如果冻结表征本身把需要修复的恶意和会受伤的良性映射成无法区分的表示，那么任何只读取该表示的 gate/head 都无能为力；这仍需要来源年实验判决，而不能从 SERAC 的其他任务结果外推成 LAMDA 结果。【外部推论，文献机制依据同上】citeturn12view0turn12view1

本次没有找到一个已经成熟、直接用于恶意软件／IDS 年度 CL、并且精确采用“**同一二元任务的保守头 + 修复头 + 各自独立阈值 + 固定总体 FPR gate**”的原始方法。最接近的是模型编辑的 local patch、concept-drift 的 stable/reactive 双模型以及输入条件化参数路由。因此，**不能把“修复头＋保守头”包装成某个成熟算法改名使用；同样也还不能据本次检索证明其组合具有论文层面的新颖性。**

综合本地交接包的八代结果，外部候选优先级可以概括为：

| 方向 | 是否真正避免继续移动旧表征 | 能否增加局部决策自由度 | 与当前病灶匹配度 | 建议地位 |
|---|---:|---:|---:|---|
| **scope-routed conservative/repair heads** | 是，可冻结 backbone | **是** | **最高** | 首个结构性候选 |
| old/new 模型按输入 gate | 可以 | **是** | 高，但 gate 本身是核心难题 | 首选近邻基线 |
| old/new 全局 ensemble／固定插值 | 是 | 有限 | 中 | 零训练诊断优先 |
| Temperature Scaling | 是 | **否** | 极低 | 不值得作为修复臂 |
| Platt／isotonic | 是 | 基本是操作点重映射 | 低 | 校准基线，不是修复主线 |
| SpotTune 式 sample-wise layer routing | **否，部分路径会更新表示** | 是 | 中高 | 冻结表征路线失败后的候选 |
| InfLoRA／低秩增量 | **否，有效表示仍改变** | 是 | 中 | PEFT/CL 对照 |
| 小 margin hinge／截断 repair loss | 是/取决于训练范围 | 不增加结构容量 | 中高 | 很便宜的损失级候选 |
| OHEM | 否/无关 | 不解决目标终点 | 与深埋 FN 甚至可能反向 | 不优先 |

其中“最高／中”等是**针对交接包病灶的外部研究排序，不是实验结论**。

## 同任务双头与“修复—保护”解耦

### SERAC 是目前最贴近的机制先例

Eric Mitchell、Charles Lin、Antoine Bosselut、Christopher D. Manning、Chelsea Finn 的 **Memory-Based Model Editing at Scale**, ICML 2022, PMLR 162:15817–15831，是本次最值得先全文对照的论文。SERAC 不直接改动原基模型来完成每次编辑，而是维护 edit memory；对查询输入，scope classifier 先判断它是否处于某次编辑的作用范围，作用范围外使用原 base model，作用范围内由 counterfactual model 给出替代预测。原文位置是 **§3，尤其 §3.1 Eq. (1) 与 §3.2 Eq. (2)–(3)**。citeturn5search1turn12view0turn12view1turn13view2

其思想与 LAMDA 的潜在任务化映射非常直接：

\[
\text{SERAC edit scope}
\longleftrightarrow
\text{“此样本是否允许恶意修复分支介入”},
\]

\[
f_{\rm base}
\longleftrightarrow
\text{冻结保守路径},
\]

\[
f_{\rm cf}
\longleftrightarrow
\text{修复路径}.
\]

但不能把 SERAC 直接称为 LAMDA 算法。它原本解决模型知识编辑，而且其编辑记忆和 counterfactual model 的容量条件与 LAMDA 的容量 200、年度流、二元 FPR 约束完全不同；特别是 SERAC 的关键失败点之一正是 **scope estimation**：如果 scope classifier 判断错，局部修改就会错误地扩散或漏掉。原文后续实验分析同样把 scope 判断视作关键难点。citeturn12view0

这与【本地转述】“修复训练自身有能力修 FN，但全局映射把大量 ER 原判对良性一起推过阈值”高度相关。这里真正应该由来源年实验检验的不是“两个头是不是比一个头强”，而是：

\[
\boxed{
\text{冻结表征中是否仍含有足够信息，使 gate 能区分 repair scope 与 benign collateral scope？}
}
\]

这是比“头能不能学习”更窄、更可证伪的问题。

### DriftSurf 给出了同任务“旧模型先保留，新模型先证明自己”的部署先例

Ashraf Tahmasbi、Ellango Jothimurugesan、Srikanta Tirthapura、Phillip B. Gibbons 的 **DriftSurf: Stable-State / Reactive-State Learning under Concept Drift**, ICML 2021, PMLR 139:10054–10064，在同一流式监督任务中维护长期稳定模型，并在检测到潜在漂移后启动第二个 reactive model。reactive 阶段的预测由近期表现更好的模型负责；如果新模型没有真正胜过旧模型，最终继续采用旧模型。机制描述集中在 **§1 与 §2**，论文之后给出风险竞争性分析。citeturn17search0turn17search1turn18view0turn18view1

这给 LAMDA 一个非常重要的边界：**“训练新模型”与“立即部署新模型”并不是必须绑定的操作。** 在 concept-drift 文献中，保留旧模型、让新模型经历 reactive probation 后再接管是成熟设计模式，而不是不规范的“作弊”。但 DriftSurf 的切换依据需要近期已确认标签／性能；若 LAMDA 部署时标签有延迟，只能使用当时已经合法到达的确认窗口，不能用尚未揭示的测试标签决定路由。citeturn17search1

DriftSurf 与你设想的 per-sample repair head 仍有本质区别：它主要是**时间段级 old/new model selection**，而不是针对某个 APK 的局部风险路由。若实际损伤在同一年、同一批数据内部同时存在，那么仅按年份选择一个整体模型仍可能重演 warm-start 的全局取舍。

### 这不是 Task-IL 的 task-specific multi-head

传统 task-incremental 多头通常把不同任务分配给不同输出头，并依赖已知 task ID 或可恢复的 task/domain identity。Expert Gate 一类方法甚至显式学习“该输入属于哪个任务专家”，每个专家负责不同历史任务。其路由语义是：

\[
x\rightarrow \text{task/domain}\rightarrow f_{\text{task}}.
\]

而这里讨论的是：

\[
x\rightarrow
\text{same-task repair scope / conservative scope}
\rightarrow
f_{\rm repair}\ \text{或}\ f_{\rm conservative}.
\]

两个分支都输出同一个 `{benign, malicious}` 标签空间；分支角色由**更新安全性**而不是任务身份定义。因此不能把它写成“采用 multi-head continual learning”；最接近的术语是 **local model patching / scope-gated editing / stable-reactive model selection**。Expert Gate 可作为反例边界，而不是直接基线。citeturn1search0turn1search4

### 双头什么时候真的比 warm-start head-only 多了东西

这里有一个非常关键的数学边界。

若两个冻结表征上的线性头只是做**固定全局插值**：

\[
s_o(h)=w_o^\top h+b_o,\qquad
s_n(h)=w_n^\top h+b_n,
\]

\[
s_\alpha(h)
=(1-\alpha)s_o(h)+\alpha s_n(h),
\]

则

\[
s_\alpha(h)
=
\big[(1-\alpha)w_o+\alpha w_n\big]^\top h
+
(1-\alpha)b_o+\alpha b_n.
\]

也就是说，它仍然只是**另一个线性头**。这并没有制造真正的局部性。

反之，如果

\[
\alpha=g(h)
\]

依赖样本特征，那么

\[
s(h)=(1-g(h))s_o(h)+g(h)s_n(h)
\]

通常已经不是单一线性头能表示的函数。**真正增加表达空间的是 feature-dependent routing，不是“多一个头”本身。**

因此，针对【本地转述】warm-start head-only 已能正常学习却 FPR 爆炸的现象，最有信息量的后续不是再跑两个全局头，而是比较：

\[
\text{单一全局头}
\quad\text{vs}\quad
\text{冻结双头＋只看旧 score 的 gate}
\quad\text{vs}\quad
\text{冻结双头＋看完整 }h(x)\text{ 的 gate}.
\]

这三个层次能够直接区分“只有全局操作点问题”与“冻结表示中存在局部可路由信息”。这是外部候选消融，不是要求现在运行。

## 推理侧组合与校准：哪些是真适应，哪些其实只是换操作点

### old/new ensemble 在漂移文献中完全有先例，但它不是天然的 FPR 保护

concept-drift 文献长期使用旧、新 experts 的 ensemble 或动态模型选择。DriftSurf 的 related work 将 ensemble 与 window-based、drift detection 并列为流式适应的主要家族，并明确描述旧专家适合非漂移状态、新专家适合漂移后状态，通常依近期性能加权；DriftSurf 自己则将模型数限制为至多两个，并让每个时刻只有一个模型负责实际预测。citeturn17search1turn18view0

因此，部署时保留 ER old model 和 repair new model，然后进行：

\[
s_\alpha(x)
=
(1-\alpha)s_{\rm old}(x)
+
\alpha s_{\rm new}(x)
\]

并不是学术意义上的不合法操作。它是新的组合分类器。

但**合法不等于符合本项目冻结合同**。如果 \(\alpha\)、gate threshold 或两个头各自的 class threshold 是看过开发 FPR 后自由调出来的，那么它们已经成为新的开发超参数。原项目明确冻结单一判定阈值 0.5，因此“保守头 0.7、修复头 0.3”这样的做法即便有部署文献先例，也不能借文献之名绕过本地合同。外部候选只能在合同允许的固定决策规则内测试。

本次没有找到一篇原始 concept-drift 论文把 old/new score blending 批评为“**变相调阈值**”这一标准术语。更准确的边界来自数学：**有些校准确实完全等价于改变原分数的有效阈值，有些 ensemble 则会真正重排样本。**

### Temperature Scaling 对当前固定 0.5 二元修复基本可以直接排除

Guo、Pleiss、Sun、Weinberger 的 **On Calibration of Modern Neural Networks**, ICML 2017, PMLR 70:1321–1330，在 **§4.2 Eq. (9)** 定义 Temperature Scaling：

\[
z\mapsto z/T,\qquad T>0.
\]

原文强调正温度不会改变 softmax 最大类别，因此不改变分类准确率。citeturn22view2turn23view1

对 LAMDA 二元 logit 更强：

\[
\sigma(z/T)\ge 0.5
\iff
z/T\ge0
\iff
z\ge0.
\]

所以在固定阈值 0.5 下：

\[
\boxed{\text{纯 Temperature Scaling 的 TP/FP/TN/FN 完全不变。}}
\]

它可以改善概率校准，但**数学上不可能修掉一个 FN，也不可能制造或修掉一个 FP**。因此在当前主问题中，TS 可以作为 calibration sanity baseline，却没有必要消耗一次“恶意修复 GPU 臂”。

### Platt Scaling 在二元固定阈值下就是有效阈值移动

Guo 等在 **§4.1** 给出二元 Platt scaling：

\[
q(z)=\sigma(az+b),
\]

其中 \(a,b\) 只用验证集学习，基础神经网络参数保持固定。citeturn22view0turn23view0

若 \(a>0\)，部署仍使用 calibrated probability 的 0.5 阈值：

\[
q(z)\ge0.5
\iff
az+b\ge0
\iff
z\ge -b/a.
\]

因此：

\[
\boxed{
\text{Platt + 固定 calibrated threshold 0.5}
=
\text{对原始 logit 使用新阈值 }-b/a.
}
\]

就**二元决策**而言，这不是“像调阈值”，而是数学上真正等价于换了有效阈值。它可能改善概率语义，却不能绕过【本地转述】“ER 标量分数在同 FP 预算下几乎没有 FN 可换”的操作点病灶。

### Isotonic 同样不会创造新的标量排序信息

Guo 等 **§4.1 Eq. (7) 附近**描述 isotonic regression：学习一个单调、分段常数的映射 \(q=f(p)\)。因为 \(f\) 被要求单调，原有分数顺序不会被反转。citeturn22view0turn23view0

于是对二元强制决策而言，寻找

\[
f(p)\ge0.5
\]

本质上仍是在原始 score 轴上寻找一个新的切分位置或区间边界。它可以制造 ties，也可以改善 calibration，但**不能从同一个一维分数中创造原本不存在的恶意—良性排序信息**。

这与【本地转述】“同 FP budget 重排 ER 自身分数，FN 几乎不动”共同意味着：**纯标量 calibration 很难是你要找的修复空间。**

### Continual Calibration 证明“每年度只改输出/校准层”本身有持续学习先例

Lanpei Li、Elia Piccoli、Andrea Cossu、Davide Bacciu、Vincenzo Lomonaco 的 **Calibration of Continual Learning Models**, CVPR Workshops 2024 / arXiv:2404.07817，在 **§2.1** 讨论 TS、Matrix Scaling 和 Vector Scaling，在 **§3** 正式把 post-processing calibration 搬入 CL：每个 experience 训练结束后，使用该 experience 的 validation split 进行校准；test 只作评价。校准层／temperature 会保留到后续 experiences，而不是下一年恢复为原始输出。citeturn24view0

其 **§3 “Replayed Calibration”** 还提出保存先前 validation examples 的小 buffer，在后续 calibration 阶段同时使用当前验证数据和历史 calibration memory，以减轻只校准当前分布造成的问题。作者公开了复现实验仓库 `lilanpei/Continual-Calibration`。citeturn24view0 fileciteturn5file0L2-L11

这对 LAMDA 有两个边界意义。

第一，**输出层／校准层持续适配本身是有 CL 文献先例的**，不能包装成创新。

第二，该论文优化的是 calibration/ECE/NLL，而不是固定 FPR 下最小 FNR；其方法结果不能迁写为 LAMDA 恶意修复证据。论文自身还指出 CL 中 experience 间数据分布不断变化，使传统 post-hoc calibration 更困难。citeturn24view0

这种担忧也得到更一般的 dataset-shift 证据支持：Ovadia 等的 **Can You Trust Your Model’s Uncertainty?**, NeurIPS 2019，在大规模 shift benchmark 中发现传统 post-hoc calibration 在分布偏移下会失效，而跨模型边缘化的一些方法相对更稳健。citeturn22view3

所以对本项目而言：

> **calibration 是必须排重的输出适配基线，但不是当前最有希望的“修复空间获取器”。**

### confidence gate 只有在读取额外信息时才真正超过阈值调节

一个 gate 若只是：

\[
g(x)=\mathbf1[s_{\rm old}(x)\in I],
\]

本质上仍围绕单一旧 score 做 piecewise threshold policy；在【本地转述】旧 score 操作点几乎无剩余空间的条件下，其上限很可疑。

若 gate 读取完整冻结表示：

\[
g(x)=g_\phi(h_{\theta^-}(x)),
\]

它就可能利用旧 classifier 未充分使用的 feature directions。这时它已经是一个**第二分类器／scope classifier**，而不再只是 calibration。这正是 SERAC 与简单 threshold routing 的根本区别。citeturn12view0turn12view1

因此，对“部署侧适应是否变相调阈值”的最精确回答是：

| 部署操作 | 固定 0.5 下的本质 |
|---|---|
| Temperature \(z/T\) | 决策完全不变 |
| Platt \(\sigma(az+b)\) | 二元情况下等价于移动原 score 阈值 |
| monotone isotonic \(f(p)\) | 保持排序，主要是重新确定 score→概率→决策切点 |
| old/new 固定全局 score blend | 新 score 函数；可能重排，也可能只是平滑 |
| feature-dependent old/new gate | **新的输入条件化决策函数，不等同单一阈值** |
| per-head independently tuned thresholds | 新的多阈值部署政策；当前 LAMDA 合同并未自动允许 |

## 样本风险路由与更细粒度参数更新

### SpotTune 是“每个样本决定哪些层允许适应”的经典直接先例

Yunhui Guo、Honghui Shi、Abhishek Kumar、Kristen Grauman、Tajana Rosing、Rogerio Feris 的 **SpotTune: Transfer Learning through Adaptive Fine-tuning**, CVPR 2019，是“head-only / full-model 二分”之外非常直接的参数路由先例。

在 **§3.1 Eq. (2)**，每个 residual block 同时存在冻结 pretrained block \(F_l\) 和可训练副本 \(\hat F_l\)，policy network 为**每个输入、每一层**产生二元动作：

\[
x_l
=
I_l(x)\hat F_l(x_{l-1})
+
(1-I_l(x))F_l(x_{l-1})
+x_{l-1}.
\]

因此不同样本可以走不同数量、不同位置的 frozen/fine-tuned blocks。**§3.2 Eq. (3)–(4)** 使用 Gumbel-Softmax 学习离散 policy。citeturn11view0turn13view0

作者公开仓库 `gyhui14/spottune`，仓库描述明确对应该论文。fileciteturn3file0L2-L11

它对 LAMDA 的启示很强，但边界也同样明确：

> SpotTune 是**按输入路由“哪些表示层可以被改动”**的成熟先例，却不是“不动表示”的方法。

它只是让表示改动从全局变成条件化；而且其 policy 目标是目标任务分类性能，不含 benign FPR 或旧恶意 negative flip 的安全定义。因此不能把“风险路由参数更新”直接叫 SpotTune，也不能引用 SpotTune 的视觉迁移结果作为 LAMDA 效果依据。citeturn11view0turn13view0

不过，如果 frozen-head scope router 失败，而诊断显示完整 frozen representation 仍不足以区分 repair-malware 与 collateral-benign，那么 SpotTune 式：

\[
x \mapsto \{\text{只开放少数层／低秩支路}\}
\]

确实比再次全模型 repair 更合理，因为它至少把**表示可塑性变成 input-conditional resource**。

### InfLoRA 是持续学习中“限制更新子空间”，不是样本条件路由

Yan-Shuo Liang、Wu-Jun Li 的 **InfLoRA: Interference-Free Low-Rank Adaptation for Continual Learning**, CVPR 2024，直接将低秩参数高效适配用于 CL。它冻结预训练主参数，通过低秩模块学习新任务，并从子空间角度设计更新以减少新旧任务干扰；作者官方仓库明确标注为该 CVPR 2024 工作的 official implementation。citeturn1search3turn1search7 fileciteturn4file0L2-L11

它比 EWC/A-GEM 更接近“只给更新一个窄参数通道”，但仍有两个重要边界：

\[
W_{\rm eff}=W_0+\Delta W_{\rm LoRA}
\]

意味着实际前向表征**仍然变了**；只是 \(W_0\) 本体冻结、增量受到低秩限制。

而且 InfLoRA 的干扰对象主要是连续任务知识，不是“这个恶意样本可以进入修复子空间、那个良性样本必须完全走原参数”的 per-sample safety routing。因此它属于**低秩全局适应**，而不是你的“风险条件参数路由”。citeturn1search3turn1search7

### 模型编辑里的 MEND 也是非常近的“局部低秩参数修复”邻居

Mitchell 等的 **Fast Model Editing at Scale**, ICLR 2022（MEND）不是 CL 分类方法，但它学习一个 editor，对给定 edit 的原始 fine-tuning gradient 做低秩变换，从而产生尽量局部的参数更新，并以“修改目标行为同时减少其他输入退化”为设计目标。其官方项目和作者仓库公开了实现。citeturn4search2turn4search3turn4search4turn4search9

因此未来若出现“只对 repair candidate 生成一个低秩参数 delta，再限制 locality”的方案，**MEND 必须作为查重近邻**。它不能被包装成“首次按修复样本生成局部更新”。

### 安全领域里有参数保持，但尚未找到同款 sample-risk routing

前轮已经核过的 **FreeMOCA: Memory-Free Continual Learning for Malicious Code Analysis**, Asadi 等，arXiv:2605.09664v1，§3.2–§3.4、Algorithm 1、Eq. (6)–(7)，在恶意代码持续学习中使用逐层的参数插值／保留机制，是本次安全领域最接近“不要任意重写旧参数”的公开先例之一；但它的路由单位是层／参数演化，而不是每个 APK 的安全风险。citeturn356574view1turn128779view3turn356574view0

因此本次检索**没有发现一个成熟的 malware/IDS CL 方法精确做到**：

\[
\text{sample risk}
\rightarrow
\text{parameter subset}
\rightarrow
\text{class-conditional FPR-safe update}.
\]

这只是“在本轮规定来源范围内未找到”，不是新颖性证明。

### 这一族最需要防的失败模式

这类方法不会自动解决八连败，原因很具体。

首先，**router 自己会成为新的误报源**。如果原问题是 repair malware 与 collateral benign 难以局部区分，那么 gate 误把良性送进 aggressive branch，FPR 问题只是从 classifier 转移到了 router。SERAC 对 scope estimation 的困难正说明这一点。citeturn12view0

其次，**冻结表示可能真的没有所需信息**。若存在

\[
h(x_{\rm mal})\approx h(x_{\rm benign})
\]

甚至完全相同的表示，那么再复杂的 head/router 都无法可靠地区分二者。这时只有改变表示或增加外部信息才能扩大可分空间。这一点需要本地冻结表征的来源年诊断，而不能由 warm-start head-only 单臂失败单独证明。

再次，**adapter/LoRA/side branch 很容易形成隐藏容量扩张**。它们保护旧 base 的代价是保存额外参数；若按年持续增长，就必须把参数存储和推理路径成本如实纳入算力／容量比较，不能因为 replay buffer 仍为 200 就称“成本不变”。SpotTune 与 InfLoRA 都是在明确新增适配容量的框架中工作的。citeturn11view0turn1search3

所以“不移动表示”的候选建议最好分成三个严格等级：

\[
\boxed{
\begin{array}{ll}
\text{Level A:} & \text{backbone 完全冻结，仅多 head/gate} \\
\text{Level B:} & \text{旧 backbone 冻结，允许新增 side/adapter 表示} \\
\text{Level C:} & \text{输入条件化地开放部分旧表示参数}
\end{array}}
\]

SERAC 任务化的 frozen-feature patch 属于 A/B 之间；Side-Tuning 更偏 B；SpotTune 属于 C；InfLoRA 是全局低秩 B/C。**这四种不能统称“不移动表征”。**

## Margin 带与“不追求深修”的成熟损失先例

### “修到一点 margin 就停”本身已有非常成熟的 hinge 先例

大间隔分类的 hinge loss 本身就是最直接的先例。Dogan、Glasmachers、Igel 的 **A Unified View on Multi-class Support Vector Classification**, JMLR 17, 2016，在 §2 的统一框架中写出标准 hinge：

\[
L_{\rm hinge}(\mu)=\max\{0,1-\mu\}.
\]

其核心性质是：一旦样本达到要求的正确 margin，损失归零，不再继续增加置信度。citeturn27search15

映射到二元恶意 logit \(z\)，若判定边界仍固定在

\[
a=0
\quad\leftrightarrow\quad
p=0.5,
\]

而只希望修复样本到

\[
p^\star=0.5+\delta,
\]

则对应 logit margin

\[
m
=
\operatorname{logit}(0.5+\delta)
=
\log\frac{0.5+\delta}{0.5-\delta}.
\]

一个完全标准的任务化形式是：

\[
L_{\rm repair}^{\rm hinge}
=
\frac1{|R_t|}
\sum_{x\in R_t}
[m-z_\theta(x)]_+.
\]

一旦 \(z_\theta(x)\ge m\)，该修复项梯度立即变成零。

所以：

> **“不要把已修恶意继续往 1.0 推，而是过 0.5 后留一个小安全 margin 就停”不是一个未经先例的损失思想。它是 hinge/margin-loss 家族的直接任务化。**

### 但小 margin target 并不自动等于“不修深埋 FN”

这一点对你现在的数据尤其重要。

对于一个深埋样本 \(z^-\ll0\)，即使目标只有 \(m=0.1\)：

\[
[m-z]_+
\]

仍然会在它跨过 \(m\) 之前持续给梯度。标准 hinge 只是**到达目标以后停止推**，不是“深样本一开始就不修”。

而且 hinge 对所有未达到 margin 的样本，logit 方向梯度基本是常数；相比你目前【本地转述】按旧 margin depth \(d_i\) 进一步加权的 BCE，它确实可以去掉“越深权重越大”的额外放大，但**七成深埋 FN 仍会同时请求更新**。

所以真正的“浅修”至少有两个独立设计轴：

\[
\textbf{修谁}
\quad\text{与}\quad
\textbf{修到哪}.
\]

例如：

\[
R_t^{\rm shallow}
=
\{x:y=1,-\Delta\le z_{\theta^-}(x)<0\}
\]

控制“修谁”；而

\[
[m-z_\theta(x)]_+
\]

控制“修到哪”。

这两个动作不能合并成一个“margin loss”创新点。

### Ramp／截断 margin 是“不要让极深错误无限主导”的更近先例

margin-loss 文献还存在 bounded / ramp loss：与 logistic/BCE 相比，其特点之一就是对非常极端的 margin violation 不再无限增加损失。JMLR 的 margin-loss 分析明确把 hinge、logistic、exponential 等放在统一 margin 风险框架中；后续 ramp-loss 文献进一步研究有界、非凸的大间隔 surrogate。citeturn27search0turn27search4turn27search10

这与【本地转述】“剩余 FN 七成在旧模型 ≤0.3，而贴边恶意只有几十个”的病灶非常相关，因为它给出了一个成熟机制：

> **不要因为一个样本特别深错，就让它获得特别大的修复影响。**

但风险也同样明显：在恶意软件里，被 capped 掉的不是随机 label-noise，而可能是真实、重要的恶意。于是 ramp/capped loss 只能作为**外部候选保守修复基线**，不能把 robust-classification 的结果外推成安全收益。

### 与 PCT FD-LM 的边界

Yan 等的 **Positive-Congruent Training: Towards Regression-Free Model Updates**, CVPR 2021，在 **§4.1–§4.2，Eq. (4)、(6)–(9)** 研究的是模型升级时的 regression/negative flips，并用 Focal Distillation，包括 FD-KL 与 FD-LM，对新旧输出关系施加保护。其目标本质是**旧模型兼容性**：减少新模型把旧模型原本正确的预测变错。citeturn876909view0

小-margin repair hinge 则是一个绝对任务目标：

\[
z_{\rm new}(x)\ge m.
\]

二者的问题不同：

\[
\boxed{
\text{PCT/FD-LM：新模型不要不必要地偏离旧模型}
}
\]

\[
\boxed{
\text{repair hinge：旧模型这里本来就错，只要求新模型达到最低足够 margin}
}
\]

如果把 distillation 施加到旧模型漏判的恶意上，它可能直接和修复相冲突；如果严格按 PCT 的正向兼容样本选择，只保护旧模型正确样本，则这种冲突会减弱。具体取决于你本地 PCT 任务化 mask，不能拿“PCT”三个字代替实际信息集合定义。

因此，未来如果采用“浅修 hinge + 旧正确样本 PCT”，合理的论文叙事也不是“提出新的 margin distillation”，而是：

> **把一个成熟的 sufficient-margin repair objective 与一个成熟的 model-update regression regularizer 放在 LAMDA 的非对称角色集合中对照。**

其新颖性若存在，只能来自任务化结构、病灶和实验证据，而不是两个损失部件。

### 与 OHEM 的边界甚至方向相反

Shrivastava、Gupta、Girshick 的 **Training Region-based Object Detectors with Online Hard Example Mining**, CVPR 2016，在 **§4.1** 的核心是从候选样本中选择当前 loss 最大、最困难的 examples 进入反向传播。它改变的是**样本曝光／选择**，不是“样本被修到哪里后停止”。citeturn748738view0

对本地当前病灶，朴素 OHEM 很可能正好优先选中那些七成深埋 FN，因为它们通常具有较高正类损失。这与“不要让极深 FN 主导更新”可能方向相反。

所以：

\[
\text{OHEM} \neq \text{margin-band repair},
\]

\[
\text{PCT FD-LM} \neq \text{margin-band repair},
\]

\[
\text{hinge stop-after-margin}
\neq
\text{shallow-only eligibility}.
\]

三者必须分开。

### Reject-option 文献有“决策带”，但不适合直接搬入当前合同

learning-with-rejection / selective classification 文献确实允许在分类边界附近设置 reject/abstain 区域，以用拒答成本换取更可靠的已接受预测；例如 Charoenphakdee 等 ICML 2021 formalize 的分类规则明确增加 reject 输出和 reject cost。citeturn27search2

但这改变了输出空间：

\[
\{0,1\}
\rightarrow
\{0,1,\text{reject}\}.
\]

当前 LAMDA 合同是固定二元决策，因此它只能作为“margin band/保守决策”的文献边界，**不能直接作为现有实验臂而不修改合同**。

## 八连败究竟在文献中叫什么

### 最上位名称确实是 stability–plasticity dilemma

持续学习文献中的标准上位概念是 **stability–plasticity dilemma**：模型需要足够 plasticity 学新知识，同时足够 stability 保持已有知识。De Lange、Aljundi、Masana、Parisot、Jia、Leonardis、Slabaugh、Tuytelaars 的综述 **A Continual Learning Survey: Defying Forgetting in Classification Tasks** 明确把 stability–plasticity trade-off 作为 CL 的核心分析轴，并专门建立评估框架研究这种权衡。citeturn28academia10

InfLoRA、AdNS 等更近的 CL 工作仍直接使用该名称描述“保护旧知识”和“学习新任务”之间的张力。citeturn1search7turn28academia12

但对你的八连败，仅写：

> “这是 stability–plasticity dilemma”

**太宽。**

因为【本地转述】主要失败并不只是“学 2018 忘 2016”：大量新增 FP 发生在**当前年度原本正确的 benign** 上，是当前适应自身的 class-conditional collateral damage。

### PCT 的 model-update regression／negative flip 是第二个更精确的轴

PCT 研究的“old model correct → new model wrong”就是 model-update regression / negative flip。citeturn876909view0

因此，本地现象实际上可以分成：

\[
\underbrace{\text{malicious FN repair}}_{\text{plasticity}}
\]

\[
\underbrace{\text{old malicious correct}\rightarrow\text{wrong}}_{\text{model-update regression}}
\]

\[
\underbrace{\text{current benign correct}\rightarrow\text{FP}}_{\text{same-domain collateral interference}}
\]

\[
\underbrace{\mathrm{FPR}\le \mathrm{FPR}_{ER}}_{\text{operating-rate constraint}}.
\]

这比单纯说“灾难性遗忘”更准确。

### 固定 FPR 下最小化 FNR 已经是成熟的 rate-constrained classification 目标

Kumar、Narasimhan、Cotter 的 **Implicit Rate-Constrained Optimization of Non-decomposable Objectives**, ICML 2021, PMLR 139:5861–5871，把“固定某一错误率，同时优化另一错误率”作为典型的 rate-constrained classification 问题，并讨论 FPR/FNR 一类不可分解指标。其方法本体还会处理隐式阈值，因此并不能直接无修改搬进你固定 0.5 的合同。citeturn785611view0

所以，对第三章最稳妥的文献化描述建议是：

> **“固定 FPR 操作约束下的 stability–plasticity / model-update-regression conflict。”**

或者中文：

> **“固定误报约束下的修复—保持冲突”。**

这里后一句是**描述性项目术语，不是我在文献中找到的标准专名**。

本次没有找到一个已经公认的术语叫做 “FPR-constrained stability-plasticity dilemma” 或“false-positive-constrained continual plasticity”。因此论文里若使用，应明确是本研究对多个既有概念的组合描述，不能写成“文献将其称为……”。

DriftSurf 的 stable/reactive 也值得引用，但必须注明该文中的 false positive 主要指**误报 drift event**，而不是分类器的良性 FPR。citeturn17search0turn17search1

### 你的八连败反而说明了一个重要边界

【本地转述】全参数 repair、head-only repair、梯度保护、PCT、乘子、配额和课程都出现“修则 FPR 抬、抑则修复消失”的结构，再加上固定 score operating point 无明显残值，这一组证据目前更像是在否定：

\[
\boxed{\text{“用一个全局输出函数同时承担保守与修复”这一设计假设}}
\]

而不是已经否定：

\[
\boxed{\text{“冻结表征中不存在任何局部修复信息”}}.
\]

这两者差别很大。

后一个命题只有当 full-feature scope/router 也无法区分 repair-malware 与 collateral-benign，或者发现冻结特征层面的异标签碰撞／可分性严重不足时，才获得更强支持。

因此，文献给出的真正“下一层”不是第九种 global regularizer，而是从

\[
f(h)
\]

转向

\[
f_{\rm conservative}(h),
\quad
f_{\rm repair}(h),
\quad
g(h).
\]

这正是 SERAC、DriftSurf、SpotTune 等不同领域工作共享的结构性启示。citeturn12view0turn17search1turn11view0

## 外部候选排序、最小可证伪设计与完整题录

### 为避免无效 GPU，优先级建议

**最高优先：先判“冻结表示可否支持局部 scope”，而不是立刻解冻层。**

最有信息量的下一候选是 SERAC-style **conservative path + repair path + scope gate**，但应把它写成任务化候选，不写成“提出双头学习”。底层表示保持年度开始时合法冻结；保守路径作为默认输出；修复路径只在 gate 许可区域接管。gate 必须读取当前合法可用的冻结 feature，而不是开发/test 标签。SERAC 只是机制先例，不提供 LAMDA 效果保证。citeturn12view0turn12view1

最低限度需要一个非常关键的可证伪对照：

\[
g_{\rm score}(x)=g(z_{\theta^-}(x))
\]

对比

\[
g_{\rm feature}(x)=g(h_{\theta^-}(x)).
\]

如果只有完整 feature gate 能通过，说明 frozen representation 中有单一 classifier score 丢失的局部信息；如果二者都失败，而且 gate 对 repair-malware / benign collateral 的 ROC 在来源年也没有可用区域，才更有理由转向表示层。

**第二优先：old/new 预测组合只做零训练 Pareto 诊断。** 对已经存在的 old/new predictions，可以在本地合法开发信息上判断是否存在某个预登记组合规则同时降低 FN 而不增加 FP；这不需要新增模型训练。如果任何全局 blend 都没有可行点，就不值得单独开 ensemble GPU 实验。DriftSurf/DWM 类文献支持保留旧模型这一部署范式，但不保证当前 pair 有可行组合。citeturn17search1

**第三优先：小 margin hinge 可以作为便宜的直接损失基线。** 其主要价值不是“新算法”，而是检验现行 depth-weighted BCE 是否因持续推动／深度加权造成不必要的全局压力。最清晰的比较应只改变 repair loss，不同时改变候选集合、学习率或保护机制。hinge 的成熟先例使其适合作为排重基线。citeturn27search15

**暂缓 SpotTune/InfLoRA。** 它们值得在“frozen feature scope gate 确认不可行”之后再进入，因为它们实际重新开放了表示自由度；过早引入会无法回答这次主问题究竟是**缺少局部路由**还是**确实必须改变表征**。citeturn11view0turn1search3

**不建议把 TS、Platt、isotonic 当正式恶意修复候选。** TS 在固定 0.5 下数学上不改变任何预测；Platt／isotonic 主要重映射 scalar operating point，而本地探针已经显示该轴空间极少。它们可以作为论文中的“输出适配直接基线”，无需期待其成为主方法。citeturn22view0turn22view2

### 仍然保持的失败门

所有外部候选均不改变原合同：相对同流 ER，hard FPR 不增、旧恶意负向翻转不增，并且 FNR 或恶意正向修复至少一项改善。对于 routed dual-head，还应把**gate 自身**列入机制诊断：恶意 repair-scope recall、benign gate activation、旧正确恶意被 route 到何处、以及最终误报究竟来自 repair head 还是 gate 误路由。

尤其不能出现这样的“伪通过”：

\[
\text{repair head 本身很好}
\quad\text{但}\quad
\text{gate 使用 test labels 决定调用}.
\]

也不能通过给两个头独立调阈值绕开固定 0.5 合同。所有开发选择只能来自已裁决开发信息集合，未授权的未来标签不能进入 gate、calibrator 或 ensemble weight 的学习。

### 原始题录与精确机制位置

| 文献 | 原始出处与版本 | 关键位置 | 对 LAMDA 的机制边界 | 官方代码 |
|---|---|---|---|---|
| **Mitchell, Eric; Lin, Charles; Bosselut, Antoine; Manning, Christopher D.; Finn, Chelsea. _Memory-Based Model Editing at Scale_.** | ICML 2022, PMLR 162:15817–15831 | **§3.1 Eq. (1); §3.2 Eq. (2)–(3)** | base + scope classifier + counterfactual model；最直接的“保守路径＋局部修复路径”近邻，但不是 malware CL | 本次未确认到可作为原作者官方 GitHub 直接引用的独立 SERAC 仓库；不以第三方实现替代。citeturn5search1turn12view0turn12view1 |
| **Tahmasbi, Ashraf; Jothimurugesan, Ellango; Tirthapura, Srikanta; Gibbons, Phillip B. _DriftSurf: Stable-State / Reactive-State Learning under Concept Drift_.** | ICML 2021, PMLR 139:10054–10064 | **§1–§2**，后续风险竞争性分析 | 同任务旧／新模型并存与 probation；按时间状态选择，不是 per-sample repair head | PMLR 原件与 supplement。citeturn17search0turn17search1 |
| **Guo, Yunhui; Shi, Honghui; Kumar, Abhishek; Grauman, Kristen; Rosing, Tajana; Feris, Rogerio. _SpotTune: Transfer Learning through Adaptive Fine-tuning_.** | CVPR 2019 | **§3.1 Eq. (2); §3.2 Eq. (3)–(4)** | 每输入、每层选择 frozen/fine-tuned block；是条件化表示更新，不是“完全不动表示” | `gyhui14/spottune`，已核实公开作者仓库。citeturn11view0turn13view0 fileciteturn3file0L2-L11 |
| **Liang, Yan-Shuo; Li, Wu-Jun. _InfLoRA: Interference-Free Low-Rank Adaptation for Continual Learning_.** | CVPR 2024, pp. 23638–23647 | **§3 方法部分** | CL 低秩受限更新；减少任务干扰，但非 sample-risk route，effective representation 仍变 | `liangyanshuo/InfLoRA`，仓库明确标为 official implementation。citeturn1search3turn1search7 fileciteturn4file0L2-L11 |
| **Mitchell, Eric et al. _Fast Model Editing at Scale_.** | ICLR 2022 | **§3，MEND editor / gradient transformation** | 局部参数编辑、低秩梯度变换；非 CL 检测，但未来“repair-specific delta”必须查重 | 作者公开 MEND 项目／仓库。citeturn4search2turn4search3turn4search9 |
| **Guo, Chuan; Pleiss, Geoff; Sun, Yu; Weinberger, Kilian Q. _On Calibration of Modern Neural Networks_.** | ICML 2017, PMLR 70:1321–1330 | **§4.1 Eq. (7) 与 Platt 定义；§4.2 Eq. (8)–(9)** | TS 不改 fixed-0.5 分类；Platt 二元下等价 effective threshold shift；isotonic 保序 | 原始 PMLR 论文。citeturn22view0turn22view2turn23view0turn23view1 |
| **Li, Lanpei; Piccoli, Elia; Cossu, Andrea; Bacciu, Davide; Lomonaco, Vincenzo. _Calibration of Continual Learning Models_.** | CVPRW 2024 / arXiv:2404.07817 | **§2.1; §3，尤其 Post-processing continual calibration 与 Replayed Calibration** | 每 experience 输出校准有 CL 先例；目标是 calibration，不是 FPR-constrained FN repair | `lilanpei/Continual-Calibration`。citeturn24view0 fileciteturn5file0L2-L11 |
| **Ovadia, Yaniv; Fertig, Emily; Ren, Jie; Nado, Zachary; Sculley, D.; Nowozin, Sebastian; Dillon, Joshua; Lakshminarayanan, Balaji; Snoek, Jasper. _Can You Trust Your Model’s Uncertainty? Evaluating Predictive Uncertainty under Dataset Shift_.** | NeurIPS 2019 | Abstract 与 shift benchmark | 传统 post-hoc calibration 在 distribution shift 下可能失效；不能把静态 calibration 当 drift 保证 | NeurIPS 原始论文。citeturn22view3 |
| **Yan, Sijie et al. _Positive-Congruent Training: Towards Regression-Free Model Updates_.** | CVPR 2021, pp. 14299–14308；arXiv:2011.09161v3 | **§4.1–§4.2, Eq. (4), (6)–(9)** | model-update regression / FD-KL / FD-LM；保护兼容性，不是 absolute repair margin | 本轮未确认原作者官方独立代码，不采用第三方仓库。citeturn876909view0 |
| **Shrivastava, Abhinav; Gupta, Abhinav; Girshick, Ross. _Training Region-based Object Detectors with Online Hard Example Mining_.** | CVPR 2016, pp. 761–769 | **§4.1** | OHEM 选择高 loss 样本；不规定停止修复 margin，深 FN 可能反而被优先 | 原作者公开实现已有历史代码；本报告仅引用原论文机制。citeturn748738view0 |
| **Dogan, Ürün; Glasmachers, Tobias; Igel, Christian. _A Unified View on Multi-class Support Vector Classification_.** | JMLR 17, 2016 | **§2，hinge \(L=\max(0,1-\mu)\)** | “达到足够 margin 后停止”的成熟直接先例 | 原始 JMLR 论文。citeturn27search15 |
| **Kumar, Abhishek; Narasimhan, Harikrishna; Cotter, Andrew. _Implicit Rate-Constrained Optimization of Non-decomposable Objectives_.** | ICML 2021, PMLR 139:5861–5871；arXiv:2107.10960 | **§2–§3；§5.2** | fixed-rate / FPR-FNR 目标近邻；原 ICO 涉及隐式阈值，不能直接套固定 0.5 合同 | `google-research/google-research/implicit_constrained_optimization`。citeturn785611view0 |
| **De Lange, Matthias; Aljundi, Rahaf; Masana, Marc; Parisot, Sarah; Jia, Xu; Leonardis, Aleš; Slabaugh, Gregory; Tuytelaars, Tinne. _A Continual Learning Survey: Defying Forgetting in Classification Tasks_.** | arXiv:1909.08383；后发表于 IEEE TPAMI | 综述中的 stability–plasticity framework | “稳定—可塑性”是标准上位术语，但没有直接包含固定 benign FPR 条件 | 原始公开稿。citeturn28academia10 |
| **Asadi, Zahra et al. _FreeMOCA: Memory-Free Continual Learning for Malicious Code Analysis_.** | arXiv:2605.09664v1, 2026-05-10 | **§3.2–§3.4, Algorithm 1, Eq. (6)–(7)** | malware-specific CL 参数保持近邻；不是 per-sample safety routing | `IQSeC-Lab/FreeMOCA`。citeturn356574view1turn128779view3turn356574view0 |

### 本轮能回答与仍未回答的边界

**能够回答：** 文献里确实存在成熟的结构性办法，把“保持默认行为”和“局部适应”拆开；最直接的是 SERAC 型 scope-gated patch、DriftSurf 型 stable/reactive deployment，以及 SpotTune 型 sample-conditional parameter routing。它们共同说明“全局单函数更新”并不是持续适应的唯一框架。citeturn12view0turn17search1turn11view0

**能够明确排除：** 在二元固定 0.5 阈值下，纯 Temperature Scaling 不可能修 FN；Platt scaling 对决策等价于移动原 logit threshold；单调 isotonic 不能创造新的样本排序。因此这三者不应被期待解决【本地转述】的“操作点无残值”病灶。citeturn22view0turn22view2

**仍未回答：** LAMDA 的 frozen representation 是否真的包含足够信息，让 scope classifier 把深埋恶意与会被 repair 波及的良性分开。这是当前最关键、也最小可证伪的未知量。

**仍未找到：** 一个公开成熟的 malware/IDS continual-learning 方法，已经完整实现“同任务 conservative head + repair head + sample-risk gate + fixed benign-FPR safety constraint”。本次检索不足以据此声明新颖性；只能说明直接成熟近邻来自多个相邻家族，而不是一个可以直接改名采用的现成算法。

### 执行元数据

| 字段 | 实际值 |
|---|---|
| `actual_model` | **GPT-5.5 Thinking** |
| `actual_effort` | **high**；按高强度研究执行，平台未暴露可独立核验的内部 effort 遥测 |
| `actual_mode` | **deep-research**，在当前会话继续完成，未新建会话 |
| `used_apps` | **GitHub** |
| `public_source_types` | PMLR、CVF Open Access、NeurIPS proceedings、arXiv、JMLR、作者／组织官方 GitHub |
| `local_code_execution` | **none** |
| `git_modification` | **none** |
| `future/sealed_labels_accessed` | **none** |
| `project_paths_accessed` | **none**；本轮任务按交接包自包含证据研究，不依赖项目文件 |

**外部候选总判读：在“不继续移动旧 backbone”这一约束下，当前最有文献依据、同时真正增加局部修复能力的方向是“冻结默认路径＋局部 repair patch＋feature-dependent scope gate”；不是双阈值，不是纯 calibration，也不是再加一个全局损失。小-margin hinge 是一个值得做的低成本成熟损失基线，但只有 scope/routing 这一层真正针对了 warm-start head-only 所暴露的“全局映射缺乏局部性”问题。**