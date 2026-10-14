# 笔记：重放比率／暴露倍数文献核验

> 代理每完成一个子问题**立即**在本文件追加。禁止任务结束后凭记忆补写。

## 主代理已核事实（跑前基线）

| 事实 | 来源 | 等级 |
| --- | --- | --- |
| 「提高历史样本复用次数」在 RL 称 replay ratio / UTD ratio | WebSearch 命中（IEEE MARL 论文、Experience Replay 综述） | **在线摘要**（未取全文） |
| 已知失效形态：对陈旧样本过拟合、可塑性丧失、primacy bias、样本多样性下降、离策略发散 | 同上 | **在线摘要** |
| 本地 `wiki/papers/` 全文 `rg`「replay ratio／重放比／重放频率」**零命中** | 主代理 `rg`（683 篇笔记） | **实测**（但仅覆盖本地入库范围） |
| 本地文献索引在本工作树**未构建**，无法用混合检索 | `status --json` → `missing_index` | **实测** |

## Q1 — replay ratio / UTD 的定义与出处

**结论：两词都定义在 off-policy RL 语境下，语义都是「每收集一条（或一步）环境数据做多少次梯度更新」；但两词是否完全同义，文献本身有微妙分歧（见末尾）。**

### 1. `replay ratio` 的标准定义（已取全文）

**Fedus, Ramachandran, Agarwal, Bengio, Larochelle, Rowland, Dabney. *Revisiting Fundamentals of Experience Replay*. ICML 2020 (PMLR 119). arXiv:2007.06700.**
证据等级：**在线全文已下载**（`/tmp/replay_ratio_verify/md/2007.06700.md`，MinerU 转换）。

- 摘要第 1–2 句原文：「focusing on two fundamental properties: **the replay capacity** and **the ratio of learning updates to experience collected (replay ratio)**」——该文首次把 replay ratio 与 replay capacity 并列为「two fundamental properties」做系统消融。
- **§3.3 Definition 3 原文**：「The replay ratio is **the number of gradient updates per environment transition**.」
- §3.3：DQN 默认 replay ratio = 0.25（每 4 个环境步 1 次梯度更新，Mnih et al. 2015 超参）。
- §3.3 末尾：「Quantities similar to the replay ratio have also been identified as important hyperparameters in several recent works (Wang et al., 2016; Kapturowski et al., 2019; Hamrick et al., 2020; **Lin & Zhou, 2020**; van Hasselt et al., 2019)。」——即该概念**早于 2020 已被隐式使用**，Fedus 只是命名并系统化。
- 相关工作段：「van Hasselt et al. (2019) vary this ratio in combination with batch sizes to obtain a more sample-efficient version of Rainbow」+「Fu et al. (2019) report that agent performance is sensitive to the number of environment steps taken per gradient step」。

### 2. `update-to-data (UTD) ratio` 的标准定义（已取全文）

**Chen, Wang, Zhou, Ross. *Randomized Ensembled Double Q-Learning: Learning Fast Without a Model* (REDQ). ICLR 2021. arXiv:2101.05982.**
证据等级：**在线全文已下载**（`/tmp/replay_ratio_verify/md/2101.05982.md`）。

- §1 定义原文：「a high Update-To-Data (UTD) ratio, **which is the number of updates taken by the agent compared to the number of actual interactions with the environment**」。
- REDQ 超参表（附录 Table 1）：UTD ratio G = 20（MuJoCo 四环境）。
- **REDQ 自己没有声称首创该术语**（只说「REDQ is the first successful model-free DRL algorithm ... using a UTD ratio ≫1」）；且明确写道 MBPO (Janner et al., 2019)「uses a large UTD ratio of 20-40」、SAC「uses a UTD of 1」——**UTD 一词至少在 2019 年 MBPO 语境已在用语中**，归属首篇需再核 MBPO 原文（待办）。

### 3. replay ratio 的另一处定义与失效表述（已取全文）

**Nikishin, Schwarzer, D'Oro, Bacon, Precup, Courville. *The Primacy Bias in Deep Reinforcement Learning*. ICML 2022. arXiv:2205.07802.**
证据等级：**在线全文已下载**（`/tmp/replay_ratio_verify/md/2205.07802.md`）。

- §2 定义原文：「The number of resampling times of given data is controlled by the **replay ratio** (van Hasselt et al., 2019b; D'Oro & Jaśkowski, 2020) which plays a critical role in the algorithm's performance. **Set too low, the agent would underuse the data it has and become sample-inefficient; set too high, the agent would overfit the existing data.**」
- §3.1 heavy priming 实验：SAC 在 DMC quadruped-run，收集 100 个数据点后对 buffer 做 10^5 次梯度更新，此后继续正常训练近 10^6 步**无法恢复**——「overfitting to early experiences might inexorably damage the rest of the learning process」。
- §5：resets 机制解除后可承受更高 replay ratio（resets 与 replay ratio 的交互实验）。
- **注意**：Nikishin 引用的 replay ratio 出处是 **van Hasselt et al. 2019b 与 D'Oro & Jaśkowski 2020**，不是 Fedus 2020——说明「replay ratio」一词的归属在文献里就有分歧（待查这两篇原文后可收口）。

### 4. 是否只在 RL / off-policy 框架下被定义？

- **就这两个术语本身**：是。Fedus 的定义（§3.3）与 REDQ 的定义都嵌在「环境步（environment step / transition）」的语义里；监督学习没有「environment transition」，故直接搬用名词在语义上是空指。
- **语义等价物（多 epoch 训练）在监督学习里是否被当作同一件事**：检索至今未发现任何监督式 CL 论文自称在做「replay ratio / UTD」，但 Bagus & Gepperth（IJCNN 2021，arXiv:2108.06758，全文已下载）的调参轴 `epochs ∈ {1,3,5}` 与 `iterations ∈ {1,3,5}` 在功能上正是暴露倍数 m（见 Q2）。**术语不同、机制同构**——目前证据支持「RL 与监督 CL 两条文献线各自发展、未互相引用同一术语」这一判断，但仍需对 CL 综述（Rehearsal revealed, TNNLS 2022）rg 「replay ratio / update-to-data」确认零命中后才能写成定论。

### 检索面（Q1 部分）

| 工具/库 | 查询式 | 结果 |
| --- | --- | --- |
| WebSearch | `"replay ratio" reinforcement learning definition update-to-data ratio` | 命中但给的 arXiv ID **错误**（2404.13448 是物理论文、2305.16268 是物理论文），摘要级 |
| arXiv API（https + 代理） | `ti:"The Primacy Bias in Deep Reinforcement Learning"` | **2205.07802** ✓ |
| arXiv API | `ti:"Revisiting Fundamentals of On-Policy..."`（3 种变体） | 零命中（该题录真实性存疑， urex 论文待另查） |
| arXiv API | `ti:"Revisiting Fundamentals of Experience Replay"` → abs 页核验 | **2007.06700** ✓ |
| 全文 rg | `rg "replay ratio"` 于 2007.06700.md / 2205.07802.md | 命中（见上） |

**教训（必记）**：WebSearch 返回的 arXiv ID 多次张冠李戴（4 条里 4 条错），一切题录必须经 arXiv API 标题查询或 abs 页 `<title>` 核验。

## Q2 — 持续学习设定下「记忆样本重复暴露」的既有工作

**判决：有，且不止一篇——这是一个已被系统研究的机制，不是无人区。** 最直接的一篇（Zhang et al. 2022）标题就叫「Repeated Rehearsal」，并把「何时有益何时有害」作为研究问题。

### 2.1 最直接近邻：Repeated Rehearsal（已取全文）

**Zhang, Bifet, Pfahringer. *A simple but strong baseline for online continual learning: Repeated Augmented Rehearsal*. NeurIPS 2022. arXiv:2209.13917.**
证据等级：**在线全文已下载**（`/tmp/replay_ratio_verify/md/2209.13917.md`）。

- **机制定义（§2）**：「Repeated Rehearsal (Multiple Iterations)」——对每个 incoming batch 做 K 次梯度更新，每次从 memory 重采一个 batch 与 incoming batch 拼接（§3.2 式 K 次更新）。
- **既有工作定位（§2）**：「Aljundi et al. [2019] propose to perform multiple gradient updates instead. Their experiment with CIFAR10 shows using MIR with five iterations leads to a **1.7% improvement** in accuracy.」——**multiple iterations 在 2019 年 MIR 论文里已是超参**。
- **理论（§3.2）**：k>1 时是**有偏梯度估计**（「in the case of k>1, it provides a biased gradient estimate as the same incoming batch is used for consecutive gradient updates」）；k=1 才无偏。
- **memory overfitting 实证（§3.2）**：ER 在 online 设定下 10 iterations → 严重 memory overfitting（loss-landscape 分析，图 1(a)）；并明确指出 Verwimp et al. (2021)（Rehearsal revealed）已在 **offline 10-epoch** 设定演示同一现象。
- **机制解释（§3.2）**：k>5 后 incoming batch 损失比 memory batch 低 10–10² 倍 → 新数据的正则化效应被削弱 → 近似「训练于 memory only」。
- **总判词（§3.2 末）**：「Applying repeated rehearsal ameliorates the former problem but aggravates the latter problem. Therefore, **the performance gain from repeated rehearsal is quite limited**.」
- **修正方案（§4）**：RAR = repeated rehearsal + 数据增强；证明增强把有偏梯度变成增强经验风险上的无偏 SGD（Proposition 3, Appendix A）；并用 RL 在线调 K 与增强强度。

**与本任务 m 杠杆的同构与差异**：同构——都在提高记忆样本的每轮暴露次数；差异——RAR 在 iteration 层面（每 incoming batch 会话内 K 次重采），本任务 m 在训练集构成层面（同一批样本复制进每轮训练集）。期望暴露次数同构（K×buffer 采样占比 ≈ m）。

### 2.2 Oversampling / 复用比率的网格研究（已取全文）

**Bagus, Gepperth. *An Investigation of Replay-based Approaches for Continual Learning*. IJCNN 2021. arXiv:2108.06758.**
证据等级：**在线全文已下载**（`/tmp/replay_ratio_verify/md/2108.06758.md`）。

- **调参轴（Table IV）**：`epochs ∈ {1,3,5}`、`iterations ∈ {1,3,5}`（TEM/GBSS/NSR+）、`buffer size ∈ {50,200,500}`、batch size、lr——**暴露倍数与 buffer size 在同一网格**。
- **结论三条（原文）**：
  1. 「A higher number of epochs or iterations correlates with a better CL performance **up to a certain point**.」
  2. 「(A-)GEM generally performs better with an **additional repetition of stored samples**. This applies for a task-wise, as well as a batch-wise rehearsal setting.」
  3. 「The **over-sampling of buffer contents** has a positive effect. However, **too high rehearsal rates can result in lower generalization and overfitting**.」
- 数据集：MNIST/F-MNIST/SVHN/CIFAR10（D2₅/D5₂/D10₁ 协议），iCaRL/GEM/A-GEM/TEM/GBSS/NSR/NSR+ 七方法。
- **注意**：这是「暴露倍数 + 缓冲大小」**分别调参**，不是联合优化。

### 2.3 综述级证据：Rehearsal revealed（已取全文）

**Verwimp, LArg...（作者清单见 arXiv 页）. *Rehearsal revealed: The limits and merits of revisiting samples in continual learning*. IEEE TNNLS 2022. arXiv:2104.07446.**
证据等级：**在线全文已下载**（`/tmp/replay_ratio_verify/md/2104.07446.md`）。

- 标题即研究对象：「revisiting samples」的 limits 与 merits。TNNLS 2022 出版版被引 170+（Scholar 实测）。
- 摘要定位：「rehearsal ... by sampling the input distribution in a limited rehearsal memory from which samples are revisited in later training batches」。
- 它的核心实验是 loss-landscape 分析（先拟合再压缩假设），不是暴露倍数扫描；**暴露倍数轴的证据主要由 Zhang et al. 2022 与 Bagus & Gepperth 2021 提供**，本文提供的是「memory overfitting 现象的学术命名与首个可视化」（被 RAR §3.2 引用为 offline 10-epoch 版本证据）。
- 引用链事实（来自 RAR 全文）：Verwimp et al. 2021 用「先在 T1 训到收敛，再在 T2 用 ER 训 10 epochs」演示 memory overfitting；RAR 在 online 设定用 10 iterations 复现同型现象。

## Q3 — 存储预算 × 复用预算的联合约束（**预判缝隙，重点查**）

**判决（分两类报告，按主代理要求）：**

- **A 类「有此工作但与我们的设定不同」：不少，且最近邻已到「两轴同测、交互已讨论、预算框架已提出」的程度。**
- **B 类「形式化联合优化（max Nm s.t. 比特预算 + 暴露/计算约束）」：检索面内未检出。**
- **表述建议**：可写「既有工作分别测过两个轴、提出过统一预算口径，但未见把缓冲容量 N 与暴露倍数 m 作为联合决策变量的形式化优化」；**不可写**「无人研究复用频率」「无人提出存储×计算统一预算」——两者都有反例（见 A 类）。

### A. 有此工作，但与「max Nm s.t. 联合预算」的设定不同

#### A1. 最近邻：replay capacity × replay ratio 同文双轴（已取全文）

**Fedus et al., arXiv:2007.06700（ICML 2020）。**
- 同一论文把 **replay capacity**（0.1M–10M）与 **replay ratio**（经 oldest policy 25k–25M 控制）作为两个独立消融轴，全部在 Rainbow/DQN 上扫描（§3、§4）。
- **交互已被明确讨论**（§3.2「Increasing buffer size with a fixed replay ratio...」段）：「When the replay ratio is fixed while the buffer size is modified, there is an **interplay** between the improvements caused by increasing the replay capacity and the deterioration caused by having older policies in the buffer. The magnitude of both effects depends on the particular settings of these quantities.」
- Table 1（DQN/Rainbow 在 fixed replay ratio vs fixed oldest policy 两种口径下增大容量的差异：DQN +0.1%/−0.4%，Rainbow +28.7%/+18.3%）证明**同一存储操作的效果依赖复用口径**——这正是「两轴耦合」的实验证据。
- §5 承认：「these aspects may be difficult to control independently... two examples of such adjustments are the replay capacity and replay ratio」。
- **但没有目标函数**：全文无 max Nm、无预算约束式、无一阶条件；两轴是实验矩阵不是优化变量。

#### A2. 统一预算口径已提出，但 m 不是决策变量（已取全文，代理 D 独立核验一致）

**Seo, Koh, Choi. *Budgeted Online Continual Learning by Adaptive Layer Freezing and Frequency-based Sampling*. ICLR 2025. arXiv:2410.15143。**
- **budget 指两者**：摘要原文「use **floating point operations (FLOPs)** and **total memory size in Byte** as a metric for computational and memory budgets, respectively, to compare and develop CL algorithms in the same 'total resource budget'」；存储预算还并入 logits 与模型参数字节（following Zhou et al. 2023）。
- **explicit 批评单 epoch 口径**：「single-epoch training would incur a different amount of computations per CL algorithm」→ 改用每样本训练 FLOPs。
- **算力再分配方向已打开**（图 1 说明）：「aL-SAR ... can **utilize the saved computational cost for further training**」——省下的 FLOPs 用于更多训练。这是「固定总预算下，计算与存储可以互换来花」的最近表述。
- **但**：frequency 部分是 use-frequency 启发式排序（§3.2，采低频样本、带折扣 r^t 与类间梯度相似度），**无目标函数、无一阶条件、m 不是决策变量**（代理 D 核验同此结论）。

#### A3. 「用计算换比特」的同构技巧已存在（已取全文）

**Fini, Lathuilière, Sangineto, Nabi, Ricci. *Online Continual Learning under Extreme Memory Constraints* (MC-OCL/BLD). ECCV 2020. arXiv:2008.01510。**
- 预算只有**存储轴**：两个约束（时间步间除网络外零信息传递；禁辅助网络内存）。
- 行 163：数据增强不存增强后图像，**只存变换类型与参数、训练时重算**（「the memory cost of data augmentation remains negligible」）——与我们「m 不花比特只花计算」的**资源结构同构**（计算替代存储），但对象是增强而非复用倍数，且没有把省下的比特显式换算成任何暴露量。

#### A4. 两轴同表分别调参（已取全文）

**Bagus & Gepperth, arXiv:2108.06758（IJCNN 2021），Table IV**：epochs ∈ {1,3,5} × buffer size ∈ {50,200,500} 同一网格；结论只给边际方向（「up to a certain point」「oversampling positive but too high → overfitting」），无联合结构。

#### A5. 问题错位与重复-as-实验轴（全文已核，代理 D 主核）

- **Smith et al. 2024（arXiv:2404.12526）AMR**：全量存储下的重放样本选择（continual pre-training 场景），明言「not adding training cost」——**存储免费、稀缺的是计算**，与「固定小缓冲 + 抬暴露」的问题错位。
- **Zhang et al. 2022（arXiv:2209.13917）RAR**：重复次数 K 是实验轴与理论分析对象（有偏梯度、正则化衰减），自适应版本用 RL 调 K，但 K 不是显式优化问题的变量。

#### A6. 仅题录（全文不可得，不得据此下结论，只列候选）

| 论文 | 出处 | 摘要片段可见内容 | 状态 |
| --- | --- | --- | --- |
| Ma, Ma, Hong, Li. *Joint memory optimization for continual learning* | IEEE TNNLS 2025, doc 10877933, 10 被引 | 「...replay buffer separately, we **jointly optimize them from a memory perspective**, aiming to balance memory...」 | **仅题录＋摘要片段**（IEEE JS 墙；scholar --bibtex 两次零结果；arXiv ti: 查询零命中）。「jointly optimize」的主语被截断，从片段看是模型与 buffer 的联合，非比特×次数 |
| Azadi et al.（WebSearch 称 *Jointly Optimizing the Memory Buffer and Learner for CL*, TNNLS Early Access 10788676） | IEEE | 摘要未取得 | **题录真实性待核**：WebSearch 给的 arXiv ID 2210.02231 已证伪（真实为 2D-3D pose lifting 论文）；arXiv API `ti:"Jointly Optimizing the Memory Buffer"` 零命中 |
| Yu et al. *Learning to Replay: meta-RL approach to experience replay in CL* | Pattern Recognition 2026 | 「optimize content or timing separately, our method jointly...」 | **仅题录**（joint 的对象是重放内容与时机） |
| Wang et al. *Release the Potential of Memory Buffer in CL: A Dynamic System Perspective* | IEEE TPAMI 2025 | 「adversarial optimization objective that jointly...」 | **仅题录** |
| Sun. *Investigating Replay Buffer Capacity and Batch Size for DQN Learning* | 2026, 0 被引 | — | **仅题录**（容量×批大小，RL 侧两轴研究） |
| *Scaling DRL for decision making: survey on data, network, and training budget strategies* | 2025 综述 | — | **仅题录**（训练预算策略综述，未核内容） |

### B. 查无此类工作：形式化联合优化未检出 + 检索面记录

**未检出的问题形态**：总预算 B 下 $\max_{N,m} \text{性能}(N,m)$ s.t. $N \cdot c_{\text{bytes}} \le B_{\text{存储}}$、$m$ 不耗比特但受计算预算/泛化上限约束——即把「比特预算」与「暴露/计算预算」作为**同一优化问题的两个约束**，求解 N 与 m 的联合最优或帕累托前沿。

**检索面（2026-10-14，全部实测）**：

| # | 库/工具 | 查询式 | 结果 |
| --- | --- | --- | --- |
| 1 | Scholar CLI | `"Joint memory optimization for continual learning"` | **零结果**（error: No results found） |
| 2 | Scholar CLI | `"memory optimization continual learning joint"` | 命中 Ma TNNLS 2025、Fini ECCV 2020、Pellegrini 2019、Wang 2025 PAMI、Yu 2026 PR——均非比特×次数联合 |
| 3 | Scholar CLI | `"Jointly Optimizing the Memory Buffer and Learner for Continual Learning"` | **零结果** |
| 4 | Scholar CLI | `"amplification data augmentation continual learning rehearsal Verwimp AAAI"` | 命中 RAR 等；**未见「Data Amplification」论文** |
| 5 | Scholar CLI | `"continual learning joint optimization memory size computational budget replay"` | 8 条均非联合优化（压缩/潜伏重放/边缘 AI 综述） |
| 6 | Scholar CLI | `"reinforcement learning jointly optimize replay buffer size update-to-data ratio"` | 6 条均非联合优化（CrossQ、Reset Replay、容量×批大小研究） |
| 7 | arXiv API | `ti:"Joint Memory Optimization"` | **零命中** |
| 8 | arXiv API | `ti:"Jointly Optimizing the Memory Buffer"` | **零命中** |
| 9 | arXiv API | `all:"data amplification" AND cat:cs.LG` | 6 条均非 CL（信息论 property estimation）——WebSearch 所称「Boosting CL with Data Amplification」在 arXiv **无此题**，其给 ID 2205.09051 已证伪（实为 Gagliardo-Nirenberg 不等式论文） |
| 10 | arXiv API | `ti:"Revisiting Fundamentals of On-Policy..."`（3 变体） | **零命中**——WebSearch 所称 UREX 论文（给 ID 2404.13448）题录未证实，2404.13448 实为超引力物理论文 |
| 11 | 全文 rg（我方 13 篇转换件） | `rg -i "jointly optimize|max.*budget|budget.*constraint"` | 命中 A1–A5 的相关段落，均无形式化联合优化（上文已逐条给出） |
| 12 | 本地 | `rg -il "replay ratio\|update.to.data\|UTD ratio\|重放比\|重放频率\|memory oversampling" raw/ wiki/ thesis/` | **零命中**（本工作树全文范围） |

**零命中的效力边界**：上述「未检出」覆盖 Scholar（6 组查询式）、arXiv API（4 组）、我方 13 篇全文、本地三目录；**未覆盖** IEEE Xplore 全文库、Scopus/WoS、中文库（CNKI）、Ma et al. 与 Azadi 两篇 IEEE 全文。若审稿要写「未见」，主张限定为「在我们检索面内未见」，并把 A6 两篇 IEEE 论文列为待核全文的边界项。

### C. 对「任务化改造落点」的直接回答（按修正后口径）

**组装清单（本任务 LAMDA Domain-IL 上装配「存储分配 + 暴露倍数」必须引用并划界的部件）**：
1. **暴露倍数的机制与失效**：Zhang et al. RAR（arXiv:2209.13917）——重复排练的形式化、有偏梯度、memory overfitting；Bagus & Gepperth（arXiv:2108.06758）——epochs/iterations/oversampling 网格与拐点；Aljundi et al. 2019 MIR（multiple iterations 的先例，经 RAR §2 转引，我方未取原文）。
2. **存储容量轴**：Fedus et al.（arXiv:2007.06700）在 RL 侧的 capacity 系统消融；CL 侧缓冲大小敏感性属常识轴（Bagus Table IV 同表出现）。
3. **统一预算口径**：Seo et al.（arXiv:2410.15143）——FLOPs + Byte 总预算作为公平比较框架；引用后划界：其用于比较与算力再分配，未把 m 作为决策变量。
4. **计算换比特的结构先例**：Fini et al. MC-OCL（arXiv:2008.01510）——存变换参数、重算增强。
5. **数学形式化的候选骨架**：代理 C 正在核 Boyd §5.5.3 water-filling 与 Rahman 2022——「给定预算分配到两个边际收益递减的轴」的现成凸优化形式；若成立，$\max_{N,m}$ s.t. 比特预算恰好落入该骨架（**待代理 C 全文核验**）。
6. **失效诊断工具**：Verwimp et al.（arXiv:2104.07446）loss-landscape 路径分析——m 扫描时可复用为拐点观测。

**文献停在哪一步、我们要补哪一段**：既有工作停在「两轴分别调参（Bagus）、两轴同测交互讨论（Fedus）、统一预算口径（Seo）、重复的理论分析（RAR）」；**没有一步走到「在冻结的比特预算下，把 N 与 m 作为联合决策变量求解，并给出暴露倍数的预算依赖最优值 m\*(B)」**。本任务（LAMDA、年份到达、10 epochs/年、MLP）恰好是一个 m\*(B) 可被实测刻画的小预算场景——这是任务化改造的落点，属「既有部件 + 未被联合的约束」，与参照论文第三章「组装既有方法家族＋任务化改造」同级。

## Q4 — 失效形态在持续学习设定下的实验证据

**判决：RL 已知的失效形态在监督式 CL 里有对应的、可指页的实验证据，且「m 曲线有拐点」这一预测已被 CL 文献两条线独立记录。我们的 m=8 臂就是在测这个拐点。**

### 4.1 memory overfitting 的 loss-landscape 证据（监督 CL，已取全文）

**Zhang, Bifet, Pfahringer. arXiv:2209.13917（NeurIPS 2022），§3.2。**
- ER + 10 iterations（online）→ 严重 memory overfitting：learning trajectory「avoids the high-loss ridge region for the memory data but **goes right into the high-loss ridge region for the past tasks' test data**」（图 1(a)）。
- **机制量化**：k>5 后 incoming batch 的训练损失比 memory batch 低 10–10² 倍 → 「the regularization effect of the incoming data batch is greatly undermined: the joint training ... becomes similar to **training on memory only**」。
- 理论：k>1 有偏梯度（§3.2）；RAR（重复+增强）恢复无偏（Proposition 3, Appendix A）。
- 总判词：「the performance gain from repeated rehearsal is **quite limited**」。

### 4.2 offline 版本：10-epoch memory overfitting（全文在手，现象经二级转述确认）

**Verwimp et al., arXiv:2104.07446（IEEE TNNLS 2022）。**
- RAR §3.2 原文转述：「Verwimp et al. (2021) use this method to demonstrate the memory overfitting in ER for **offline continual learning setting with 10 epochs**」。
- 我方全文核验：Rehearsal revealed 的图 1/3/6 均为 loss-path 分析（w₁ → w₂ 线性插值路径损失），确实演示「先拟合 memory 再压缩」；「10 epochs」这一具体数值经 RAR 转述确认，我方未在 2104.07446.md 中逐字复核——标注：**现象已全文确认，epoch 数为二级转述**。

### 4.3 网格证据：拐点存在（已取全文）

**Bagus & Gepperth, arXiv:2108.06758（IJCNN 2021），结论清单：**
- 「A higher number of epochs or iterations correlates with a better CL performance **up to a certain point**」——拐点表述。
- 「too high rehearsal rates can result in **lower generalization and overfitting**」——失效形态。
- 配套事实：epochs ∈ {1,3,5}、buffer size ∈ {50,200,500} 同表网格（Table IV）。

### 4.4 暴露不均有害的旁证（已取全文）

**Seo, Koh, Choi. arXiv:2410.15143（ICLR 2025），§A 消融表 Tab. 7/8：**
- 单独使用 use-frequency 采样（优先采低暴露样本）在 CIFAR-10 上 A_last = 69.40，**低于**随机检索 70.08——说明「把暴露从均匀改成不均」本身就可能伤性能；其 discounted/similarity 修正后才超过随机。
- 该结果反向佐证：暴露分布是敏感超参，本任务 m=2/4 的增益与「暴露从 1 升到有效暴露」一致。

### 4.5 RL 侧对照（已取全文，供类比而非等同）

**Nikishin et al., arXiv:2205.07802，§3.1 heavy priming**：100 个数据点 + 10^5 次更新 → 不可恢复过拟合；§5 resets 解锁更高 replay ratio。
**Fedus et al., arXiv:2007.06700**：replay ratio 扫描（0.25→更高）在 DQN 上不稳定、Rainbow 上增益；结论与 m 拐点同型。
- **使用边界**：RL 侧证据不能直接搬到监督 CL（无 TD/bootstrapping、无离策略分布偏移），只能作机制类比；监督 CL 侧自有 4.1–4.4 的直接证据，**不需要** RL 类比来支撑。

### 4.6 对 m=8 臂的预测（可证伪）

若 4.1–4.3 成立，m=8（N=200，每轮 10 epochs）下每个历史样本本轮暴露次数 = m×epochs×(batch 中该样本占比)；当有效暴露超过文献拐点区间（Bagus: >5；RAR: >10 iterations 出现 overfitting 信号），应看到增益趋平或回撤，且 loss-landscape 型诊断可用（对 memory 子集与对当前数据集的损失差随 m 扩大）。**这是实验待证，不是文献已证于 LAMDA。**

## 代理 B — MEMO / Forget Forgetting

（待代理 B 填写）

## 代理 C — Boyd §5.5.3 / Rahman 2022

（待代理 C 填写）

## 代理 D — 约束优化与最优遍数

> 代理 D 任务：找「给有限的历史样本，看多少遍最优」（内部最优 $m^*$）的现成形式化；裁决 water-filling/KKT 适用性。
> 检索工具面：arXiv export API（`https://export.arxiv.org/api/query`，经 `-x http://127.0.0.1:7890`）、OpenReview API、WebSearch、arXiv/ar5iv HTML 全文（`curl` 落盘后 `rg`）。
> 教训记录（2026-10-14）：WebSearch 返回的 arXiv 编号不可直接采信——其给出的 `2504.00653` 实为 Siegel modular forms 论文、`2403.13271` 实为 code generation 蒸馏论文，均已实测证伪；所有 ID 以 arXiv API 二次确认为准。

### 优先核验 1｜Seo, Koh, Choi, "Budgeted Online Continual Learning by Adaptive Layer Freezing and Frequency-based Sampling"（ICLR 2025）

- 定位：arXiv **2410.15143**（v2，标题一致，作者 Seo/Koh/Choi 已确认）；OpenReview forum `dOAkHmsjRX` 等同名条目。
- **证据等级：在线全文已下载**（`https://arxiv.org/html/2410.15143v2` 全文 HTML 落盘检索，133,751 字符正文）。
- 方法名 aL-SAR（adaptive Layer freezing and Similarity-Aware Retrieval），在线 CL。
- **它有没有把「存储/预算」与「复用频率」写进同一目标函数或约束集：没有。** 具体结构：
  1. **计算维度有显式优化**：每个训练批自适应冻结层，最大化「Fisher 信息增益 / 所需计算量」，原文 "we propose to maximize the expected amount of information gained per computation (I/C)"；另一处写作 $\max_m (I/C)_m\cdot\sum_i (\text{BF})_i$。该 $m$ 是**逐批的层冻结决策/批内计算分配**，不是「同一批历史样本重复暴露倍数」。
  2. **复用频率是启发式排序，不是优化变量**：Similarity-Aware Retrieval 按每个样本的 use-frequency（被训练次数计数 $c_i$）与类间梯度相似度排序，"samples with high use-frequency yield marginal knowledge gains in training, and samples with low use-frequency are likely to contain knowledge that the model has not yet learned" → 优先取低频样本。**只有排序规则，没有关于 $m$ 的目标函数、没有一阶条件、没有 $m^*$。**
  3. **存储预算是固定比较口径**：以总内存字节数与 FLOPs 作为跨方法公平比较的预算定义（正文多处 "budget"），buffer 大小固定，不进入联合优化。
- **对本课题的含义（缝隙证据）**：该文把「计算预算 × 信息增益」联立了，但「存储预算 × 复用频率」仍未联立；其 use-frequency 排序恰恰以「高频复用边际收益递减」为经验前提，却未给出该前提的函数形式——与我们观测的 $m^*$ 内部最优同源。**与我们最直接竞争的形式仍未出现。**

### 优先核验 3｜Bagus & Gepperth, "An Investigation of Replay-based Approaches for Continual Learning"（IJCNN 2021）

- 定位：arXiv **2108.06758**（已确认标题与作者：Benedikt Bagus, Alexander Gepperth，Fulda University）。
- **证据等级：在线全文已下载**（ar5iv HTML 全文，57,147 字符正文）。
- **主代理点名的「更高的轮数或迭代数与更好 CL 性能相关」原文**（结论节）："A higher number of epochs or iterations correlates with a better CL performance **up to a certain point**."
- **相邻更关键的原文**（同节）："The over-sampling of buffer contents has a positive effect. However, **too high rehearsal rates can result in lower generalization and overfitting**." 以及 "(A-)GEM generally performs better with an additional repetition of stored samples."
- **有没有最优轮数刻画或一阶条件：没有。** 全文 `epoch` 仅 2 处：其一为超参网格设置（`epochs 1, 3, 5`；`buffer size 50, 200, 500`；`iterations 1, 3, 5`），其二即上引经验句。无目标函数、无 $m^*$ 表达式、无边际条件。`up to a certain point` 是对网格内 3 档的经验描述。
- **对本课题的含义**：这是「先升后降」现象在 CL 文献中的**同型经验陈述**（可作动机引用），但**形式化空缺仍在我们这边**——它不是竞争形式，是证据。

### 优先核验 2｜Ma, Chen, Li, "Continual Learning with Joint Memory Optimization"（IEEE TNNLS 2025, JMO）

- 定位尝试：scholar CLI 精确标题零命中；arXiv API `ti:"Joint Memory Optimization"`、`au:"Guangyuan Ma"` 均未命中该文（该文疑似无 arXiv 预印本）；主代理给的 IEEE 页 `document/10877933` curl 仅返回 15,410 字节脚本壳，正文与摘要均被 JS 渲染墙挡住。
- **证据等级：仅题录**（标题「Continual Learning with Joint Memory Optimization」、作者 Guangyuan Ma/Hong Chen/Huaiyu Li、TNNLS 2025）。WebSearch 片段称其方法为「gradient correction + logit distillation 联合框架」——**摘要级候选，未经全文核验，不得引用其结构细节**。
- **本代理无法核验其目标函数与约束**。需要全文才能判断「存储 × 复用」是否联立。⇒ 待办：通过机构订阅或联系作者获取 PDF，MinerU 转换后补记本节。**在此之前，「该文是否占据缝隙」对代理 D 而言是未决项。**

### 代理 D 补核｜Zhang, Pfahringer, Frank, Bifet et al., "Repeated Augmented Rehearsal"（NeurIPS 2022）

- 定位：arXiv **2209.13917**（v2，"A simple but strong baseline for online continual learning: Repeated Augmented Rehearsal"，作者 Yaqian Zhang / Bernhard Pfahringer / Eibe Frank / Albert Bifet 等，Waikato）。
- **证据等级：在线全文已下载**（arXiv HTML 全文，92,308 字符）。
- **与 m 轴的关系（最重要的一篇既有工作）**：
  1. §3 标题即 "Is Repeated Rehearsal a Good Idea?"；§3.2 "Repeated Rehearsal: The Decaying Regularization Effect of Incoming Data"。
  2. 机制论述（§3）：iteration 数增大 → 记忆批的 loss landscape 对过去任务 loss landscape 的近似变差 → 轨迹落入过去测试数据的高损失脊；incoming batch 的训练损失在 $k>5$ 后比 memory batch 低 $10$–$10^2$ 倍，正则效应被破坏，联合训练退化为「只训记忆」。
  3. 总结句（§3 末）：online rehearsal 受 "**overfitting locally and underfitting globally**" 两难约束。引用 Verwimp et al. (2021) 的 offline 10-epoch memory overfitting 实验作先例。
  4. 附录 A 三个 Proposition：把 ER / augmented ER / online ER+reservoir 的 SGD 更新写成**有效经验风险的无偏估计**（如 $\mathcal{R}(\theta)=\sum_{\mathcal{D}_T}\mathcal{L}+\frac{|\mathcal{D}_T|}{|\mathcal{D}_M|}\sum_{\mathcal{D}_M}\mathcal{L}$，Proposition 2）。
- **有没有 $m^*$ 的解析刻画或一阶条件：没有。** 它形式化的是「重复排练为何有过拟合风险」（更新偏差 + 正则衰减），解法是 RAR（重复 + 数据增强）与 RL 调超参；重复次数仍是实验轴，不是被优化的量。
- **对本课题的含义**：这是与我们机制解释（「保持旧知识收益 vs 有限样本过拟合代价」）**最接近的既有理论化**，可在正文中作直接对照；但「收益-代价权衡的内部最优 $m^*$」在它那里只有定性表述（dilemma），无定量形式。

### 代理 D 补核｜Smith, Valkov, Halbe, Gutta, Feris, Kira, Karlinsky, "Adaptive Memory Replay for Continual Learning"（arXiv 2404.12526, 2024）

- 定位：arXiv **2404.12526** v1（标题已核），MIT-IBM Watson AI Lab。
- **证据等级：在线全文已下载**（arXiv HTML 全文，60,889 字符）。
- 结构：§3 Preliminaries 含 K-armed Bandits；§4.2 "Adaptive Memory as a Bandit Optimization"。
- **目标函数（其式 1 与式 3）**：$O=\min_\theta\big[\frac{1}{|X_T|}\sum_{X_T}L+\sum_{t<T}\frac{1}{|X_t|}\sum_{X_t}\mathcal{F}(x;\theta)+C\big]$，后近似为 $\min_\theta\big[\cdot+\alpha\sum_{x\in\mathcal{M}^*(\theta)}\mathcal{F}(x;\theta)/|\mathcal{M}^*(\theta)|+C\big]$，其中 $\mathcal{M}^*(\theta)$ 是「当前被遗忘最多的过去数据子集」。
- **它优化的是「重放哪些样本」（遗忘度排序）**；计算预算的处理是**等量交换**——每批从新数据中随机丢弃 $|\mathcal{M}^*(\theta)|$ 条以保持梯度计算数恒定。设置是 FM 扩展预训练（过去数据可全存，稀缺的是计算）。
- **「复用倍数 $m$」不是决策变量；存储预算不进入目标**（其设定里存储免费）。与我们的问题（存储固定、稀缺维度是复用）**错位**。

### 检索面小结（优先核验部分）

| 目标 | 工具 | 结果 |
| --- | --- | --- |
| Seo ICLR 2025 | OpenReview API + arXiv API `ti:"Budgeted Online Continual Learning"` | **2410.15143** ✓ 全文 |
| Bagus IJCNN 2021 | arXiv API `id_list=2108.06758` | **2108.06758** ✓ 全文（ar5iv） |
| Ma TNNLS 2025 | scholar lookup ×2、arXiv API（标题/作者/关键词 ×4）、IEEE 直连 | **未获全文**（仅题录） |
| RAR | arXiv API `ti:"Repeated Augmented Rehearsal"` | **2209.13917** ✓ 全文 |
| AMR | arXiv API `ti:"memory" AND ti:"continual learning"` | **2404.12526** ✓ 全文 |

### Q1（代理 D 主问题）｜有限数据重复暴露的「最优遍数」泛化理论

> 与代理 A 的 Q1（RL replay ratio 定义）不同，本支查**监督学习泛化理论**：同一批有限数据看 $m$ 遍，最优遍数有没有定理级刻画。

#### 命中 1（**定理级「最优遍数」显式表达，最贴近）**：Lin, Camoriano, Rosasco, "Generalization Properties and Implicit Regularization for Multiple Passes SGM"（AISTATS 2016）

- 定位：arXiv **1605.08375**（API `abs:"number of passes" AND abs:generalization` 命中；作者 Junhong Lin, Raffaello Camoriano, Lorenzo Rosasco，LCSL MIT & IIT）。
- **证据等级：在线全文已下载**（ar5iv HTML 全文，105,391 字符）。
- **设定**：凸损失 + 线性参数化函数（可分希尔伯特空间/核类），SGM 多遍训练；「在无惩罚、无约束时，步长与遍数都可作为隐式正则化旋钮」（摘要）。
- **核心定理（Corollary 5，步长 $\eta_t=1/\sqrt m$ 时）**：excess risk 上界
  $$\mathbb{E}[\mathcal{E}(g_t)]-\inf_w \mathcal{E}(w) \lesssim \frac{\sqrt t\,\log t}{m^{3/4}} + \frac{\log t}{\sqrt m} + \Big(\frac{\sqrt m}{t}\Big)^\beta$$
  其中 $t$ 为迭代数、$m$ 为样本数、$\beta$ 为目标函数谱衰减指数。**上界三项结构即「先升后降」的数学形态**：前两项随 $t$ 增（稳定性/估计误差＝重复暴露的代价），第三项随 $t$ 降（逼近误差＝欠拟合的代价）。**平衡两类误差给出最优遍数的显式表达**
  $$t^*=\Big\lceil m^{\frac{2\beta+3}{4\beta+2}}\Big\rceil,\qquad \text{optimal excess risk}\ \lesssim m^{-\frac{\beta}{2\beta+1}}\log m$$
  另一步长方案下 $t^*=\lceil m^{(\beta+3)/2(\beta+1)}\rceil$（对应最优风险 $m^{-\beta/(\beta+1)}\log m$）。定理陈述与证明见正文 §3（Theorem 1–3, Corollary 5）与附录（Rademacher 复杂度工具，承 [12]）。
- **对本课题的意义**：这是「**最优遍数存在、有显式表达、来自收益-代价两项平衡**」的定理级原型。它就是一阶条件的积分形式（对上界求最小）。**适用边界**：凸损失 + 线性参数化 + 单任务静态分布——不直接覆盖深度 MLP + 顺序年份 + 检索缓冲，但「平衡估计误差与逼近误差」的骨架可直接移植。
- **注意**：本理论中「过拟合代价」由稳定性项随遍数增长刻画，与我们观测的「对 200 条样本过拟合」机制同型。

#### 命中 2（**重复数据损害的中间峰值 + 实用诊断**）：Hernandez et al.（Anthropic）, "Scaling Laws and Interpretability of Learning from Repeated Data"（arXiv 2022）

- 定位：arXiv **2205.10487**（API 命中验证：Danny Hernandez, Tom Brown, ... Chris Olah, Jared Kaplan, Sam McCandlish，全 Anthropic）。
- **证据等级：在线全文已下载**（arXiv HTML 全文，68,723 字符）。
- LLM 语料设定：90% 唯一 + 10% 重复 token，扫重复集大小、模型大小、重复暴露份额各 2–3 个数量级。
- **主要发现（§1.1）**：重复数据诱导强 double-descent——「data repeated a few times does not cause much damage..., data repeated very many times also does not cause much damage, **but there is a peak in the middle where damage is surprisingly large**」；峰值处「**train loss on the repeated data approaches zero**」（重复子集被记住），并给此作实用诊断：「This also provides a practical diagnostic for when repeated data is likely to be harming the model」（§1.1，Fig. 2 右）。
- **对本课题的意义与差异**：它给出「重复暴露的损害何时开始」的**可测诊断**（重复子集训练损失是否趋零——对应我们「对 200 条缓冲过拟合」的可观测量），且中间峰值现象与我们「先升后降」同型。**差异**：其纵轴是重复子集造成的**损害**（其任务是唯一数据上的 LM 损失），不是「重复暴露的**收益**曲线」；且无 $m^*$ 公式。可作机制证据与诊断工具引用，不是竞争形式。

#### 命中 3（**重复收益的参数化饱和模型 + 「4 epoch」量级论断**）：Muennighoff et al., "Scaling Data-Constrained Language Models"（NeurIPS 2023）

- 定位：arXiv **2305.16264**（API `id_list` 验证标题一致；Stanford/Together 团队）。
- **证据等级：在线全文已下载**（arXiv HTML 全文，153,255 字符）。
- **式 (5)（§3.1 Parametric Fit；推导见附录 A）**：
  $$L(N,D)=\frac{A}{N'^\alpha}+\frac{B}{D'^\beta}+E,\qquad D'=U_D+U_D R_D^*\big(1-e^{-R_D/R_D^*}\big)$$
  其中 $U_D$ 为唯一 token 数、$R_D$ 为重复 token 数、$R_D^*$ 为拟合常数。**重复 token 的边际价值每次重复损失 $(1-1/R_D^*)$ 份额（几何衰减）**。
- **关键经验论断（原文）**："**up to 4 epochs of repeated data yields negligible changes to loss compared to having unique data**"；§6："returns ... start dropping **after around 4 epochs (25% budget)**"；"returns diminish extremely fast at **around 16 epochs** ($R_D^*$)"。
- **对本课题的意义与差异**：
  1. 「4 epochs 收益近乎无损」与我们在 LAMDA 上实测的 $m^*\approx 4$ **同一量级**——但这只能作为巧合量级参照，不能当依据（任务/模型/数据都不同）。
  2. 该模型 $D'$ 随 $R_D$ **单调饱和（凹增），无内部峰**——它只建「收益衰减」，不建「过拟合代价」。**它自身解释不了内部最优**；其附录 D 与 Hernandez 2022 才处理损害区间。
  3. 「收益侧凹饱和 + 代价侧（另加）」正是主代理建议形式化可借的两块板。

#### 命中 4（**「多遍可证有益」定理**）：Pillaud-Vivien, Rudi, Bach, "SGD: The Role of Implicit Regularization, Batch-size and Multiple-epochs"（NeurIPS 2018）

- 定位：arXiv **2107.05074**（API `ti:"implicit regularization" AND ti:"multiple-epochs"` 命中验证）。
- **证据等级：在线全文已下载**（arXiv HTML 全文，261,585 字符）。
- **Theorem 4（§5.1 "Multiple Passes Can Help!"）**：构造性 SCO 实例上，单遍 SGD 有下界 $\Omega(1/\sqrt n)$，而 $k$ 遍 multi-pass SGD 达到 $O(1/\sqrt{nk})$——**多遍可证严格更优**；且正则化 ERM（RERM）在该实例有 $\Omega(1)$ 下界。
- **对本课题的意义**：把「为什么有人重复」的理论基础钉住（多遍降低优化/估计误差）。**注意其 $k$ 越大越好的结论是在总体目标 $F$ 上**——本理论的 excess risk 是对总体风险的，过拟合代价不在该定理的权衡里；与 Lin-Rosasco 2016 的「两误差平衡出 $t^*$」结合看，二者分别对应收益侧与代价侧。

#### 待全文核验的现代理论候选（已确认存在，未取得全文）

1. **"Larger datasets can be repeated more: A theoretical analysis of multi-epoch scaling in linear regression"**（scholar 精确标题命中；OpenReview forum `9DA8NiVtmB`，`api.openreview.net/notes?id=` 与 `openreview.net/pdf?id=` 均被 Challenge 反爬拦截，PMLR v258 目录无该题）。**证据等级：仅题录（标题）**。从标题看：固定计算下最优遍数随数据集大小增长、线性回归多遍 scaling 的理论分析——与本问题同族，**必须取得全文后再引用其定理**。
2. **"Multi-Epoch Learning: ...Data Repetition Saturate Generalization"**（NeurIPS 2025 proceedings PDF `0f705a932553c08ebf0d1bc520b7cbc6`，5.96 MB 已下载至 `/tmp/me_neurips.pdf`，标题以 scholar 返回的 proceedings.neurips.cc 链接为准；WebSearch 声称结论为「饱和出现在遍数 ≈ 模型/数据比」——**摘要级候选，待 MinerU 转换核验定理编号**）。

### Q2（代理 D）｜water-filling / KKT 能不能用在我们的问题上

#### Boyd & Vandenberghe §5.5.3 的形式到底是什么（页 245–247）

- 结构（WebSearch 对官方 PDF 的结构描述，**页码与公式待代理 C 对原件逐字核验**；官方书页 https://web.stanford.edu/~boyd/cvxbook/）：
  $$\min_x\ -\sum_{i=1}^n \log(\alpha_i+x_i)\quad \text{s.t.}\ \mathbf{1}^Tx=P,\ x\succeq 0$$
  即「总预算 $P$ 分配到 $n$ 个通道，每通道收益 $\log(\alpha_i+x_i)$ 凹」。由**凹目标 + 仿射约束**，KKT 充要，解析解 $x_i^*=\max(0,\,\beta-\alpha_i)$（$\beta$ 为水平台阶）。
- **该形式成立的四个前提**：①每通道收益函数凹；②收益对变量**可分离**（$\sum_i f_i(x_i)$）；③约束线性；④强对偶成立（凸问题 + Slater）。

#### 逐条对照我们的问题：哪里断

1. **凹性未证**。我们只有 $m\in\{1,2,4,8\}$ 四个实测点，单种子，无法判定 $f(m)$ 凹性。**但注意方向**：机制上「收益侧」凹饱和（Muennighoff 式 (5) 的 $D'$ 即凹增饱和）、「代价侧」凸增（Hernandez 2022：重复子集训练损失趋零即过拟合起效）⇒ 若两侧都能给出机制论证，$f=$ 收益 $-$ 代价**应当是凹的**，此时 KKT 充分性**可以恢复**。也就是说，问题不是「目标非单调所以 KKT 全部不能用」，而是「**充分性取决于收益-代价分解后的凹性论证，这需要独立机制证据，不能由 4 个实测点保证**」。
2. **可分离性不成立（对联合配置）**。water-filling 的水平台阶解析解依赖同形凹收益可分离。若我们把预算联合配置到 $(N,m)$（存储 × 暴露），收益项大概率含交互（实测已证「有效量 $\ne N\cdot m$」），闭式解失效；KKT 一阶条件（作为必要条件）仍可写。
3. **结构错配（对单标量 $m$）**。water-filling 是**多维分配**工具；若决策变量只有标量 $m$，问题退化为 $f'(m)=0$ 求内点 + 边界比较，根本不需要它。只有当我们把预算分配到**多个对象**（例如各年份的 $m_i$、或每轮「新样本 : 重放样本」配比）时，才进入 water-filling 的适用场景。
4. **敏感性解释失效（若凹性不证）**。Boyd §5.6 的 $\lambda^*=-\partial f^*/\partial b$ 需要强对偶；非凸/未证凹时对偶 gap 非零，该解释不能引用。

#### 非凸/非凹目标 + 预算约束的标准工具（文献）

- **KKT 一阶必要条件在非凸下依然成立**：Nocedal & Wright, *Numerical Optimization*（2nd ed., Springer 2006）§12.3——**Theorem 12.1**（局部解 + LICQ（Def 12.4）⇒ KKT 点，**假设中无凸性**，pp. 340–343）；§12.4 二阶必要/充分条件（Lagrangian Hessian 在 critical cone 上半负定/正定）。来源：Springer 书页 https://link.springer.com/book/10.1007/978-0-387-40065-5 与多所大学课程讲义（Brown/Rochester/Waterloo）一致引用。**证据等级：在线摘要（多源一致的教科书结构，未逐页对原件）**。
- 对偶 gap 与弱对偶：Boyd Ch.5（§5.2.2 弱对偶总成立；强对偶需凸 + 约束规范）。
- 实务推论：**一维 $m$ 用一阶条件 + 网格实测即可，无需重型工具**；多维分配若凹性论证成立可写 KKT 闭式，若不能，则网格/贝叶斯优化等黑盒方法先于全局优化理论。

#### 裁决（对主代理原方案）

**「Boyd §5.5.3 作为理论依据照搬：不能用；KKT 一阶条件作为必要条件：可用。」** 缺的前提按重要性排序：①目标凹性未证（water-filling 充分性与敏感性解释全部依赖它）；②收益可分离性不成立（联合配置 $(N,m)$ 时）；③多维分配结构不匹配（标量 $m$ 时整个工具无的放矢）。**修复路径**：把目标写成「凹收益（保持旧知识，饱和形式）− 凸代价（对有限缓冲过拟合）」，一旦两侧各有独立机制证据，KKT 从必要升格为充分，water-filling 型论证在「多对象预算分配」版本下才重新可用。

### Q3（代理 D）｜这是不是双层优化，以及它管不管用

- **结构判断**：若 $m^*$ 定义为「给定存储预算 $B$ 下最大化下游 avg_f1 的暴露倍数」，上层选 $m$、下层是（随 $m$ 变化的）训练轨迹与评估——这是**超参数优化的退化情形**（1–2 维决策变量、黑盒、单次评估昂贵），在 bilevel 框架的谱系内，但动用 implicit differentiation 的重型机器无性价比。
- **标准引用（题录已核）**：
  1. Colson, Marcotte, Savard, "An overview of bilevel optimization", *Annals of Operations Research* **153**: 235–256, 2007，DOI **10.1007/s10479-007-0176-2**（Crossref API 实核）。**证据等级：仅题录（DOI/卷/页已核）**。
  2. Franceschi, Frasconi, Salzo, Grazzi, Pontil, "Bilevel Programming for Hyperparameter Optimization and Meta-Learning", ICML 2018，arXiv **1806.04910**（API 标题核验）。
  3. Lorraine, Vicol, Duvenaud, "Optimizing Millions of Hyperparameters by Implicit Differentiation", AISTATS 2020，arXiv **1911.02590**（API 标题核验）。
  4. （旁证）"Stability and Generalization of Bilevel Programming in Hyperparameter Optimization", arXiv **2106.04188**（API 标题核验）。
- **适用条件与结论**：1806.04910 / 1911.02590 的 implicit differentiation 需要**下层最优解唯一、光滑**（强凸或近似 PL 条件）才能把 $\nabla_m$ 上层目标写成对下层解的函数。我们的「下层」是 SGD 训练轨迹（非凸、无唯一解、评估带随机性）——**前提不满足；这类方法也不能把「评估 avg_f1」换成可微代理时保持含义**。它们的适用场景是数百至数百万**连续**超参的可微代理目标。⇒ **bilevel 框架可作「问题的正式命名」，不建议作为求解工具；1–2 维黑盒决策量用网格 + 多种子 + 置信区间即可**。

### Q4（代理 D）｜「回放策略写成约束优化问题」的既有形式

- **GEM（Chaudhry et al., NeurIPS 2019, arXiv 1706.08840）**——最直接的「回放记忆进入约束」形式。**证据等级：在线全文已下载**（ar5iv 全文 86,701 字符）。原文（其式 (6)(7)）：
  $$\min_\theta\ \ell(f_\theta(x,t),y)\quad \text{s.t.}\quad \ell(f_\theta,\mathcal{M}_k)\le \ell(f^{t-1}_\theta,\mathcal{M}_k)\ \ \forall k<t \;\Rightarrow\; \langle g,g_k\rangle\ge 0\ \ \forall k<t$$
  记忆 $\mathcal{M}_k$ 只用于估计梯度 $g_k$；每批解一个小 QP 投影更新。**决策变量是 $\theta$，不是回放策略**：buffer size 外生、每批只看一遍（无暴露倍数变量）。
- **AMR（2404.12526）**：bandit 优化「重放哪些」（遗忘度），计算预算用「丢等量新数据」平衡（见前）。
- **RAR（2209.13917）**：RL 在线调重复次数 $K$ 与增强强度（重复次数仍是受控量而非被优化的解析对象）。
- **Seo ICLR 2025（2410.15143）**：计算预算维有显式 $\max I/C$；重放内容用 use-frequency 启发式排序（见前）。
- **判决**：「把回放策略做成优化问题」在 CL 里已有三种成熟形式——**QP 约束投影（GEM）/ bandit（AMR）/ RL（RAR）**；但它们优化的都是「**重放什么**」或「重放**与否**」，**没有任何一篇把「存储预算 × 暴露倍数」作为联立决策量并给出内部最优 $m^*$**。唯一未排除项仍是 Ma et al. TNNLS 2025（JMO，全文未取得）。

### Q1 补充核验｜NeurIPS 2025 PDF 实为「Diffusion Beats Autoregressive in Data-Constrained Settings」＋「Rolinek multi-epoch」题录存在性存疑

- **证伪记录**：WebSearch 曾声称 "Multi-Epoch Learning: Deep Neural Networks Trained With Data Repetition Saturate Generalization"（作者 Rolinek, Samek, Gretton, Schölkopf）为 arXiv 2403.13271 / NeurIPS 2024。实测：**2403.13271 是 code generation 蒸馏论文**（arXiv API 核验）；scholar lookup 该标题两次，返回条目中**均无该题**（前四条为 Entropy-guided token dropout 2025 / Data Repetition Beats Data Scaling 2026 / Diffusion beats autoregressive 2026 / Memorization-Guided Data Reuse 2026）；`au:Rolinek AND all:repetition` 零命中；`ti:"multi-epoch learning"` 精确短语仅两篇 CTR 论文。**结论：该题录存在性存疑，按「WebSearch 幻觉候选」处理，禁止引用**（404≠不存在，但两轮独立检索 + arXiv 全库三查询未现，已满足「记录检索面」的否定义务）。
- **MinerU 转换结果（extract 模式，26 页 → `/tmp/me_neurips_md/me_neurips.md`，89,400 字符）**：proceedings.neurips.cc hash `0f705a93...` 实际是 **Prabhudesai, Wu, Zadeh, Fragkiadaki, Pathak, "Diffusion Beats Autoregressive in Data-Constrained Settings"**（CMU + Lambda，NeurIPS 2025，scholar 显示被引 70）。**意外收获**：该文复用并强化了 Muennighoff 的 $R_D^*$ 模型（Markdown 行 114）："$R_D^*$ represents the **half-life of data reuse**, repeating data beyond $R_D^*$ epochs will result in significant diminishing returns"；且 "$D'\to U+U\cdot R_D^*$ ... the maximum usable signal is bounded by $(1+R_D^*)\cdot U$ ... This defines a **natural saturation point on returns**"。**证据等级：在线全文已下载（本地 MinerU Markdown）**。
- **对本课题的意义**：为「收益侧饱和」提供了第二条独立来源（LLM 语境）。饱和界 $(1+R_D^*)\cdot U$ 是纯收益模型——同样**不含过拟合代价项，不能产生内部最优**；与 Muennighoff/Hernandez 合并看，「收益饱和模型（凹）+ 过拟合代价（凸）」的两块板都有独立文献支撑，**拼起来才是内部最优**。

### 代理 D 结论｜「最优暴露倍数」的现成形式化：有最近的，无现成的

**一句话**：**没有**任何已核验的现成形式化直接刻画我们的场景（固定存储 + 同批样本每轮重复 $m$ 次 + 非平稳 CL + 内部最优 $m^*$）；**最近的现成形式化**是 Lin–Camoriano–Rosasco（AISTATS 2016）的 multi-pass SGM 理论——它给出「估计误差项随遍数增 + 逼近误差项随遍数降、平衡出显式 $t^*$」的定理级骨架（Corollary 5），但其设定是凸损失 + 线性参数化 + 静态分布。

**两级结论**：
1. **「收益−代价权衡出内部最优遍数」的定理级原型存在**（凸情形，Lin-Rosasco 2016 的 $t^*=\lceil m^{(2\beta+3)/(4\beta+2)}\rceil$）。机制两块板也有独立文献：收益侧饱和（Muennighoff 式 (5)；Prabhudesai 饱和界 $(1+R_D^*)U$）+ 代价侧记忆化起效点（Hernandez 2022 的「重复子集 train loss→0」诊断）。
2. **在 CL/回放场景（我们的场景）**：RAR（NeurIPS 2022）有同型 dilemma 的机制分析（有偏梯度 + 正则衰减 + locally overfit / globally underfit），Bagus 2021 有同型经验曲线（`up to a certain point` / `too high rehearsal rates ... overfitting`），但**全部止于定性**——没有目标函数、没有 $m^*$ 表达式、没有一阶条件。Seo/AMR/GEM 优化的都是「重放什么」而非「重复几遍」。**这个缝隙在已核验范围内是空的**（唯一未关闭项：Ma TNNLS 2025 全文）。

### 建议的形式化骨架（供主代理裁决，**实验待证，非冻结方案**）

设第 $t$ 年缓冲 $B$（$|B|=200$ 固定），暴露倍数 $m$。把「每轮 avg_f1」或「旧年测试损失」写成：
$$J(m) = \underbrace{G\big(m\cdot|B|\big)}_{\text{收益：历史暴露量，凹饱和}} - \underbrace{C\big(m,\ |B|\big)}_{\text{代价：对 }B\text{ 过拟合，随 }m\text{ 凸增}}$$
- 收益侧可借 Muennighoff 式 (5) 的饱和形（$G(m|B|)=g_0(1-e^{-m|B|/R^*})$ 型，参数 $R^*$ 由源侧不读最终标签的诊断估计）；
- 代价侧可观测量 = 缓冲训练损失趋零点（Hernandez 2022 诊断）或缓冲/新样本损失比（RAR §3.2 的 $k>5$ 判据）；
- $m^*$ 由 $J'(m)=0$ 一阶条件给出；若把预算分配到多年份 $m_i$（$\sum_i m_i=M$）则进入 water-filling 型结构——**但仅当收益凹 + 代价凸成立时 KKT 才是充分的**（Nocedal & Wright Thm 12.1 只给必要性）。
- **先决实证问题（在建形式化之前）**：多种子复现是否稳定给出内部峰；$m^*$ 是否随 $|B|$ 移动（$m^*$ 依赖 $N$ 的证据）；缓冲过拟合是否真实发生（缓冲 train loss 曲线）。这三点不成立则整个骨架无对象。

### 检索面（代理 D 汇总）

| 工具 | 查询式（代表性） | 结果 |
| --- | --- | --- |
| arXiv API | `ti:"multi-epoch learning"` / `all:"multi-epoch"+generalization` / `abs:"repeated data"+generalization` / `abs:"number of passes"+generalization` / `au:Rolinek` / `ti:"Joint Memory Optimization"` / `ti:"Budgeted Online Continual Learning"` / `ti:"Gradient Episodic Memory"` / bilevel 三查 | 命中 1605.08375、2205.10487、2305.16264、2107.05074、2209.13917、2404.12526、2410.15143、1706.08840、1806.04910、1911.02590、2106.04188；**零命中**：Rolinek 题录、JMO 预印本 |
| scholar CLI | 标题精确查询 ×6 | 定位 AISTATS「Larger datasets can be repeated more」与 NeurIPS hash；间歇反爬（两次空返回） |
| OpenReview API v2/v1 + pdf | `9DA8NiVtmB` | search 端点通；**notes/pdf 端点被 Challenge 拦**，全文未取得 |
| PMLR v258 目录 | 全文检索 "repeat" | 无该题 |
| Crossref API | Colson bilevel 综述 | **153:235-256, 2007, DOI 10.1007/s10479-007-0176-2** ✓ |
| MinerU extract | proceedings hash PDF | 实为 Diffusion beats autoregressive（NeurIPS 2025），89,400 字符 Markdown |
| DBLP / IEEE 直连 | bilevel / JMO | DBLP 反爬；IEEE JS 壳，均未取得 |

### 未关闭疑点（代理 D）

1. **Ma et al. TNNLS 2025（JMO）全文**——唯一直接威胁「缝隙为空」结论的未读文献。需机构订阅或作者渠道取得后按本节格式补核。
2. **"Larger datasets can be repeated more"（OpenReview 9DA8NiVtmB）全文**——标题层面与本问题同族（线性回归多遍 scaling 理论），未取得，其定理不可引用。待 OpenReview 反爬解除或经 PMLR/作者页另取。
3. **Boyd §5.5.3 页码级原件核验**由代理 C 负责；本节对该节结构的描述目前是 WebSearch 级（公式形式多源一致，但页 245–247 未对原件逐字核）。
4. **本代理 Q2 裁决的一个隐含假设**：「收益凹 + 代价凸 ⇒ f 凹」在 $m$ 的凸定义域上成立（凹−凸=凹，标准结果），但两侧函数形式的机制论证尚未做（这是建议骨架的先决实证问题 3）。

---

## 主代理直接检索（Google Scholar CLI，2026-10-14）

**用户质询「为什么不用 google scholar」后主代理亲自执行。** 命令：
`~/.local/bin/scholar lookup "<查询式>" --json --limit N`（须 export 代理，见 task_plan）。

**证据等级：仅题录 + 摘要片段**——以下**全部未取全文**，只用于确定下一步读什么。

### 高相关命中（**可能占据主代理预判的缝隙**）

| 论文 | 年份/被引 | 为什么相关 |
| --- | --- | --- |
| **Seo, Koh, Choi,「Budgeted online continual learning by adaptive layer freezing and frequency-based sampling」** ICLR 2025 | 19 | 标题同时含 **Budgeted** 与 **frequency-based sampling**——即「预算 × 采样频率」联合，**正是主代理预判为唯一缝隙的形态** |
| **Ma et al.,「Joint memory optimization for continual learning」** IEEE TNNLS 2025 | 10 | 「**联合记忆优化**」——可能已在做存储与使用的联合求解 |
| **Bagus & Gepperth,「An investigation of replay-based approaches for continual learning」** IJCNN 2021 | 71 | 摘要片段：「**A higher number of epochs or iterations correlates with a better …**」——**直接落在 $m$ 轴** |
| **Zhang, Pfahringer, Frank,「Repeated augmented rehearsal」** NeurIPS 2022 | 91 | 「**Repeated** rehearsal」——记忆样本的重复使用 |
| **Smith et al.,「Adaptive memory replay for continual learning」** 2024 | 62 | 记忆回放的**自适应**调度 |
| **Chaudhry et al.,「Continual learning with tiny episodic memories」** 2019 | 576 | 小容量记忆的奠基作之一 |
| **Brignac & Lobo,「Improving replay sample selection and storage」** 2023 | 31 | 同时动**选择**与**存储** |
| **Rolnick et al.,「Experience replay for continual learning」** NeurIPS 2019 | 2577 | 该方向最高被引奠基作 |
| Cho et al.,「Forget forgetting」ICLR 2026 | 9 | 已下载全文，代理 B 在读 |

### 主代理即时判读（**待代理核实，不得直接引用**）

**「存储预算 × 复用频率的联合约束」大概率不是空白。** 至少两篇（ICLR 2025 的 Budgeted＋frequency、
TNNLS 2025 的 Joint memory optimization）在标题层面就指向该形态。
⇒ 第三章**不能**以「未被联合研究过」立论；差异化必须另找落点。
**⇒ 这正是「用 Google Scholar 而不用摘要式检索」的直接价值：它在我把错误主张写进方案前就命中了。**

### 待办

- 上述九篇**均需取全文**后按 `raw/`→`wiki/` 入库，再作引用与划界
- 优先取：ICLR 2025 Budgeted、TNNLS 2025 Joint memory optimization、IJCNN 2021 Bagus（三篇直接决定主张边界）

---

## 代理 E — 复用分配与调度

> 任务：方向 A（复用权重按年度/类/样本分配）与方向 B（复用随训练进程调度）是否有先例；三篇点名论文（Zhang 2022 / Bagus 2021 / Chaudhry 2019）逐篇核「动没动复用次数、常数还是变数」。
> 本地三篇 MinerU 全文：`wiki/papers/attack-detection/lamda-related/`（`2022-Zhang-重复增强排练-在线持续学习的简单强基线-全文.md`、`2021-Bagus-Gepperth-重放式持续学习方法的考察-全文.md`、`2019-Chaudhry-微型情景记忆的持续学习-全文.md`）。
> **页码说明**：MinerU 产物不含 PDF 页码，以下定位用「章节/表号/图号 + md 行号」；行号指该 md 文件内行号，可直接 rg 复查。原始 PDF 在 `raw/papers/attack-detection/lamda-related/`。

### E.1 三篇逐篇核验（全部 `本地全文`）

#### ① Zhang, Pfahringer, Frank, Bifet, "Repeated Augmented Rehearsal"（NeurIPS 2022, arXiv:2209.13917）——**动了复用次数；主结果常数，另有变数版本**

- **动没动**：动。全文主题就是「每个 incoming batch 对 memory 重采样并重复 K 次梯度更新」（§3.2 定义，md 行 96–103：对每个 $B_t$ 做 K 次更新，每次 $B_{t,k}^{\mathcal M}\sim\mathcal M$ 与 $B_t$ 拼接）。
- **常数还是变数**：**两套都做了**。
  - **常数**：附录（md 行 412）「By default, the repeated rehearsal parameter for all the results is **K = 10** and the augmented rehearsal parameters are P = 1, Q = 14」；正文主表（md 行 189）即用 $(K=10, P=1, Q=14)$，RAR 对 ER 提升 +8.8%~+17.2%（MIR +9.1%~+17.7%、ASER +7.2%~+14.7%、SCR +5.1%~+17.9%）。
  - **变数（§5, md 行 139–152）**：RL-RAR——把 $K_t$（1–20 档）与增广强度（5 档）合为 100 维动作空间（附录 md 行 575），RL 每步依当前 memory batch accuracy 反馈在线选 $K_t$（md 行 430：`a higher repeated replay iteration leads to higher memory accuracy`，以 $A^*_\mathcal M$ 为目标带）。**动机原文（md 行 141）**：memory overfitting 程度「related to the CL problem features (e.g., task data size and memory size) and **also varies at different training stages**」——即他们明确承认最优复用次数随训练阶段变化，且用 RL 在线自适应，而非预定义调度曲线。
  - **变数版效果（附录 md 行 585 表）**：RL-RAR（平均 K=19.8）acc 29.2±0.3 > RAR(K=10) 27.3±0.3 = RAR(K=20) 27.3±0.5；代价是运行时间 6137s vs 1294s。
  - **对比基线（md 行 220）**：HTOCL（用前几个任务的验证集选超参）倾向「选大 repeats + 小增广」，对长任务序列不优——**跨阶段固定常数被点名次优**。
- **K 的扫描/消融**：有。Fig 4（md 行 224）K 从 1 到 20：无增广的 RER 在 CIFAR100/MiniImageNet 上 **K>2 即开始掉**；RAR 则在 K≈10 后平坦、K=20 无明显下降（md 行 226）。
- **维度**：全局标量。**不按类、不按任务、不按样本分配**——K 对所有 incoming batch 同一策略（RL 版随时间变，但仍是单标量序列）。

#### ② Bagus & Gepperth, "An Investigation of Replay-based Approaches for Continual Learning"（IJCNN 2021, arXiv:2108.06758）——**动了复用次数；网格扫描后取常数；另有一条「回放不均＋加权」的方向 A 级观察**

- **动没动**：动。复用次数是其正式调参轴：Table IV（md 行 177）`epochs ∈ {1,3,5}`（离线任务级遍数）、`iterations ∈ {1,3,5}`（TEM/GBSS/NSR+ 在线对 buffer 的迭代次数），与 `buffer size ∈ {50,200,500}`、batch size、lr 同表网格。
- **常数还是变数**：**常数**——网格扫描后为每个方法/设定取一档；无任何随训练进程或按样本调度的机制。
- **结论三条（§结论, md 行 258–262）**：
  1. 「A higher number of epochs or iterations correlates with a better CL performance **up to a certain point**.」
  2. 「(A-)GEM generally performs better with an **additional repetition of stored samples**. This applies for a task-wise, as well as a batch-wise rehearsal setting.」
  3. 「The **over-sampling of buffer contents** has a positive effect. However, **too high rehearsal rates can result in lower generalization and overfitting**.」——回放率的非单调效应被明确报告。
- **方向 A 级观察（§ Discussion–Replay issues, md 行 276）**：「the learning process itself is **unbalanced** for the most replay-based approaches, since **samples from earlier tasks are replayed more often than samples of later tasks**. Depending on individual approaches, this could create problems and **has to be avoided by an additional weighting**.」——**「跨任务回放次数天然不均」被点名，且「加权」被提出为修法；但该文只停在观察与建议，未实现任何按年/类的复用分配机制**（指蓄水池机制下老样本待得久、被采样次数自然偏多这一现象）。

#### ③ Chaudhry et al., "On Tiny Episodic Memories in Continual Learning"（arXiv:1902.10486）——**没把复用次数当配置变量；重复是隐式的、由数据流自然发生**

- **动没动**：没动复用次数。其实验设定是每个任务 **single pass**（md 行 130「after doing a single training pass over each task」），标准 ER：当前 batch(10) + memory batch(10) 各一次前向、一次平均梯度更新（md 行 86、136）；甚至为与 MER 公平比较把 MER 的 inner gradient steps 特意设为 1（md 行 148）。附录超参表（Tab. 8, md 行 421）只有 lr、EWC 的 χ、MER 的 γ/s，**没有复用次数这一轴**。
- **常数还是变数**：都谈不上——复用次数不是其设计变量。「repetitive training on tiny memories」（摘要与 §5.5）指的是**同一批 memory 样本跨后续任务被自然反复重放**：重复量由「后续任务数量 × 每步 1/2 混合比」决定，非人为设定。
- **对本课题的真正贡献**：证明「对极小 memory 重复训练**不伤泛化反而提升**（+7%~+17%，单样本/类时；md 行 30、38、167）」——这是 m>1 可行性的奠基证据；机制解释（§5.5, md 行 194–214）：后续任务数据像 data-dependent regularizer，纯训 memory 才过拟合（40% vs 85%）。
- **注意区分（方向 A 对照点）**：该文比较的 ring buffer / k-Means / MoF 等选择策略（md 行 173）动的是**存储槽位的类平衡**，不是复用分配——正是主代理要求区分的那一类工作。

### E.2 三篇小结表

| 论文 | 动复用次数？ | 常数/变数 | 取值/调度依据 | 定位 |
| --- | --- | --- | --- | --- |
| Zhang 2022 (RAR) | 是 | 主结果常数 K=10；另有 RL 在线变数（1–20 档） | 网格消融（Fig 4）+ RL 按 memory 准确率反馈 | §3.2、§5、附录 md 行 412/430/575/585 |
| Bagus 2021 | 是 | 常数（网格 1/3/5 档） | 超参网格 Table IV；结论：先升后降、过高过拟合 | Table IV、结论节 md 行 177/258–262 |
| Chaudhry 2019 (TEM) | 否（隐式重复） | —（非设计变量） | 重复量由数据流自然决定 | §5.5、附录 Tab. 8 |

### E.3 方向 B（复用随训练进程调度）外部检索——**有直接先例，不止一篇**

#### ① Klasson, Kjellström, Zhang, "Learn the time to learn: Replay scheduling in continual learning"（arXiv:2209.08660, 2022，被引 22）

- **证据等级：在线全文已下载**（ar5iv HTML 全文落盘 `/tmp/agent-e-verify/klasson_2022.txt`，247,886 字符）。
- **它调度什么**：摘要原文「continual learning systems should **learn the time to learn and schedule which tasks to replay at different time steps**」。机制：把「回放记忆的**跨任务构成比例**」作为决策变量，用 MCTS 离线搜出 replay schedule（T=5 任务时动作空间 1050 条路径），再用 DQN/A2C 学可泛化的调度策略；每步选择「用哪些任务的样本、各占多大比例填回放记忆」。
- **效果**：MCTS 找到的 schedule 「can **outperform replaying all tasks equally** or relying on heuristic scheduling rules」（结论节）；案例（图 7）：Task 3/4 时调度器用 Task 2 样本填满记忆、放弃重放 Task 1，保住 Task 2 精度、轻微多忘 Task 3。
- **与主代理方向 B 的同构与差异**：它调度的是「**回放预算的跨任务构成随任务步变化**」——即把分配量从「常数构成」变成「随训练进程的序列」，与主代理「m(t) 随轮次变化」**在『随训练进程变』这一层同构**；但分配的对象是「记忆/回放构成的跨任务比例」而非「每个样本的重复次数 m」。
- **注意**：其动机段原文「storing historical data is cheap in many real-world settings, yet replaying all …」——它的稀缺轴是**处理时间**，不是存储。

#### ② "FOREVER: Forgetting curve-inspired memory replay for language model continual learning"（ACL 2026, aclanthology.org/2026.acl-long.1144，被引 9）

- **证据等级：仅题录 + 摘要片段**（scholar 返回，未取全文）。
- 摘要片段：「a novel CL framework that **aligns replay schedules with a model-centric notion of time**. FOREVER defines model time using the magnitude of optimizer updates」——**按遗忘曲线（心理学 Ebbinghaus 式间隔重复）调度回放**，是「复用强度随训练进程变化」的直接先例形态。
- 待全文核验后再引其调度曲线形状与数字。

#### ③ Yu, Feng, Qiu, Wang, Bao, Yang, "Learning to Replay: A meta-reinforcement learning approach to experience replay in continual learning"（Pattern Recognition, 2026）

- **证据等级：仅题录 + 摘要片段**（scholar 返回，未取全文）。
- 摘要片段：「a **closed-loop adaptive replay framework** that jointly … On the timing side, it **adjusts replay frequency and intensity** by sensing forgetting risks」——「replay frequency and intensity」被闭环调节，**频率与强度两个轴都点了名**。需全文核验其分配维度。

#### 其他方向 B 候选（仅题录）

- Trust-region adaptive frequency for online continual learning（IJCV 2023, 被引 17）：标题含「adaptive frequency」，摘要片段指向 replay-based 方法的频率自适应；Springer 直链 PDF 可得，待核。
- AdaER（Neurocomputing 2024, 被引 83）：摘要片段「The **frequency of replaying experience** is set to be the same as the …」（截断）——疑似「回放频率与接收新样本频率对齐」类设计，待核。

### E.4 方向 A（复用权重按类/样本/年度分配）外部检索——**有先例，且「分槽位 vs 分频率」两类都命中**

#### 已命中候选（全部先标 `仅题录`，全文核验前不得支撑论断）

| 候选 | 检索式 | 命中片段（方向指示） |
| --- | --- | --- |
| **Class-incremental learning with repetition**（2023, 被引 19） | per-class replay frequency | 「a novel Replay approach, called **Frequency-Aware Replay** (… here is **the fraction of samples per class in experience size S**)」——按类频率分配回放构成的直接候选 |
| **An analysis of best-practice strategies for replay and rehearsal in continual learning**（2024, 被引 29） | importance weighted rehearsal | 「This study focuses on **three distinct approaches to replay: balanced, constant and weighted**」——把「均衡/常数/加权回放」当研究对象做系统对比，**是方向 A 最直接的实验型先例候选** |
| **Dynamic replay training for class-incremental learning**（2024, 被引 7） | per-class replay frequency | 「To achieve a **balanced number of samples** for the new and old classes」——疑似存储构成轴，待核 |
| Class-wise balancing data replay for federated class-incremental learning（2026, 被引 25） | 同上 | 「balancing **per-class sample counts in the replay buffer**」——存储轴（槽位分配），非复用分配 |
| Prototype-guided memory replay（2023, 被引 82） | 同上 | 「accuracy improves as the number of stored samples per class increases, but **stops at 20 per class**」——存储轴 |
| Seo et al. ICLR 2025 aL-SAR（arXiv:2410.15143，代理 D 已核全文） | — | use-frequency **排序采样**（按被训练次数计数的低频优先）——**介于两者之间**：分配的是「采样概率」（复用轴），但通过排序实现而非显式 $m_s$；消融显示单用 use-frequency 采样低于随机（69.40 vs 70.08） |

#### 「分槽位 vs 分频率」的文献格局（当前证据下的中间判读，待全文收口）

- **占多数**：按类/任务/难度分配的是**存储槽位与选择**（reservoir、CBRS、GSS/MIR、k-Means、类平衡缓冲、CoPE/ODM 类）——Chaudhry 2019 的选择策略对比（md 行 173）与 q3 检索的多条命中（Class-wise balancing、Prototype-guided、Imbalanced CL partitioning reservoir 被引 199）均属此类。
- **分「复用频率/权重」的**：目前命中 3 类——(a) 排序采样型（aL-SAR 的 use-frequency，ICLR 2025，全文已核）；(b) 调度型（Klasson 2022 调跨任务构成、FOREVER 调遗忘曲线节奏、L2R 闭环调频率强度，均待/已部分核）；(c) 加权回放型（best-practice 2024 的 weighted 策略对比、Frequency-Aware Replay 2023，待核）。**结论（「哪一种居多」）须等 (b)(c) 全文核验后收口，暂不写死。**

### E.5 全文核验续：Hemati 2023（方向 A 候选①）与 FOREVER 2026（方向 B 候选②）

#### ① Hemati, Cossu, Carta, Hurtado et al., "Class-incremental learning with repetition"（CoLLAs 2023, PMLR v232）

- **证据等级：本地全文**（原件已落 `raw/papers/attack-detection/lamda-related/2023-Hemati-类增量学习中的重复.pdf`，MinerU 转换 `wiki/papers/attack-detection/lamda-related/2023-Hemati-类增量学习中的重复-全文.md`；全文核验后 INDEX/结构化笔记登记待主代理验收）。
- **它分的是存储槽位，不是复用次数**。§3 原文（md 行 109）：「We propose Frequency-Aware (FA) **storage policy** that addresses the imbalance issue in CIR streams by **online adjustment of the buffer slots** in accordance with the amount of repetition for each class.」——计数每类在流中被观察的次数 $O[c]$，取反比 $Q=[1/O[c]]$ 归一化为**缓冲配额**，少出现的类分到更多槽位；多余配额回填给频繁类（行 109 末）。
- **但动机句正是方向 A 的论证**（同段，md 行 109）：「the less frequent classes will require **more repetition** to prevent forgetting, while the frequent classes will be **repeated naturally via stream occurrences**」——**「每个类需要的重复量不同」被明确陈述**，只是该文把这一需求落到存储配额（存得多→被采得多），没有直接调每类采样权重或复用次数。
- **场景差异**：CIR（类在流中重复出现）不是任务边界式 CL；其「频率」是**数据流中类出现次数**，不是训练配置量。与本课题「固定存储预算下给每个年度的缓冲块配复用次数」机制不同层。

#### ② Feng et al., "FOREVER: Forgetting Curve-Inspired Memory Replay for Language Model Continual Learning"（ACL 2026, aclanthology 2026.acl-long.1144）

- **证据等级：本地全文**（原件已落 `raw/papers/attack-detection/lamda-related/2026-Feng-FOREVER-遗忘曲线启发的记忆回放.pdf`，MinerU 转换 `wiki/papers/attack-detection/lamda-related/2026-Feng-FOREVER-遗忘曲线启发的记忆回放-全文.md`；INDEX/结构化笔记登记待主代理验收）。
- **方向 B 的直接强先例，两个组件都落在「回放强度随训练进程变化」上**：
  1. **When to replay（§2.1, md 行 71–113）**：Ebbinghaus 间隔序列 $\mathcal D_{\text{human}}=\{1,2,4,7,15,30,...\}$（**间隔递增曲线，先密后疏**）映射到「模型时间」轴（参数更新幅度累积 $\tau_t$），$\tau_t$ 触到阈值即触发回放（触发判据 md 行 107）。
  2. **How to replay（§2.2, md 行 115–157）**：以近期更新强度 $\mu_t$ 与基线 $\mu_0$ 之比（instability ratio $r_t$）调制回放正则强度，clip 至 $[g_{\min},g_{\max}]=[0.5,3.0]$（超参见 md 行 179）。原文（md 行 157）：「applies **stronger constraints when the model undergoes rapid changes** and **relaxes replay as learning stabilizes** ... **without relying on fixed replay weights or hand-crafted schedules**」。
- **把「静态回放权重」当靶子**（摘要与引言, md 行 27）：「Existing approaches typically rely on hand-crafted replay heuristics, such as **uniform replay intervals or static replay weights**」——这句可直接作主代理论证「常数 m 不够」的对照文献句。
- **效果（Table 1, md 行 189）**：Standard CL 上 FOREVER OP **72.9** vs Fixed-interval Replay **65.1**（+7.8），BWT −4.7 vs −9.2；SuperNI OP 42.1 vs 34.7。**其基线里就有 Fixed-interval Replay 与 MixReplay——「调度 vs 固定」正是它的实验设计本身**。
- **引用链（md 行 29）**：Zhong et al. 2024、Chen et al. 2025a、Kang et al. 2025a 已做 Ebbinghaus 式 spaced replay（按训练步数）——**间隔重复调度 2024 年起已成串**，FOREVER 的增量只是换时间轴。
- **适用边界**：LLM CL（0.6B–13B，LoRA，每任务存 2% 数据）；分配的是「回放触发时机 + 正则强度」，不是每样本复用次数 $m$；与监督式小缓冲 CL 的直接迁移需再核。

#### ③ Kong, Liu, Qiao, Wang, Tao, "Trust-Region Adaptive Frequency for Online Continual Learning"（IJCV 2023, DOI 10.1007/s11263-023-01775-0，被引 17）

- **证据等级：本地全文**（原件已落 `raw/papers/attack-detection/lamda-related/2023-Kong-在线持续学习的信任域自适应频率.pdf`，MinerU 转换 `wiki/papers/attack-detection/lamda-related/2023-Kong-在线持续学习的信任域自适应频率-全文.md`；INDEX/结构化笔记登记待主代理验收）。
- **它调度什么**：方法名 TRAF——交替进行标准过程（当前数据与 coreset 交错训练）与 intra-process（**仅用 coreset 训练**）；**intra-process 的触发频率随训练进程动态调整**（§4.1–4.2，md 行 129–159）：触发函数 `mod(k, inv)`，inv 越大频率越低；以当前 batch 平均置信度分数是否高于阈值 $\epsilon_{\mathrm{fre}}$ 判定当前任务是否进入后期（coreset 更平衡），是则减小 inv（**提高复用频率**）、否则增大。
- **调度方向（对主代理「由小到大」形态的对应）**：当前任务早期 intra-process 频率低、**后期频率高**——复用强度随任务内训练进程递增（md 行 139：coreset 类分布在当前任务后期更均匀，故应更频繁触发）。
- **「变数优于常数」的同篇消融（§实验, md 行 246）**：「using **adaptive frequency** can achieve higher ACCs (**relative improvement of at least 4.38%**) and lower FTs than using **constant frequency (any integer between the range 2, 5)**」——在 Task-Free 设定、排除 CCS 与 DKD 组件的公平对比下，**自适应频率优于 2–5 范围内任何常数频率**。这是「$m(t)$ 优于常数 $m$」的直接实验证据（在线 CL 场景）。
- **适用边界**：online CL（单遍数据流、Split MNIST/CIFAR-10/CIFAR-100/TinyImageNet，coreset 200–1000）；调度对象是「仅对 coreset 训练的阶段的触发频率」，即 coreset 样本的复用强度——**与主代理方向 B 在对象层同构，但调度信号是置信度反馈，不是预定义曲线**。

#### ④ Krawczyk & Gepperth, "An analysis of best-practice strategies for replay and rehearsal in continual learning"（CVPR Workshops 2024, DOI 10.1109/cvprw63382.2024.00423，被引 29）

- **证据等级：本地全文**（原件已落 `raw/papers/attack-detection/lamda-related/2024-Krawczyk-重放与排练最佳实践策略分析.pdf`，MinerU 转换 `wiki/papers/attack-detection/lamda-related/2024-Krawczyk-重放与排练最佳实践策略分析-全文.md`；INDEX/结构化笔记登记待主代理验收）。
- **性质**：系统对比「回放比例/权重的配置策略」的实验研究——**正是方向 A 所问「文献里哪一种居多」的同类工作**。
- **三种策略的显式定义（§2.3, md 行 78–92）**：定义参数 $\chi_\mathcal M$ =「**the proportion of replayed samples at each task**」（每任务回放样本比例——即回放强度配置量）：
  - **balanced**：重放生成量随已见类数**线性缩放**（md 行 84），保证每个 mini-batch 内各类样本量相同；
  - **constant**：$\chi_\mathcal M = 0.5$ 固定（md 行 90）——**常数回放比例**；
  - **weighted**：给真实/生成样本分设损失权重 $w_{i,R},w_{i,M}$（md 行 92），按任务数（task-weighted）或按类数（class-weighted）两种变体。
- **结论（§结论, md 行 187）**：「**Balanced replay performs best** ... across virtually all dataset splits and generative replay methods ... The other weighting schemes we tested can be competitive for some datasets, but perform generally worse.」——**「把回放构成按需放大」优于「用损失权重补偿」**。对 ER 单独一条（md 行 148）：显式损失加权在长任务序列上有益。
- **留给未来的恰好是方向 B**（md 行 177）：「It would also be interesting to investigate whether there is a **perfect timing for replaying** certain aspects of the data as discussed in [26], and combine this with a dynamically balanced replay mechanism」——Krawczyk & Gepperth 把「回放时机调度」明确列为未做、引向 Klasson 等的 scheduling 工作。
- **适用边界**：其「weighted」是**损失权重**而非复用次数权重；「constant/balanced」是**回放生成量/构成比例**而非每样本重复次数。对象多为生成式回放（DGR：cVAE/cGAN/WGAN）+ ER。

### E.6 代理 E 最终判定

#### 方向 A 判定：**部分先例（先例集中在「动机」与「相邻量」，显式 per-task/per-year 复用次数分配未见同款）**

- **有先例的部分**（全部全文核验）：
  1. 「不同类/任务需要不同重复量」的**动机**已被多次陈述：Bagus 2021（早期任务样本回放更频繁、建议 additional weighting，md 行 276）；Hemati 2023（少出现的类需要更多重复、频繁类被流自然重复，md 行 109）；Krawczyk 2024（balanced/constant/weighted 三种回放配置的对比本身）。
  2. 「按类逆频率分配**存储槽位**」已有直接实现（Hemati 的 FA；Chaudhry 2019 的类平衡选择；被引 199 的 partitioning reservoir）——**文献里「分配」的默认落点是槽位，证据确凿**。
  3. 「按任务数/类数缩放**回放构成比例**」已有实现与对比（Krawczyk 的 balanced，最优；weighted 损失权重，通常更差）。
- **未见同款的部分**（已核范围内）：把「**每个年度（任务）的缓冲样本重复次数 $m_s$**」作为一等分配量、且与固定存储预算 $B$ 联合配置的显式机制，未在任何已核全文中出现。最近邻依次是：Krawczyk 的 $\chi_\mathcal M$（全局比例、按策略形状变）、Klasson 的跨任务构成调度（对象是记忆构成而非重复次数）、Zhang 的 RL-K（全局标量随时间变）。**此判断仅限已核语料，见 E.7 检索面与 E.8 疑点。**

#### 方向 B 判定：**已有直接先例，且「变数优于常数」有同篇消融证据——不能立为创新主张，只能作设计选择**

- TRAF（IJCV 2023）：置信度反馈调复用频率，**自适应 vs 2–5 内任意常数，相对提升 ≥4.38%**（md 行 246）。
- FOREVER（ACL 2026）：Ebbinghaus 间隔递增调度（1,2,4,7,15,30 天映射到模型时间）+ 更新强度自适应正则；基线含 Fixed-interval Replay，**Standard CL 上 +7.8 OP**（md 行 189）；且把「static replay weights」点名为要打破的现状（md 行 27）。
- Zhang 2022（RL-RAR）：RL 按训练阶段在线调 K（1–20 档），变数版 29.2 vs 常数 K=10 的 27.3（md 行 585），动机明确写「overfitting 程度随训练阶段变化」（md 行 141）。
- Klasson 2022：MCTS/RL 调度回放记忆的跨任务构成，**优于均匀回放**（结论节）。
- 调度曲线形状实测分布：FOREVER 用**间隔递增（先密后疏）**；TRAF 用**任务内由低到高**（置信度反馈）；RL-RAR 无预定义曲线（反馈控制）；Klasson 由搜索产生无固定形状。**「预定义解析调度曲线（线性/指数）+ 监督式小缓冲 CL」的组合在已核语料中未见——但这属于设计空间选择，不构成创新主张。**

### E.7 检索面记录（代理 E）

| 工具/库 | 查询式 | 结果 |
| --- | --- | --- |
| Zotero 语义检索 | `adaptive replay frequency allocation weighting rehearsal continual learning` | **零有效命中**（返回全为多任务学习/大模型无关条目） |
| scholar CLI | `adaptive replay frequency continual learning` | 命中 TRAF、L2R、AdaER（Top3） |
| scholar CLI | `replay schedule continual learning` | 命中 FOREVER、Klasson 2209.08660（Top2） |
| scholar CLI | `per-class replay frequency sampling continual learning` | 命中 Hemati（Frequency-Aware Replay）、Dynamic replay training、Class-wise balancing、Prototype-guided、partitioning reservoir |
| scholar CLI | `importance weighted rehearsal memory continual learning` | 命中 Rolnick、Rehearsal revealed、CoPE（Online coreset selection）、**Krawczyk best-practice 2024** |
| scholar CLI | `Frequency-Aware Replay class-incremental` | 确认 Hemati 2023 = PMLR v232（CoLLAs） |
| scholar CLI | `Krawczyk Gepperth best-practice...` | 确认 CVF 路径为 CLVISION（此前 CLVision 404 的原因） |
| arXiv API | `ti:"Class-incremental learning with repetition"`、`all:"Frequency-Aware Replay"`、`ti:"AdaER"` 等 | **零命中**（Hemati 在 PMLR 不在 arXiv；AdaER 无预印本） |
| Crossref API | 两篇题名查询 | 确认 Krawczyk CVPRW 2024 DOI；Hemati 未命中 |
| Semantic Scholar API | 同上 | **429 限流**，未取得 |
| WebSearch | `"Class-incremental learning with repetition" "Frequency-Aware Replay"` | **返回训练记忆而非真实检索结果**（其自述无法浏览），全部丢弃 |
| CVF Open Access | Krawczyk PDF | 首试 `CLVision` 路径 404，改 `CLVISION` 成功（教训：CVF workshop 目录名全大写） |
| ScienceDirect | AdaER AM 链接 | 返回 HTML 拒绝页，未取得全文 |
| OpenAlex | — | 本日额度已耗尽（主代理已报），未使用 |

**新入库原件（4 份，MinerU 全文已转换，INDEX/结构化笔记登记待主代理验收）**：
`raw/papers/attack-detection/lamda-related/` 下 `2023-Hemati-类增量学习中的重复.pdf`、`2026-Feng-FOREVER-遗忘曲线启发的记忆回放.pdf`、`2023-Kong-在线持续学习的信任域自适应频率.pdf`、`2024-Krawczyk-重放与排练最佳实践策略分析.pdf`；对应 `wiki/papers/attack-detection/lamda-related/*-全文.md` 四份。

### E.8 未关闭疑点

1. **AdaER（Neurocomputing 2024，被引 83）未取全文**——其片段「The frequency of replaying experience is set to be the same as the …」疑似「回放频率与新样本接收频率对齐」类设计；若其对齐的是**随任务数变化的接收频率**，则构成方向 A/B 的又一先例。被引数高，**建议主代理走机构订阅补全文**。
2. **L2R（Pattern Recognition 2026）未取全文**——「closed-loop ... adjusts replay frequency and intensity」两轴均点名；ScienceDirect 无开放获取。等级：仅题录+摘要片段。
3. **Klasson 2022 的任务维度与 LAMDA 的 12 年份任务的适配**：其调度对象是「回放记忆的跨任务构成比例」，在 Domain-IL 12 任务设定下等价于「按年度分配回放构成」——与本课题模块一（位置分配）交界，需主代理判断它是否已占据模块一的一部分。
4. **「per-year $m_s$ 显式分配」的否定性结论只覆盖已核语料**（scholar 前 8 条/查询 × 5 查询式 + 4 篇新全文引文网络）；未做引文正向追踪（谁引用了 TRAF/FOREVER）与逆向追踪（它们引用谁），如需把「未见」升级为「无」，需再做一轮引文网络追踪。
5. **FOREVER 引用的 Zhong et al. 2024 / Chen et al. 2025a / Kang et al. 2025a（Ebbinghaus 式 spaced replay）未逐篇核**——若主代理要写「间隔重复调度已成串」，这三篇需补全文。
