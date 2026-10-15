# 检索笔记：任务级/经验级记忆预算分配（滚动更新）

任务计划见同目录 `task_plan.md`。约束：不跑实验；PDF 一律 pdf-converter；scholar 挂代理。

## 时间线

- 2026-10-15 14:18 建目录、task_plan.md、notes.md。开始本地盘点。
- 2026-10-15 14:20 本地盘点启动：Zotero 语义检索 + 本地混合索引并行。
- 2026-10-15 14:22–14:30 scholar 7 轮检索（q1–q7），全部落盘 /tmp/scholar-task-budget/q*.json。
- 2026-10-15 14:25–14:28 下载 9 篇 Tier A PDF（arXiv×7、NeurIPS×1、AAAI×1）。
- 2026-10-15 14:30–14:40 MinerU extract 转出 9 篇全文 markdown。
- 2026-10-15 14:40–14:50 逐篇精读，定位分配规则与公式；核验 Yoon 2606.30067 真实存在（arXiv API id_list 查询）。

## 逐篇精读记录（PDF 位置 /tmp/scholar-task-budget/pdf/，转出 md 在同目录 md/）

### A1 GEM（Lopez-Paz & Ranzato, NeurIPS 2017, arXiv:1706.08840）证据等级：本地全文
- **等额分配的规范出处**：§2（转出 md 行 75，对应 arXiv 版 p.3）原文："If the number of total tasks T is known, we can allocate m = M / T memories for each task. Conversely, if the number of total tasks T is unknown, we can gradually reduce the value of m as we observe new tasks [Rebuffi et al., 2017]"。
- 任务数未知时的替代做法是逐步缩减每任务容量（iCaRL 式），**没有给出最优性论证**，是工程约定。
- Table 2（p.6）：CIFAR-100 上 memory size 200/1280/2560/5120 的 ACC 单调升，称"无需仔细调这个超参"。
- 与我们的规则同构：已知年度数 k → ⌊N/k⌋；未知时随到达缩减。**我们的规则就是 GEM 的约定 + iCaRL 缩减式。**

### A2 CORE（Zhang et al., 2024, arXiv:2402.01348）证据等级：本地全文（未见正式发表出处）
- **把任务级分配规则本身当研究对象**，开篇批评"allocate the replay buffer space indiscriminately across all tasks"（行 15）。
- AQA 公式（§Adaptive Quantity Allocation）：Eq.3 att_p = −log(1−f_p)（旧任务按遗忘率）；Eq.4 att_τ = −log(1−Σ_p f_p·i_p)（当前任务按干扰度）；Eq.5 softmax 归一为 A^s；Eq.6 阈值 1/(λ|P|) 把旧任务分为 SR（间隔重复）/TR（靶向复习）；Eq.7 SR 任务保底 1/(λ|P|)；Eq.8 TR 任务按 softmax 注意力占比分配剩余。
- λ 网格搜索定 2（Table 2）。缓冲 500、10 任务、split-MNIST/CIFAR10/CIFAR100。
- 消融（Table 4）：去掉 AQA 平均精度 −5.17%、最差任务精度 −5.30%（37.95→32.78 / 16.30→11.00）。
- **无最优性/遗憾界理论**，是启发式（遗忘率驱动的软配额）。

### A3 PDCL（Elenter, NaderiAlizadeh, Javidi, Ribeiro, arXiv:2310.00154）证据等级：本地全文
- **任务级约束 + 拉格朗日对偶**：把 CL 写成当前任务风险最小化 s.t. 各旧任务损失 ≤ ε_k（P_t）。
- **缓冲划分公式**（§3.2，行 174-174）：n(t) = |B|·λ(t)/‖λ(t)‖₁（按对偶变量线性比例），并加仿射下界防零分配；α∈[0,1]，α=1/2 时每任务保底 |B|/2t（恰好是均分的一半），α=1 时保底 0。
- Theorem 1：对偶变量是约束扰动的敏感度指标（含 deviation bound；附录 A.2/A.4）。
- **直接对照**（Figure 3）：按任务难度非均匀划分（PDCL）优于均匀划分（PDCL₀、ER Ring、AGEM）。
- 小缓冲时对偶变量质量退化（引 Chaudhry 2019），语音任务小缓冲下样本选择无增益（行 261）。
- **这是检索到的唯一有理论支撑的任务级非均匀分配**（敏感度界，非最优性/遗憾界）。

### A4 Replay Scheduling（Klasson, Kjellström & Zhang, arXiv:2209.08660）证据等级：本地全文
- 任务级**回放比例** p=(p_1,…,p_{t−1}), Σp=1（§3.2 行 70-74）：MCTS 可搜出显著优于均匀调度的日程；再用 RL 学可迁移策略。
- **基线含 ETS（Equal Task Schedule，等额比例）**（行 135）；学习策略在泛化测试中平均排名优于 ETS（Table 4、Fig.5：A2C 对被遗忘任务 2 加大回放）。
- 关键设定差异：**假设历史数据随时可访问**，每个任务开始时从全部历史数据重新取 M 条填缓冲——是"采样比例"问题，不是固定缓冲的存量分配。对我们的在线固定缓冲设置，其结论只能间接参考。
- 无理论界。

### A5 RMM（Liu, Schiele & Sun, NeurIPS 2021）证据等级：本地全文
- 批评现有 CIL 内存分配"arbitrary and static"（行 9/15：ImageNet-Full 旧类 20 vs 新类 1300 的失衡例子）。
- 层级 RL：Level-1 把内存分给旧样本 vs 新数据（动作=相对增减比例）；Level-2 按训练熵二分组（难/易类）组内均分（行 67-75）。
- 策略在伪 CIL 任务（第 0 相数据构造）上预训练再迁移；累计验证精度作 reward。
- 增益：POD+AANets 在 25-phase CIFAR-100/ImageNet-Subset/ImageNet-Full +3.6%/+4.4%/+1.9%（摘要）。
- **分配单元是"阶段间新旧"与"类间"**，跨时间片维度即任务级；RL 无理论界。

### A6 SER（Isele & Cosgun, AAAI 2018）证据等级：本地全文
- FIFO 短期缓冲 + 长期情景记忆，4 种选择策略：惊喜度、奖赏、**分布匹配**、**覆盖最大化**（摘要行 9）。
- 分布匹配全程最优；**覆盖最大化在"训练少的任务更重要"时更有利**（行 9/25）。
- 对我们：分布匹配 = 缓冲构成 ∝ 流中各任务频率（**隐式比例分配**）；均匀目标 = 等额。两种"目标分布"的选取即任务级分配规则，但该文未从任务预算角度建模。

### A7 IES（Brignac & Lobo, WACV 2023, arXiv:2308.01895）证据等级：本地全文
- 固定缓冲（**200/500/5120**）与动态缓冲对照；蓄水池 vs herding vs GSS vs IPM 四种群体策略 × ER/DER/GDumb/ER-ACE（Table 2 完整数字）。
- 行 83：小缓冲下蓄水池导致"unbalanced fixed buffer"；**Table 3 实测任务份额（N=200）：23.5/19.0/16.0/22.0/19.5%**——注意均匀期望 20%，偏差 ≤3.5 个百分点，与二项采样波动量级（σ≈2.8%）相当，**其"偏向早期任务"的表述证据强度有限**，但"蓄水池=隐式比例分配、herding/IPM=均分"的对照成立。
- 行 145-147：动态缓冲按 intracluster variance / Kaiser criterion 定每类样本数（复杂度驱动配额）。
- 结论：herding/IPM（均分）在小缓冲普遍优于蓄水池（比例）于 FAA/FF（Table 2, N=200 行）。

### A8 Adaptive Memory Replay（Smith et al., WACV 2024, arXiv:2404.12526）证据等级：本地全文
- 设定是**内存充裕、算力受限**（保留全部旧数据），把"每步从哪个旧任务取多少回放"建模为非平稳 K 臂老虎机 + Boltzmann 采样（行 100-102），按遗忘倾向调各旧任务回放占比。
- 回放:新数据 1:1；温度 t=0.1、β=0.01；遗忘最多降 10%（摘要）。
- 对我们：是"回放预算的时间分配"而非"存储预算的任务分配"，设定不同，作对照参考。

### A9 Memory Bounds（Chen, Papadimitriou & Peng, FOCS 2022, arXiv:2204.10830）证据等级：本地全文
- Theorem 1.1（p.2）：k+1 个任务的 (ε,0.01)-continual learner 即使 improper 也需 Ω(kdb/ε) 比特内存——**总内存随任务数线性增长，无"数量折扣"**。
- Theorem 1.2：c 遍扫描时内存 (k/ε)^{O(1/c)}·db；Theorem 1.3：proper 学习器多遍仍需 ~kdb/(c³ε)。
- 对我们的意义：固定 N=200 在任务/年度数增长下必然摊薄，这是**信息论下界层面的必然**，不是我们规则的缺陷；但该文不管"如何在任务间切"。

## 新增候选（q5 中发现，未取全文）

- Krawczyk & Gepperth, "An analysis of best-practice strategies for replay and rehearsal in continual learning", IEEE (ECAI/ICPR 类) 2024：balanced/constant/weighted 三种回放策略对照，参数=每任务回放样本比例——**疑似最接近"任务级等额 vs 其他比例"的直接实验对照，arXiv 无收录，待查作者主页**。
- Yoon, "Neural Subspace Reallocation", arXiv:2606.30067（2026）：声称无记忆分配策略在循环环境下的累计遗憾界（vs 历史感知策略）。已核真实存在。
- FeDMRA arXiv:2603.28455（联邦类增量动态比例分配）；CL-KR-TD（IEEE 2026，任务散度动态内存缓存）；PROXYMIX arXiv:2606.00400（含 Proportional Replay 基线）。


## 本地盘点结果

- Zotero 语义检索（2026-10-15 14:19）：15 条命中全部不相关（多任务学习、RWKV、AdapterFusion 等），本地 Zotero 库无本主题条目，无重复调研风险。
- 本地混合索引（scripts/literature_search）：索引缺失需重建，自动构建报错 `EmbeddingBackend.__init__() got an unexpected keyword argument 'device'`；且本机 CPU 正在训练禁止计算，**标阻塞**，本任务改用 scholar + arXiv API。

## scholar 检索记录（均已存 /tmp/scholar-task-budget/q*.json）

- q1 "memory allocation across tasks replay buffer continual learning"
- q2 "adaptive replay buffer allocation forgetting rate per task continual learning"
- q3 "how many exemplars per task memory budget continual learning"
- q4 "optimal memory allocation across tasks continual learning theory bound"
- q5 "replay buffer size per task proportional allocation continual learning"
- q6 "dynamic exemplar allocation class incremental learning reinforcement memory management"
- q7 "reservoir sampling online continual learning buffer analysis"

## 候选池（证据等级滚动标注）

### Tier A（已取得 PDF，待转全文精读）

| # | 论文 | 年份/会议 | 分配单元 | 规则 | 证据等级 |
|---|---|---|---|---|---|
| A1 | GEM, Lopez-Paz & Ranzato, arXiv:1706.08840 | NeurIPS 2017 | 任务 | 预算按任务数**等额**分给每任务 | 本地 PDF 已下 |
| A2 | CORE (AQA), Zhang et al., arXiv:2402.01348 | 2024 (arXiv) | 任务 | 按遗忘率+干扰度**动态不等额**分配，明确批评"一律均分" | 本地 PDF 已下 |
| A3 | Primal-Dual CL, Elenter et al., arXiv:2310.00154 | 2023 (arXiv/ICLR 投稿) | 任务 | 对偶变量作敏感度指标**划分缓冲**（拉格朗日理论） | 本地 PDF 已下 |
| A4 | Replay Scheduling, Klasson et al., arXiv:2209.08660 | 2022 (arXiv) | 任务 | 任务级**采样比例**（缓冲内容比例）可调度 | 本地 PDF 已下 |
| A5 | RMM, Liu, Schiele & Sun | NeurIPS 2021 | 阶段+类别 | RL 学**动态分配策略**，批评静态分配 | 本地 PDF 已下 |
| A6 | Selective Experience Replay, Isele & Cosgun | AAAI 2018 | 跨任务经验 | 分布匹配/覆盖最大化等 4 种选择策略 | 本地 PDF 已下 |
| A7 | Brignac & Lobo (IES), arXiv:2308.01895 | WACV 2023 | 缓冲整体+个体 | 最优存储量分析、群体策略对比、动态内存 | 本地 PDF 已下 |
| A8 | Adaptive Memory Replay (bandit), Smith et al., arXiv:2404.12526 | WACV 2024 | 任务（采样比例） | 多臂老虎机调**各旧任务回放占比** | 本地 PDF 已下 |
| A9 | Memory Bounds for CL, Chen, Papadimitriou, Peng, arXiv:2204.10830 | FOCS 2022 | 总内存下界 | 记忆须随任务数**线性增长**的下界定理 | 本地 PDF 已下 |

### Tier B（仅摘要级候选，待定）

- Krawczyk & Gepperth 2024（IEEE 10678096）balanced/constant/weighted 回放策略对照——**无 arXiv 版，疑似付费墙**
- Ma et al. 2025 IEEE（10877933）联合内存优化 bi-level
- Lu & Rossi 2025 DM-DAR（按类别动态配额，类级但动态预算思想）
- Rezaei & Sabokrou CASP arXiv:2311.16485（类级）
- PRS, Kim et al. ECCV 2020（类级分区水库采样）
- Chrysakis & Moens CBRS ICML 2020（类级）
- Buzzega et al. ICPR 2021 BRS/LARS（bag of tricks）
- Aljundi et al. GSS NeurIPS 2019（梯度重要性选择）
- Sun et al. InfoRS arXiv:2204.04763（信息论在线记忆选择）
- Nikoloutsopoulos & Koutsopoulos KL-reservoir ICML 2024（缓冲分布匹配目标分布）
- Zhou et al. MEMO arXiv:2205.13218（模型参数 vs 样本之间的预算分配）
- Knoblauch & Husain ICML 2020（最优 CL NP-hard、需完美记忆）
- Wen et al. arXiv:2507.12043（回放 CL 信息论泛化界，含缓冲规模）
- Li, Wu, Braverman ICLR 2026（两任务内存-统计权衡上下界）
- Yoon arXiv:2606.30067（无记忆策略 regret 界，待核真伪）
- Chaudhry et al. tiny episodic memories arXiv:1902.10486（小预算下 reservoir vs 其他）

## 已下载 PDF 清单（/tmp/scholar-task-budget/pdf/）

1706.08840, 2402.01348, 2310.00154, 2209.08660, rmm2021, isele2018, 2308.01895, 2404.12526, 2204.10830 —— 共 9 篇，下一步 pdf-converter (MinerU) 转全文。

## 未关闭疑点

- ~~Krawczyk & Gepperth 2024 是否有公开版~~ **已解决**：并行代理 2026-10-14 已将该文 PDF 入库（`raw/papers/attack-detection/lamda-related/2024-Krawczyk-重放与排练最佳实践策略分析.pdf`）并建 `-全文.md`；本轮补齐 8 字段 frontmatter 并追加「任务级/构成比例视角」补注。此前「疑似付费墙」判断作废。
- CORE 正式发表信息（仅 arXiv）——报告已如实标注预印本。
- 任务级「等额 vs 按规模比例」直接存量对照——**已裁定不存在**（report.md §三），由 E1 自建。

## 无法获取原文清单

- Ma et al. 2025 IEEE（付费墙）、Yoon arXiv:2606.30067、Wen arXiv:2507.12043、Li/Braverman ICLR 2026、Knoblauch ICML 2020 及 Tier B 其余 13 篇——明细见 report.md §五。

## 阻塞

- 本地混合索引构建报错 + 本机算力占用，跳过本地索引通道（不影响主检索线）。
- scholar CLI 14:43 起限流（返回空），第 8 轮检索式未取得结果即停，不再重试。

## 收尾状态（2026-10-15 14:55）

- 入库：9 篇新 PDF（raw/papers/attack-detection/lamda-related/）+ 9 篇 `-全文.md`（8 篇新建含 8 字段 frontmatter + 五类分节摘要头 + MinerU 全文；Krawczyk 为补齐既有笔记）。
- INDEX：`wiki/papers/attack-detection/INDEX.md` 新增「LAMDA 第三章：固定记忆预算的任务级/经验级分配（2026-10-15 新增）」分节，10 条目 + 检索方法与边界。**INDEX.md 原有他人未提交改动，未做快照提交（遵守「含他人文件不夹带提交」），提交决定留主代理。**
- 交付：`report.md`（§一做法清单 / §二研究对象与最优性 / §三等额vs比例对照 / §四E1-E6证伪实验 / §五未取得原文清单 / §六交叉核对 / §七裁决：**部分现成、关键对照需自创**）。

