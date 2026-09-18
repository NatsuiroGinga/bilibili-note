# DRIFT N12 G1 文献与实验方法学审查：PF-FAC 的 G2 最小资格、直接近邻与反例设计

## 审查边界与回收记录

**本次实际模型：GPT-5.5 Thinking；研究/思考强度：高。** 本次仅进行了公开文献与理论方法审查，没有运行代码，没有访问服务器、检查点、日志或任何 T18–T25 数据，也没有对本地实验作结果裁决。Scite 接口在本次会话中可见但调用时已达到账户月度额度；Consensus 仅用于发现/交叉核对，以下实质性方法判断尽量以论文原文、正式 proceedings、arXiv/OpenReview 原文为依据。

对 DRIFT，公开原文确认其三项自监督损失确实以简单和
\(\mathcal L_{\rm MTP}+\mathcal L_{\rm TPP}+\mathcal L_{\rm TOV}\)
联合优化；其公开消融也确认 MTP+TOV 的总体 F1 为 0.9660，高于三任务全开的 0.9646，而全开配置具有更高 Recall、较低 FNR，原作者将其描述为 precision–recall 的运营取舍。这里最多能推出“固定任务组合的效果不相同”，不能推出 TPP 本身造成负迁移，更不能推出动态权重一定优于固定子集。citeturn27view2turn28view5

本报告把用户提供的 G1 数字视为**脱敏、已给定但未由本次外部研究独立复核的诊断汇总**。因此，下面凡涉及“六个单元均过 G1”“53 个 family”“150,000 个成员”“任务范数/监督计数”等，均是在分析交接包，而不是声称从公开论文重新得到了这些读数。

**总判定先行：按交接包内已经冻结的 G1 规则，现有信号足以支持“允许进入 G2 做最小证伪”，但不支持“PF-FAC 有效”，甚至尚不足以证明 G1 捕捉到了 family 特异的可利用信号。** 这一边界与 PCGrad、GCS、ForkMerge 的原始研究尤其一致：梯度冲突或负余弦本身并不是下游负迁移的充分条件；ForkMerge 的核心实验观察甚至明确指出，梯度冲突与负迁移并不存在必要的一一对应关系。citeturn16view0turn22view0turn22view2turn12view0

**结论标签：外部候选，待本地全文和实验复核。**

## G1 信号究竟支持到哪一步

### 它足以支持“做 G2”的理由

G1 的预冻结规则不是在问“哪个任务最好”，而是在问：**在当前共享编码器参数点上，对于同一个下游风险，三项任务是否至少提供了两种相反的一阶方向。** 按包内数据，六个“分支 × 风险”单元全部满足“一项负、一项非负”，所以按事先冻结规则，过筛是自洽的。

这个筛选标准具有一个有限但真实的方法学意义：如果三项任务对某一风险在当前点上的方向完全同号，那么仅靠调整非负任务权重，局部上能产生的风险方向自由度会更小；现在观察到符号异质性，至少说明“权重选择可能有东西可选”，值得用真实有限步更新去证伪。它没有借助任务范数大小决定正负，因此，单纯把某项任务梯度放大，并不能制造 G1 的“混合符号通过”。

但这只是一阶局部陈述。GCS 原论文自己就强调，其 cosine gating 只提供有限的下降/收敛性质，并不保证辅助任务能够加速主任务；论文还专门构造了“余弦方向看似可用但实际收敛变慢”的负例，并指出小批量梯度会使 cosine 估计有噪声。citeturn22view0turn22view1turn22view2 PCGrad 更进一步指出，仅有 conflicting gradients 并不自动产生有害结果，其理论动机还依赖曲率和梯度量级等附加条件。citeturn12view0turn12view1 ForkMerge 的实验分析也直接把“优化冲突”与“验证集上的泛化负迁移”区分开。citeturn16view0turn16view1

因此，G1 更合适的身份是 **mechanism-enabling screen（机制可检验筛）**，而不是 efficacy evidence（有效性证据）。

### 当前最重要的反向观察：family-macro 尚未表现出独立符号信息

把包内 G1 只压缩成符号，可以看到一个比“六单元都混合”更重要的结构：

| 分支 | 良性 BCE | DGA 微平均 BCE | DGA family 宏平均 BCE |
|---|---|---|---|
| 字符 | MTP \(+\)，TPP \(−\)，TOV \(−\) | MTP \(−\)，TPP \(+\)，TOV \(+\) | MTP \(−\)，TPP \(+\)，TOV \(+\) |
| 子词 | MTP \(−\)，TPP \(−\)，TOV \(+\) | MTP \(+\)，TPP \(+\)，TOV \(−\) | MTP \(+\)，TPP \(+\)，TOV \(−\) |

这里有两个很强的 G2 证伪线索。

第一，**同一分支内，DGA 微平均风险与 family 宏平均风险对三项任务的符号完全一致。** 字符分支只是幅度不同，例如 TPP 对 micro 为 \(0.152199\)、对 macro 为 \(0.232954\)；子词分支 MTP 则是 \(0.849191\) 与 \(0.773977\)。因此 G1 尚未隔离出“family-macro 元反馈相对于普通恶意 micro 风险的不可替代信息”。现在完全可能出现一种更简单解释：模型只是在做普通的 benign-versus-DGA 判别方向权衡，而 family 宏平均只改变了强弱，没有改变任务排序的基本方向。

第二，良性风险与恶意风险的符号几乎成镜像。这正是为何 G2 中 **benign guardrail 必须是硬资格条件，而不能只是报告一个次要指标**：一个显著降低 malicious BCE 的任务方向，完全可能同时推高 benign BCE。公开 DRIFT 消融本身也表明 FPR 和 FNR 会随任务组合发生不同方向的运营取舍。citeturn28view5

因此，在进入任何“family-aware curriculum 有效”的叙述之前，一个很便宜但非常关键的 G2 负控是：

> 在完全相同的训练期样本、family 隔离折和更新预算下，只把元反馈从 **family-macro BCE** 换成 **DGA micro BCE**。若二者产生几乎相同的任务排序、权重轨迹和真实短步结果，则 G1 支持的是“一般恶意风险方向选择”，而不是 family-aware 机制。

### 分支差异也不是小效应

包内数字显示 MTP 在字符与子词分支上几乎反向：字符分支对 benign 有利、对 malicious 不利；子词分支反之。TOV 在字符分支有可见方向，但在子词分支三个风险上的余弦都接近零。与此同时，子词 TPP 的梯度范数 \(1.566194\) 远高于同分支 MTP 的 \(0.631611\) 和 TOV 的 \(0.416117\)。

这不否定 G1，因为 G1 是单位方向筛选；但它意味着真实有限步更新中，**分支、范数、优化器状态和任务权重会发生乘法式耦合**。特别是如果 PF-FAC 最终对两个分支使用一个共同的三任务权重向量，那么“字符希望 MTP 减少、子词希望 MTP 增加”之类的冲突可能被融合层抵消；反之，如果允许每分支独立权重，则 PF-FAC 又获得了更多自由度，应有相应的同自由度静态控制。

辅助任务彼此之间的余弦也值得注意：包内字符 MTP–TPP 仅为轻微负值 \(-0.022351\)，而子词三对均非负，甚至 MTP–TPP 达 \(0.388721\)。换言之，**下游风险方向冲突并不等同于辅助任务间梯度冲突**。这反而支持将 GradNorm/PCGrad/GCS 视作“不同机制的解释对照”，而不是把它们当 PF-FAC 的同义方法；但它同样不能证明 PF-FAC 会成功。PCGrad 与 ForkMerge 的原文都警告了这种从梯度冲突直接跳到负迁移结论的问题。citeturn12view0turn16view0

**结论标签：外部候选，待本地全文和实验复核。**

## 直接近邻题录、稳定标识与证据等级

下表把既核近邻和本轮重点补全的候选一起列出。证据等级定义为：**A = 本轮直接读取原始全文/正式 proceedings 的方法段；B = 原始摘要/元数据已核，但某些方法细节需借同作者原始论文交叉确认；C = 仅元数据或摘要，不应用于新颖性定论。**

| 文献 | 稳定标识与原始链接 | 可核位置 | 本轮证据等级与关键事实 |
|---|---|---|---|
| Chaeyoung Lee, Chaeri Jung, Seonghoon Jeong, **DRIFT: Drift-Resilient Invariant-Feature Transformer for DGA Detection**, IEEE/IFIP DSN 2026, pp. 786–799 | DOI `10.1109/DSN69566.2026.00077`；arXiv `2605.10436`；[arXiv 原文](https://arxiv.org/abs/2605.10436)；[DOI](https://doi.org/10.1109/DSN69566.2026.00077) | Sec. III.2；Table III–IV；用户已核正式 p.795 | **A。** 原文明确三 SSL 任务等权求和；Table III–IV 独立确认 MTP+TOV F1 0.9660、三任务 F1 0.9646，以及二者 FPR/FNR 取舍。citeturn27view2turn28view5 |
| Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, Andrew Rabinovich, **GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks**, ICML 2018, PMLR 80:794–803 | arXiv `1711.02257`；[PMLR 原文](https://proceedings.mlr.press/v80/chen18a.html)；[arXiv](https://arxiv.org/abs/1711.02257) | Sec. 3.1–3.2，论文物理 pp.3–4；实验后续页 | **A。** 用共享层梯度范数、任务相对训练速率和超参数 \(\alpha\) 调整 loss weights；不是验证集/family 风险驱动。citeturn27view3turn10view0turn10view2 |
| Tianhe Yu, Saurabh Kumar, Abhishek Gupta, Sergey Levine, Karol Hausman, Chelsea Finn, **Gradient Surgery for Multi-Task Learning**, NeurIPS 2020, 33:5824–5836 | arXiv `2001.06782`；[NeurIPS 原文](https://proceedings.neurips.cc/paper/2020/hash/3fe78a8acf5fda99de95303940a2420c-Abstract.html)；[arXiv](https://arxiv.org/abs/2001.06782) | Sec. 2.2–2.3；物理 pp.3–5，Algorithm 1 | **A。** 当任务梯度内积为负时做投影；论文明确指出冲突本身不必然有害。citeturn12view0turn12view1turn12view2turn26search7 |
| Junguang Jiang, Baixu Chen, Junwei Pan, Ximei Wang, Dapeng Liu, Jie Jiang, Mingsheng Long, **ForkMerge: Mitigating Negative Transfer in Auxiliary-Task Learning**, NeurIPS 2023, 36:30367–30389 | DOI `10.52202/075280-1322`；arXiv `2301.12618`；[arXiv](https://arxiv.org/abs/2301.12618)；[DOI](https://doi.org/10.52202/075280-1322) | Sec. 3–4，尤其 pp.4–6；Sec. 4.1 | **A。** 先证明/展示梯度冲突不等于负迁移，再周期性 fork 多个参数分支，依据 target validation performance 搜索权重，并对参数做凸合并。citeturn16view0turn16view1turn15view0 |
| Shikun Liu, Stephen James, Andrew J. Davison, Edward Johns, **Auto-Lambda: Disentangling Dynamic Task Relationships**, TMLR 2022 | arXiv `2202.03091`；OpenReview `KKeCMim5VN`；[arXiv](https://arxiv.org/abs/2202.03091)；[OpenReview](https://openreview.net/forum?id=KKeCMim5VN) | Sec. 4，约物理 pp.5–7；附录复杂度讨论 | **A。** 直接用 primary-task validation loss 对训练 loss 的 task weights 做双层/元梯度优化；因此“验证驱动动态任务权重”本身已不是 PF-FAC 的可主张新颖点。citeturn8view0turn8view1turn8view2turn28view4 |
| Lucio M. Dery, Paul Michel, Mikhail Khodak, Graham Neubig, Ameet Talwalkar, **AANG: Automating Auxiliary learniNG**, ICLR 2023 | arXiv `2205.14082`；[arXiv](https://arxiv.org/abs/2205.14082) | Sec. 4–5，物理 pp.5–6；Appendix B 约 p.14 | **A。** AANG 不只调权，还构造结构化辅助目标空间；其权重搜索依赖 META-TARTAN，以 end-task validation loss 的元梯度衡量各辅助目标影响，并允许权重随训练变化。citeturn15view1turn16view2turn16view3 |
| Xingyu Lin, Harjatin Singh Baweja, George Kantor, David Held, **Adaptive Auxiliary Task Weighting for Reinforcement Learning**, NeurIPS 2019, Vol. 32 | NeurIPS stable hash `0e900ad84f63618452210ab8baae0218`；[NeurIPS 原文](https://proceedings.neurips.cc/paper/2019/hash/0e900ad84f63618452210ab8baae0218-Abstract.html) | Sec. 4.1–4.2，PDF pp.4–5；Sec. 5.4 p.7 | **A。** 方法名 **OL-AUX**；一阶版用 main/aux 梯度点积更新权重，N-step 版累积多个训练步的点积，以近似辅助任务对较长期 main loss 的作用，不需要 held-out family validation。citeturn20view0turn20view1turn20view2 |
| Yunshu Du, Wojciech M. Czarnecki, Siddhant M. Jayakumar, Mehrdad Farajtabar, Razvan Pascanu, Balaji Lakshminarayanan, **Adapting Auxiliary Losses Using Gradient Similarity** | arXiv `1812.02224`；[arXiv](https://arxiv.org/abs/1812.02224)；[OpenReview](https://openreview.net/forum?id=r1gl7hC5Km) | Sec. 2–4；Algorithm 1；Appendix B–C | **A。** GCS 以 main–aux 梯度 cosine 决定是否加入或按 cosine 缩放辅助梯度；原文自己给出噪声与减速反例，所以它非常适合作 G1 的反事实对照。citeturn22view0turn22view1turn22view2 |
| Shikun Liu, Edward Johns, Andrew J. Davison, **End-to-End Multi-Task Learning with Attention**, CVPR 2019 | arXiv `1803.10704`；[arXiv](https://arxiv.org/abs/1803.10704)；CVPR 正式发表已由原始页确认 | Sec. 4.1.3 “Dynamic Weight Average” | **A。** **DWA** 只使用连续时期 task loss 的下降比率，经温度 softmax 形成动态权重；不使用梯度、不使用验证风险、更不使用 family 隔离。citeturn24view0turn25view0 |
| Lucio M. Dery, Paul Michel, Ameet Talwalkar, Graham Neubig, **Should We Be Pre-training? An Argument for End-task Aware Training as an Alternative** | arXiv `2109.07437`；[arXiv](https://arxiv.org/abs/2109.07437) | 原始摘要；AANG Appendix B 对 META-TARTAN 的公式性回顾 | **B。** 原始摘要确认其提出在线 meta-learning 来学习多辅助任务权重；AANG 同作者体系进一步明确 META-TARTAN 用 end-task validation loss 的元梯度学习辅助权重。由于本轮没有直接完整读取该论文 Sec. 3，页码级细节不应视为完全复核。citeturn26academia25turn15view1 |

关于 OL-AUX，公开二手文献对传统页码有 `4772–4783` 与 `4773–4784` 两种写法；本轮可以稳定核的是 NeurIPS proceedings 页面和 PDF 内部 pp.4–7，因此**不建议在未查正式 BibTeX 前把某一传统页码范围写死**。其方法内容本身则已由正式 NeurIPS PDF 直接核实。citeturn18view0turn19view0

关于 GCS，本轮稳定核到 arXiv 和 OpenReview 全文，但没有把它提升为某个未经核实的正式主会论文；最保守题录应按 arXiv/OpenReview 处理。citeturn21search0turn21search1

这轮检索没有找到一篇可以直接据原文判定为“训练期 family-macro 隔离反馈 + 独立 benign 方向硬护栏 + 同一既有 SSL 任务集合的下一块权重选择 + 单参数轨迹、不 fork + 部署端不输入 family 身份”这一**完整组合**的已发表等价方法。但“没有在本轮检索到”绝不等于“该组合已证明新颖”；尤其 Auto-Lambda、META-TARTAN/AANG 和 ForkMerge 已覆盖了其中很大一部分技术骨架。citeturn8view1turn16view3turn16view1

**结论标签：外部候选，待本地全文和实验复核。**

## 方法与 PF-FAC 的信息、目标、更新和差量矩阵

下表中的“family 隔离”指**论文原始算法是否内生要求** family/group-aware 的隔离反馈，而不是“能否经过改造后喂给它一个 family-macro 验证损失”。后者对 Auto-Lambda、META-TARTAN/AANG、ForkMerge 特别重要：它们原则上可以把不同的验证目标代入，所以不能把“使用 family-macro 作为验证标量”自动当作全新的优化框架。

| 方法 | 原算法可用信息 | 目标/元目标 | 实际更新操作 | 原生 family 隔离反馈 | 原生独立良性风险护栏 | 参数分叉 | 与 PF-FAC 的重合与真正差异 |
|---|---|---|---|---|---|---|---|
| **PF-FAC（拟议）** | 既有 MTP/TPP/TOV；训练期 family 隔离的 malicious macro 风险；良性风险方向信息；不把 family 身份作为部署输入 | 拟降低 malicious family-macro 风险，同时满足 benign/source-frozen FPR 约束 | 为**下一训练块**选择同一三任务集合的权重；单轨迹 | **是，拟议核心** | **是，拟议核心** | **否** | 尚未给出精确数学约束、权重域、分支共享规则与 block update 公式，因此目前只能比较机制轮廓 |
| **GradNorm** | 训练 loss、共享层各任务梯度范数、相对 loss 下降速率 | 平衡任务训练速率/梯度规模 | 梯度下降更新 task weights，并归一化权重和 | 否 | 否 | 否 | “动态权重”重合；反馈变量完全不同。它是训练动力学平衡器，不是 group-validation meta-selector。citeturn27view3turn10view0 |
| **PCGrad** | 同一步骤的任务梯度及两两内积 | 缓解梯度冲突导致的优化困难 | 对负内积任务梯度做投影，再聚合更新 | 否 | 否 | 否 | 与 PF-FAC 都看到梯度方向，但 PCGrad 不学习 task weights，也没有 held-out/family 泛化目标。citeturn12view1turn12view2 |
| **ForkMerge** | target/aux 训练更新 + target validation performance | 动态选择有利于 target 验证泛化的 task weight | 周期性 fork 分支；不同 task weights 训练若干步；在参数空间凸组合后 merge | 原生否；可把 target validation 改造成 group metric | 原生否 | **是** | “验证驱动、随训练变化的辅助任务选择”高度重合；**fork + 参数插值**与 PF 的单轨迹 block weighting 是明确结构差异。citeturn16view1turn15view0 |
| **Auto-Lambda** | task training losses/gradients + primary-task validation loss | 双层优化 primary validation loss | 对 loss weights \(\lambda\) 做 meta-gradient/有限差分近似，同时更新单一模型 | 原生否；**容易通过定义 validation objective 改造** | 原生否 | 否 | **最危险的新颖性近邻之一。** “验证损失驱动动态 task weights、单模型轨迹”已经覆盖；PF 不能把这一层当新意。citeturn8view0turn8view1turn8view2 |
| **AANG / META-TARTAN** | end-task data、end-task validation loss、辅助目标梯度；AANG 另有结构化生成的目标空间 | 最小化 end-task validation loss、让组合辅助目标更接近 end-task | 元梯度在线调各辅助目标权重；AANG 同时搜索/采样结构化辅助目标 | 原生否；可改造 validation objective | 原生否 | 否 | “end-task validation 反馈学习动态辅助权重”高度重合；AANG 的**自动生成目标空间**反而是 PF 不做的部分。citeturn16view2turn16view3 |
| **OL-AUX** | main loss 梯度和各 aux 梯度；N-step 历史 | 让辅助任务在一段更新后降低 main loss | 用累计 main–aux 梯度点积更新 task weights；单轨迹 | 否 | 否 | 否 | 与“跨训练块看任务帮助程度”概念很接近，但它不用 held-out group validation，而是在线训练轨迹内的 main loss。citeturn20view0turn20view1 |
| **GCS** | main/aux 当前梯度 cosine | 仅在辅助方向是 main-loss 局部下降方向时利用它 | cosine 非负则加入；或以 \(\max(0,\cos)\) 缩放 | 否 | 否 | 否 | 与 G1 的“方向信息”最直接，但没有 family 泛化反馈，也不解决有限步泛化可靠性；原文明确有失败模式。citeturn22view0turn22view2 |
| **DWA** | 连续 epoch 的 task loss 数值 | 按相对 loss 下降速率自动平衡任务 | loss ratio 经 softmax 产生动态权重 | 否 | 否 | 否 | 只重合“权重会变”；信息和目标都远离 PF-FAC，是普通课程/动态平衡的廉价负控。citeturn25view0 |

### 哪些差异只是应用场景

**“把验证 loss 换成 DGA family-macro BCE”单独看，更像目标实例化，而不是已经证明不可约的方法创新。** Auto-Lambda 已经建立了“用 primary-task validation loss 元优化训练任务权重”的框架；META-TARTAN/AANG 也直接学习“哪个辅助目标有利于 end-task validation”。citeturn8view1turn16view3 如果 PF-FAC 最后只是

\[
\lambda_{t+1}
  \leftarrow \operatorname{MetaUpdate}
  \big(L_{\text{family-macro,val}}\big)
\]

那么“family”很可能只是把现有 validation objective 换成了一个新的应用指标。

同理，**“部署模型不输入 family 身份”是很重要的数据治理/部署隔离属性，但不是 task-weighting 算法本身的新颖性**。Auto-Lambda 或其他元权重方法同样可以只在训练端使用某个验证分组，而不把分组 ID 放进部署网络。

“每个 block 调一次，而不是每个 step 调一次”也暂时更像更新频率/时间尺度差异。OL-AUX 已经证明了从一步扩展到 N-step 累积反馈是已知思路；没有额外理论或实验前，单纯换成 block 粒度难以构成不可约差量。citeturn20view0turn20view1

### 哪些差异有机会成为不可约方法差量

最有机会保住的方法差量不是“动态权重”，而是下面这个**组合是否被形式化为一个真正受约束的选择问题**：

\[
\text{降低 family-isolated malicious macro risk}
\quad
\text{s.t.}\quad
\Delta R_{\rm benign}\le 0
\]

并且该 benign 条件不是把两者简单揉成

\[
R_{\rm family}+\mu R_{\rm benign}
\]

这样的标量惩罚。

原因是：若只是加权求和，Auto-Lambda 一类双层框架很容易吸收这个 composite validation loss；那就更像应用适配。反过来，若 PF-FAC 明确定义为**lexicographic / constrained admissibility rule**——例如只有满足良性风险非恶化方向的候选权重才进入 family-macro 排序——那么“目标风险和安全风险非对称、不可互相补偿”才可能成为方法结构，而不仅是损失函数换名。

第二个真实结构差异是相对 ForkMerge 的：**PF-FAC 若能在单一参数轨迹上，用训练期隔离验证反馈筛选下一块权重，而不 fork 多个参数分支、不做参数凸组合**，这是算法操作层面的明确差异。ForkMerge 原算法恰恰依赖周期性分叉、验证搜索和参数 merge。citeturn16view1 不过，“少做了 fork”本身仍不是效果新颖性；需要证明单轨迹规则获得的收益不能被相同信息预算下的 ForkMerge 或 Auto-Lambda 解释。

第三个潜在差量是 **family 隔离反馈 + 同规模随机分组负控被内生为元反馈有效性的识别设计**。但这里要非常谨慎：这首先是一项实验识别设计，而不是天然的算法创新。只有当 family-isolation 决定了权重优化问题本身的训练/验证信息边界，并且随机分组负控证明“真实 family 结构”提供了超出一般重采样噪声的信号，它才对 PF-FAC 的机制主张形成支持。

因此，当前最稳妥的新颖性命题不是：

> PF-FAC 首次动态学习辅助任务权重。

这明显会与 Auto-Lambda、AANG/META-TARTAN、OL-AUX 等冲突。citeturn8view1turn16view3turn20view1

更可辩护、但尚未证明的候选命题是：

> **在固定既有自监督任务集合中，用训练期 group/family 隔离的宏风险作为元反馈，并以独立 benign-risk 非恶化作为硬可行性护栏，在不向部署模型提供 group 身份且不进行参数分叉/合并的情况下，跨训练块选择单轨迹任务权重。**

其中“hard guardrail 是否真是 hard”“family 信息如何隔离”“两个分支是否共享权重”必须先数学化，否则这句话仍可能被 Auto-Lambda 的复合 validation objective 吸收。

**结论标签：外部候选，待本地全文和实验复核。**

## G2 反例、最小实验与负控

下面的重点不是“证明 PF-FAC”，而是尽量便宜地让它失败。ForkMerge 和 GCS 的原文都提供了强烈方法学先例：局部梯度信息可以与真正的验证泛化效果分离，因此 G2 首先应该挑战 G1 的因果解释，而不是直接跑一套长课程。citeturn16view0turn22view2

| 反例 | 若观察到什么，G1 的解释会被削弱 | 最小实验/负控 | 应如何降级 |
|---|---|---|---|
| **任务范数伪影** | 原生优化器短步差异主要由 TPP 等大范数任务控制；在等更新位移后任务排序消失 | 从同一冻结起点，对三任务分别做真实短步；同时做一个**共享编码器参数位移范数匹配**的诊断步，与 optimizer-native 步并列 | 若只有 native 大范数产生差异，不能把 cosine 符号解释成任务语义效果 |
| **一阶 Taylor 不成立** | 负 cosine 的任务真实短步并不增加对应风险，或结果随步长轻微变化就翻转 | 对每项任务用同一预定步长以及一个更小步长重复真实更新，直接测三项既有 BCE 风险 | 若有限步方向不复现，G1 只能保留为几何描述，停止课程机制推断 |
| **分支特异而非通用课程** | 字符/子词最优任务方向长期相反；融合后效应抵消 | 三任务真实短步分别在字符、子词分支评估，同时看现有融合输出；不把两分支提前平均 | 若只能靠分支专用权重有效，则不得声称一个共享 PF-FAC 规则已被支持 |
| **额外自由度造成收益** | 分支独立权重比共享权重好，但相同自由度的静态分支权重一样好 | 若 PF 允许 branch-specific weights，增加一个**同参数量/同自由度静态 branch-specific** 控制 | 若静态同自由度解释收益，则不是动态 family feedback |
| **单一高影响 family** | leave-one-family-out 后某一个 family 被移除就使 meta 排序或短步方向翻转 | 不改变 53-family 划分，仅做 leave-one-family-out influence 检查；family 仍只作为既有分组，不解释为生成器 | 若信号被单 family 支配，不进入“family 宏普适”叙述 |
| **family-macro 其实只是 micro** | family-macro 与 DGA micro 产生相同权重选择、相同真实风险变化 | 同一 family-isolated 验证成员上，唯一改变为 meta feedback 使用 micro BCE 或 macro BCE | 若等价，PF 的 family-aware 差量不成立 |
| **随机分组也能得到同样信号** | 相同规模的 shuffled groups 与真实 family groups 给出同等或更稳定收益 | 两个互补 family 隔离折，各自配一个/多个预冻结的**同规模随机分组**；训练预算完全一致 | 若真实 grouping 不胜随机 grouping，停止 family-structure 解释 |
| **监督数量/SNR 伪影** | TPP 的“有利/有害”地位随有效监督数量或梯度估计精度改变 | 在同一 T17 数据边界内做 size-matched diagnostic：每个任务以相同数量的基础样本/监督单元估计短步；同时保留原始规模结果 | 若排序只在不匹配规模下出现，应解释为估计/曝光差异而非 curriculum 信号 |
| **benign–malicious 普通分类权衡** | family macro 降低总与 benign BCE 上升、source-frozen FPR 上升绑定 | 不改阈值，直接按预冻结阈值同时记录 benign BCE 与既有 source-frozen FPR | 任一安全护栏稳定恶化即不满足 PF-FAC 目标，不得用 macro 改善抵消 |
| **固定 MTP+TOV 就够了** | PF 权重长期接近 MTP+TOV，且固定 MTP+TOV 取得相同风险结果 | 必须保留固定 MTP+TOV 臂；DRIFT 公开消融使它成为最强直接固定子集之一。citeturn28view5 | 降级为固定子集选择，不得称动态课程 |
| **静态元权重就够了** | 第一个 family-isolated meta 估计得到的权重固定到底，与动态 PF 无差异 | 从同一起点用同一 meta 折求一次权重后冻结，和动态 PF 并列 | 降级为静态 meta weighting |
| **普通开放环课程就够了** | 不看实时 family feedback 的预定权重轨迹取得同样效果 | 在一个折上得到的权重轨迹冻结后，在互补折上**replay**；与实时 feedback PF 比较 | 若 replay 同样好，动态反馈机制未被支持 |
| **GradNorm 能解释** | 只要平衡训练速率/范数就取得同样风险收益 | 同任务、同训练预算跑 GradNorm | 降级为普通 loss balancing；GradNorm 原目标就是通过梯度范数和相对训练速率调权。citeturn27view3 |
| **PCGrad/GCS 能解释** | 只需消除负内积或只接受正 cosine 即可复现收益 | 分别做 PCGrad 与 GCS-style gating 控制，不给它们 family 信息 | 若匹配 PF，则无需 family meta 反馈解释。citeturn12view1turn22view1 |
| **Auto-Lambda 能解释** | 给 Auto-Lambda 完全相同的 training-only family validation 信息后结果相同 | **最关键同信息预算对照**：Auto-Lambda 的 primary validation objective 直接设为相同 family-macro 风险；另按 PF 规格公平处理 benign 条件 | 若匹配 PF，PF 的“validation-driven dynamic weighting”不可主张为新方法。citeturn8view1 |
| **OL-AUX 能解释** | 不用 family held-out validation，仅用 N-step main/aux 梯度历史就产生相同动态权重与收益 | OL-AUX N-step 臂，保持任务集合和训练预算一致 | 若匹配，所谓“跨块动态反馈”可能只是在线长期梯度相关性。citeturn20view1 |
| **ForkMerge 能解释** | target-validation 驱动的 fork/merge 达到全部收益 | 给 ForkMerge 同样的 training-period target validation 信息和任务集合 | 若匹配，则 PF 可能仍有单轨迹计算优势，但“验证驱动过滤负迁移”的效果不是独有。citeturn16view1 |
| **验证噪声过拟合** | 两个互补 family 折方向不一致；动态权重频繁翻转且与重复噪声同量级 | 两互补折必须独立复现；权重轨迹同时报告重复间波动，不事后选最稳定窗口 | 不满足 G2 资格；不得用单折最好结果继续 |
| **“动态”实际不存在** | 权重从早期到晚期基本不变，或变化不超过重复噪声 | 记录每个训练块三权重，不新增结果指标，只把它当机制诊断 | 降级成静态权重，而不是课程 |

有一个尤其值得强调的最小负控：**family-macro feedback vs DGA-micro feedback**。这是当前 G1 最容易遗漏、但成本很低的反例。因为两者在现有六个任务方向上的**符号模式完全一致**，若不做这个控制，即使 G2 family-macro arm 成功，也很难知道收益来自 family 均衡还是仅来自“恶意类风险反馈”。

另一个关键点是 family 的解释边界。即使 leave-one-family-out 或真分组优于随机分组，也只能说明**现有 operational family partition 含有稳定的分组结构信息**；根据交接包，不能把这反推为真实生成器身份或 generator-level causal mechanism。

**结论标签：外部候选，待本地全文和实验复核。**

## 最小 G2 方案、停止条件与近邻优先级

### 先做资格短步，不先做长课程

最省实验的方式不是一开始铺开十个完整训练臂，而是分两道闸。

**第一道闸只回答“G1 的方向到底有没有真实有限步含义”。** 从现有 T17、现有 I/O block、同一个起始状态出发，对 MTP、TPP、TOV 分别做真实短步更新；字符与子词保持分支可分辨；每次都直接量现有的 benign BCE、DGA micro BCE、DGA family-macro BCE。至少再用一个更小的预定步长检查方向对局部尺度是否稳定。这个阶段不训练 PF 课程，不用 T18–T25，也不需要 family 隔离元学习。

只有当真实短步至少复现了预期的**任务间差异**，才进入第二道闸。这里不要求 cosine 数值精确预测真实 \(\Delta R\)，但如果符号和任务排序在实际 optimizer step 下完全不稳定，继续构建 family-aware curriculum 就没有足够机制基础。GCS 自身的失败分析正说明“小批量 cosine 噪声 + 非线性有限步”不能被忽略。citeturn22view2

### family 隔离的最小识别设计

第二道闸应严格使用交接包已经要求的两个互补 family-isolation folds。每个折至少同时有：

**真实 family grouping、同规模 shuffled grouping、family-macro feedback、DGA-micro feedback。**

这样一个很小的二维负控就能同时问两个问题：

\[
\text{真实 family 是否比随机 grouping 有额外信息？}
\]

以及

\[
\text{family-macro 是否比普通 DGA micro 有额外信息？}
\]

只有两个答案都偏向 family-specific 解释，而且两个互补折同方向，才值得继续花成本在完整动态课程上。

### 到完整 PF-FAC 主张时，最少需要哪些训练臂

为节省计算，可以按“过一道闸才展开下一组”的方式运行；但若最终目标是满足交接包中完整 G2 资格，而不仅是机制探索，则下面这些解释必须被覆盖：

| 层级 | 实验臂 | 它排除什么 |
|---|---|---|
| 核心基线 | DRIFT 三任务固定等权 | 原始 published recipe |
| 固定子集 | 固定 MTP+TOV | DRIFT 公开最强 F1 固定组合之一，直接排除“其实删 TPP 就行”。citeturn28view5 |
| 静态控制 | family-meta 权重只估一次后冻结 | 排除静态元权重 |
| 开放环控制 | 在另一隔离折上 replay 一条冻结课程轨迹 | 排除普通预定 curriculum |
| **最直接方法对照** | Auto-Lambda，给予与 PF **完全相同的训练期 family meta 信息预算** | 排除“只是 validation-driven dynamic loss weighting” citeturn8view1 |
| 候选方法 | PF-FAC dynamic | 待检对象 |
| 机制挑战 | GradNorm | 排除训练速率/范数平衡 citeturn27view3 |
| 机制挑战 | PCGrad | 排除一阶梯度冲突投影 citeturn12view1 |
| 机制挑战 | ForkMerge | 排除一般 target-validation filtering + parameter branching citeturn16view1 |

这已经是**完整资格主张的最低核心集合**。OL-AUX 不一定要在第一轮完整长训练里与九个臂同时展开，但如果 PF-FAC 的论文叙述强调“跨 block 的长期任务帮助度”，它应被提升为直接近邻，因为 OL-AUX 的 N-step 更新已经明确针对“单步 main-loss 改善不能代表长期作用”而设计。citeturn20view0turn20view1

AANG 则不必把其“自动生成目标空间”整套重现为主实验臂，因为 PF-FAC 明确保持 MTP/TPP/TOV 固定；但 **AANG/META-TARTAN 的 validation-gradient weighting 部分必须在相关工作与新颖性讨论中正面对照**，否则会高估 PF-FAC 的方法差量。citeturn16view3

### 直接近邻的实验优先顺序

就 PF-FAC 当前声称的机制而言，优先级应当是：

**Auto-Lambda/META-TARTAN 类同信息元权重 > OL-AUX > ForkMerge > GCS > GradNorm/PCGrad > DWA。**

这不是按论文强弱排序，而是按“最可能把 PF-FAC 的拟议贡献解释掉”的程度排序。Auto-Lambda 最危险，因为它已经是**单模型、validation-driven、动态 task weighting**；AANG/META-TARTAN 又明确把 auxiliary weights 与 end-task validation gradient 对齐。citeturn8view1turn16view3 OL-AUX 则最接近“跨若干训练步骤评价辅助任务长期作用”。citeturn20view1 ForkMerge 与 PF 的信息反馈类似，但参数更新操作差异更大。citeturn16view1

GradNorm 和 PCGrad 仍然必须保留，因为交接包明确要求排除它们，但就**方法新颖性**而言，它们比 Auto-Lambda 更远：一个以梯度范数/训练速率为信号，一个以任务间负内积投影为操作，都不使用 held-out target validation。citeturn27view3turn12view1

### 最关键的测量

不需要改变现有论文指标。最关键的是把已有指标按机制阶段同步记录：

真实短步后的三个 BCE 风险变化；每个训练 block 后的 benign BCE、DGA micro BCE、DGA family-macro BCE；既定阈值上的 source-frozen FPR；两个 family-isolation folds 的方向一致性；真实 grouping 与 shuffled grouping 的差异；以及三项任务权重随 block 的轨迹。

权重轨迹是**算法诊断量**，不是替换评价指标。它只回答“PF 是否真的动态”。不能在看到未来表现后再挑“看起来最合理”的时间段或阈值。

此外，benign/source-frozen FPR 的“不恶化”需要在真正运行前就给出预冻结的判定容差或非劣界。若“完全不得变差”是字面规则，就按字面执行；若允许统计误差，则误差界必须预先规定，不能在结果出来后调整。

### 最容易证伪的停止条件

一旦出现下面任一类结果，就没有必要先跑更大的课程搜索：

1. **真实短步不复现任务差异。** 尤其是 G1 预测“有害”的方向在实际 optimizer step 下并不稳定，且缩小步长也无法恢复一致性。此时 G1 只剩几何描述价值。GCS 与 ForkMerge 的原文都说明从梯度方向直接推下游负迁移并不可靠。citeturn22view2turn16view0
2. **真实 family grouping 不优于同规模 shuffled grouping，或两个互补 family 折方向不一致。** 这直接击穿 family-aware 解释。
3. **family-macro feedback 与 DGA-micro feedback 没有可分辨差异。** 此时应把候选贡献降级为 generic malicious-risk-aware weighting。
4. **固定 MTP+TOV 或一次性静态元权重解释全部收益。** 前者尤其必须严肃对待，因为公开 DRIFT 已显示它在 F1/FPR 方向具有强竞争力。citeturn28view5
5. **开放环 replay curriculum 与实时 PF-FAC 等效。** 这说明动态 family feedback 不是必要机制。
6. **给予完全相同 family-meta 信息的 Auto-Lambda 达到相同结果。** 这不会证明 PF 无工程价值，但会显著削弱“不可约新 task-weighting 方法”的主张。Auto-Lambda 的原方法已经以 validation loss 直接元优化动态任务关系。citeturn8view1
7. **family-macro 改善伴随 benign risk 或既有 source-frozen FPR 恶化。** 根据 PF-FAC 自己的目标定义，这不是可用的成功。
8. **动态权重没有跨 block 的实质变化。** 应明确降级为 static weighting，不得继续叫 curriculum。
9. **leave-one-family-out 显示一个 operational family 就能决定结论。** 应先解释高影响 family，而不是宣称宏风险普适改善。

这里最关键的研究纪律是：**停止条件要比“显著性成功条件”更早冻结。** 否则一个高度灵活的动态权重方法很容易通过多折、多 block、多权重轨迹制造事后选择空间。

**结论标签：外部候选，待本地全文和实验复核。**

## 不确定项与最终判断

### 尚未解决的 PF-FAC 定义缺口

在可以对“不可约方法差量”作更强判断前，PF-FAC 本身还有几处数学定义必须固定；这些不是要求新数据，而是要求把拟议算法说清楚：

**权重域尚未给出。** 目前不知道权重是否要求非负、是否和为常数、是否允许任务权重为零、是否对两个表示分支共用一组权重。不同选择会显著改变它与 GradNorm、Auto-Lambda 和 GCS 的等价性。

**benign guardrail 的形式尚未给出。** 这是最重要的不确定点。若它只是
\(L_{\rm family}+\mu L_{\rm benign}\)
式软惩罚，PF-FAC 很可能只是 Auto-Lambda 类方法的复合 validation objective 应用；若它是独立的 hard feasibility/lexicographic constraint，则才更有机会形成不可约结构。Auto-Lambda 本身对 validation objective 的元优化已经非常一般。citeturn8view1

**block selection 规则尚未给出。** 不清楚它使用一阶方向、真实 look-ahead short step、有限候选权重网格，还是连续 meta-gradient。这决定它究竟更接近 GCS/OL-AUX、Auto-Lambda，还是 ForkMerge。citeturn22view1turn20view1turn16view1

**source-frozen FPR 是训练时约束还是最终资格门槛尚未完全区分。** 不应在没有公式的情况下假设 PF-FAC 会用不可微 FPR 直接做 meta update；最保守的做法是把 benign BCE 方向护栏与 source-frozen FPR 的最终资格检查分开描述。

**两个表示分支的权重共享方式未定。** 由于 G1 中 MTP/TOV 的方向跨分支差异很大，这不是实现细节。如果 PF 有两套三任务权重，就需要同自由度静态控制；如果只有一套，则必须证明融合后没有把分支相反信号互相抵消。

### 文献获取上的明确不确定

Auto-Lambda 的 OpenReview 页面本轮受到浏览器验证页阻挡，但其完整 arXiv PDF 已直接获取并检查，因此方法判断为高证据，OpenReview 页面访问障碍不影响核心结论。citeturn28view0turn26search0

META-TARTAN 的源论文在本轮只直接核到 arXiv 原始元数据/摘要；其 validation-gradient 公式是通过同研究线的 AANG 原文 Appendix B 直接核到的。因而 META-TARTAN 的精确算法页码应在本地全文复核后再写入最终论文，不宜仅凭本报告定稿。citeturn26academia25turn15view1

OL-AUX 的方法全文已直接核实，但传统 bibliography 页码范围在公开引用中存在一页偏移的写法；应以正式 NeurIPS BibTeX/本地全文为最终准绳。citeturn18view0turn19view0

GCS 的完整 arXiv/OpenReview 方法文本已核，但本轮不把它强行归入一个未独立核实的正式主会 venue。citeturn21search0turn21search1

本轮没有发现与 PF-FAC 完整约束组合完全同构的公开方法，但检索的“不命中”不能证明不存在近邻。尤其 Auto-Lambda、META-TARTAN/AANG、OL-AUX 和 ForkMerge 已分别覆盖 validation-driven weighting、end-task-aware meta weighting、N-step auxiliary weighting 与 validation-driven branch filtering，因此 PF-FAC 的新颖性空间比“动态任务权重”这一表述窄得多。citeturn8view1turn16view3turn20view1turn16view1

### 最终判断

**关于 G1 → G2：** 按交接包已经冻结的规则，六个分支×风险单元均具有混合符号，足以作为“存在可检验任务方向差异”的最低进入条件；文献并不反对把这种信号作为后续有限步实验的筛选依据。但 PCGrad、GCS 和 ForkMerge 都提供了直接理由，禁止把负 cosine/梯度冲突直接升格为负迁移或泛化收益证据。citeturn12view0turn22view2turn16view0  
**结论标签：外部候选，待本地全文和实验复核。**

**关于 PF-FAC 有效性：** G1 对此没有正面证据。尤其 family macro 与 DGA micro 在六组三任务上的符号模式完全一致，当前最简单替代解释仍是普通 benign–malicious 风险权衡，而不是 family-specific curriculum signal。真实短步、两折 family 隔离、随机 grouping、micro-vs-macro 元反馈四项反例必须先过。  
**结论标签：外部候选，待本地全文和实验复核。**

**关于新颖性：** “动态多任务权重”“用验证 loss 调任务权重”“权重随训练变化”“依据主任务梯度判断辅助任务帮助度”都已经分别被 Auto-Lambda、META-TARTAN/AANG、OL-AUX、GCS 等覆盖。citeturn8view1turn16view3turn20view1turn22view1 因此 PF-FAC 的潜在不可约部分只能更窄地落在 **family-isolated group-macro meta feedback + 独立 benign hard guardrail + 单轨迹 blockwise selection + deployment-group-identity isolation** 的组合上，而且其中只有前两项若被数学化为真正不可由普通 scalar validation objective 吸收的约束结构，才有较强的方法创新潜力。  
**结论标签：外部候选，待本地全文和实验复核。**

**关于最优先的 G2 对照：** 在满足交接包明确要求的 fixed subset、static weighting、plain curriculum、GradNorm、PCGrad、ForkMerge 之外，最不能省的是**同信息预算 Auto-Lambda/META-TARTAN-style baseline**；若 PF-FAC 强调跨 block 的长期辅助作用，还应尽早加入 OL-AUX。不给 Auto-Lambda 相同的训练期 family-meta 信息，却声称 PF 优于既有动态权重方法，会把“信息优势”误写成“算法优势”。Auto-Lambda 和 AANG 原文已经证明 validation-driven task relationship learning 是直接近邻。citeturn8view1turn16view3  
**结论标签：外部候选，待本地全文和实验复核。**

**当前最严格、也最可证伪的状态因此仍应保持为：N12/PF-FAC“设计可行，实验待证”；G1“仅有资格进入 G2”。任何 family-aware 效果、真实短步伤害、动态课程有效性、跨年收益或低误报收益，都不应由本轮外部文献审查提前裁决。**

**结论标签：外部候选，待本地全文和实验复核。**