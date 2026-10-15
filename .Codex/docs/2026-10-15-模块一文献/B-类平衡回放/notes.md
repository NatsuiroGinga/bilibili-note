# B-类平衡回放：逐篇判读笔记

> 判读参照：我们的配额臂 = 年度间等额（⌊N/k⌋/年）+ 年度内标签分层（正负各半，正例不足由负例补足）。寻找文献中「分层 vs 不分层」的直接消融。

---

## 论文 6：Hemati et al. 2023, Class-Incremental Learning with Repetition (CIR + ER-FA)

- 原件：`raw/papers/attack-detection/lamda-related/2023-Hemati-类增量学习中的重复.pdf`（19 页）
- 全文来源：`wiki/papers/attack-detection/lamda-related/2023-Hemati-类增量学习中的重复-全文.md`（MinerU extract 转换，2026-10-14 已入库）
- 证据等级：**全文已核**（页码待回原件核对，见下方待办）

### 1. 平衡做在哪一层

**类别层**（class-level），针对「类在流中的重复频率」做配额，不是任务层、不是时间层。他们把不平衡定义为 CIR 流中类重复频率的双峰分布（frequent vs infrequent 类），与「标签天然不平衡」不同——流本身可以从平衡数据集（CIFAR-100）构造出不平衡的重复结构。

### 2. 规则与公式（Frequency-Aware 存储，Algorithm 3，附录 E）

对已见类集合 C、每类观测次数 O[c]、缓冲容量 M：

- 每类配额（观测次数取倒数）：$Q = [1/O[c],\ \forall c \in C]$
- 归一化：$\hat{Q} = Q / |Q|$
- 每类槽位数：$S = [\hat{Q}[c] \cdot M,\ \forall c \in C]$
- 未用满的槽位由更频繁的类按观测次数排序填充（保证缓冲不空）

对比的另两种存储策略：**CB**（每类固定配额）与 **RS**（Vitter 1985 蓄水池，缓冲内类频率复制流内频率，即**不做任何分层**）。

### 3. 「分层 vs 不分层」直接消融：**有，且是最直接的一篇**

Table 2（正文第 4.4 节，约印刷页 8；待核对）：ER / ER-ACE / DER 三种策略 × RS / CB / FA 三种缓冲，CIFAR-100 与 TinyImageNet，双峰不平衡流（infrequent 类重复概率 0.1，frequent 1.0），Fraction = 不频繁类比例 ∈ {0.1, 0.3, 0.5}，3 种子平均，缓冲 2000/4000。

**RS vs CB 的差 = 「按类分层 vs 不分层」的作用量级**（MCA = 缺席类精度，ACA = 全类平均精度）：

| 数据集 | Fraction | ER-RS MCA | ER-CB MCA | ΔMCA | ER-RS ACA | ER-CB ACA | ΔACA |
|---|---|---|---|---|---|---|---|
| CIFAR-100 | 0.1 | 11.4±0.9 | 30.9±2.7 | **+19.5** | 57.7±0.7 | 59.5±0.1 | +1.8 |
| CIFAR-100 | 0.3 | 16.7±3.6 | 34.5±1.7 | **+17.8** | 51.1±0.4 | 55.3±0.1 | +4.2 |
| CIFAR-100 | 0.5 | 20.5±1.9 | 35.7±0.5 | **+15.2** | 45.6±0.8 | 52.0±1.5 | +6.4 |
| TinyImageNet | 0.1 | 3.7±0.6 | 10.4±0.2 | **+6.7** | 31.8±1.2 | 32.2±0.7 | +0.4 |
| TinyImageNet | 0.3 | 4.4±0.7 | 10.0±1.0 | **+5.6** | 28.1±0.2 | 28.8±0.2 | +0.7 |
| TinyImageNet | 0.5 | 6.0±0.1 | 11.0±0.2 | **+5.0** | 24.0±0.1 | 26.0±0.3 | +2.0 |

模式：类平衡在**少数类（缺席类）精度上有大增益，全类平均精度增益小**；且存在反例——ER-ACE 在 TinyImageNet 上 CB/FA 的 ACA（25.7/24.3）低于 RS（26.0），FA 用频繁类精度换不频繁类精度。**平衡不是免费的，在 ACA 上可能小幅为负。**

附录 E.2（Figure 19）进一步给出：Fraction→100%（全类同频）时三种策略配额收敛一致——**平衡策略的收益随不平衡程度下降而消失**。这直接支持「不平衡流是分层起作用的前提」。

### 4. 数据集与设定

- CIFAR-100、TinyImageNet（附录另有 MNIST），ResNet-18，Avalanche 框架
- 在线 experience 流（N=500 长流），存储约束：缓冲 2000（CIFAR）/4000（Tiny）
- 不平衡是**人工构造的重复频率双峰**，不是天然标签不平衡；无时间漂移概念、无恶意软件
- 二分类？否，C 类多分类（CIFAR-100 有 100 类）

### 5. 证据等级与页码

- 全文已核（wiki 转换全文）；Table 2、Figure 19、Algorithm 3 位置需回 PDF 原件核对页码
- 待办：核对 Table 2 所在印刷页、FA 公式所在页

### 与我们的关系（初判）

- 他们分层在「类重复频率」维度，我们在「标签 × 年度」二维。共同点：都是**在缓冲内对某一维做配额化**，且对照都是「全局蓄水池（RS，不分层）」。
- 他们证明的是：**流分布不均匀时，缓冲分布复制流分布（RS）是次优的**——这一逻辑可直接迁移到「年度间流量分布不均匀、年度内正负不均匀」的论证。
- 他们**没有**做过「时间维度分层」——「按时间/年度分桶」在他们框架里不存在（重复是随机的，无时间结构）。我们的年度维度是文献空白的一部分。

---

（后续论文逐篇追加）

---

## 论文 1：Chrysakis & Moens 2020, Online Continual Learning from Imbalanced Data (CBRS)

- 原件：`raw/papers/attack-detection/lamda-related/2020-Chrysakis-CBRS-Online-Continual-Learning-Imbalanced-Data.pdf`（10 页）
- 全文来源：MinerU extract 转换 `/tmp/b-class-balance-replay/2020-Chrysakis-CBRS-Online-Continual-Learning-Imbalanced-Data.md`（2026-10-15，云端 API，本机零计算）
- 证据等级：**全文已核**（表格页码待回 PDF 核对，见文末待办）
- 发表信息：ICPR 2020（原 arXiv:2003.06271）

### 1. 平衡做在哪一层

**类别层**。在线 CL、无任务边界、流高度不平衡且时间相关。他们明确把「缓冲内按类平衡」作为存储策略，与时间/任务维度无关——流是单类任务流（每任务一个类），但算法本身不知道任务边界。

### 2. 规则与公式

**CBRS（Algorithm 1）**：缓冲未满时全存；满后收到实例 $(x_i, y_i)$：
- 若 $c \equiv y_i$ **不是** full 类（当前最大类）：新实例**替换最大类中的一个随机实例**（平衡化机制，向少数类倾斜）
- 若 $c \equiv y_i$ 是 full 类：以概率 $m_c/n_c$ 替换同类随机存储实例（$m_c$ = 类 c 当前存储数，$n_c$ = 流中已见类 c 实例数）——同类内即标准蓄水池

两条性质（正文 §2.2）：
1. 流中实例数 $< m/n_c$ 的类**全量入缓冲**，一个不丢；
2. 每类内部存储子集对同类流实例 iid（保留蓄水池的无偏性，只是改了**类间配额**）。

配套 **weighted replay**（§2.3）：回放某实例的概率与同类存储数成反比（少数类回放概率高）。

训练损失（式 1）：$\mathcal{L} = a\mathcal{L}_s + (1-a)\mathcal{L}_r$，$a = 1/n_c$（无任务边界时按已见类数递减）。

### 3. 「分层 vs 不分层」直接消融：**有，且有三处，是全部文献中最干净的**

不平衡构造（§3.2）：每类保留因子 $\mathbf{r} = (10^{-2}, 10^{-1.5}, 10^{-1}, 10^{-0.5}, 10^{0})$，类间不平衡最小约 3:1、最大 100:1。所有方法在**同一组不平衡流**上比较，10 runs 95% CI。

**(a) Table 1（主对比，RESERVOIR vs CBRS，均用 weighted replay 以隔离存储策略差异）**：

| 方法 | MNIST | F-MNIST | CIFAR-10 | CIFAR-100 |
|---|---|---|---|---|
| RESERVOIR | 67.9±3.0 | 64.1±1.8 | 54.7±2.2 | 28.1±1.2 |
| CBRS | **83.3±2.5** | **75.0±2.5** | **73.4±2.2** | **40.2±1.0** |
| Δ（类分层 − 不分层） | **+15.4** | **+10.9** | **+18.7** | **+12.1** |

（缓冲 m=500/1000；GSS 为 74.2/64.9/63.3/23.0）

**(b) Table 2（缓冲大小扫描，Fashion-MNIST）**：CBRS 全胜，**小缓冲差距更大**：
- m=100：RESERVOIR 53.7 vs CBRS 66.5（**+12.8**）
- m=500：64.3 vs 75.8（+11.5）
- m=1000：68.2 vs 76.7（+8.5）
- m=5000：75.2 vs 77.1（+1.9）

**(c) Table 3（消融：存储端分层 × 回放端加权重采样，MNIST/CIFAR-10 × m=1000/5000）**：

| 设置（MNIST, m=1000） | uniform replay | weighted replay |
|---|---|---|
| RESERVOIR（不分层） | 71.3±2.0 | 76.3±2.8 |
| CBRS（分层） | **86.0±2.6** | 86.1±2.6 |

**两个决定性结论**：
1. **存储端分层的作用 > 回放端重采样的作用**：CBRS(uniform) 86.0 远超 RESERVOIR(weighted) 76.3——把缓冲先摆平衡，比事后用加权重采样补偿更根本；
2. **缓冲平衡后加权重采样无增益**：CBRS 86.0→86.1（≈0），RESERVOIR 71.3→76.3（+5.0）——weighted replay 只是部分掩盖存储端的不平衡，掩盖不彻底。反向印证：若我们的配额已保证年度内正负各半，回放端不需要再加权。

另有一个反直觉细节（§3.6）：m=5000 时 CBRS(uniform) MNIST 85.6 < m=1000 的 86.0——**缓冲越大、严重不平衡流灌入越多，类间反而更难平衡**。平衡配额在小缓冲下更容易维持。

### 4. 数据集与设定

- MNIST、Fashion-MNIST、CIFAR-10、CIFAR-100（图像），MLP / ImageNet 预训练 ResNet-18
- **在线流**（batch=10，每 batch 5 步更新，不可回访），缓冲 m=500/1000
- 不平衡为**人工构造**（保留因子随类随机指派，每次 run 不同）；单类任务流，时间相关性极强
- 无恶意软件、无二分类、无天然时间漂移域；不平衡在**类间**而非时间域间

### 5. 证据等级与页码

- 全文已核；Table 1（§3.4）、Table 2（§3.5）、Table 3（§3.6）、Algorithm 1（§2.2）页码待回 10 页 PDF 原件核对

### 与我们的关系（初判）

- **可比性最好的一篇**：他们的「严重不平衡 + 时间相关流」与我们的年度流结构同型（都是 temporally correlated 的不平衡流，都无任务边界）。
- 直接支持：**缓冲内按标签分层优于全局蓄水池**，且不平衡越重、缓冲越小，增益越大（我们缓冲 ⌊N/k⌋/年，若 k 小则年配额小——小缓冲场景正是分层增益最大的区域）。
- Table 3 说明：若配额臂已做存储端分层，回放端不必再加权——提示我们的消融若含「分层 × 加权回放」需注意两者的替代关系。
- **空白仍在**：他们分层只按类；「按时间/年度分桶等额」不在其设计空间内。其流是单类任务流，年度间等额与类内分层从未被同时分离。

---

## 论文 2：Liu, Liu & Cui 2024, Prior-free Balanced Replay (PBR)——ACM MM 2024

- 原件：`raw/papers/attack-detection/lamda-related/2024-Park-PBR-Prior-Free-Balanced-Replay.pdf`（10 页）
- 全文来源：MinerU extract `/tmp/b-class-balance-replay/2024-Park-PBR-Prior-Free-Balanced-Replay.md`（2026-10-15）
- 证据等级：**全文已核**（页码待核对）
- **题录警示**：文件名作 "2024-Park"，但正文 ACM Reference Format 实际作者为 **Lei Liu（CUHK-Shenzhen）、Li Liu（HKUST-GZ）、Yawen Cui（PolyU）**，DOI 10.1145/3664647.3681106。文件名作者与正文不符，引用时以正文为准。

### 1. 平衡做在哪一层

**类别层**，但**间接实现**（"prior-free"）：不显式按标签配额，而是用不确定性引导的蓄水池优先存少数类样本——依据是「少数类样本预测不确定性更高」（§3.1 动机实验：少数类遗忘更陡、分类器权重幅值偏向旧多数类、少数类聚集在任务边界）。

他们明确与 CBRS（Chrysakis & Moens 2020，引文 [9]）划界：CBRS 做「类平衡配额」但「忽视缓冲内不同样本的不等角色」；PBR 做「样本不确定性优先」。两者互补。

### 2. 规则与公式

不确定性引导蓄水池（在**每个任务结束时**执行，非逐样本在线）：
- Candidate（式 3）：$\mathcal{K} = \arg\min_{(x,y)\in D_c} \mathbb{I}[y,\theta \mid x, D_c]$——选**互信息最小**（最不确定）的样本；MI 由 MC-dropout 预测熵近似（式 5–7）
- Sample-In（式 4）：$\mathcal{P}(\mathcal{K}) = |\mathcal{M}| / (N_c + \sum_i^{c-1} s_i w_i)$，$w_i = e^{-s_i}/\sum_j e^{-s_j}$（$s_i$ = 任务 i 的运行频率）——隐式在新旧任务间折中
- Sample-Out：被移除样本服从缓冲上均匀分布 $1/|\mathcal{M}|$
- 附加组件：cosine 原型约束（式 9–10，归一化分类器 + 原型蒸馏）与边界约束（式 11–13，MCE + KL 蒸馏）

### 3. 「分层 vs 不分层」直接消融：**没有干净的「类平衡配额 vs RS」消融**

- Table 2 与 Table 5 有 **"Ours - Random"（随机蓄水池）vs "Ours - Uncertainty"（不确定性引导）** 的直接对比：Seq-CIFAR-10-LT Class-IL，buffer 200：44.77±1.23 vs **51.00±1.74**（**+6.23**）。但两者都是其完整框架（含 cosine 分类器 + 双约束），这组消融隔离的是「不确定性选样」的作用——由于「少数类不确定性高」，它**隐含**了少数类优先，却不是显式按标签配额，不能直接读作「类平衡 vs 不平衡」的量级。
- Table 5 分解：random+linear 33.21 / random+cosine 44.77 / uncertainty+linear 33.66 / uncertainty+cosine 51.00。cosine 分类器贡献大于不确定性选样（+11.56 vs +6.23）。
- Table 4（少数类任务精度，Task-3/4/5）：SGD 28.23/29.76/37.20 → Ours 48.75/46.52/58.66（+20.5/+16.8/+21.5），但对照是不带任何缓冲的 SGD，不是 RS。
- **结论：PBR 全文没有「显式类平衡配额 vs 全局蓄水池」的干净对照**；它把 CBRS 作为相关工作引用而不在实验中复现对比。

### 4. 数据集与设定

- Seq-CIFAR-10-LT、Seq-CIFAR-100-LT、Seq-TinyImageNet-LT（按 [28] 人工长尾化，IR=0.01/0.02/0.05/0.1），ResNet-18 **随机初始化**（无预训练），batch 32，SGD
- **离线任务序列**（每任务一个数据集，采样在任务末执行）——**不是在线单遍流**，与我们的年度在线流设定不同
- 有缓冲（200/500）；ordered-LTCL（任务按样本数排序）与 shuffled-LTCL 两种
- 无恶意软件、无时间漂移域

### 5. 证据等级与页码

全文已核；Table 2（p.5 附近）、Table 5（§4.4，p.6 附近）、式 3–7（§3.2，p.3–4）待回原件核对。

### 与我们的关系（初判）

- 对「标签分层是否有用」的**增量证据弱于 CBRS**：其正增益来自不确定性选样与原型约束的混合，无法拆出「平衡」本身。
- 可引用的价值点：(a) 少数类更易被遗忘、更聚集在决策边界（其 §3.1 动机实验）——支持「少数类（恶意样本）必须被优先保留」；(b) 其与 CBRS 的互补划界（配额层 vs 样本层）印证「缓冲内分层」是文献公认的一层设计轴。
- 空白不变：无时间维度分层。

---

## 论文 3：Rahman, Coull, Yu & Wright（MADAR, Distribution-Aware Replay for Malware）——IEEE 格式 13 页

- 原件：`raw/papers/attack-detection/lamda-related/2025-Rahman-MADAR-Distribution-Aware-Replay-Malware.p.pdf`（13 页）
- 全文来源：MinerU extract `/tmp/b-class-balance-replay/2025-Rahman-MADAR-Distribution-Aware-Replay-Malware.p.md`（2026-10-15）
- 证据等级：**全文已核**（页码待核对）
- 场景匹配度：**与我们的设定最接近的一篇**——恶意软件、二分类 Domain-IL、按月/按年分任务（EMBER 按月 12 任务、AZ 按年 2008–2016 共 9 任务）、有存储预算。

### 1. 平衡做在哪一层

**三层嵌套分层，全部在缓冲/回放集合内**：
- **标签层**：预算 β 按 γ 拆分 $\beta_G = \gamma\beta,\ \beta_M = (1-\gamma)\beta$（式 1）。**γ 跟随数据实际不平衡比例**：EMBER（约 1:1）用 γ=0.5，AZ（9:1 goodware:malware）用 **γ=0.9**——即**在标签维度上维持自然比例，不强制再平衡**。
- **家族层**（仅恶意类内部）：Ratio 预算 $\mathcal{B}_f = \frac{|X_f|}{|X_{mal}|}\beta_M$（跟随家族比例）或 Uniform 预算 $\mathcal{B}_f = \frac{\beta_M}{|\mathcal{F}|}$（强制家族平衡）。
- **家族内层**：IF（Isolation Forest，$C_r=0.1$）把家族预算再拆为代表样本 $|S_f| = \alpha\mathcal{B}_f$ 与异常样本 $|A_f| = (1-\alpha)\mathcal{B}_f$，α=0.5 最优。

**没有时间/年度维度**：数据池 P 全局累积，跨年不隔离；按年分任务只是训练顺序。

### 2. 显式对照：GRS（全局蓄水池）

他们把 **Global Reservoir Sampling（GRS）**作为正式 baseline：「provides an unbiased sampling of the underlying class distributions and serves as a strong point of comparison for our distribution-aware approach」（§IV.D）。GRS = 从全局池随机抽 β 个，类频率复制池内频率——**正是「不做任何分层」的对照**。

### 3. 「分层 vs 不分层」直接对照结果：**分层在 Domain-IL 几乎无增益**

**Domain-IL（二分类、时间任务，与我们同构）**——MADAR-R vs GRS（全局平均精度 AP）：

| 预算 | EMBER GRS | EMBER MADAR-R | AZ GRS | AZ MADAR-R |
|---|---|---|---|---|
| 1K | 93.6±0.3 | 93.7±0.1 | 95.3±0.1 | 95.8±0.1 |
| 10K | 94.1±1.3 | 94.7±0.1 | 96.4±0.1 | 96.6±0.1 |
| 50K | 95.3±0.2 | 95.4±0.1 | 96.9±0.1 | 96.9±0.1 |
| 100K | 95.3±0.7 | 95.3±0.6 | 97.1±0.1 | 97.0±0.1 |
| 200K | 95.9±0.1 | 96.0±0.1 | 97.1±0.1 | 97.0±0.1 |
| 400K | 96.0±0.3 | 96.1±0.1 | 97.2±0.1 | 97.0±0.1 |

**差距 ≤0.6pp，多数在 0.1–0.2pp，大预算端甚至反超（AZ 100K–300K GRS 略优）**。正文自认（§VII.D）：「GRS remains a strong baseline at high budgets... GRS performs comparably at higher budgets, particularly in Domain-IL. This suggests that distribution-aware replay is most impactful when the number of available samples per class is limited」。

**但必须同时记录两个限定**：
1. 他们的标签层 γ=0.9/0.5 **复制了自然比例**，与 GRS 在标签维度上等价——Domain-IL 里真正的差异只在家族层与代表/异常层。**「强制再平衡标签」（如 AZ 上 γ=0.5）从未被测试**；
2. 因此 Domain-IL 的「分层≈无增益」应读作「**跟随自然比例的分布感知 ≈ 无增益**」，不能读作「强制标签再平衡无效」——后者在本文与全部 8 篇中都没有实验。

**Class-IL（家族长尾多分类）**——分层增益大且集中于小预算：
- EMBER Class-IL（Table IV）：budget 100：GRS 51.9 vs MADAR-R 68.0（**+16.1**）；500：70.3 vs 76.5（+6.2）；1K：75.4 vs 79.4（+4.0）；20K：84.6 vs 86.2（+1.6）。
- AZ Class-IL（Table V）：100：43.8 vs 59.4（**+15.6**）；500：62.9 vs 70.4（+7.5）；1K：70.2 vs 76.2（+6.0）；20K：89.1 vs 91.5（+2.4）。

**Ratio vs Uniform = 「跟随比例 vs 强制平衡」的直接对照（同一分层维度的两种配额）**：
- Domain-IL（输出=二分类标签）：Ratio 略优（§VII.D「ratio-based selection performs best in Domain-IL」）；
- Class-IL/Task-IL（输出=家族多分类）：**Uniform 显著更优**（EMBER 1K：Ratio 76.0 vs Uniform 79.4；AZ 20K：Ratio 89.1 vs Uniform 91.5）；
- 规律：**强制平衡的收益出现在「被平衡的维度就是分类输出维度」时**。

### 4. 数据集与设定

- EMBER 2018（Windows PE，2381 维手工特征，40 万 goodware + 35 万 malware）；AndroZoo（Android，Drebin 特征，AZ-Domain 80690 malware + 677756 goodware **9:1 不平衡**，按年 9 任务）
- MLP（非预训练），10–15 次随机初始化重复；预算 β ∈ {1K…400K}（Domain）/ {100…20K}（Class/Task）
- **离线任务序列**（每任务可完整训练），非在线单遍流；评估为各任务留出集上的全局平均精度
- Table I（EMBER 月度 goodware/malware 数）显示**月度标签比例波动**（如 10 月 29955/56459，11/12 月人工平衡的 50000/50000）——现实月份流中正负比例不恒定，可作「按标签分层」的现实动机参照

### 5. 证据等级与页码

全文已核；Table I（§V，p.3 附近）、Algorithm 1 与式 1–3（§VI，p.4–5）、Table II/III（Domain-IL，p.6–7）、Table IV/V（Class-IL，p.7–8）、Table VI/VII（Task-IL，p.8–9）、§VII.D（p.9）待回原件核对。

### 与我们的关系（初判）

- **最可迁移的一篇**：恶意软件 + 时间分任务 + 存储预算 + GRS 对照。
- 支持我们的部分：分布感知分层在**低预算**下有真实增益（Class-IL 数据）；分层维度的配额结构是文献中活的决策轴。
- **不利/警示我们的部分**：在二分类 Domain-IL 下他们的分布感知相对 GRS 增益 ≤0.5pp——若我们的年度流标签比例较稳定，标签分层的增益可能同样有限；**且他们从未测「强制再平衡标签比例」**，γ 参数只是跟随自然比例。
- Ratio vs Uniform 的规律（平衡维度=输出维度时强制平衡更优）是我们配额臂的一个可引用的间接依据，但需注明出自多分类场景。

---

## 论文 4：Mohamed 版 MADAR（Diversity-Aware Replay）——**确认为论文 3 的同文异版，非独立证据**

- 原件：`raw/papers/attack-detection/lamda-related/2025-Mohamed-MADAR-Diversity-Aware-Replay.pdf`（13 页）
- 全文来源：MinerU extract `/tmp/b-class-balance-replay/2025-Mohamed-MADAR-Diversity-Aware-Replay.md`（2026-10-15）
- **核验方式**：将两篇 MinerU 全文做归一化 diff（统一 diversity/distribution 术语后逐行比较，676 行差异，几乎全部为措辞改写、引文编号偏移与图片哈希不同）；抽查关键数字（93.6/95.3/96.9/97.2/85.8/91.5）两版均在且一致。
- **判定**：同一 MADAR 论文的两个版本（一版题名 "Distribution-Aware"、一版 "Diversity-Aware"，作者同为 Rahman/Coull/Yu/Wright，数据集、算法、全部实验表格一致）。**判读以论文 3（Rahman 版）为准，本篇不提供独立证据，不重复计数。**
- 影响：原阅读清单「两篇同族，注意区分」的预期成立——它们是同文异版，不是两篇独立工作。8 篇清单实际独立论文为 **7 篇**。

---

## 论文 5：Amalapuram, Channappayya & Tamma 2023, ECBRS + PAPA（网络入侵检测）

- 原件：`raw/papers/attack-detection/lamda-related/2023-Amalapuram-ECBRS-PAPA-Continual-NIDS.pdf`（14 页）
- 全文来源：MinerU extract `/tmp/b-class-balance-replay/2023-Amalapuram-ECBRS-PAPA-Continual-NIDS.md`（2026-10-15）
- 证据等级：**全文已核**（页码待核对；γ/缓冲消融在补充材料 `2023-Amalapuram-ECBRS-PAPA-Supplemental.pdf`，本任务未读）
- 场景匹配度：**二分类（benign/attack）Domain-IL 流**，任务由「良性数据切分 + 攻击类样本组合」构成并保持真实类不平衡——与我们的年度流二分类同构。

### 1. 平衡做在哪一层

**类别层（二分类）+ 少数类内部再分层**。ECBRS 是 CBRS（Chrysakis 2020）的扩展，处理「少数类之间也严重不平衡」时 CBRS 用缓冲内局部信息误判的问题。

### 2. 规则与公式

- 替换决策（Algorithm 1）：缓冲未满全存；满后若 $y_i$ 非 full 类，选「缓冲内最大类 ∧ 运行统计值（全局累计频率）最高 ∧ $m_c \ge \gamma(c)$」的类做替换对象；否则退到次高统计值类。full 类内部仍是蓄水池（$u \le m_c/n_c$）。
- 保护阈值（式 1）：$\gamma(i) = m \times w(i)$，$w(i) = \mathrm{softmax}(-n_i)$（负运行频率 softmax，偏向少数类），w 固定 0.1。**保证攻击类样本不被替换到阈值以下**。
- 与 CBRS 的第二处差异：replay 样本与流样本合并计算**单一损失**（CBRS 为两分量损失），实测更优——归因于合并后 batch 内类平衡更好。

### 3. 「分层 vs 不分层」直接消融：**主表里没有；但藏在 MIR 组合实验里**

- **Table 3 主表无 RESERVOIR（不分层）对照**：baseline 为 EWC/SI/GEM/A-GEM/GSS-greedy/MIR/CBRS/ECBRS/MIR+ECBRS。ECBRS vs CBRS 是「两种分层策略互比」，不是「分层 vs 不分层」。
- ECBRS vs CBRS（同为类平衡，比的是分层策略的精度）：在分布频繁偏移的 6 个基准（AnoShift、SVHN、CIFAR-10/100、CLEAR-10/100）上 PR-AUC(A) 平均 **+7%**、PR-AUC(B) 平均 **+3%**（§4.1）。但逐点看 AnoShift 仅 +0.005（0.949 vs 0.949/0.944），CLEAR-10 上 −0.4pp（0.941 vs 0.937）——平均增益被个别基准拉高。
- **间接对照 MIR vs MIR+ECBRS**：MIR 默认用随机内存填充（random memory population），换成 ECBRS 后：全基准平均 **+12%（PR-AUC(A)）/ +14%（PR-AUC(B)）**；大基准（AnoShift、CICIDS-2018、UNSW-NB15、CICIDS-2017）平均 **+30%/+31%**。单点最大：AnoShift 0.655→0.942（**+0.287**），CICIDS-2017 0.785→1.00（+0.215）。**这是入侵检测二分类场景下「缓冲类平衡填充 vs 随机填充」最强的一组证据，但它是「ECBRS+MIR 检索」的组合效果，不是纯存储策略隔离**（检索策略相同，差异只在填充策略）。
  - 注意甄别：MIR 的随机填充是否等价于蓄水池未明说（"random memory population method"），增益归因到「类平衡」时需保守。

### 4. 数据集与设定

- 入侵检测：KDDCUP'99、NSL-KDD（5 任务）、CICIDS-2017/2018（10 任务）、UNSW-NB15（9 任务）、CTU-13、**AnoShift（十年时间偏移，10 任务，OTDD=7189 为最大分布偏移）**；CV：SVHN/CIFAR/CLEAR-10/100（人工 1:100 类不平衡）
- 二分类 Domain-IL（benign vs attack，标签空间固定）；缓冲 M=1333–13333；75% 缓冲用于回放；batch 1024（大 NID 数据集）；5 次独立重复取均值
- 缓冲按池组织（无任务边界信息），在线任务自由设定

### 5. 证据等级与页码

全文已核；Table 1（p.2）、式 1 与 Algorithm 1（§3.1，p.3）、Table 2（p.4）、Table 3（§4，p.5）、Table 4/5（p.6）待回原件核对。

### 与我们的关系（初判）

- **正向**：在二分类安全检测流（benign/attack）中，把缓冲填充从随机换成类平衡，MIR 框架下平均 +12~14pp、大基准 +30pp——「缓冲内按标签配额」在安全域有强证据；
- **限定**：增益是「填充策略 × 检索策略」的组合，且其 CBRS/ECBRS 线从未与「纯蓄水池 + 同一训练流程」直接对照（CBRS 论文有该对照，见论文 1）；
- 该组的类不平衡程度极高（CICIDS-2018 少数类差距 2.1M），与我们年度流的实际不平衡幅度需对比后才可迁移。

---

## 论文 7：Aljundi et al. 2019, MIR（Maximally Interfered Retrieval）——检索策略对照

- 原件：`raw/papers/attack-detection/lamda-related/2019-Aljundi-MIR-Maximally-Interfered-Retrieval.pdf`（15 页）
- 全文来源：MinerU extract `/tmp/b-class-balance-replay/2019-Aljundi-MIR-Maximally-Interfered-Retrieval.md`（2026-10-15）
- 证据等级：**全文已核**（定位句已核，页码待核对）

### 1–2. 层次与规则

MIR 是**回放检索策略**（决定从缓冲里取什么回放），**不涉及存储端的标签分层**。原文明确固定存储为蓄水池：「We restrict ourselves to the use of reservoir sampling for deciding which samples to store」（§4.1 实验设置）。机制：对候选样本做虚拟参数更新，选使损失增加最大（被干扰最严重）的 C 个样本回放（sMI-2 准则，C=50）。

### 3. 分层消融：无（不在其设计空间）

全文以蓄水池为唯一存储策略，不比较任何分层/平衡存储。与「类平衡」的关系是正交轴：ECBRS 论文把两者组合（MIR+ECBRS）证明可叠加。

### 4. 设定

MNIST/Permuted-MNIST/CIFAR-10/CIFAR-100，在线流（batch 10 + 缓冲 10），存储用蓄水池。图像多分类，无恶意软件。

### 5. 与我们的关系

作为「检索轴」的对照策略定位：我们的配额臂改变的是存储轴；文献中检索轴（MIR/GSS）与存储轴（CBRS/ECBRS）可组合，说明两轴正交，配额臂的消融设计不需要控制检索策略（保持基线检索不变即可隔离存储分层的作用）。

---

## 论文 8：Aljundi, Lin, Goujaud & Bengio 2019, GSS——时间不平衡流下蓄水池的直接对照

- 原件：`raw/papers/attack-detection/lamda-related/2019-Wei-GSS-Gradient-Sample-Selection-Online-Continual-Learning.pdf`（13 页）
- 全文来源：MinerU extract `/tmp/b-class-balance-replay/2019-Wei-GSS-Gradient-Sample-Selection-Online-Continual-Learning.md`（2026-10-15）
- 证据等级：**全文已核**（Table 4 已核原文数字，页码待核对）
- 文件名警示：文件名作 "2019-Wei-GSS"，但论文作者是 **Rahaf Aljundi, Min Lin, Baptiste Goujaud, Yoshua Bengio**（NeurIPS 2019）。与 MIR 同一第一作者。引用时以正文为准。

### 1. 平衡做在哪一层

**不按标签**。GSS 按梯度空间多样性选样（solid angle 最小化），其「免疫不平衡」指的是**任务间（时间段间）样本数不平衡**——这恰是与我们「年度间不均匀」最相关的轴！

### 2. 对蓄水池的机制批判（§4.3，原文）

「Reservoir sampling is a simple replacement strategy... based on the underlying assumption that the overall data stream is i.i.d distributed. It would work well when each of the tasks has a similar number of examples. However, it could lose the information on the under-represented tasks if some of the tasks have significantly fewer examples than the others.」——**蓄水池在任务/时间段大小悬殊时会丢失欠表示时间段的样本**。这是「年度间等额」必要性的最直接文献依据。

### 3. 直接对照（Table 4）：**有数字**

设置：disjoint MNIST，某任务 2000 样本、其余各 200（10 倍悬殊），5 种序列，缓冲 300，3 runs，序列末平均精度：

| 方法 | Seq1 | Seq2 | Seq3 | Seq4 | Seq5 | Avg |
|---|---|---|---|---|---|---|
| Reservoir | 63.7±0.8 | 69.4±0.7 | 66.8±4.8 | 69.1±2.4 | 76.6±1.6 | **69.12±4.3** |
| GSS-IQP | 75.9±3.2 | 76.2±4.1 | 79.06±0.7 | 76.6±2.0 | 74.7±1.8 | 76.49±1.4 |
| GSS-Greedy | 71.2±3.6 | 78.5±2.7 | 81.5±2.3 | 79.5±0.6 | 79.1±0.7 | **77.96±3.5** |

蓄水池落后 **+8.84（Greedy 平均）**，Seq1（首任务欠表示）差距最大 63.7 vs 75.9/71.2；正文称改进最高达 15%。**限定**：GSS 的补救是梯度多样性选样，不是按时间段配额——它证明「时间不平衡伤害蓄水池」，但没有测「按时间分层配额」本身。

### 4. 设定

disjoint MNIST 在线流，缓冲 300，3 runs；另有 CIFAR-10 等（GSS-Greedy 效率与蓄水池同级）。无恶意软件、无标签不平衡实验（其 imbalance 均指任务大小）。

### 5. 与我们的关系

- 直接支持「年度间流量不均匀 → 全局蓄水池会被大年度淹没、小年度欠保留」这一机制前提（我们 ⌊N/k⌋ 等额的直接文献依据）；
- 但「按年度配额」这个具体补救在他们框架中不存在，其补救轴是梯度多样性。**「年度间等额 vs 全局蓄水池」的干净消融在文献中不存在**。

---

## 页码核对记录（2026-10-15，单页 MinerU 转换回原件核对）

| 论文 | 内容 | 页码 | 验证命中 |
|---|---|---|---|
| CBRS | Table 1 + Table 2 | **p.6** | 67.9/83.3/40.2/66.5 |
| CBRS | Table 3（消融） | **p.7** | 86.0/76.3/71.3/UNIFORM |
| CBRS | Figure 1 | p.4 | 图题文本 |
| PBR | Table 2 主结果 | **p.6** | 44.77/51.00 |
| PBR | Table 5 消融 | **p.7** | 33.21/89.99/44.77 |
| MADAR | Table II/III Domain-IL | **p.8** | 表题 TABLE II/III |
| MADAR | Table IV EMBER Class-IL | p.9 | 表题 TABLE IV |
| MADAR | §VII.D Analysis and Discussion | **p.11** | 小节标题 |
| ECBRS | 式 1 + Algorithm 1 + Table 3 首块 | **p.4** | gamma(i)=m·w(i)/softmax/0.896/0.929/0.969/0.949 |
| Hemati | Table 2 | **p.8** | 表题 + MCA×4（表体为图像占位，数字以 wiki 全文为准） |
| Hemati | FA 正文（§3 quota） | p.4 | quota |
| Hemati | Algorithm 3（附录 E） | p.15–16 区 | 未逐字定位 |
| GSS | Table 4 | **p.8** | 69.12/76.49/77.96 |
| MIR | 蓄水池固定声明 | **p.6** | restrict ourselves / reservoir sampling for deciding |

- 单页文本仅用于定位页码，数字与结论一律以全文转换文本交叉核验，未据单页增删。
- 中间产物全部在 `/tmp/b-class-balance-replay/`（页文件 29 个 + 全文 8 个 + diff），未进入 raw/wiki/output。
- 本机全程零 OCR/零张量计算，PDF 转换均走 MinerU 云端 API。
