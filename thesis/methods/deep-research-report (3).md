# LAMDA“固定表征下吃修复空间”文献深研：双头解耦、推理组合、风险路由与 Margin 带

**状态：全部结论均为外部候选建议，待本地全文与实验独立复核；不验证交接包中的 LAMDA 实验有效性，不裁决候选存废，不修改冻结合同。**

| 字段 | 本次实际状态 |
|---|---|
| `actual_model` | **GPT-5.5 Thinking** |
| `actual_effort` | 运行时未暴露可独立核验的 effort 遥测；`requested_effort=high` |
| `actual_mode` | **deep-research，本会话内继续执行，未新建会话** |
| `used_apps` | **GitHub**，用于核对作者/组织官方仓库 |
| 其他公开来源 | 原始会议/期刊页面、arXiv、作者论文全文 |
| 本地项目访问 | **未访问项目文件**；本题按交接包自包含证据处理 |
| 代码/实验 | **未运行代码、未训练、未复算本地数据** |

证据等级在下文统一为：**A**＝同行评审原始论文且机制直接相关；**A−**＝同行评审原始论文，但任务或部署条件与 LAMDA 有明显差异；**B**＝原始论文/预印本，机制有参考价值但成熟度或匹配度较弱；**M**＝由原文公式作出的数学推论；**L**＝用户交接包给出的本地 `screening_only` 证据，不是本次外部复核结果。

## 总体判断：有成熟路线，但“固定表征”必须先分成两种含义

按交接包，八代机制的共同现象不是简单“不会学”：修复侧能把 FNR 往下推，但单一全局决策函数会把大量良性一并推过操作点；warm-start head-only 更进一步说明，**仅冻结 backbone 权重并不能自动提供局部性**。与此同时，你们的零训练探针又显示，剩余 FN 多数不是轻微贴边，而是旧分数显著低于 0.5；在固定 FP 预算下仅重排 ER 分数几乎没有 FN 残值。【L：用户交接包】

外部文献给出的答案可以浓缩成一句话：

> **有“不更新原 backbone 参数而获取额外适应自由度”的成熟办法；但在“连表示函数 \(h(x)\) 都严格不变”的更强条件下，真正能产生新的局部修复能力的核心不是再加一个全局线性头，而是输入条件化的模型选择/路由、多个非等价专家，或更丰富的固定表示上的非线性决策函数。单调校准和常数权重头插值不会凭空创造这种空间。**

这里尤其要区分：

\[
\text{backbone weights frozen}
\quad\neq\quad
\text{effective representation }h(x)\text{ frozen}.
\]

InfLoRA、MoE-Adapters、PromptFusion 一类参数高效持续学习方法通常冻结预训练主干，却通过 LoRA、adapter、prompt 等改变网络中间激活，所以它们满足前一个定义，**不满足严格的“表示函数完全不移动”**。InfLoRA 本身明确把 LoRA 解释为冻结预训练参数、在低维子空间中进行适配；MoE-Adapters 同样在冻结 CLIP 基座上加入并路由 adapter 专家。citeturn26view0turn26view1 作者官方仓库也分别将 InfLoRA 标注为 CVPR 2024 官方实现，将 MoE-Adapters 仓库标注为 CVPR 2024 代码。fileciteturn4file0L2-L5 fileciteturn5file0L2-L5

对四个子题，我的外部文献判断如下：

| 子题 | 文献结论 | 对 LAMDA 的优先级 |
|---|---|---|
| 同任务“保守+修复”双头 | **有非常近的稳定/可塑双模块、快/慢模型、旧/新专家融合先例；但本轮没有找到成熟论文正好采用“二元同任务 repair head + conservative head + 各自阈值 + 固定 FPR”这一完整配置。** | **高**，但关键是**路由器**而不是“两只头”本身 |
| 推理组合/校准 | 漂移流中的 ensemble、专家加权和旧模型复用是成熟合法方法；temperature/Platt/isotonic 属于校准，不能等同于获得新局部表示能力 | **动态 gate 可研究；纯校准宜作负控/直接基线** |
| 细粒度参数子集 | PackNet/HAT、LoRA/InfLoRA、MoE-Adapters、PromptFusion-Lite 都提供不同粒度的隔离/路由先例 | **若允许有效表示变化则很强；若要求严格固定 \(h\)，只有输出侧专家/路由符合** |
| Margin 带 | hinge、reject-option、margin-preserving 更新都有成熟祖先；“达到 \(0.5+\delta\) 后停止继续推”的损失本身不能作为新损失创新 | **很适合作为最低成本可证伪臂，但不大可能单独解决深埋 FN** |

更精确的文献术语方面，八连败最稳妥的上位名称仍是 **stability–plasticity dilemma**；PromptFusion 直接以此作为动机，并显式构造 Stabilizer 与 Booster 来解耦二者。citeturn22academia35 对“模型升级修好一些样本、同时制造旧正确→新错误”这一现象，Bansal 等给出了 **performance/compatibility tradeoff**，PCT 则采用 **negative flip / model regression** 的表述。citeturn27search2turn25academia11 **本轮没有找到已经成为标准术语的“FPR-constrained stability–plasticity dilemma”**；因此论文里最好写成描述性组合词，例如“**固定 FPR 操作点下的 stability–plasticity / update-compatibility tradeoff**”，而不是声称这是已有命名的独立研究范式。

## 同任务双头：成熟先例的核心不是“两只分类头”，而是稳定—可塑路径加输入路由

### 最接近的先例是 PromptFusion，而不是 Task-IL 多头

Chen 等的 **PromptFusion: Decoupling Stability and Plasticity for Continual Learning**，ECCV 2024，直接把持续学习中的稳定—可塑冲突拆成 **Stabilizer** 和 **Booster** 两条路径；论文再对两者输出进行融合。其 PromptFusion-Lite 更进一步，使用输入相关机制动态判断一个样本是否值得激活两条路径，而不是所有样本无差别经过同一个更新分支。citeturn22academia35turn9view0turn9view1 官方仓库 README 也明确写明 Stabilizer 负责 catastrophic forgetting、Booster 学习新知识，并且 Lite 版本“for each input image”动态决定是否同时激活两模块。fileciteturn2file0L2-L5

原文最值得与你们排重的是 **§3 的输出融合 Eq. (3)–(4)**，以及 Lite 版输入条件选择的 **Eq. (7)–(8)**：前者属于稳定/可塑两输出的学习式混合，后者才引入样本依赖选择。citeturn9view0turn9view1

因此，若 LAMDA 下一候选写成：

> “首次用两个头分别负责稳定和可塑，再把输出组合”

**不够新颖。** PromptFusion 已经把“Stabilizer/Booster + fusion”做成核心结构。真正可以任务化研究的是：

> 在同一个二元检测任务、同一固定表示、固定 0.5 最终操作点下，能否由**因果可观测的输入 gate**识别“允许交给 repair expert 的局部区域”，而默认保持 ER/conservative expert 的决策？

这和 PromptFusion 的科学对象仍然不同：PromptFusion 是视觉持续学习中的 prompt 模块，目标不是 hard FPR 不升，也没有 LAMDA 的“旧正确良性不能变 FP”安全合同。这个差异可以构成**任务化约束与失败判据差异**，但不是“双路径”结构创新。citeturn22academia35

### CLS-ER 提供了另一种快—慢双模型先例

Arani、Sarfraz、Zonooz 的 **Learning Fast, Learning Slow: A General Continual Learning Method based on Complementary Learning System**，ICLR 2022，用具有不同时间尺度的 stable/plastic semantic memories 来处理新知识获取与旧知识保持；其训练过程中还会基于样本上的预测置信信息选择语义记忆作为一致性目标。citeturn16search5turn9view3 官方 `NeurAI-Lab/CLS-ER` 仓库明确标注为该 ICLR 2022 论文的官方 PyTorch 实现。fileciteturn6file0L2-L5

但它与你设想的“repair head + conservative head”有重要边界：CLS-ER 的两套快/慢记忆是**持续学习状态的双时间尺度维护**，不是两个相互竞争的二元部署决策器，也不分别持有 FPR 与 FNR 阈值。其意义在于说明“把稳定与适应放进两个不同速率的预测路径”已经有强先例，不提供 LAMDA 的固定 FPR 解法。citeturn9view3

### 漂移检测里，同任务旧/新专家 ensemble 更成熟

Kolter 与 Maloof 的 **Dynamic Weighted Majority: An Ensemble Method for Drifting Concepts**，JMLR 2007，正是在**同一个持续漂移预测任务**中维持多个专家，根据性能重新加权、淘汰并增加专家；这不是 Task-IL 的“已知任务 ID 后选对应 head”。citeturn27search1turn27search4

因此，“部署期保留旧模型/旧头，并与新模型联合决策”在 concept drift 文献中完全属于正常模型适应策略，而不是原则上不合法的做法。关键审计点不是“用了两个模型是否作弊”，而是**组合器依赖什么信息、组合参数何时冻结、有没有使用不允许的目标期标签**。DWM 本身就是依据在线表现动态管理专家。citeturn27search1

### 为什么 Task-IL 多头不能充当这个问题的直接先例

InfLoRA 在其问题设定中明确区分 Task-IL 与 Class-IL：Task-IL 可以在测试阶段知道 task identity，而 Class-IL 不享有这一信息。citeturn26view0 HAT 与 PackNet 一类经典参数隔离方法也主要围绕“任务对应掩码/参数子集”组织知识，而不是在同一个二元判别任务中判断“这个具体样本应该走安全头还是修复头”。citeturn15search1turn15search0turn15search7

对 LAMDA 来说，“安全”和“修复”不是两个 task：

\[
y\in\{0,1\}
\]

仍然是同一个 label space；同一年度的 benign 与 malware 同时出现。没有一个免费提供的 task-ID 告诉系统“这一条请走 repair head”。

所以真正困难的变量变成：

\[
g(x)\in\{0,1\},
\]

其中 \(g(x)=1\) 才允许 repair expert 覆盖 conservative expert。

这也是为什么**两头本身不够**。

设冻结表示为 \(h(x)\)，两只头都是 affine：

\[
z_C(x)=w_C^\top h(x)+b_C,\qquad
z_R(x)=w_R^\top h(x)+b_R.
\]

若只是常数插值：

\[
z_\alpha(x)
=(1-\alpha)z_C(x)+\alpha z_R(x),
\]

则

\[
z_\alpha(x)
=
[(1-\alpha)w_C+\alpha w_R]^\top h(x)
+
[(1-\alpha)b_C+\alpha b_R],
\]

**它仍然只是一只新的线性头。**【M：代数恒等式】

在你们已经观察到“warm-start head-only 可学但全局外溢”的条件下，常数权重双头不能从函数类上解决“单一全局 affine map 缺乏局部性”的问题。【L+M】

真正增加函数表达能力的是：

\[
z(x)
=
[1-g(x)]\,z_C(x)+g(x)\,z_R(x),
\]

其中 \(g(x)\) 随输入变化。PromptFusion-Lite 的输入条件模块、MoE-Adapters 的路由器，都属于这个一般方向。citeturn9view1turn26view1

还有一个必须提前写清的简单边界。若没有 gate，而是：

\[
\hat y=1
\iff
z_C\ge a_C\;\lor\;z_R\ge a_R,
\]

则其恶意判定区域是两个正类区域的并集。因此相对于完全保留 conservative 头的决策集合，OR 只能不变或扩大正类集合；一旦 repair 头在任何原 benign 区域触发，就会增加 FP。【M】反之 AND 规则只会缩小正类区域，天然牺牲 recall。**所以“各自阈值的双头”本身没有解开安全—修复矛盾；输入选择器才是关键部件。**

**外部候选结论：**同任务双头值得继续做文献化设计，但建议把候选明确命名为 **input-gated conservative/repair experts**，不要把“two-head”本身当创新，更不要使用 Task-IL 多头的结果替代证据。其首要零训练可证伪条件，是在现有冻结 \(h(x)\) 下必须存在某种因果可观测信号，能把“值得修的旧 FN”与“repair 路径会伤害的 benign”分开；否则 gate 只是把原来的不可分问题转移到选择器。

## 推理组合与校准：ensemble 合法，但单调校准基本吃不到你们的 oracle 空间

### 新旧模型 ensemble 不是天然“变相调阈值”

DWM 是概念漂移领域的经典反例：部署系统可以合法保留多个同任务专家并根据在线表现加权和替换。其四个主要机制就是训练在线专家、按表现调整权重、删除表现差的专家、在 ensemble 全局表现下降时增加新专家。citeturn27search1

因此，从文献规范看：

\[
s(x)
=
(1-\alpha)s_{\mathrm{old}}(x)
+\alpha s_{\mathrm{new}}(x)
\]

本身不是“作弊”。是否合法取决于 \(\alpha\) 如何得到、目标期标签是否被非法使用，以及最终性能是否仍用冻结协议独立评价。

但对**固定表示上的两个 affine 头**，上一节已证明常数 \(\alpha\) 只产生第三个 affine 头。【M】所以它在你们这里更多应作为**直接 ensemble 基线**，而非“获得局部修复空间”的主要机制。

如果 \(s_{\mathrm{old}}\) 与 \(s_{\mathrm{new}}\) 是不同的非线性模型，常数融合可以改变排序；如果权重是输入相关的 \(\alpha(x)\)，也可以产生 piecewise/nonlinear decision surface。DWM、PromptFusion-Lite、MoE-Adapters 分别代表“动态专家系统”“输入条件稳定/可塑选择”“输入/分布条件专家路由”的不同成熟邻域。citeturn27search1turn9view1turn26view1

### Temperature scaling 在固定 0.5 二元阈值下，严格不能修一个 FN

Guo、Pleiss、Sun、Weinberger 的 **On Calibration of Modern Neural Networks**，ICML 2017，§4 系统比较 histogram binning、isotonic regression、Platt scaling 与 temperature scaling；论文明确将这些作为训练完成后的 calibration procedure，并在验证集上估计校准参数。citeturn17view4turn19view1

对二元 logit \(z\)，temperature scaling 是：

\[
p_T=\sigma(z/T),\qquad T>0.
\]

在合同阈值 0.5 下：

\[
p_T\ge0.5
\iff
z/T\ge0
\iff
z\ge0.
\]

因此 **TP、FP、TN、FN 一个都不会改变**。【M】Guo 原文对多类 softmax 也明确指出 temperature scaling 不改变最大 logit 对应类别，因此不会改变分类准确率；它改变的是置信校准。citeturn21view0

所以在当前固定阈值合同下，temperature scaling 可以作为**校准负控**，不能成为“修复漏判”的主候选。

### Platt scaling 对 hard decision 来说，确实等价于改一个全局阈值

Guo §4.1 给出的 Platt scaling 形式可写为：

\[
p'(x)=\sigma(a z(x)+b).
\]

当 \(a>0\) 时，

\[
p'(x)\ge0.5
\iff
z(x)\ge-\frac ba.
\]

因此，**如果最终仍以 calibrated probability 的 0.5 作为 hard threshold，Platt scaling 对原 logit 的 hard decision 完全等价于把全局阈值改到 \(-b/a\)**。【M，基于 Guo §4.1】citeturn19view1

这就是你问的“有没有被批评成变相调阈值”需要非常谨慎表述的地方：

> 我没有找到 Guo 等原文把 Platt scaling 贬称为“cheating”或“disguised threshold tuning”。**“对二元 hard decision 等价于全局阈值变化”是数学事实，而不是原论文的价值判断。**

如果你们合同冻结 0.5 的实质含义是“不得改变 ER 原操作点”，那么把 Platt 输出再阈值于 0.5，虽然形式上阈值数字没变，**操作上确实改变了原模型决策边界**。因此不能把它包装成“没有调阈值”。

### Isotonic regression 也不能创造新的排序几何

isotonic calibration 学习的是一个**非递减**的标量映射。Guo §4.1 将其列为非参数 calibration 方法。citeturn20view0

若

\[
q=f(p), \qquad f \text{ nondecreasing},
\]

那么它不会颠倒样本的原始顺序，只可能把一段分数压成相同值。最终再以 \(q\ge0.5\) 判断，本质仍然是在原排序上的一个 cut。【M】

按交接包，“在相同 FP 预算下重排 ER 自身分数，FN 几乎不动”已经是一个很强的本地病灶提示。【L】它不能证明所有校准必败，但和上述数学性质合在一起，意味着：

> **temperature / positive-slope Platt / isotonic 都不应被期待从现有一维分数排序里创造 oracle 所显示的局部修复空间。**

### 在线校准在 drift 下有合法先例，但需要因果标签

Gupta 与 Ramdas 的 **Online Platt Scaling with Calibeating**，ICML 2023，研究的正是流式、可能 non-IID 的预测校准：标量 base score 随数据流通过在线 logistic calibration 更新，目标是处理时间变化和分布漂移。citeturn8view2turn12view2

这说明“每年或在线重校准输出”在 drift 文献中并不非法；合法性关键在于**校准标签在决策时是否已经因果到达**。它不能授权使用尚未到达年份的 test 标签，也不能让开发面板 test 标签反向进入训练。

而且这种方法依旧只有原模型的一维 score 作为主要输入，因此它解决的是 calibration drift，不是缺失的局部特征分离能力。citeturn8view2

**外部候选排序：**若目标是严格固定 \(h(x)\)，推理侧最值得研究的是**输入相关 old/new expert gate**；constant interpolation 可做直接基线；temperature / Platt / isotonic 更适合作为“单调输出适应是否足够”的否定性基线。不能将它们的其他数据集效果当成 LAMDA 结果。

## 选择性参数更新：成熟方法很多，但“按恶意风险逐样本路由参数”仍不是同一件事

### PackNet 与 HAT：成熟的是任务级参数隔离

Mallya 与 Lazebnik 的 **PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning**，CVPR 2018，通过迭代剪枝释放参数供新任务使用，并为已有任务保留其参数子网络。它证明“不是全参数更新，也不是只训练最后一层，而是在参数空间中划出不同子集”是成熟持续学习思路。citeturn15search0turn15search7

Serra 等的 **Overcoming Catastrophic Forgetting with Hard Attention to the Task (HAT)**，ICML 2018，则显式学习 task-specific hard-attention masks，并用已有任务的 mask 来保护参数。citeturn15search1

但二者的核心条件都是**任务/任务掩码结构**。它们没有解决同一年度、同一 label space 下“这一条 malware 可以走 plastic 参数，这一条 benign 必须走 stable 参数”的样本风险路由问题。

因此，不能把“sample-risk routed repair subnet”简单重命名成 PackNet/HAT；反过来，也不能把 PackNet/HAT 的结果当成风险路由在 LAMDA 有效的证据。

### InfLoRA：比 head-only 更细的子空间更新，但不是严格固定表征

Liang 与 Li 的 **Interference-Free Low-Rank Adaptation for Continual Learning (InfLoRA)**，CVPR 2024，把低秩适配解释为在低维参数子空间里学习，并专门设计该子空间来减少新旧知识间干扰。原文 §1–§3 将 PEFT 的优势与现有方法仍可能产生 interference 的问题分开讨论。citeturn26view0 官方仓库明确为该 CVPR 2024 工作的官方实现。fileciteturn4file0L2-L5

它非常适合作为“**全参数 vs head-only 之间是否存在低维可塑子空间**”的成熟近邻。

但这里有一个对你的主问题至关重要的边界：

若 adapter/LoRA 位于 backbone 中间层，

\[
h_{\mathrm{new}}(x)\neq h_{\mathrm{old}}(x)
\]

通常正是它获得额外能力的来源。基础权重 \(W\) 没改，并不意味着有效表示没改。

所以：

- 若科学约束是 **“不修改旧 backbone 权重”**，InfLoRA 是非常合理的成熟直接候选；
- 若科学约束是 **“任何样本的表示 \(h(x)\) 都不能改变”**，它不符合要求。

此外，如果把 LoRA 只放到最后一个二元标量线性头，对一个 rank 本来就极低的输出映射，LoRA 未必增加你真正需要的局部函数自由度；它更多改变参数化方式，而不是使不同输入获得不同路径。【M】

### MoE-Adapters 是更接近“风险路由”的结构先例

Yu 等的 **Boosting Continual Learning of Vision-Language Models via Mixture-of-Experts Adapters**，CVPR 2024，在冻结 CLIP 基座上增量使用 MoE adapter，并通过 router 对专家进行 gated aggregation；论文 **§3.3、Eq. (1)** 给出多个专家输出的加权组合，后续的 distribution-aware selection 则处理何时使用适配模块与原始模型。citeturn26view1 官方 `JiazuoYu/MoE-Adapters4CL` 仓库明确登记为 CVPR 2024 MoE-Adapters 代码。fileciteturn5file0L2-L5

这和你们想要的结构有一个非常有价值的类比：

\[
\text{default stable path}
\quad\text{vs}\quad
\text{adapted expert path},
\]

由输入相关 router 选择。

但它的路由信号是任务/分布适应语义，并不是“这个输入如果进入 repair expert 会不会制造 FP”。因此 LAMDA 若使用类似结构，真正需要验证的是：

\[
g(h(x))
\approx
P(\text{repair beneficial and safe}\mid h(x)),
\]

而不是照搬 ID/OOD 或 task router。

### PromptFusion-Lite 的输入动态激活更接近你描述的“按样本风险路由”

PromptFusion-Lite 专门为了避免所有输入都承担双模块开销而引入输入条件激活。官方 README 明确写的是“dynamically determining whether to activate both modules for each input image”。fileciteturn2file0L2-L5 原论文的输入选择通过可学习离散化机制实现。citeturn9view1

因此，“**按样本决定是否开放塑性通路**”本身也已有强先例。LAMDA 的可研究差量应是**路由依据从一般计算/持续学习需要，转成固定-FPR 下的 repair-safety region**，而不能把 per-input routing 宣称成新概念。

### 这一类方法的真正失败门

由这些论文结构与 LAMDA 本地病灶综合起来，最值得先做的不是 GPU，而是一个**表示可分性 gate**。【外部候选，M+L】

设已有冻结表示：

\[
h(x).
\]

定义两种当前合法样本集合：

\[
R=\{\text{旧模型漏判、且希望修复的 malware}\},
\]

\[
H=\{\text{一旦开放 repair 路径最容易被伤害的 benign}\}.
\]

若任何低复杂度、预登记 selector

\[
g(h(x))
\]

都无法在 source/dev 合法信息上把 \(R\) 与 \(H\) 形成有用区分，那么：

- LoRA 的**全局**低秩适配仍可能外溢；
- 两只 affine heads 也不会自动产生局部性；
- MoE/router 只是把最困难的问题移到 router；
- “风险路由”没有足够源年可观测信号。

反过来，若 \(R/H\) 在 frozen \(h\) 中存在明显可分的局部区域，**input-gated experts 才是真正符合“表示不动但增加局部决策容量”的成熟方向。**

因此，外部候选优先级是：

**严格 \(h(x)\) 固定时：** gated output experts > constant dual-head fusion > monotone calibration。

**只要求旧 backbone 参数固定时：** PromptFusion/adapter/InfLoRA/MoE 类 PEFT 路线都可以进入成熟近邻池，但应明确它们仍让有效表示移动。

## Margin 带：非常成熟，适合作为最小反事实，但不能绕过“深 FN 必须跨很远”的事实

### “达到小正 margin 后不再推”本质是 shifted hinge 家族

假设二元恶意 logit 为 \(z\)，当前阈值 \(p=0.5\) 对应：

\[
z=0.
\]

若希望修复目标只达到：

\[
p^\star=0.5+\delta,
\qquad 0<\delta<0.5,
\]

则目标 logit 是：

\[
m_\delta
=
\operatorname{logit}(0.5+\delta)
=
\log
\frac{0.5+\delta}{0.5-\delta}.
\]

一个最直接的“达到小带就停止”损失为：

\[
L_{\mathrm{band}}(z)
=
[m_\delta-z]_+.
\]

它在：

\[
z\ge m_\delta
\]

后严格没有继续把恶意 logit 往 \(+\infty\) 推的梯度。【M】

这属于 margin/hinge loss 的成熟函数族，**不能作为损失形式本身的新颖性**。

Bartlett 与 Wegkamp 的 **Classification with a Reject Option using a Hinge Loss**，JMLR 2008，在 **§1 Eq. (1)** 明确定义围绕决策边界的拒绝带，在 **§2** 构造 generalized hinge loss。citeturn17view5turn19view3turn19view2 其问题当然不同：它允许第三种动作“reject”，而你们合同仍是二元 0.5 hard decision。因此它只证明“边界带/hinge 形式是成熟设计”，不证明 LAMDA 应增加 abstention。

### 它与当前 BCE 修复有什么实际差异

标准正类 BCE：

\[
L_{\mathrm{BCE}}(z,1)
=
\operatorname{softplus}(-z)
\]

的导数是：

\[
\frac{\partial L}{\partial z}
=
\sigma(z)-1.
\]

对任何有限 \(z\)，它都不为零。因此即便样本已经从 0.49 修到 0.7、0.9，它仍然继续鼓励更高正类置信度。【M】

而 band hinge：

\[
\frac{\partial L_{\mathrm{band}}}{\partial z}
=
\begin{cases}
-1,&z<m_\delta\\
0,&z>m_\delta
\end{cases}
\]

会在达到所登记 margin 后停止额外修复压力。【M】

所以它非常适合回答一个具体而干净的问题：

> **你们已有外溢有多少来自“必须跨过 0.5 的必要更新”，又有多少来自“跨过去以后 BCE 还继续深推”的 overshoot？**

这是一个高度可证伪的任务化问题。

### 但本地“七成深埋”让它不太可能成为完整解法

对旧模型 \(p_{\mathrm{old}}=0.3\)：

\[
z_{\mathrm{old}}
=
\log\frac{0.3}{0.7}
\approx-0.847.
\]

即使只修到恰好 0.5：

\[
\Delta z\ge0.847.
\]

如果目标是 \(0.5+\delta\)，需要的位移更大：

\[
\Delta z
\ge
m_\delta-z_{\mathrm{old}}.
\]

因此 **band 只截掉 crossing 之后的过度推进，并不能消除深 FN 跨过边界之前所需要的那段几何移动。**【M】

按交接包，2016 和 2018 约七成旧 FN 分数不高于 0.3，而 0.3–0.5 的贴边样本很少。【L】所以其合理预期应是：

> “先测试是否能显著降低 overshoot 外溢”，

而不是：

> “文献表明 margin 带可以解决主要 FN 修复”。

### 与 OHEM 完全不是同一个部件

Shrivastava、Gupta、Girshick 的 **Training Region-based Object Detectors with Online Hard Example Mining**，CVPR 2016，在 **§4.1** 的核心操作是计算候选样本 loss、按 loss 排序，再选择高损失 hard examples 参与优化。citeturn25search3 作者官方仓库 `abhi2610/ohem` 明确是 OHEM for Fast R-CNN。fileciteturn7file0L2-L5

所以：

- OHEM 回答：**哪些样本训练？**
- band hinge 回答：**选中的正类样本推到哪里停止？**

如果你们只对旧 FN 使用 band loss，这是一种**样本资格条件 + margin target**；不应改名成 OHEM，也不能声称“首次困难样本定向训练”。

### 与 PCT FD-LM 的边界更清楚

Yan 等 **Positive-Congruent Training: Towards Regression-Free Model Updates**，CVPR 2021，核心问题是减少模型升级时的 negative flips。论文 **§4.2、Eq. (7)–(9)** 的 Focal Distillation 对旧正确样本增强蒸馏，FD-LM 中的 **LM 是 Logit Matching**，不是 Large Margin。citeturn25academia11turn26view2

因此：

\[
L_{\mathrm{FD-LM}}
\sim
\|z_{\mathrm{new}}-z_{\mathrm{old}}\|
\]

的思想是**保持旧输出兼容性**；

而：

\[
L_{\mathrm{band}}
=
[m_\delta-z_{\mathrm{new}}]_+
\]

是**对指定旧 FN 设最小修复边界，达到后停止**。

两个方向一个主要保护旧正确决策，一个主要限制修复的终点。把它们联合可能是任务设计，但“蒸馏 + margin”本身不能先验宣称创新；而且你们已有 PCT 任务化筛选未过门这一点只能写成本地 LAMDA screening 证据，不能反推 PCT 原方法一般无效。【L】

**外部候选建议：**在所有需要新训练的方案中，stop-at-band repair 是最值得作为**最低成本机制反事实**保留的之一，因为它只回答一个变量：“停止过度修复有没有帮助？”但按深 FN 结构，建议预先把失败门写得很硬；若外溢基本不变，就应记录为“外溢主要发生在 crossing 所需更新，而非 crossing 后 overshoot”，而不是继续调很多 \(\delta\)。

## 八连败应该怎么命名：stability–plasticity 是上位词，update compatibility 更贴近你们的误报病灶

### Stability–plasticity dilemma 是最稳妥的持续学习总括

PromptFusion 的论文和官方代码都直接把研究问题称为 **stability-plasticity dilemma**：系统既要保持旧知识，又需要充分学习新知识。其 Stabilizer 与 Booster 正是为了显式解耦两种需求。citeturn22academia35 fileciteturn2file0L2-L5

因此，你们观察到：

- 强修复 → plasticity 高，但 benign FP 外溢；
- 强投影/保护 → stability 提高，但 FNR 变坏；

完全可以在第三章讨论中放在 stability–plasticity umbrella 下。【外部解释，结合 L】

但“catastrophic forgetting”不是八连败全部现象的准确名字。交接包中很多新增 FP 是**当前年度 benign 原本由 ER 判对、被新的 repair update 推错**；这不要求证明模型“忘掉了旧任务”。【L】因此若全文把所有误报外溢都叫 forgetting，会把当前决策回归与历史知识遗忘混在一起。

### Performance/compatibility tradeoff 比 catastrophic forgetting 更贴近“修复制造新错”

Bansal 等 **Updates in Human-AI Teams: Understanding and Addressing the Performance/Compatibility Tradeoff**，AAAI 2019，讨论了模型升级后的一个核心现象：即使新版总体预测性能提高，也可能产生与旧模型行为不兼容的新错误；论文由此引入 update compatibility 概念。citeturn27search2turn27search5

这与 LAMDA 的局部问题高度同构：

\[
\text{old correct benign}
\longrightarrow
\text{new false positive}.
\]

PCT 则把：

\[
h_{\mathrm{old}}(x)=y,
\qquad
h_{\mathrm{new}}(x)\ne y
\]

称为 **negative flip**，其 Positive-Congruent Training 正是围绕减少 model update regressions 展开。citeturn25academia11

所以最精确的写法可以是：

> **本地筛选揭示的是固定 FPR 操作点下的 stability–plasticity conflict，并表现为显著的 benign-side update regression / negative-flip externality。**

这里前三个已有文献锚点：

- `stability–plasticity dilemma`：成熟 CL 术语；citeturn22academia35
- `performance/compatibility tradeoff`：模型升级兼容性文献；citeturn27search2
- `negative flips/model regression`：PCT 直接邻域。citeturn25academia11

而“**FPR-constrained stability–plasticity dilemma**”在本轮原始论文检索中**没有找到足以认定为公认固定术语的来源**。因此可以作为你们自己的描述性短语，但必须写成“we refer to / 本文称为”，不能写成“文献通常称为”。

### 与你们八连败结构的更准确映射

| 本地机制现象【L】 | 最接近的已有文献概念 | 不能越界声称 |
|---|---|---|
| ER 后修复 FN，却制造旧正确 benign→FP | update regression / negative flip / compatibility | 不等于一般 catastrophic forgetting |
| 投影/约束压住 FP，却吞掉修复 | stability–plasticity dilemma | 文献没证明 LAMDA 无可行解 |
| warm-start head-only 仍全局外溢 | global output-map interference 的本地证据 | 不能由一只 MLP head 推广到所有固定表示分类器 |
| PCT 未解决本地 FPR gate | 直接 regression-aware baseline 已筛过 | 不能说 PCT 一般无效 |
| Top-K benign pinning覆盖低 | 本地说明旧分数尾并非主要损伤定位器 | 不能推导完整表示空间不可分 |
| 固定 FP 预算重排无残值 | 单调校准/阈值移动缺少本地空间 | 不能排除 input-dependent rerouting |

这最后一点尤其重要。你们的 oracle half-FN repair 显示**标签层面存在理想修复空间**，但原一维 score ordering 够不着。【L】文献上与之最一致的下一步并不是继续寻找更聪明的 global scalar calibration，而是问：

\[
\text{能否构造新的 sample-dependent decision coordinate？}
\]

在严格不移动 \(h(x)\) 的合同下，这个 coordinate 最自然地来自 **selector/gate over fixed experts**；若连 frozen \(h(x)\) 都无法提供 selector 的分离信号，才有较充分理由转向有效表示变化。

## 外部候选优先级、完整题录与未决问题

### 对避免无效 GPU 的排序

基于文献机制与交接包病灶，而**不是替本地作存废裁决**，我会这样排：

| 外部候选 | 是否严格固定 \(h(x)\) | 能否产生新的局部决策能力 | 本轮文献判断 |
|---|---:|---:|---|
| **输入 gated conservative/repair heads** | 是 | **是**，前提是 gate 依赖输入 | **最值得先做零训练分离性探针；最符合主问题** |
| **stop-at-band FN repair** | 可 | 否，仍是一只全局头 | **最低成本可证伪训练基线** |
| 输入相关 old/new model selector | 可 | 是 | 漂移 ensemble 文献成熟；与上一项结构近邻 |
| 常数 old/new score interpolation | 是 | 对 affine heads **否** | 直接基线即可，不宜当主创新 |
| Temperature scaling | 是 | 否；0.5 hard labels完全不变 | 负控 |
| Platt / isotonic calibration | 是 | 不创造新排序；主要改变 operating point | 校准基线，尤其不适合当前“同 FP 预算无残值”病灶 |
| InfLoRA | **否（严格意义）** | 是 | 若合同放宽为“旧 backbone 权重不变”，是成熟强候选 |
| MoE-Adapters / PromptFusion | **否（严格意义）** | 是，且有路由 | 若允许 adapter/prompt 改变有效表示，文献依据很强 |
| PackNet/HAT | 通常否/取决于实现 | 参数隔离 | task-level 先例，不是同任务风险路由直接解 |

**最关键的研究前置不是另跑一个双头 GPU 臂，而是确定 gate 是否有信号。**【外部候选】

在已经合法到达的 source/dev 信息内，可定义：

\[
R_t=
\{\text{旧模型 FN malware}\},
\]

并定义一个严格不使用候选模型未来错误标签反选的 benign 风险参考 \(H_t\)。对 frozen \(h(x)\) 检验一个极简 selector family 是否能让：

\[
g(h(x))
\]

在保持 benign 路由率极低的同时覆盖显著一部分 \(R_t\)。若没有这一最低信号，再复杂的 MoE gate 很容易只是学习一个新的全局 tradeoff；若有，则双头/专家路由才具有比 constant score fusion 更明确的机制根据。这是可证伪性建议，不是文献保证。

### 原始题录与精确位置

**Haoran Chen, Zuxuan Wu, Xintong Han, Menglin Jia, Yu-Gang Jiang. _PromptFusion: Decoupling Stability and Plasticity for Continual Learning._ ECCV 2024；arXiv:2303.07223。**重点核对：方法部分 Stabilizer/Booster；输出融合 **Eq. (3)–(4)**；PromptFusion-Lite 输入条件选择 **Eq. (7)–(8)**。论文明确以 stability–plasticity dilemma 为研究动机。citeturn22academia35turn9view0turn9view1 官方仓库：`HaoranChen/PromptFusion`。fileciteturn2file0L2-L5

**Elahe Arani, Fahad Sarfraz, Bahram Zonooz. _Learning Fast, Learning Slow: A General Continual Learning Method based on Complementary Learning System._ ICLR 2022；arXiv:2201.12604。**重点：stable/plastic semantic memories、不同更新时间尺度及样本级一致性来源选择；附录关于单一 semantic memory 的稳定/近期适应取舍讨论。citeturn16search5turn9view3 官方仓库：`NeurAI-Lab/CLS-ER`。fileciteturn6file0L2-L5

**J. Zico Kolter, Marcus A. Maloof. _Dynamic Weighted Majority: An Ensemble Method for Drifting Concepts._ Journal of Machine Learning Research 8(91):2755–2790, 2007。**重点：同任务 concept drift ensemble，动态权重、删除与新增专家。citeturn27search1turn27search4

**Gagan Bansal, Besmira Nushi, Ece Kamar, Daniel S. Weld, Walter S. Lasecki, Eric Horvitz. _Updates in Human-AI Teams: Understanding and Addressing the Performance/Compatibility Tradeoff._ AAAI 2019, 33(01):2429–2437。**重点：“Compatibility of Updates to Classifiers”部分及 compatibility 定义；全文专门讨论 performance 与 compatibility 的更新取舍。citeturn27search2turn27search5

**Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger. _On Calibration of Modern Neural Networks._ ICML 2017, PMLR 70:1321–1330。**重点：**§4** calibration methods；**§4.1** histogram/isotonic/Platt；temperature scaling 的标量温度形式及其不改变 argmax class 的性质。citeturn17view4turn19view1turn20view0turn21view0

**Chirag Gupta, Aaditya Ramdas. _Online Platt Scaling with Calibeating._ ICML 2023, PMLR 202。**重点：online calibration / online Platt scaling，在流式、non-IID/漂移条件下依据顺序到达标签更新校准映射。citeturn8view2turn12view2

**Yan-Shuo Liang, Wu-Jun Li. _Interference-Free Low-Rank Adaptation for Continual Learning._ CVPR 2024:23638–23647；arXiv:2404.00228。**重点：引言与方法关于 PEFT、LoRA 低维子空间以及减少新旧干扰的构造；论文也明确区分 TIL 与 CIL 的 inference 信息条件。citeturn26view0 官方仓库：`liangyanshuo/InfLoRA`。fileciteturn4file0L2-L5

**Jiazuo Yu et al. _Boosting Continual Learning of Vision-Language Models via Mixture-of-Experts Adapters._ CVPR 2024:23219–23230；arXiv:2403.11549。**重点：**§3.3、Eq. (1)** MoE expert gated aggregation，以及后续 distribution-aware adapter selection。citeturn26view1 官方仓库：`JiazuoYu/MoE-Adapters4CL`。fileciteturn5file0L2-L5

**Arun Mallya, Svetlana Lazebnik. _PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning._ CVPR 2018。**重点：迭代剪枝、为后续任务释放参数、任务间参数隔离。它是参数子集持续学习先例，不是 same-task sample-risk router。citeturn15search0turn15search7

**Joan Serra, Didac Suris, Marius Miron, Alexandros Karatzoglou. _Overcoming Catastrophic Forgetting with Hard Attention to the Task._ ICML 2018, PMLR 80:4548–4557。**重点：task-conditioned hard attention masks 与以前任务 mask 对参数更新的保护。citeturn15search1

**Peter L. Bartlett, Marten H. Wegkamp. _Classification with a Reject Option using a Hinge Loss._ JMLR 9(59):1823–1840, 2008。**重点：**§1 Eq. (1)** 决策/拒绝带；**§2** generalized hinge loss。它是 margin-band 的成熟近邻，但部署动作空间多了 reject。citeturn17view5turn19view3turn19view2

**Abhinav Shrivastava, Abhinav Gupta, Ross Girshick. _Training Region-based Object Detectors with Online Hard Example Mining._ CVPR 2016；arXiv:1604.03540。**重点：**§4.1** 按当前 loss 排序并选择 hard examples。它改变样本选择，不规定“修到哪里停止”。citeturn25search3 官方仓库：`abhi2610/ohem`。fileciteturn7file0L2-L5

**Sijie Yan, Yuanjun Xiong, Kaustav Kundu, Shuo Yang, Siqi Deng, Meng Wang, Wei Xia, Stefano Soatto. _Positive-Congruent Training: Towards Regression-Free Model Updates._ CVPR 2021:14299–14308；arXiv:2011.09161v3。**重点：negative flips；**§4.2 Eq. (7)–(9)** Focal Distillation。FD-LM 为 **Logit Matching**，不是 margin loss。citeturn25academia11turn26view2

### 不确定性与尚未回答的问题

**同款双头的文献空缺属于“本轮未检出”，不是不存在证明。** 我找到的是 PromptFusion、CLS-ER、DWM/MoE 等非常近的稳定—可塑双路径与输入路由机制，但没有找到同行评审原始论文正好把“同一二元恶意检测任务中的 conservative head 与 repair head、独立操作点、hard FPR 不升”作为完整问题定义。因此未来若要做 novelty statement，仍需在正式写作前做一次专门的同义词检索，例如 model update routing、selective model patching、patch classifier、fallback classifier、safe model update、selective prediction under model update；不能把这次“未检出”写成“首次”。

**严格固定表示下，gate 是否有足够信息，是当前最大未知数。** 文献能证明 input-conditioned routing 是成熟工具，却不能证明 LAMDA 的 frozen \(h(x)\) 能提供安全路由信号。交接包目前证明的是 old scalar score 的高尾定位失败以及 global head 更新外溢；它还没有等价证明整个高维 frozen representation 无法区分 repair-needed malware 与 endangered benign。【L】

**校准应与分类能力分开写。** Temperature 在固定 0.5 下严格不改 hard labels；positive-slope Platt 对 hard decision 等价于移动原 logit 的全局阈值；isotonic 保留排序。这些是由经典 calibration 公式得到的数学结论，而不是“校准文献被社区判定为作弊”。citeturn19view1turn20view0turn21view0

**Margin 带的创新边界很窄。** Hinge/margin/reject-band 都是成熟方法；真正可能形成任务化贡献的只能是诸如“只对因果识别的旧 FN 使用 stop-at-small-band repair，并在固定 FPR/update-compatibility gate 下验证其是否减少 benign regressions”这样的完整问题设计，而不能以“用了 margin”本身作算法创新。citeturn19view2turn25search3turn26view2

**最保守的外部文献结论是：**按交接包的八连败和操作点探针，目前不值得把主要希望放在单调校准、常数双头插值或再一轮全局 head-only 修复上；真正与病灶结构相匹配、且有成熟方法邻域支撑的“表示不动”方向，是**固定表示上的输入条件化 conservative/repair expert routing**。其必要的前置可证伪问题不是“多一只头能不能学”，而是**合法源/开发信息是否能让 gate 找到 repair-beneficial 且 benign-safe 的局部区域**。若这一条件在冻结表示上也缺失，InfLoRA、PromptFusion、MoE-Adapters 一类允许有效表示变化的 PEFT 路线才是文献上更自然的下一层搜索空间，而这将属于另一种“冻结”定义。citeturn22academia35turn26view0turn26view1