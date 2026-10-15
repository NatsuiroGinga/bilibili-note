# notes.md：逐查询落盘记录

**日期**：2026-10-15
**证据等级**：`本地全文` / `在线全文已下载` / `仅摘要` / `仅题录`

---

## 0. 本地查重（开工前复核）

命令：
```
rg -il "optimizer state|momentum_buffer|loss of plasticity|continual backprop|可塑性" wiki/papers/
rg -il "optimizer|优化器|warm.?start|cold.?start" wiki/papers/
rg -in "plasticity|可塑性" wiki/papers/
```

结论：**优化器状态／momentum_buffer 在本地零命中**（与父代理实测一致，已复核）。
但 **可塑性线有一个本地全文强命中**，见下。

### 本地命中 L1：Cho et al. 2025（ICLR 2026）"Forget Forgetting"

- 笔记路径：`wiki/papers/attack-detection/2025-Cho-遗忘遗忘-充裕记忆-全文.md`
- 原件：`raw/papers/attack-detection/2025-Cho-Forget-Forgetting-Abundant-Memory.p.pdf`
- arXiv：`2502.07274`；Zotero key `THC658DJ`
- 证据等级：**本地全文**
- 与本提案关系：**可塑性丧失（§3.2）** 的机制归因是**梯度对齐** `ρ_t→1` 使有效步长 `‖θ⁽ᵗ⁾−θ⁽ᵗ⁻¹⁾‖→0`（Eq. 10–13），
  **不是优化器状态**；其提出的补救是「每个任务前重置**参数**」（不是重置优化器状态）。
  §3.2 明确说「在每个任务前重置参数」能恢复可塑性。
- 可迁移性：机制层面**不直接支撑**「优化器状态携带历史造成危害」；
  但它是**可塑性丧失**在持续学习语境下的本地全文证据，且引 (Lee et al. 2022) node-reuse、(Rolnick et al. 2019) 全量回放妨碍学新任务。

---

## 1. 工具限流记录

| 工具 | 结果 |
| --- | --- |
| `scholar search "optimizer state continual learning" --json`（挂 `HTTPS_PROXY`） | **429 Too Many Requests**，与前序代理报告一致，弃用 |
| `export.arxiv.org/api/query`（经 curl 走代理） | **空输出**，未取到结果，改走 WebSearch |
| WebSearch | 正常，为主要来源 |

---

## 2. 问 1：优化器状态在分布边界携带历史造成危害

### Q1-a. Asadi, Fakoor, Sabach — *Resetting the Optimizer in Deep RL: An Empirical Study*

- 出处：NeurIPS 2023（第 37 届）；arXiv:2306.17833
- URL：https://neurips.cc/virtual/2023/poster/72524 ；https://www.amazon.science/publications/resetting-the-optimizer-in-deep-rl-an-empirical-study
- 证据等级：**仅摘要**（尚未取全文；需补全文）
- 核心结论：
  - 把 deep RL 的值函数逼近表述为「每次迭代损失函数都变的优化问题序列」，Adam 的一阶/二阶矩估计会被**历史污染（contamination effect）**。
  - **重置两个矩效果最好**；只重置二阶矩「quite effective」；只重置一阶矩**无效**。
  - 55 个 Atari 游戏、10 seeds、human-normalized 平均：重置 Adam / RAdam 明显优于不重置。
  - 连续控制（MuJoCo + SAC）软目标更新下**帮助不明显**，作者称「何时重置不清楚」。
- 与提案关系：**直接支撑**「优化器状态携带历史造成危害」的机制家族，且给出「重置哪一个矩」的操作性细节。
- 可用性三问：待全文核（RL/Atari 设定，非分类；机制本身与架构无关）。

### Q1-b. 2024 NeurIPS 反例论文（Adam-Rel / Adam-MR）

- 出处：NeurIPS 2024，`papers.nips.cc/paper_files/paper/2024/file/f2733d3b0dde1d74995f35a9cf442d38-Paper-Conference.pdf`
- 证据等级：**仅摘要**（标题未直接核到，需补全题录）
- 结论（与 Asadi 部分相反）：**Adam-MR**（完全重置优化器，如 PPO 采样新 batch 时）**substantially worse than Adam**；
  作者认为「阻止任何梯度信息跨越目标变化是 excessive correction，甚至有害」。
  但在 Asadi 用过的游戏集合上，**Adam-Rel 在 IQM 上优于 Adam 基线**。
- 与提案关系：**直接反证**——「重置优化器不一定有益，可能有害」。
- 意义：说明该机制**存在争议**，不是单向结论。

### Q1-c. Local-Time AdamW (LT-AdamW)

- 出处：Analemma Research，https://analemma.ai/papers/786c7661-d46b-4395-ad43-8b8b3908fc4f/
- 证据等级：**仅摘要**（未查到 arXiv 号；来源非主流预印本平台，可信度待核）
- 结论：AdamW 的**偏差校正**为冷启动设计，在任务边界「矩估计是热的但与新任务梯度错位」时**反成负担**。
  只重置**偏差校正步数** `t`、保留矩缓冲，产生更新阻尼（切换后早期有效学习率约降 3×）。
  Split CIFAR-100 稳定性缺口 −31%，最低切换后准确率 +24%；Rotated MNIST −17%。一行代码改动。
- 与提案关系：**直接支撑**「年度边界处置优化器状态」的**中间路线**（不全重置，只重置时间步）。
- 注意：来源为研究机构站点，**须核 arXiv 是否存在**。

### Q1-d. *A Step Towards Forgetting: Optimiser History and the Loss of Answer Mass*

- 出处：arXiv:2610.03940，https://export.arxiv.org/pdf/2610.03940
- 证据等级：**仅题录**（仅从检索片段看到题名与一句描述）
- 片段：研究「梯度的年龄决定它在优化器记忆中的权重」，关联到「优化器在学习新任务时累积的信息」。
- 与提案关系：**可能直接相关**，须补全文核验。

### Q1-e. HAT-CL 包的工程建议

- 出处：https://pypi.org/project/hat-cl/0.1.0/
- 证据等级：**仅题录**（工程文档，非论文）
- 内容：「refreshing the optimizer state after every task, to avoid carrying over the momentum from the previous task」。
- 与提案关系：**工程惯例层面**的佐证——「每任务后刷新优化器」是 HAT（硬注意力持续学习）实现里的通行做法。

---

## 3. 问 2：可塑性丧失（loss of plasticity）

### Q2-a. Dohare et al., Nature 2024 — **已核验存在**

- 题录：Shibhansh Dohare, J. Fernando Hernandez-Garcia, Qingfeng Lan, Parash Rahman,
  A. Rupam Mahmood, Richard S. Sutton. "Loss of plasticity in deep continual learning."
  *Nature* **632**(8026):768–774, 2024-08-21. DOI **10.1038/s41586-024-07711-7**；PMID **39169245**；PMCID **PMC11338828**。
- URL：https://pubmed.ncbi.nlm.nih.gov/39169245/ ；https://preview-www.nature.com/articles/s41586-024-07711-7.pdf
- 证据等级：**在线全文可下载**（n / preview PDF 可见；待正式下载）
- 结论：标准反向传播在持续学习设定下会逐渐**丧失可塑性**，直至退化到不比浅层网络更好（ImageNet + RL，多种网络/算法变体）。
- **机制归属（关键）**：**网络单元**，不是优化器状态。提出 **continual backpropagation (CBP)**：
  对**低效用的隐藏单元**做持续随机重初始化（贡献效用为激活幅度×输出权重的滑动平均，η=0.99；
  超过成熟阈值的单元候选；以替换率 ρ 重置每层最低效用单元：入权重重采样、出权重清零、效用/年龄清零）。
  **梯度下降之外需要「随机的非梯度成分」**来维持变异性。
- 相关前序预印本：arXiv:2108.06325（Continual backprop: SGD with persistent randomness, 2021）；
  arXiv:2306.13812（Maintaining plasticity in deep continual learning, 2023）。
- 与提案关系：**同族但机制不同**——它把「历史危害」定位在**单元/权重**的饱和与休眠，而非优化器矩缓冲。
  对固定小回放恶意软件设定：CBP 需改动网络结构（单元级重初始化），**不是优化器层改动**；
  但其「历史使网络失去适应能力」的**问题陈述**与提案同源。
- 可用性三问：待全文核。

---

## 4. 问 3：非平稳优化的收敛理论（**最重要发现**）

### Q3-a. Sahu, Hogan, Wells — *On the Provable Suboptimality of Momentum SGD in Nonstationary Stochastic Optimization*

- 出处：**ICML 2026**；arXiv:**2601.12238**
- URL：https://icml.cc/virtual/2026/poster/63752 ；https://papers.cool/arxiv/2601.12238 ；https://browse-export.arxiv.org/pdf/2601.12238
- 证据等级：**在线全文可下载**（browse-export PDF 可见）
- 设定：均匀强凸 + 光滑下，跟踪**时变最优**；动态遗憾 `R_T^π(G)=E[Σ_t (G_{t+1}(θ_t) − G_{t+1}(θ*_{t+1}))]`。
- **核心结论（正是提案要的理论）**：
  1. 跟踪误差三项分解：初始化瞬态项 + 噪声方差项 + **漂移引起的跟踪滞后项**。
  2. **动量放大漂移误差**：静态下抑制梯度噪声的动量，在分布漂移下产生**漂移放大惩罚**，
     随 `β→1` **无界**，量级 `(1-β)^{-1}` 与 `(1-β)^{-2}`。
  3. 三条机制（对「参数 + 动量缓冲」的 2D Lyapunov 分析）：
     - **惯性视野（inertia horizon）** 量级 `(1-β)^{-1}`，跟踪依赖高阶漂移、制度切换下易过冲；
     - **漂移-噪声耦合项** 量级 `(1-β)^{-2}`（路径浓度）；
     - 病态条件（κ≫1）下稳定性迫使步长收缩（`γ ≲ (1-β)²/L`），无法快速适应漂移。
  4. **极小极大下界**：动态遗憾在梯度变化约束下有**信息论屏障**；漂移主导区动量造成不可避免的「惯性窗口」，
     **vanilla SGD 可证明地更鲁棒**，严格优于加速版本。
  5. 高概率界用**加权历史漂移** `𝔇_t = Σ_ℓ (1-γμ/2)^{t-ℓ-1}|Δ_ℓ|²`，**motivates restart/windowing strategies**。
- 与提案关系：**这是本提案理论家族的直接支撑**——它证明了「动量缓冲在漂移下携带过期梯度的历史」有明确代价，
  且**明确指向 restart/windowing（即边界重置/衰减）作为对策**。与参照论文第四章「复杂度＋收敛」形态匹配。
- 可用性三问：理论工作，无需代码；其结论可直接作为提案的收敛性论据。

### Q3-b. 相关支线（未取全文，仅题录）

- EWMA-SGD tracking nonstationary streaming data（sciengine PDF）——动态遗憾下加权平均可恢复最优速率。
- "The Anytime Convergence of SGD with Momentum: From a Continuous-Time Perspective" arXiv:2310.19598。
- "Convergence Analysis of the Last Iterate in Distributed SGD with Momentum" arXiv:2505.10889。
- Zinkevich 框架（在线凸优化的动态遗憾）——Q3-a 的上游。

---

## 5. 问 4：恶意软件/入侵检测年度漂移上的同类机制

**结论：未发现。明确空白。**

两次定向检索（查询式见报告）共同返回：
> 「results support that annual temporal concept drift degrades malware/IDS detection performance …
> **But they do not provide evidence on optimizer momentum reset or explicit loss-of-plasticity interventions.**」

邻近但**不相关**的工作（不可充数）：
- *Adversarial Vulnerability Under Temporal Concept Drift*（arXiv:2605.23623）——年度切片 Android，但研究**对抗脆弱性**。
- *MEASURING CONCEPT DRIFT IN MALWARE AND NETWORK INTRUSION*（UIUC）——只度量漂移，无干预。
- *Navigating the Latent Manifold*（arXiv:2609.08623）——NIDS 潜表示漂移 + 选择性冻结，表征层。
- TraMEL（OpenReview）——恶意流量回放式 CL，回放缓冲层。
- IoT-23 持续学习对比（PeerJ）——ER/EWC/LwF 比较，**经验回放**路线。
- 多篇 Android CL（EWC+MANN、自监督+PPO 控制器）——数据/正则/架构层。

**模式**：这些工作普遍报告「顺序微调崩塌、EWC/LwF 严重遗忘、回放最好」，
即**症状**已被反复报告，但**归因与对策无一篇落到优化器状态**。

---

## 6. 题录核验（curl + arXiv abs 页，逐条核到）

| arXiv | 标题 | 作者 | 日期 |
|---|---|---|---|
| 2601.12238 | On the Provable Suboptimality of Momentum SGD in Nonstationary Stochastic Optimization | Sahu, Hogan, Wells | 2026-01-18 |
| 2306.17833 | Resetting the Optimizer in Deep RL: An Empirical Study | Asadi, Fakoor, Sabach | 2023-06-30 |
| 2306.13812 | Maintaining Plasticity in Deep Continual Learning | Dohare, Hernandez-Garcia, Rahman, Mahmood, Sutton | 2023-06-23 |
| 2108.06325 | Continual Backprop: SGD with Persistent Randomness | Dohare, Sutton, Mahmood | 2021-08-13 |
| 2412.17113 | Adam on Local Time: Addressing Nonstationarity in RL with Relative Adam Timesteps | Ellis, Jackson, Lupu, Goldie, Fellows, Whiteson, Foerster | 2024-12-22 |
| 2410.23495 | DASH: Warm-Starting Neural Network Training in Stationary Settings without Loss of Plasticity | Shin, Oh, Cho, Yun | 2024-10-30 |
| 2406.05114 | The Expanding Scope of the Stability Gap | Kamath, Soutif-Cormerais, van de Weijer, Raducanu | 2024-06-07 |
| 2404.05555 | On the Convergence of Continual Learning with Adaptive Methods | Han, Kim, Cho, Lee | 2024-04-08 |

**Nature 2024**：Dohare et al., *Nature* 632(8026):768–774, doi:10.1038/s41586-024-07711-7, PMID 39169245, PMCID PMC11338828；
OA PDF 直接下载成功，第 768–769 页逐页核（第 768 页确认「gradient descent 不够、需随机非梯度成分」；第 769 页确认「优化器选择影响**下降时点**而非**是否下降**」）。

---

## 7. 入库

PDF → `raw/papers/methodology/`（7 个）；笔记 → `wiki/papers/methodology/`（8 个）；
`INDEX.md` 新增一节「优化器状态、动量与非平稳优化（2026-10-15 新增）」。
Zotero 无命中，本次未写入 Zotero。**未执行 git 提交（按任务要求）。**

## 8. 待办（已清）

- [x] 取全文（curl 直下 arXiv PDF + Nature OA PDF）
- [x] 核题录（逐条 curl abs 页）
- [x] 检索 Q4（结论：空白）
- [x] 入库 + INDEX
- [x] 写报告 → `报告.md`
