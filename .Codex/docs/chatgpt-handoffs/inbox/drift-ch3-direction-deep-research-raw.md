# 域名检测抗漂移方法：公开文献定点排重原始报告

actual_model: GPT-6 Astra Pro（本会话模型标识；未读取界面模型选择器）  
actual_effort: 无可核值（未暴露独立思考强度档位）  
actual_mode: 普通 ChatGPT 对话中的多轮公开文献检索与审查；未取得独立“深度研究”作业标识或模式切换凭据  
used_apps: Sider Scholar（候选发现，成功）、GitHub（公开作者实现与公开数据权限核对，成功）、Scite（已调用，但月度配额阻断，未取得引用语境证据）；补充使用 web 读取公开一手题录、全文和权限声明  
检索日期: 2026-09-08；检索收尾核时: 2026-09-08 05:37:10 UTC  
统一状态: **外部候选，待本地全文和实验复核**

本文为完整原始研究报告，不是论文全文转录。全部候选、重复判断、反例与待证问题均具有上述统一状态。材料范围为公开论文、作者公开仓库说明和数据权限声明。没有执行论文实现、训练、推理或诊断程序；没有访问私有仓库，也没有索取私有数据、日志、模型、权重、目标期材料或凭据。生成的唯一交付物是本 Markdown 报告，不更改任何研究合同或既有实验。

“全文已读”在本文具体表示：取得可读全文，并阅读与本问题有关的方法、公式和评估协议章节；不表示逐页通读所有附录，更不表示完成实验复现。只读题录或摘要的外围检索结果没有进入机制排重依据。页码均为下列链接所对应 PDF 的文件页序，从第 1 页计，未与期刊连续页码混用。

## 一、一页候选矩阵：仅六篇新增直接近邻

以下六项均为 **外部候选，待本地全文和实验复核**。完整题录、全文 URL、权限与待证问题见第五节。

| 编号／新增近邻 | 最能改变的排重判断 | 不能外推的边界／关键反例 | 全文定位 |
|---|---|---|---|
| N1 Feature-Critic，ICML 2019 | 源域拆成 meta-train/meta-test；比较有／无辅助更新在留出域的主任务收益。方向一的核心反馈结构已有直接先例。 | 研究视觉域泛化；更换为 DGA 家族留出不是自动获得的新算法。留出域也可能不代表未来。 | §§3.2–3.4，PDF pp.3–5，式(3)–(5)、算法1。 |
| N2 Auto-Lambda，TMLR 2022 | 主任务验证损失驱动动态任务权重；“动态选择有益辅助任务”不能单独作为差量。 | 实际 train/val 更新批次可来自同一训练集，不等于留出家族／环境；验证信号也可能过拟合。 | §4，PDF pp.5–7，式(3)–(7)及 Swapping Training Data。 |
| N3 Test-Time Training，ICML 2020 | 冻结主任务分支，以自监督损失更新共享编码器，已经覆盖方向二的基本结构。 | 视觉而非 DGA；在线实验打乱测试顺序，不能直接代表真实时间序列漂移；任务收益依赖额外条件。 | §2，PDF p.2，式(2)–(3)；p.3 顺序说明；§4。 |
| N4 EATA，ICML 2022 | 选择更新样本、仅更新部分参数、用 Fisher 正则减轻遗忘，已覆盖“轻量更新＋伤害缓解”的一般设计。 | 视觉熵最小化，不是恶意软件重构任务；减轻遗忘不等于同时保证 FPR、FNR 不恶化。 | §4，PDF pp.4–5，式(2)–(9)、算法1。 |
| N5 MORPH，arXiv 2024 | 真正研究 Android／Windows 恶意软件；不对称伪标签筛选、再平衡及自训练是直接安全领域先例。 | 不是纯重构自监督，也不是冻结分类头的同构方法；“误报稀少、恶意预测可信”前提失效会污染更新。 | §4，PDF pp.7–9，算法1；p.9 未编号损失；§5.1 p.10。 |
| N6 META-DES，Pattern Recognition 2015 | 从局部信息预测每个专家是否正确，再选择专家／集成；局部键可靠性路由有更早先例。 | 需历史带标签的动态选择集 DSEL；所有专家同错时，即使完美预测错误也无法纠错。 | §3，PDF pp.9–16，算法1 p.12；§2 对局部估计失效的讨论。 |

矩阵证据：[N1 全文](https://arxiv.org/pdf/1901.11448)、[N2 全文](https://arxiv.org/pdf/2202.03091)、[N3 全文](https://arxiv.org/pdf/1909.13231)、[N4 全文](https://arxiv.org/pdf/2204.02610)、[N5 全文](https://arxiv.org/pdf/2401.12790)、[N6 全文](https://arxiv.org/pdf/1810.01270)。所有六项均已读相关全文章节，而不是根据摘要归属机制。

## 二、三类整体方法的排重判断

### 2.1 源侧留出家族／环境反馈选择辅助更新

用一个抽象式表示所述方案：

\[
 a^* = \arg\min_a \widehat R_{\mathrm{main}}^{\mathrm{source\text{-}holdout}}
 \bigl(U_a(\theta;D_{\mathrm{source\text{-}train}})\bigr).
\]

这只是对问题的数学归纳，不是提出新算法。决定性的区分是：反馈来自哪里、评价的是单步还是多步后的主任务、以及反馈最终改变权重、更新接受与否还是分支合并。

静态任务子集只在训练前或训练结束后比较，是模型选择；把它改为训练期间动态权重，是 Auto-Lambda 已覆盖的基本框架。把验证批次升级为留出源域，并用“有辅助更新”相对“无辅助更新”的主任务差值反馈，则直接接近 Feature-Critic 的式(3)–(5)。Feature-Critic 不仅研究异质标签空间，也包含同质域泛化；二分类 DGA 的家族留出更应与其同质设定比较，而不是借异质标签空间差异回避最近邻。[N1](https://arxiv.org/pdf/1901.11448) [N2](https://arxiv.org/pdf/2202.03091)

若方案会复制参数、让候选更新独立运行，再以主任务验证表现选择或合并，则与 ForkMerge §4、式(6)–(8)、算法1直接重叠。ForkMerge 还讨论多辅助任务选择，因此“不是只选一个任务”或“不是单步反馈”也不能直接作为新增差量。[ForkMerge，PDF pp.5–7](https://arxiv.org/pdf/2301.12618)

PCGrad 的反馈是训练任务梯度之间的冲突；GradNorm 的反馈是训练梯度范数和相对训练速度。它们与留出域主任务风险不是同一个判断量。因此，所述方案相对 PCGrad／GradNorm 确实改变了反馈信息，但这一区别已经被验证驱动和元学习先例占据。课程学习若只是按同一个反馈改变任务出现顺序、采样率或权重，则是调度形式不同，不能凭名称获得独立机制。[PCGrad，PDF p.4 算法1](https://arxiv.org/pdf/2001.06782) [GradNorm，PDF pp.2–4、式(1)–(2)](https://arxiv.org/pdf/1711.02257)

**外部判断：按当前描述，没有已经建立的不可约算法差量。** 可见变化主要是源侧划分方式、辅助任务参数化和更新粒度；这些变化需要证明不能被上述方法在相同信息条件下实例化，才有进一步讨论空间。源侧留出协议本身可以是有意义的评估设计，但不自动构成新的辅助学习原理。

尚需实证的是：控制器是否只学会了反复使用的留出组，收益是否超出普通动态调权／同预算 ForkMerge，以及用于选更新的风险是否能代表未参与选择的源侧家族或环境。这些是证据问题，不是本文对任何具体实验的裁决。

### 2.2 无标签自监督 TTA：结构先例存在，双侧伤害约束并未随之成立

必须分别对待“研究对象是恶意软件”“更新目标无人工标签”“整个评估协议无目标真值参与”和“严格在线”这四件事。

MADCAT 确实是 Android 恶意软件研究，且其 §3.2 已有“更新编码器的重构损失，配合预训练分类头推断”的结构。MORPH 也确实研究恶意软件，但属于伪标签自训练并保留原始带标签数据，不应归为同一重构自监督结构。DRIFT 确实研究 DGA，不过其主方法是训练期自监督预训练加监督微调；所述持续学习实验冻结骨干、更新分类头，不能当成冻结头的无标签 TTA 实证。[MADCAT，PDF pp.2–3](https://arxiv.org/pdf/2505.18734v1) [MORPH，§4](https://arxiv.org/pdf/2401.12790) [DRIFT，§III、§IV.4](https://arxiv.org/html/2605.10436v2)

TTT、EATA、SoTTA 在这里提供的是视觉机制先例，而不是 DGA／恶意软件效果证据。AIRL 是源域序列上的非平稳域泛化；其实验也不能充当 DGA TTA 证据。MalMoE 的对象是加密流量图漂移，而非域名字符串。没有保留单纯异常检测论文来填充六篇名额。[TTT](https://arxiv.org/pdf/1909.13231) [EATA](https://arxiv.org/pdf/2204.02610) [SoTTA](https://arxiv.org/pdf/2310.10074) [AIRL](https://arxiv.org/pdf/2405.06816v1) [MalMoE](https://arxiv.org/pdf/2602.10157v1)

**外部判断：冻结头、更新编码器或轻量参数，加上筛样／正则化，均已有直接先例；当前描述没有建立不可约差量。** “限制误报与漏报伤害”是尚待实现和检验的约束，不能因冻结头或加入正则项而视为已满足。

### 2.3 局部字符／子词键估计专家相对可靠性

META-DES 将局部邻域、输出轮廓等信息变成专家是否正确的元特征，再进行动态选择。MalMoE 更直接：式(8)以哪个专家的分类损失较小构造门控标签，式(9)–(10)只对专家预测分歧样本计算门控训练损失。因此，“不预测最终类别，而预测谁更可靠”本身也不是未被研究的决策结构。[META-DES，§3](https://arxiv.org/pdf/1810.01270) [MalMoE，PDF p.5、式(8)–(10)](https://arxiv.org/pdf/2602.10157v1)

在本任务的抽象层面，动态专家是按输入选择分支，质量感知融合是按可靠性给出软权重，条件记忆是用键检索历史信息的实现方式，普通错误预测估计某个模型是否会错。把字符／子词作为键，会改变信息和泛化偏置，但不自动改变“局部能力估计→专家选择”的原理。MalMoE 使用流量及图信息，不是局部字符串键，故只能否定一般门控原理的新颖性，不能据此声称两种完整模型相同。

设基线专家为 B、替代专家为 A、局部键为 K。与纠错直接相关的是：

\[
\Delta(k)=\mathbb E[\ell(B(X),Y)-\ell(A(X),Y)\mid K(X)=k],
\]

而不是单独的 \(P(B(X)\ne Y\mid K(X)=k)\)。如果选择器 S 只能在 A、B 间切换，在 0–1 损失下有恒等式：

\[
R_B-R_S=
P(S=A,\ B\ne Y,\ A=Y)
-
P(S=A,\ B=Y,\ A\ne Y).
\]

这两个式子是本文的分析推导，不是引自候选论文。右边分别是实际救回和错误换路的概率。运营中的误报／漏报代价可能不同，还须分别核验，不能用总体错误率掩盖一侧伤害。

**外部判断：当前描述没有建立超出特征受限的动态专家选择的不可约差量。** 真正尚缺的证据是分支可救回集合、选择器净收益，以及键条件下相对误差次序跨源侧留出环境是否保持，而不是仅证明键能预测某个分支的错误。

## 三、标签、统计量与因果边界审计

所有行均为 **外部候选，待本地全文和实验复核**。这里的“未发现”仅限已经阅读的章节，不表示完成了全部作者代码的标签流向审计。

| 方法 | 目标真值／类平衡 | 实际使用的目标信息范围 | 可支持和不可支持的结论 |
|---|---|---|---|
| MADCAT | §4.2 主结果明确以真值标签平衡训练和 TTA 数据；§4.3 才讨论伪标签替代。 | 月度数据分适应与验证；top-N 伪标签策略需要在该数据池内排序。 | 主结果不能一概作为纯无标签证据。月度验证是否参与停止、选模、调参未由已读文字完全交代，不能擅自宣判泄漏，也不能默认严格源侧选择。 |
| MORPH | 核心使用预测类别和伪标签，加原始带标签样本；另有主动学习结合情形，不能混称零目标标注。 | 对当前测试数据池预测，再按伪类别筛选、平衡并更新。 | 不是纯重构自监督。池式 top-N 不等于到达即决策。正文 §5.1 的年月说明内部不一致，准确时间协议仍待复核。 |
| TTT | 自监督更新不需要目标类别真值；不是按真值平衡。 | 可用单个当前样本及其增强；在线版本保留已更新状态。 | 主任务头固定的结构成立，但正文说明在线实验打乱测试顺序，因此不能将该实验等同自然时间漂移。 |
| EATA | 使用预测熵；Fisher 重要度来自预先收集的无标签 ID 样本及模型伪标签。 | 当前 mini-batch、过去输出的移动平均，以及事先的 ID 参考集合。 | 不能称为完全没有参考样本；mini-batch 统计不等于使用整个未来目标期。动机图中的全体熵排序不是在线算法本身。 |
| SoTTA | 缓冲区平衡的是预测类别，不是真值类别。 | 历史到当前的高置信缓冲区；用它更新 BN 统计和仿射参数。 | 不是已经查明的真值平衡泄漏，但均匀伪类别缓冲仍是人为适应分布，不能保证自然不平衡检测上的双侧风险。 |
| DRIFT | 主训练和所述分类头持续更新包含监督学习。 | 按年训练／更新后测试后续年份。 | 有时间前向评估不等于无标签测试时适应，更不等于编码器更新、分类头冻结。 |

定位与来源：[MADCAT §4.1–4.3，PDF pp.3–4](https://arxiv.org/pdf/2505.18734v1)；[MORPH §4–5，PDF pp.7–10](https://arxiv.org/pdf/2401.12790)；[TTT §2–3，PDF pp.2–3](https://arxiv.org/pdf/1909.13231)；[EATA §4，PDF pp.4–5](https://arxiv.org/pdf/2204.02610)；[SoTTA §3.1，PDF pp.4–5、算法1](https://arxiv.org/pdf/2310.10074)；[DRIFT §IV.4](https://arxiv.org/html/2605.10436v2)。

审计口径：标签只用于独立评分，不等于泄漏；标签参与采样、平衡、停止或选模，则改变无标签条件。拿到完整批次后再预测，可以是合法的批式转导，但必须明示等待和信息范围；只有把这种结果宣称为较细时间粒度的到达即决策时，才出现因果口径冲突。本文没有把所有批次统计都判为非因果，也没有把未交代的调参来源当作已经确认的未来标签使用。

## 四、简短反例清单

以下均为 **外部候选，待本地全文和实验复核**。除明确标注的文献前提外，它们是逻辑反例，不是本地实验结果。

1. **留出验证也会被学会。** 多次按同一批家族／环境接受更新，能提高被用作控制反馈的风险，却不必提高另一个未参与选择的源侧环境表现。把反馈集称为“验证集”并不能免除适应性选择过拟合。
2. **梯度不冲突仍可能负迁移。** 训练任务共同强化同一个源侧捷径时，训练梯度可以一致，但跨环境主任务可能更差。ForkMerge §3.1 的讨论已明确区分梯度冲突与验证集迁移收益，不能把 PCGrad 的训练优化结果当作未来风险保证。[原文](https://arxiv.org/pdf/2301.12618)
3. **冻结头不等于冻结决策边界。** 对输入的分类函数是 \(h(f_\theta(x))\)。即使 h 固定，改变编码器也能让样本越过阈值；重构误差下降或参数改变量小，不推出 FPR、FNR 不增加。
4. **无标签边际不能识别任意条件漂移。** 两个世界具有相同的 \(P_t(X)\)，却有相反的 \(P_t(Y\mid X)\)。适应器看到的信息相同，因而实施相同更新；该更新可能在一个世界改善、在另一个世界恶化。没有附加假设时，非平凡无标签更新不能仅凭替代损失获得普遍双侧无伤害保证。
5. **高置信和“恶意预测较可信”都可能反转。** 置信筛样可能保留共同的高置信错误；若良性分布也漂移，MORPH 所依赖的低误报背景就不再稳固。真值平衡结果也不能替代伪标签平衡结果。[MORPH §4.1](https://arxiv.org/pdf/2401.12790) [MADCAT §4.2–4.3](https://arxiv.org/pdf/2505.18734v1)
6. **完美错误键也可能零纠错。** 若 A 与 B 对所有样本给出相同预测，K 即使完美指出 B 在哪里错，任何纯分支选择器的输出都不变。若只存在少量可救回样本，错误换路的损失还可能大于救回收益。允许选择器自行反转标签，则已变成额外分类器，不能再用纯分支选择的结果论证它。

## 五、六篇新增近邻的完整证据卡

### N1 — Feature-Critic｜外部候选，待本地全文和实验复核

**题录：** Yiying Li, Yongxin Yang, Wei Zhou, Timothy M. Hospedales. *Feature-Critic Networks for Heterogeneous Domain Generalization*. Proceedings of the 36th International Conference on Machine Learning, PMLR 97:3915–3924, 2019。作者稿和仓库使用英式拼写 Generalisation，属于同一论文，不应重复计数。

**稳定标识与全文：** arXiv:1901.11448；已读作者稿 v3。全文 URL：https://arxiv.org/pdf/1901.11448 。[PMLR 题录](https://proceedings.mlr.press/v97/li19l.html)。

**读取等级／机制定位：** 全文相关章节已读，§§3.2–3.4、PDF pp.3–5；式(3)–(5)及算法1。尤其是留出源域上有／无辅助更新的主任务收益差。异质设定下最终任务还涉及目标训练数据学习新分类器，因此不能把异质实验直接描述成完全无标签新类别识别。

**公开实现与数据权限：** 作者公开仓库 [liyiying/Feature_Critic](https://github.com/liyiying/Feature_Critic)。已读 [README](https://github.com/liyiying/Feature_Critic/blob/master/README.md)，确认 PACS 与 Visual Decathlon 入口；其中 ImageNet 部分明确要求注册，并因版权单独提供。没有下载数据／模型，未核验所有原始数据许可或仓库独立代码许可证，不能据公开链接推断无限制再分发。

**最近邻覆盖：** 方向一的留出环境主任务反馈与辅助更新反事实比较。**关键反例：** 留出源域不足以代表未来漂移；异质目标标签空间还引入不同评估条件。**尚需实证：** 固定辅助任务候选上的离散选择，是否在同样源划分、反馈目标和计算预算下提供超出已知框架的收益。

### N2 — Auto-Lambda｜外部候选，待本地全文和实验复核

**题录：** Shikun Liu, Stephen James, Andrew J. Davison, Edward Johns. *Auto-Lambda: Disentangling Dynamic Task Relationships*. Transactions on Machine Learning Research, 2022。

**稳定标识与全文：** arXiv:2202.03091v2，2022-06-02。全文 URL：https://arxiv.org/pdf/2202.03091 。[作者 arXiv 题录及 TMLR 状态](https://arxiv.org/abs/2202.03091)。

**读取等级／机制定位：** 全文相关章节已读；§4、PDF pp.5–7，式(3)–(7)。以主任务验证损失优化任务权重；Swapping Training Data 段落说明实际实现可交换同一训练集的不同批次，不是自动具备留出环境泛化资格。

**公开实现与数据权限：** 作者仓库 [lorenmt/auto-lambda](https://github.com/lorenmt/auto-lambda)，[README](https://github.com/lorenmt/auto-lambda/blob/main/README.md)给出 NYUv2、Cityscapes 预处理数据链接及 CIFAR-100 实验说明。公开下载入口已核到；原始数据条款、镜像再分发授权和各数据集完整权限未逐项核验，没有下载镜像。公开代码不转移原始数据权利。

**最近邻覆盖：** 普通验证驱动调权与动态辅助关系。**关键反例：** 对普通同分布批次的短视收益，不必对应跨家族风险。**尚需实证：** 加入源侧留出划分后，观察到的是协议选择收益，还是无法由相同双层优化实例化的机制差量。

### N3 — Test-Time Training｜外部候选，待本地全文和实验复核

**题录：** Yu Sun, Xiaolong Wang, Zhuang Liu, John Miller, Alexei A. Efros, Moritz Hardt. *Test-Time Training with Self-Supervision for Generalization under Distribution Shifts*. Proceedings of the 37th International Conference on Machine Learning, PMLR 119:9229–9248, 2020。

**稳定标识与全文：** arXiv:1909.13231v3，2020-07-01。全文 URL：https://arxiv.org/pdf/1909.13231 。[PMLR 题录](https://proceedings.mlr.press/v119/sun20b.html)。

**读取等级／机制定位：** 全文相关章节已读；§2、PDF p.2 式(2)–(3)，§3 p.3，§4 条件分析。固定主任务参数、更新共享特征参数的结构已经存在。其关于有益更新的分析具有条件，而不是任意漂移保证。

**公开实现与数据权限：** 作者 [ttt_cifar_release](https://github.com/yueatsprograms/ttt_cifar_release) 的 [README](https://github.com/yueatsprograms/ttt_cifar_release/blob/master/README.md)已核；其中指向 ImageNet 实现，以及 CIFAR-10-C、CIFAR-10.1 来源。原论文项目站本次返回 404，但代码入口成功取得。未下载数据，未把这些入口当作全部数据统一授权。

**最近邻覆盖：** 方向二的基本冻结头自监督 TTA。**关键反例：** 视觉旋转任务不能直接保证域名字符重构与检测目标同向；打乱测试顺序也不能提供真实时间流顺序证据。**尚需实证：** 在允许的信息集合内，辅助更新对两类条件错误的关系是否稳定，而非仅辅助目标下降。

### N4 — EATA｜外部候选，待本地全文和实验复核

**题录：** Shuaicheng Niu, Jiaxiang Wu, Yifan Zhang, Yaofo Chen, Shijian Zheng, Peilin Zhao, Mingkui Tan. *Efficient Test-Time Model Adaptation without Forgetting*. Proceedings of the 39th International Conference on Machine Learning, PMLR 162:16888–16905, 2022。

**稳定标识与全文：** arXiv:2204.02610。全文 URL：https://arxiv.org/pdf/2204.02610 。[PMLR 题录](https://proceedings.mlr.press/v162/niu22a.html)。本文定位基于本次读取的 17 页 arXiv PDF，不以 PMLR 页序替代。

**读取等级／机制定位：** 全文相关章节已读；§4、PDF pp.4–5、式(2)–(9)、算法1。低熵与非冗余筛选、BN 仿射参数更新、Fisher 正则。式(9)的重要度估计使用预先收集的无标签 ID 样本及模型伪标签；不存在“完全没有参考集合”的同等信息条件。

**公开实现与数据权限：** 作者 [mr-eggplant/EATA](https://github.com/mr-eggplant/EATA)，[README](https://github.com/mr-eggplant/EATA/blob/main/README.md)明确需要 ImageNet 测试／验证图像及 ImageNet-C；给出公开来源。未下载数据，未逐一复核原始图像许可；不能从代码开放推断 ImageNet 授权。

**最近邻覆盖：** 轻量、筛样、抗遗忘的 TTA 控制。**关键反例：** 高置信错误可能被优先保留；保护原分布表现不等于约束漂移后的误报与漏报。**尚需实证：** 批次依赖、参考集合资格、类别不平衡及受限更新的双侧错误影响。图2的排序动机实验不能被误记为算法需要全未来样本排序。

### N5 — MORPH｜外部候选，待本地全文和实验复核

**题录：** Md Tanvirul Alam, Romy Fieblinger, Ashim Mahara, Nidhi Rastogi. *MORPH: Towards Automated Concept Drift Adaptation for Malware Detection*. arXiv preprint, 2024。本次未另核正式同行评审出版状态。

**稳定标识与全文：** arXiv:2401.12790v1，2024-01-23；DOI:10.48550/arXiv.2401.12790。全文 URL：https://arxiv.org/pdf/2401.12790 。[题录](https://arxiv.org/abs/2401.12790)。

**读取等级／机制定位：** 全文相关章节已读；§4、PDF pp.7–9；算法1 p.8，未编号的半监督损失 p.9；§5.1 p.10。按预测类别做不对称筛样，再用伪标签与原始带标签样本共同训练。

**公开实现与数据权限：** 公开仓库定点查询 `MORPH "concept drift" is:public` 未返回匹配；这只表示本次未核准作者实现，不表示实现不存在。AndroZoo 的[官方访问条件](https://androzoo.uni.lu/access)要求申请、限制商业使用和未经同意的再分发，不能当作任意下载的 APK 集。Windows 部分所用 EMBER 的[官方 README](https://github.com/elastic/ember/blob/master/README.md)给出公开特征下载和校验信息，但不等于可再分发全部原始 PE 文件；论文使用的准确子集和切分未独立取得。

**最近邻覆盖：** 真正恶意软件漂移下的自动伪标签适应。**关键反例：** 低误报前提不稳会破坏其不对称筛选逻辑；另外，EMBER 官方说明跨年样本选择规则不同，跨年退化不能仅据时间索引归因自然演化。**尚需实证：** 正文 §5.1 同时出现 2019–2021 数据和 2018 年验证月，属于需要澄清的协议叙述；不足以据此宣判未来标签泄漏。

### N6 — META-DES｜外部候选，待本地全文和实验复核

**题录：** Rafael M. O. Cruz, Robert Sabourin, George D. C. Cavalcanti, Tsang Ing Ren. *META-DES: A dynamic ensemble selection framework using meta-learning*. Pattern Recognition 48(5):1925–1935, 2015。

**稳定标识与全文：** DOI:10.1016/j.patcog.2014.12.003；公开作者稿 arXiv:1810.01270v1。全文 URL：https://arxiv.org/pdf/1810.01270 。[出版记录](https://doi.org/10.1016/j.patcog.2014.12.003)。2018 年是该作者稿的 arXiv 存档年份，不是方法首次发表年份。

**读取等级／机制定位：** 全文相关章节已读；§3、PDF pp.9–16；算法1 p.12 用专家正确／错误生成元标签，§3.2.3 为推断选择。历史带标签 DSEL 的局部正确性进入推断特征；这不等于使用当前目标样本真值，也不等于无标签记忆。

**公开实现与数据权限：** 已核同一研究团队参与的公开库 [scikit-learn-contrib/DESlib](https://github.com/scikit-learn-contrib/DESlib)，[README](https://github.com/scikit-learn-contrib/DESlib/blob/master/README.rst)列出 META-DES 引用，并标注 BSD-3-Clause。该库不能不经核验就等同 2015 年论文的冻结实验制品；代码许可也不是 UCI／STATLOG／PRTOOLS 各任务的统一数据许可。原论文全部任务的数据权限与切分尚未逐项核验。

**最近邻覆盖：** 局部条件信息估计专家能力，继而进行动态分支／集成选择。**关键反例：** 邻域污染、局部／目标分布不同以及共同错误会破坏选择；预测错误不能创造不存在的正确专家。**尚需实证：** 局部字符／子词键是否预测相对可救回收益，而非类别、家族或单专家难度的代理。

## 六、用户给定八篇锚点的题录与边界登记

以下是既有锚点，**不计入六篇新增候选**。全部仍为 **外部候选，待本地全文和实验复核**。

### B1 DRIFT

Chaeyoung Lee, Chaeri Jung, Seonghoon Jeong. *DRIFT: Drift-Resilient Invariant-Feature Transformer for DGA Detection*. IEEE/IFIP DSN, 2026, pp.786–799；DOI:10.1109/DSN69566.2026.00077；arXiv:2605.10436，已核 v2 为 2026-08-02。全文 URL：https://arxiv.org/pdf/2605.10436 ；[v2 HTML](https://arxiv.org/html/2605.10436v2)；[题录](https://arxiv.org/abs/2605.10436)。

已读相关全文：§III.2 式(1)为三个预训练辅助任务之和；§IV.3／IV.4 涉及家族、跨年与持续学习评估。它提供 DGA、字符／子词双分支和静态自监督任务组合背景，但不是来源一的验证控制器，也不是来源二的冻结头无标签 TTA。

作者公开实现：[snsec-net/2026-DSN-DRIFT](https://github.com/snsec-net/2026-DSN-DRIFT)。数据 DOI:10.21227/za2s-9e09；[官方 HF 数据卡](https://huggingface.co/datasets/snsec-net/dga-detection-drift26dsn)声明 CC BY-NC-SA 3.0、非商业研究／个人使用。重要冲突：[GitHub README](https://github.com/snsec-net/2026-DSN-DRIFT/blob/main/README.md)称公开数据不含家族标签，HF 当前数据卡却声明 `raw_including_TLD` 含 `family` 列。因此，**不能单凭 README 宣告家族标签不可得，也不能仅凭数据卡宣告具体文件、版本与论文家族实验已完整对齐**。本次未下载数据，保留发布文档不一致。

### B2 MADCAT

Eunjin Roh, Yigitcan Kaya, Christopher Kruegel, Giovanni Vigna, Sanghyun Hong. *MADCAT: Combating Malware Detection Under Concept Drift with Test-Time Adaptation*. arXiv preprint, 2025；arXiv:2505.18734v1。全文 URL：https://arxiv.org/pdf/2505.18734v1 ；[题录](https://arxiv.org/abs/2505.18734)。

已读相关全文：§3、PDF pp.2–3 为 MAE 与分类头；§4.1–4.3、pp.3–4 为月度切分、真值平衡与伪标签替代。它是方向二最直接的既有恶意软件锚点，但主结果和无真值替代结果的证据资格必须分开。

公开仓库查询 `MADCAT malware is:public` 只返回未能与作者／论文建立关系的同名结果，未据同名认定官方实现。APIGraph／Drebin 特征实验的准确发布物、数据权限与时间切分未独立核全；不把论文使用某数据等同其 APK 可自由获取。

### B3 ForkMerge

Junguang Jiang, Baixu Chen, Junwei Pan, Ximei Wang, Dapeng Liu, Jie Jiang, Mingsheng Long. *ForkMerge: Mitigating Negative Transfer in Auxiliary-Task Learning*. Advances in Neural Information Processing Systems 36, 2023；DOI:10.52202/075280-1322；arXiv:2301.12618v3。全文 URL：https://arxiv.org/pdf/2301.12618 。[NeurIPS 记录](https://proceedings.neurips.cc/paper_files/paper/2023/hash/60f9118a849e8e9a0c67e2a36ad80ebf-Abstract-Conference.html)。

已读相关全文：§3.1、PDF p.4；§4、pp.5–7，式(6)–(8)与算法1。验证反馈、主任务保护的候选更新／参数合并和动态任务选择均属于明确覆盖范围。反例边界是验证代理失配，并非它已保证任意未来域无负迁移。

[作者公开仓库](https://github.com/thuml/ForkMerge)的主分支 README 仍声明完整代码待整理，指向 `develop` 分支。确认了公开入口，未将其当作已经验证的完整复现包。论文基准的全部数据许可未逐项核验，不能给出统一开放权限结论。

### B4 SoTTA

Taesik Gong, Yewon Kim, Taeckyung Lee, Sorn Chottananurak, Sung-Ju Lee. *SoTTA: Robust Test-Time Adaptation on Noisy Data Streams*. Advances in Neural Information Processing Systems 36, 2023, pp.14070–14093；arXiv:2310.10074。全文 URL：https://arxiv.org/pdf/2310.10074 。[OpenReview](https://openreview.net/forum?id=3bdXag2rUd)。

已读相关全文：§3.1–3.2、PDF pp.4–5，算法1、式(1)及后续熵锐度目标。它使用预测类别均衡的高置信历史缓冲，更新 BN 统计和仿射参数。视觉噪声流中的“攻击”不是恶意软件检测任务；筛样及均衡也不能自动保证部署类别先验下的双侧风险。

已核 [作者公开仓库及 README](https://github.com/taeckyung/SoTTA/blob/main/README.md)，包含 CIFAR-C、ImageNet-C、MNIST-C 数据入口。未访问 README 所链接的权重或日志，没有完整核验各数据集再分发许可。

### B5 PCGrad

Tianhe Yu, Saurabh Kumar, Abhishek Gupta, Sergey Levine, Karol Hausman, Chelsea Finn. *Gradient Surgery for Multi-Task Learning*. NeurIPS 2020；arXiv:2001.06782。全文 URL：https://arxiv.org/pdf/2001.06782 。

已读相关全文：PDF p.4 算法1及理论分析。冲突时进行梯度投影；理论条件与训练目标收敛相关，不是源侧留出环境或未来 FPR／FNR 的无伤害证书。本文没有对其公开代码与全部基准数据许可进行专项核验，权限状态为未核全，而不是不可公开获取。

### B6 GradNorm

Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, Andrew Rabinovich. *GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks*. ICML 2018，PMLR 80；arXiv:1711.02257。全文 URL：https://arxiv.org/pdf/1711.02257 。

已读相关全文：§3、PDF pp.2–3，式(1)–(2)；算法1 p.4。平衡梯度范数及训练速度，不是用留出环境的主任务验证表现来决定辅助任务资格。对未来错误率的影响仍需外部验证。公开代码／全部数据权限未专项核全。

### B7 AIRL

Thai-Hoang Pham, Xueru Zhang, Ping Zhang. *Non-stationary Domain Generalization: Theory and Algorithm*. UAI 2024；arXiv:2405.06816。全文 URL：https://arxiv.org/pdf/2405.06816v1 ；[题录](https://arxiv.org/abs/2405.06816)。AIRL 是文中算法名，不是正式论文题名。

已读相关全文：方法与推断讨论、PDF pp.7–8、算法2，以及实验设置。它利用源域时间序列的变化学习非平稳泛化，推断时不直接调用需要当前目标域信息的全部训练路径。不是无标签 TTA 或字符键错误记忆方法；所列合成／视觉基准不能充当 DGA 实证。作者公开实现与全部数据权限未核全。

### B8 MalMoE

Yunpeng Tan, Qingyang Li, Mingxin Yang, Yannan Hu, Lei Zhang, Xinggong Zhang. *MalMoE: Mixture-of-Experts Enhanced Encrypted Malicious Traffic Detection Under Graph Drift*. arXiv:2602.10157v1，2026；作者题录声明被 IEEE INFOCOM 2026 接收，本次未另外核对最终会议出版版本。全文 URL：https://arxiv.org/pdf/2602.10157v1 ；[题录](https://arxiv.org/abs/2602.10157)。

已读相关全文：§III.C–D、PDF pp.5–6；式(8)–(10)的相对损失门控标签、专家分歧掩码和门控损失。它直接覆盖“学专家相对可靠性→选分支”的一般监督结构，但对象是加密流量图，不是 DGA；局部单样本信息也未必能辨别接近分布内的漂移。官方实现、全部原始流量图数据与许可未核全；不将其安全领域归属扩展成域名检测数据证据。

## 七、引用语境核验：取得了什么，没有取得什么

**Scite 没有完成核验。** 实际仅发出一次 `search_literature`，针对 DRIFT、MADCAT、ForkMerge 的 DOI；响应为月度 MCP 配额耗尽，标示 2026-10-01 UTC 重置。没有得到 supporting／contrasting／mentioning 语境，不能写成“Scite 已证实”或“未发现反驳引用”。未为绕过配额而重复提交同题。

以下是直接读一手全文完成的人工语境对照，不冒充 Scite 输出：

| 引用链 | 在引用论文中的语境 | 回到被引论文后的边界 |
|---|---|---|
| MADCAT §2 → Alam 等 MORPH | 概括为高置信伪标签微调，并讨论其长期漂移不足。 | MORPH §4.1 实际区分预测恶意和预测良性：前者允许更不确定样本，后者更重高置信。不能把它简化成对两类对称的高置信筛选；MADCAT 的比较描述也不构成对所有 MORPH 设定的普遍否定。 |
| ForkMerge §3.1 → 梯度冲突／PCGrad 文献 | 强调梯度冲突与验证迁移收益并非同一件事。 | PCGrad p.4 的算法与定理讨论训练优化条件；ForkMerge 是在泛化／验证意义上补充限制，不能把两者写成同一个命题的直接逻辑矛盾。 |

来源：[MADCAT](https://arxiv.org/pdf/2505.18734v1)、[MORPH](https://arxiv.org/pdf/2401.12790)、[ForkMerge](https://arxiv.org/pdf/2301.12618)、[PCGrad](https://arxiv.org/pdf/2001.06782)。

## 八、检索式、应用使用与停止理由

### 8.1 Sider Scholar：候选发现

以下为实际发出的发现查询。除标注 Google Scholar 的一次外，其余使用 Sider 的 OpenAlex 搜索工具。按正式题名、arXiv／DOI 去重；没有把同一稿件的重复条目算成新增候选。

```text
auxiliary task validation domain generalization
Feature Critic auxiliary loss generalization
"test-time" ("DGA" OR "malware") adaptation self-supervised    [Google Scholar]
Auto Lambda dynamic task weighting
dynamic ensemble selection meta learning competence
MORPH malware concept drift adaptation
Test Time Training Self Supervision Generalization Distribution Shifts
Efficient Test Time Model Adaptation without Forgetting
```

第三条检索返回的结果相关性较差，外围综述与无关任务没有入选。这是召回限制，不能转化成“领域中不存在其他 DGA TTA 工作”的否定性结论。MORPH 是沿 MADCAT 参考文献追踪后由 Sider 核准的候选；没有在应用之间轮流重做其主题发现。

### 8.2 Scite：定点语境请求

```text
tool: search_literature
DOIs:
10.1109/DSN69566.2026.00077
10.48550/arXiv.2505.18734
10.52202/075280-1322
limit: 10
结果: 配额错误；未返回可用题录、全文摘录或引用语境。
```

### 8.3 GitHub：公开作者实现与权限核对

实际公开仓库发现查询：

```text
MADCAT malware is:public
MORPH "concept drift" is:public
```

其余 GitHub 请求均沿已经由论文／作者资料给出的公开仓库读取 README 或元数据，没有进行用户账号、私有仓库或未知仓库内容搜索。已成功读取：

| 仓库 | 读取用途 | README 文件标识说明 |
|---|---|---|
| snsec-net/2026-DSN-DRIFT | 官方实现关系、数据链接及家族标签发布声明 | blob SHA `eed8cd0cc76e5adbccb55b4a0f3a36172f852b10` |
| liyiying/Feature_Critic | 作者实现、PACS／VD／ImageNet 访问说明 | blob SHA `9f7061e183d03a8c87e95e7cd98b22ad9c54ea85` |
| lorenmt/auto-lambda | 作者实现、TMLR 引用、数据入口 | blob SHA `e8ed19bd12e31dfc083676069bdd7cc6ffface05` |
| yueatsprograms/ttt_cifar_release | 作者代码发布、CIFAR 数据及 ImageNet 实现入口 | 工具返回 README 内容；未据此声称冻结代码提交 |
| mr-eggplant/EATA | 作者实现和所需图像数据 | blob SHA `be78fa998574fb9dd1bc3a4a39783df1d64adfbc` |
| scikit-learn-contrib/DESlib | 研究团队关联、META-DES 引用、库许可证声明 | blob SHA `d04043d305f6e6582846a828db995f9649a8c863` |
| thuml/ForkMerge | 作者实现入口及 develop 分支说明 | blob SHA `5a66ea24ca19027386d3d1a2960ba73e5ba7f5ea` |
| taeckyung/SoTTA | 作者关系、OpenReview、视觉数据入口 | blob SHA `b1f9a2aacdde5034611a932ae225ffcf1b3af2dd` |
| elastic/ember | 官方特征数据访问、校验信息及跨年选择差异 | blob SHA `35f9c855bdb930f3dc8e6a871810e71ea5dc2c13` |

上表是 README 文件的 blob 标识，不是冻结了训练代码、数据或实验环境的提交证明。仅阅读 README 内的模型／日志链接文本，不意味着访问或下载其链接目标。

### 8.4 Web：一手全文与题录核准

主要采用对用户给定和 Sider 发现的稳定标识直接访问 arXiv abs／PDF／HTML，辅以 PMLR、NeurIPS 和出版 DOI。题名核验查询包括：

```text
ForkMerge: Mitigating Negative Transfer in Auxiliary-Task Learning NeurIPS 2023
SoTTA: Robust Test-Time Adaptation on Noisy Data Streams NeurIPS 2023
Feature-Critic Networks for Heterogeneous Domain Generalization github
META-DES dynamic ensemble selection 2015 10.1016
"Feature-Critic" "proceedings.mlr.press"
"Test-Time Training with Self-Supervision" "github"
"Efficient Test-Time Model Adaptation without Forgetting" "PMLR"
```

这些用于定位已经入选的具体文献、核题录或追回作者入口，不是另一轮开放式候选扩展。权限核准使用 DRIFT 官方 HF 数据卡和 AndroZoo 官方访问条件。搜索结果中的二手 AI 摘要、课程复现仓库和泛化综述没有被当作论文机制的证据。

停止原因：六篇新增近邻已分别覆盖源侧辅助反馈、冻结头自监督 TTA、轻量抗遗忘、恶意软件伪标签适应与局部专家能力估计；继续增加泛化综述或相同原理的实例，预计不会改变当前排重边界。仍保留 Scite 和发布权限／协议的明确缺口，不宣称穷尽检索。

## 九、不可获取全文与尚未完成的核验

**入选六篇加八篇既有锚点：均取得了公开作者稿全文入口和可读正文。** 没有用“仅摘要”或“仅题录”的论文否决机制创新。并非所有正式出版排版版本都另行读取；META-DES 使用公开作者稿，其正式出版信息另由 DOI 记录核对。

本次真正未取得或未完成的部分如下：

- Scite 引用语境：配额阻断，完全没有取得相关 Smart Citation 证据。
- 部分 PDF 图像渲染：DRIFT、MADCAT、MORPH、MalMoE、META-DES 的部分截图请求遇到缓存错误。相关机制判断使用可读正文／公式；没有使用渲染失败的图表数值宣布效果或统计优势。Feature-Critic、TTT、EATA、SoTTA、PCGrad、GradNorm 的关键页面取得了图像核对。
- TTT 原项目站：本次返回 404；作者公开代码 README 已从 GitHub 成功核准。因此是项目站不可达，不是论文全文缺失。
- 作者实现完整性：MADCAT 与 MORPH 未核准作者公开仓库；ForkMerge README 指向尚待整理的代码分支；DESlib 不等同原论文冻结制品。没有据此断言任何实现绝对不存在。
- 数据与协议：未下载任何数据；没有验证每篇论文的确切子集、文件校验、实验切分和完整数据授权链。DRIFT 两处官方发布说明对家族标签的描述不一致；MORPH 正文年月叙述不一致。上述问题保持为待核项，不以推测补齐。
- 调参与选择因果性：未完成所有作者代码的目标标签流向、预处理拟合范围、模型选择及停止条件审计。已明确写出的真值平衡和目标池排序可以定位；未明确的部分不能武断宣布泄漏或无泄漏。

**最终外部判断：** 当前三类描述都存在足以压缩原理新颖性的直接先例；没有已经建立的不可约差量。与此同时，先例存在不等于这些方法在域名漂移上有效，也不等于任何具体实现必然重复。最关键的未证问题是：源侧选择反馈能否外推、无标签更新能否控制双侧伤害，以及局部键是否识别净可救回收益。以上全部为 **外部候选，待本地全文和实验复核**。
