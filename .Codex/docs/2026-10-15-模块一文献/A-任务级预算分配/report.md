# 检索报告：固定存储预算的任务级/经验级分配

- 日期：2026-10-15；代理：文献检索代理（Claude Opus）
- 任务目录：`.Codex/docs/2026-10-15-模块一文献/A-任务级预算分配/`（含 `task_plan.md`、`notes.md`）
- 研究问题：文献如何把固定容量 $N$ 的回放缓冲在**任务/时间片段**之间切分？我们的规则（按已到达年度等额 $\lfloor N/k \rfloor$、年度内正负各半）在文献中处于什么地位？
- 边界：只做检索与判读，未跑任何实验；**类级平衡（class-balanced）不属本报告**（另代理任务），仅在与任务级纠缠处标注。
- 检索通道：Scholar CLI 8 轮（挂代理 `HTTPS_PROXY=http://127.0.0.1:7890`，检索式与返回存 `/tmp/scholar-task-budget/q*.json`）+ arXiv API 核验 ID + Zotero 语义检索（本地库无相关条目）。本地混合索引构建报错（`EmbeddingBackend.__init__() got an unexpected keyword argument 'device'`）且本机 CPU 正在训练，该通道标阻塞，不影响主线。
- 证据等级标注约定：`本地全文` = PDF 已入 `raw/papers/attack-detection/lamda-related/` 并经 MinerU `extract` 转全文精读；`仅摘要级` = Scholar 返回片段 + arXiv 题录核实，未取得全文。

---

## 一、文献里任务级预算分配的做法清单（问题 1）

按「分配规则」分五族。**分配单元一列严格区分**：任务/时间段 = 本报告对象；类 = 另代理对象；样本级策略一律不列。

| 族 | 代表方法（作者/年份/会议） | 分配单元 | 规则与公式 | 证据等级 |
|---|---|---|---|---|
| 等额 | **GEM**（Lopez-Paz & Ranzato, NeurIPS 2017） | 任务 | 任务数 $T$ 已知：$m = M/T$（§2, arXiv p.3 原文 "we can allocate m = M / T memories for each task"）；未知：随新任务**逐步缩减** m（引 iCaRL） | 本地全文 |
| 等额 | iCaRL 式缩减（Rebuffi et al., CVPR 2017，经 GEM §2 转述） | 类 | 每类固定 m，类数增长时缩减 | 本地全文（转述） |
| 隐式比例 | **蓄水池采样**（Rolnick et al. NeurIPS 2019 ER；Chaudhry et al. 2019） | 流样本 | 每条样本等概率入缓冲 ⇒ 各任务份额 ∝ 其流内样本量；**无显式配额公式** | 本地全文（Brignac/Chaudhry 侧证） |
| 隐式比例 | **FIFO/ring buffer**（ER 变体、GEM 的 ring 基线） | 流样本 | 固定窗 ⇒ 份额随时间几何衰减，新任务挤占旧任务 | 本地全文（PDCL 基线 ER Ring） |
| 显式自适应 | **CORE-AQA**（Zhang et al., arXiv:2402.01348） | 任务 | $att_p = -\log(1-f_p)$（Eq.3）；$att_\tau = -\log(1-\sum_p f_p i_p)$（Eq.4）；softmax（Eq.5）；阈值 $1/(\lambda\lvert P\rvert)$ 分 SR/TR（Eq.6，λ=2）；SR 保底（Eq.7）、TR 按比例（Eq.8） | 本地全文 |
| 显式自适应 | **PDCL**（Elenter et al., arXiv:2310.00154） | 任务 | $\mathbf{n}(t) = \lvert\mathcal{B}\rvert \cdot \boldsymbol{\lambda}(t)/\lVert\boldsymbol{\lambda}(t)\rVert_1$（对偶变量线性比例）+ 仿射保底（α=1/2 ⇒ 每任务 ≥ $\lvert\mathcal{B}\rvert/2t$，恰为均分一半） | 本地全文 |
| 显式自适应 | **RMM**（Liu, Schiele & Sun, NeurIPS 2021） | 阶段+类 | Level-1 RL 动作定旧样本/新数据内存比（相对增减），Level-2 按训练熵二分组、组内均分 | 本地全文 |
| 显式自适应 | DM-DAR（Lu & Rossi, IJCBS 2025） | 类（时间配额） | 按实时遗忘估计与特征漂移调每类配额 | 仅摘要级 |
| 显式自适应 | 复杂度驱动动态缓冲（**IES**，Brignac et al., WACV 2023 §3.5） | 类 | intracluster variance / Kaiser criterion 定每类样本数 | 本地全文 |
| 学习式调度 | **Replay Scheduling**（Klasson et al., arXiv:2209.08660, TMLR 2023） | 任务（采样比例） | 动作 = 任务比例向量 $(p_1,\dots,p_{t-1})$，$\sum p_i=1$；MCTS 搜索 + RL 学习；基线 ETS=等额 | 本地全文 |
| 学习式调度 | **Adaptive Memory Replay**（Smith et al., WACV 2024, arXiv:2404.12526） | 任务（回放占比） | 非平稳 K 臂老虎机 + Boltzmann 采样（t=0.1, β=0.01），按遗忘倾向调各旧任务回放占比 | 本地全文 |
| 学习式调度 | L2R（Yu et al., Pattern Recognition 2026） | 内容+时机 | 元 RL 联合学回放内容与时机 | 仅摘要级 |
| 分布目标 | **SER**（Isele & Cosgun, AAAI 2018） | 跨任务经验 | 四种选择策略：惊喜/奖赏/**分布匹配**/**覆盖最大化**；分布匹配全程最优 | 本地全文 |
| 分布目标 | KL-reservoir（Nikoloutsopoulos & Koutsopoulos, ICML 2024） | 流样本 | 缓冲分布对目标分布的 KL 最小化（目标可选 ⇒ 隐式等额或比例） | 仅摘要级 |
| 构成比例 | **Krawczyk & Gepperth**（IEEE 2024） | 任务/类（批内） | $\chi_\mathcal{M} = \lvert\mathcal{M}_i\rvert/(\lvert\mathcal{R}_i\rvert+\lvert\mathcal{M}_i\rvert)$（Eq.1）；balanced（Eq.2 按 $\sum_{j<i}N_j/\sum_{j\le i}N_j$）/constant（0.5）/weighted（Eq.3 按任务数、Eq.4 按类数） | 本地全文（已入库原件+补注） |
| 理论下界 | **Memory Bounds**（Chen, Papadimitriou & Peng, FOCS 2022） | 总内存 | Theorem 1.1：$k+1$ 任务 (ε,0.01)-continual learner 需 $\Omega(kdb/\epsilon)$ 比特，**线性于任务数、无数量折扣**；不涉切分方式 | 本地全文 |
| 理论下界 | Knoblauch & Husain（ICML 2020）；Wen et al.（arXiv:2507.12043）；Li, Wu & Braverman（ICLR 2026）；Yoon（arXiv:2606.30067） | 总内存/两任务 | NP-hardness 与完美记忆必要；回放 CL 信息论泛化界（含缓冲规模）；两任务内存-统计权衡上下界；无记忆策略 regret 界（ID 已核真） | 仅摘要级 |

**关键观察**：文献把「任务级分配」拆成三个不同问题，容易混读：
1. **存量配额**（缓冲里给每个任务留几个位置）——GEM 等额、CORE/PDCL/RMM 自适应。我们的规则属这一层。
2. **回放采样比例**（每个训练步从各旧任务抽多少）——Klasson、Smith、Krawczyk 的构成比例。它们假设历史数据可访问或生成器可重放，**不等于存量配额**。
3. **样本选择策略**（留哪些个体）——Isele、GSS、InfoRS。与本问题正交。

## 二、有没有人把分配规则本身当研究对象？有没有最优性结论？（问题 2）

**当过研究对象的**：
- **CORE** 明文以「任务间怎么分」为核心贡献（"They allocate the replay buffer space indiscriminately across all tasks" 是其立项批评），并用消融证明分配规则贡献 +5.17% 平均精度（Table 4：37.95→32.78）。**但无任何理论**，λ、阈值均为启发式。
- **RMM** 以「分配方案 arbitrary and static」立项（ImageNet-Full 旧类 20 vs 新类 1300 的实例），用 RL 学分配。**无理论**，且策略需在伪任务上预训练。
- **Klasson** 把「回放比例日程」当研究对象（MCTS 搜索证明存在显著优于均匀的日程，Fig.4 可视化）。**无理论**；对象是采样比例。
- **PDCL** 是唯一带定理的：Theorem 1 证明对偶变量是约束扰动的敏感度指标（含偏差界，附录 A.2/A.4），据此论证「按 λ 比例划分缓冲合理」。**但敏感度界 ≠ 分配最优性**；其凸性假设（Assumption 3）在深度网络下不成立。

**最优性/次优性结论（minimax、覆盖、遗憾界）**：
- 检索所及，**没有任何文献对「固定缓冲在任务间的切分规则」给出最优性定理、遗憾界或覆盖保证**。
- 最接近的是三块间接理论：Chen et al. FOCS 2022 的**总内存**线性下界 $\Omega(kdb/\epsilon)$（不涉切分）；Knoblauch & Husain 的 NP-hardness（针对整个 CL 问题）；Yoon arXiv:2606.30067 的「无记忆策略 vs 历史感知策略」regret 界（ID 经 arXiv API 核实真实，但未取得全文，其设定是参数子空间管理而非缓冲样本配额，**能否迁移未核**）。
- CORE/PDCL/RMM/Klasson/Smith 五篇的「非均匀更好」主张全部是**实验支持**级别，无一篇是理论支持。

## 三、任务级等额 vs 比例的直接实验对照（问题 3）

**直接存量对照：不存在。** 检索所及没有一篇在同一固定缓冲上对照「等额配额 vs 按任务规模比例配额」。原因：标准基准（split-CIFAR100 等）各任务样本量相同，等额与比例**在数学上重合**，做不出对照；Krawczyk（§3.1）明文指出均衡切分是人为假设并构造了不均衡切分（D-CP/A-CP），但他对照的是批内构成而非存量配额。

**四个最接近的间接对照**：

| 对照 | 出处 | 对比内容 | 结果 | 层次 |
|---|---|---|---|---|
| PDCL vs 均匀划分 | Elenter et al. Fig.3 | 按对偶变量非均匀划分 vs 均匀划分（PDCL₀/ER Ring/AGEM），图像+音频基准 | 非均匀（按难度）优于均匀 | 存量配额，按**难度**非按规模 |
| herding/IPM vs 蓄水池 | Brignac et al. Table 2/3（N=200/500/5120） | 每类 $\lvert\mathcal{M}\rvert/s$ 均分 vs 蓄水池（隐式流内比例） | 小缓冲下均分普遍更好（如 Split-CIFAR100 ER-ACE：herding 29.64/62.08 vs reservoir 28.78/44.40 FAA/FF）；N=5120 时差距收窄 | 存量，类维；**与 N=200 同容量，参考价值最高** |
| CORE vs 均分基线 | CORE Table 3/4 | AQA 自适应 vs iCaRL/ER（等额或近似等额） | AQA +5.17 平均 / +5.30 最差任务精度（split-CIFAR10 缓冲 500） | 存量配额，按遗忘率 |
| balanced vs constant/weighted | Krawczyk & Gepperth Fig.3 + take-home | 批内回放构成：balanced（Eq.2）/constant（0.5）/加权（Eq.3-4） | balanced 最稳，不均衡切分上优势最明显；任务加权 vs 类加权仅 1/7 切分可分 | **批内构成**，非存量 |

**诚实限定**：Brignac Table 3 的蓄水池任务份额实测（N=200：23.5/19.0/16.0/22.0/19.5%）偏差 ≤3.5 个百分点，与 $N=200$ 二项波动 $\sigma\approx2.8\%$ 同量级——其「蓄水池偏向早期任务」的表述证据强度有限，引用时应保留这一保留意见；但「小缓冲下均分式群体策略优于蓄水池」的主结论由 Table 2 多组数字支撑，不依赖该表述。

## 四、逐候选：移植形式与最小证伪实验（问题 4）

我们的设置：LAMDA 年度流，固定 $N=200$，按已到达年度等额 $\lfloor N/k \rfloor$，年度内正负各半。以下均为**设计提案**，本轮未运行。

**E1 等额 vs 按年度规模比例（直补文献缺口，最高优先）**
- 移植：臂 A = 现行 $\lfloor N/k\rfloor$ 等额；臂 B = 按年度样本量比例 $\lfloor N \cdot n_y / \sum_y n_y \rfloor$（蓄水池/流内比例的显式化）；臂 C = FIFO/蓄水池基线（隐式比例）。
- 数据与指标：同一 LAMDA 年度流、同一骨干、同一预算 $N=200$、共同预算基线；主指标为**最旧年度**的分面 FPR@固定 TPR 或 AUROC 轨迹 + 全期平均与最差年度（对标 CORE 的 Acc_min 视角）。
- 门槛（看数据前冻结）：若比例臂在最旧年度上优于等额臂 ≥1 个标准误且全期平均不降，则等额被证伪为「规模不敏感」选择；若两臂差异 <0.5 个标准误，说明年度流样本量波动不足以让两规则分歧——这也是有效结论（等额与比例在本数据上等价）。
- 成本：三次同预算训练，与现行单种子先导同量级。

**E2 遗忘率驱动自适应配额（CORE-AQA 移植）**
- 移植：$att_y = -\log(1-f_y)$，$f_y$ 用「学完年度 $y{+}1$ 后对年度 $y$ 的评测精度下降」估计；softmax 后按式(6)-(8) 分配 $N$。λ=2 起步并做 {1.5,2,3} 敏感性。
- 证伪门槛：若自适应配额相对等额在最差年度上增益 <0.5 个标准误，或 $f_y$ 估计的跨种子方差超过其均值一半（信号噪声不足，与缺陷 2 的低信噪比问题同构），则否决该机制在本数据上的适用性。
- 成本：每年度边界加一次历史年度评测（推理开销小）；单种子先导即可。

**E3 对偶变量划分（PDCL 移植）**
- 移植：任务级不遗忘约束 $\mathbb{E}_{\mathcal{D}_y}[\ell] \le \epsilon_y$，训练中收集对偶变量 $\lambda_y(t)$，缓冲按 $\lvert\mathcal{B}\rvert\lambda_y/\lVert\lambda\rVert_1$ 加保底 $\lvert\mathcal{B}\rvert/2y$ 划分。
- 证伪门槛：PDCL 自己证明小缓冲退化对偶质量（其语音小缓冲无增益）；若 $N=200$ 下 $\lambda$ 轨迹跨批方差大即预期失败，可先做零训练诊断（观察 λ 波动）再决定是否开训。
- 成本：需改训练循环（对偶变量更新），实现代价高于 E1/E2，先做零训练诊断。

**E4 保底比例作用（PDCL 的 α 消融思想的廉价版）**
- 移植：等额规则加「每年度保底 $\lceil N/2k\rceil$」不影响现行规则（本来就是 $\lfloor N/k\rfloor$）；有意义的是把保底从 $N/2k$ 到 $N/k$（纯等额）与自适应之间扫描。
- 意义：并入 E1/E2 做二级消融，不单独立项。

**E5 动态复杂度配额（IES Kaiser criterion）**
- 移植：按每年度特征簇的簇内方差/Kaiser 准则定该年度配额。属「按难度/复杂度」族，与 E2 同为自适应，信号换成无标签几何量（避免 E2 的评测泄漏面）。
- 证伪门槛：先做零训练诊断「配额与真实困难度（最差年度表现）的相关性」；无正相关即否决，不进入训练。

**E6 RL/学习式调度（Klasson/Smith 族）**
- 判定：**不建议移植**。Klasson 需全历史可访问（我们离手即弃）、Smith 需全数据保留只省算力——设定与固定存量缓冲根本不同；RL 调度的训练成本与可复现性在论文体量下不成比例。仅作「该层次存在学习式方法」的引文。

## 五、未取得原文的条目清单（阻塞与残余风险）

| 条目 | 已知信息 | 阻塞原因 |
|---|---|---|
| Ma et al., Joint memory optimization for continual learning, IEEE 2025（doc 10877933） | bi-level 同时优化参数与缓冲、跨任务内存平衡（Scholar 摘要） | IEEE 付费墙，未找到公开版 |
| Yoon, Neural Subspace Reallocation, arXiv:2606.30067 | 无记忆策略 regret 界（ID 经 arXiv API 核实） | 未下载全文；设定可迁移性未核 |
| Wen et al., arXiv:2507.12043（回放 CL 信息论泛化界） | 界显式含缓冲规模 | 仅摘要级 |
| Li, Wu & Braverman, Memory-statistics tradeoff, ICLR 2026 | 两任务联合超额风险上/下界 | 会议页未取到 PDF |
| Knoblauch & Husain, ICML 2020（最优 CL NP-hard） | 定理大意已知 | 仅摘要级（引文充分，可按需补全文） |
| DM-DAR（IJCBS 2025）、CASP（arXiv:2311.16485）、PRS（ECCV 2020）、CBRS（ICML 2020）、BRS/LARS（ICPR 2021）、GSS（NeurIPS 2019）、InfoRS（arXiv:2204.04763）、KL-reservoir（ICML 2024）、MEMO（arXiv:2205.13218）、FeDMRA（arXiv:2603.28455）、PROXYMIX（arXiv:2606.00400）、CL-KR-TD（IEEE 2026）、L2R（PR 2026） | 各为类维/采样维/联邦维代表 | 均仅摘要级；**不得**引用其数字作正文论断，只作「该方向存在」的线索 |

Tier B 中与本问题最近但未取全文的是 Yoon 2606.30067（唯一声称 regret 界者）与 Wen 2507.12043（界含缓冲规模）——若第三章需要「理论空位」的更强表述，应补这两篇全文；scholar 已限流，本轮未再取。

## 六、与既有库内文献的交叉核对（避免自相矛盾）

- `2025-Seo-预算化在线持续学习-层冻结与频率采样-全文.md`（并行代理已入库）：处理**算力预算**下的频率采样，与存量配额不同层，本报告不重复引用其数字。
- `2026-Feng-FOREVER-遗忘曲线启发的记忆回放-全文.md`：遗忘曲线驱动的回放，属采样时机/内容维；与 CORE 的遗忘率配额可互证「遗忘信号是主流自适应信号」，其存量配额结论仍需按本报告证据等级核对后才能引用。
- `2019-Chaudhry-微型情景记忆的持续学习-全文.md`（已入库）：小缓冲下 reservoir 相对 herding 的比较与本报告 Brignac 结论互补（该文发现小缓冲时 reservoir 反而占优的情形，Brignac 归因于方法耦合），引用时两文都要给。
- `2024-Krawczyk-…-全文.md`：本轮已补齐 8 字段 frontmatter 缺失（authors/year/journal/key_finding）并追加「任务级/构成比例视角」补注一节。

## 七、裁决

**这个层次没有现成的「等额 vs 比例」任务级直接对照与最优性理论——等额分配本身是 GEM (NeurIPS 2017) 的默认工程约定、自适应非均匀分配有 CORE/PDCL/RMM 等实验级先例而无任何最优性/遗憾界，因此我们的 $\lfloor N/k\rfloor$ 规则可作为「文献默认约定」被合法引用，但其相对比例分配与遗忘率驱动分配的优劣必须（也值得）在本课题数据上用 §四 的 E1/E2 自建对照证伪——判定为「部分现成、关键对照需自创」。**
