# 检索笔记（增量落盘）

## 检查点 1（2026-10-15 开始）

- 已完成：建目录、task_plan.md、清点本地库（53 篇 PDF）
- 本地库观察：
  - 有 `2025-Haque-CITADEL-Semi-Supervised-Active-Learning-Drift.pdf`（P0 先读）
  - 有 Chen 2022 MemoryBoundsContinualLearning（存储预算线）
  - 有 `2023-Chen-Continuous-Learning-Android-Malware.pdf`、`2022-Rahman-Limitations-of-Continual-Learning-Malware.pdf`（恶意软件 CL 线）
  - 有 `2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf`（SSL 线）
  - 有 `2022-Mindermann-可约损失优先训练-ICML2022.pdf`、`2025-Tong-可约损失核心集选择-ICLR2025.pdf`（核心集/标注优先级线）
  - 有 `2020-Chrysakis-CBRS-Online-Continual-Learning-Imbalanced-Data.pdf`、`2024-Park-PBR-Prior-Free-Balanced-Replay.pdf`（类不平衡回放线）
  - **未见**明显的 imbalanced active learning / long-tailed AL / PU learning 论文
- 下一条查询：Zotero 语义检索 + 本地混合索引，然后 scholar 挂代理
- 未关闭疑点：CITADEL 协议是否 Chen 式流式 AL；Faber DSAA 2022 原文未取得
- 无法获取原文清单：（暂无）

## 检查点 3（2026-10-15，OpenAlex 结构化扫描完成第一批）

- 工具状态：scholar 挂代理可用但对复杂查询返回 No results 且触 429 限流——改以 **OpenAlex 直连为主通道**（`filter=title_and_abstract.search:<短语>`），arXiv API 用 https+代理。系统 python3 裸用已避免（用 miniconda rwkv 环境）。
- **Faber 论文已定位并确认**：Faber, Corizzo, Śnieżyński, Japkowicz,「Active Lifelong Anomaly Detection with Experience Replay」, IEEE DSAA 2022, DOI `10.1109/dsaa54385.2022.10032405`。摘要确认：active lifelong anomaly detection 框架，支持任意 memory-based experience replay 方法 + 任意查询策略 + 任意异常检测模型，class-incremental 情景。**OpenAlex 标 closed access、无 arXiv 版、无期刊扩展版（已按作者检索核对）→ 列入待用户手动下载清单**。
- 问题 2 候选（active + CL + 回放）：Online Active Continual Learning for Robotic Lifelong Object Recognition（TNNLS 2023）；Active Continual Learning: On Balancing Knowledge Retention and Learnability（2024 Springer）；Continual Deep Active Learning for Medical Imaging: Replay-Based Architecture（arXiv 2501.08245）；Continual Active Learning for Efficient Adaptation of ML Models to Changing Image Acquisitions（2021 Springer）；Belouadah et al. ECML-PKDD 2020（active CIL imbalanced，arXiv 2008.10968）；Huang et al. ACM MM 2024 Class Balance Matters to Active Class-Incremental Learning（DOI 10.1145/3664647.3680822）；TypiCore（arXiv 2607.17632）；Active Domain Adaptation 与 Active Continual Learning 综述（2026 preprint）。
- 问题 3 候选（稀缺标签）：Enhancing Active Learning for Class Imbalance With an Incrementally Weighted Approach（TKDE 2026）；Active Learning From Imbalanced Data: Online Weighted ELM（TNNLS 2018，163 引）；PU 流式经典：Positive Unlabeled Learning for Data Stream Classification（SDM 2009，115 引）、Dynamic classifier ensemble for PU text stream（2011）；rare category detection 流式（DATE 2019、DAWAK 2016）；**DMAE: dual-memory active ensemble learning for multi-class imbalanced concept-drifting data streams（2026，10.1007/s44443-026-01127-1）——三轴同时占（主动+双记忆+类不平衡+漂移流）**。
- 问题 4 新候选（恶意软件标注为一等公民）：FALCON: Federated Active Learning-Based Concept Drift Adaptation for Malware Detection（IEEE TMC 2026，10.1109/tmc.2026.3684501）；ALPHA: Active Learning with PAC-Bayesian Theory for Android Malware Detection（ACM 2026，10.1145/3779208.3807494）；Geometry-Aware Risk-Guided Active Learning for Malware Concept Drift Adaptation（Applied Sciences 2026）；Jesse1103/malware-detection Zenodo「Uncertainty-Driven Hierarchical Sampling for Unbalanced Continual Malware Detection」（2026，待找正文）；DRMD（AAAI 2026，本地 raw 已有 `2025-McFadden-DRMD`）。
- 流式 AL 基线线：Online Active Learning for Drifting Data Streams（TNNLS 2021，80 引）；Nonstationary data stream classification with online AL and siamese networks（Neurocomputing 2022，38 引）。
- 下一步：DMAE/FALCON/ALPHA/Jesse1103 详情与全文；CITADEL 协议核验；联合双预算的补漏检索。
- 无法获取原文清单：Faber DSAA 2022（closed，IEEE Xplore，无 arXiv，无扩展版）bis（2026-10-15，工具通路实测）

- **scholar CLI 本会话可用**（挂代理）：`HTTPS_PROXY=http://127.0.0.1:7890 scholar search "<简单短语>" --json` 成功返回。注意：查询词太复杂（如 "label budget memory budget continual learning joint"）返回 No results——scholar 是字面匹配，要用短查询。
- **SEED 缓冲关键证据已核**（全文笔记行 313、785）：§5.4「we relax the assumption on the availability of finite size of M until the training of the seen tasks. After that, from the unseen tasks M grows slowly and constantly as the availability of the number of labeled samples is regularized by the labeling budget constraint」；§局限「This work assumes growing memory size to store the partial labeled samples until the last seen task.」⇒ **SEED 只有标注预算受限，存储不设固定预算（增长式），「存什么」不是被联合配置的自由量**。
- 昨日（2026-10-14）已有两个先行任务：`.Codex/docs/2026-10-14-C1近邻论文入库/`（SEED/HYDRA 等已入库 raw）与 `.Codex/docs/2026-10-14-LAMDA任务与基线综述/task-candidates.md`（C1/C2/C3 候选与占位扫描）。C1 零/低标签空间已被判「拥挤」：SEED、LFreeDA、MADCAT、CITADEL、HYDRA、MORPH、ADAPT。
- 新增候选（scholar 第一轮）：Huang et al. ACM MM 2024「Class balance matters to active class-incremental learning」（ACIL 范式 + 类平衡选择 CBS）；Belouadah et al. ECML-PKDD 2020「Active class incremental learning for imbalanced datasets」（arXiv 2008.10968）——都指向问题 2+3。
- 下一步：批量 scholar 检索（imbalanced AL / long-tailed AL / PU drift / malware label budget / budgeted CL），OpenAlex 结构化扫描，CITADEL 协议核验（arXiv HTML）。
- 未关闭疑点：Faber DSAA 2022 原文未取得
- 无法获取原文清单：（暂无）（2026-10-15）

- 本地混合索引在该工作树**不可用**：`scripts/literature_search/build.py:89` 报 `EmbeddingBackend.__init__() got an unexpected keyword argument 'device'`（lexcial/hybrid 均先触发 auto-build 后崩溃）。属他人代码缺陷，不修；检索通道改用 Zotero 语义检索 + rg 本地笔记 + scholar 挂代理。
- **CITADEL 已有本地全文笔记**：`wiki/papers/attack-detection/2025-Haque-CITADEL半监督主动漂移适应.md`（arXiv 2511.11979v3，fulltext_verified=true）。要点：LAMDA F1 77.7 依赖持续主动标注；表 4 月标注预算 50→F1 70.9、400→77.7；**笔记未提及存储/回放约束**（待对原件核协议：是否 Chen 式流式 AL）。MinerU 对该 PDF 失败（>10MB），笔记基于 arXiv HTML。
- **SEED 已有本地全文笔记**：`wiki/papers/attack-detection/2026-Amalapuram-SEED预算半监督持续检测.md`（arXiv 2605.24903，ACM TASP accepted 2026-06）。**这是问题 1/2 的最强近邻**：半监督持续恶意软件检测 + 月标注预算（50/100/150/200/250）+ 回放缓冲 + GPM + 延迟缓冲 + 双组平衡主动采样。**但未用 LAMDA**（BODMAS/AndroZoo/APIGraph）。待核：SEED 的缓冲是否固定容量约束、是否联合配置「标什么」与「存什么」。
- 其他本地相关笔记（待读）：`wiki/papers/malware/LAMDA-2026-原论文与时间漂移相关工作综述.md`、`2026-Sabbah-自监督强化学习漂移维护.md`、`2023-Amalapuram-ECBRS-PAPA网络入侵持续学习.md`、`2025-Gupta-NetGuard漂移与不均衡NIDS主动适应`（INDEX 提及）
- 下一条查询：读 LAMDA 综述笔记 → SEED 原件核缓冲约束 → Zotero 语义检索 → scholar 挂代理
- 未关闭疑点：Faber DSAA 2022 原文；CITADEL 协议细节
- 无法获取原文清单：（暂无）

## 检查点 4（2026-10-15 17:2x，应用户要求立即落盘现状）

### 已完成（证据级）

- **CITADEL 协议实锤**（arXiv HTML 全文 rg 核验，/tmp/citadel.html 929KB）：§2 Related Work 原文「However, CL addresses a different problem setting and is **out of the scope of this work**.」；全文零处 Domain-IL；无回放/缓冲/存储约束；标注机制为月度预算（算法步骤 8 定义 budget）+ 多准则主动采样（边界 margin、Lp 距离、低置信度）。**结论：CITADEL 是 Chen 式流式 AL，只有标注半边，与 RGA 代理结论一致。**
- **SEED 存储口径实锤**（本地全文笔记行 313/785）：存储不设固定预算——seen 任务阶段 M 无限累积，unseen 任务后随标注预算缓慢增长。「存什么」不是被配置的自由量。**结论：SEED 只有标注预算半边（标+存机制同框架但存储无固定预算）。**
- **Xie UGSR（arXiv 2509.07532）全文已核并入库**：月预算 B=50 固定（§IV.E 原文）、memory bank 累积无固定容量、codebook top-50/类有界；不平衡 9:1 为核心动机；APIGraph/AndroZoo 月度流，非 LAMDA 非 Domain-IL。
- **DMAE（10.1007/s44443-026-01127-1）全文已核并入库**：四要素（标注预算/有界记忆/多类不平衡/漂移）同框架共置的最强先例（流式集成底座）；存储有界（局限节原文「memory sizes and PDSR trial length are bounded」）；作者自认「labelling budget extremely small + rare classes 时估计不稳」。非恶意软件域。
- **Aggarwal/Belouadah ECML-PKDD 2020（arXiv 2008.10968）全文已核并入库**：两阶段获取函数吃预算 B + 类不平衡（推理期类预测缩放）；有界记忆仅背景讨论，其方法用累积标注集。
- **Daniel 2025（arXiv 2501.08245）全文已核并入库**：CAL 框架（回放式 rehearsal + 记忆管理/剪枝策略 + AL 组件），医学影像；组合存在但无联合预算形式化。
- **Chen 2023（本地笔记核对）**：月标注 200 + 重训（累积已标注集，无固定缓冲），与 RGA 代理结论一致。
- **Faber DSAA 2022 定位并确认**：Faber/Corizzo/Śnieżyński/Japkowicz；摘要确认框架=任意 memory-based 经验回放 × 任意查询策略 × 任意异常检测模型（class-incremental）；**closed access，全文细节无法核**——列入下载清单。

### 题录层候选（未核全文，报告中标证据等级）

- IFAC 2025 Szücs「Active Learning for Class-Incremental Time Series with Dual Memory and Shapley Replay」（在线摘要，OA）
- TNNLS 2023 Nie「Online Active Continual Learning for Robotic Lifelong Object Recognition」（在线摘要，closed）
- PRICAI 2024 Vu「Active Continual Learning: On Balancing Knowledge Retention and Learnability」（在线摘要）
- ACM MM 2024 Huang「Class balance matters to active class-incremental learning」（在线摘要）
- TMC 2026 FALCON（closed）；ACM 2026 ALPHA（OA 但反爬）；Appl. Sci. 2026 Geometry-Aware Risk-Guided AL（未取）
- TNNLS 2021「Online Active Learning for Drifting Data Streams」（80 引，流式 AL 基线，未取全文）

### 无法获取原文清单（待用户手动下载，完整表见最终报告）

1. Faber et al. 2022, DSAA, `10.1109/dsaa54385.2022.10032405`（任务①指定）
2. FALCON, IEEE TMC 2026, `10.1109/tmc.2026.3684501`
3. ALPHA, ACM 2026, `10.1145/3779208.3807494`（OA 但 ACM 反爬）
4. Nie et al., IEEE TNNLS 2023, `10.1109/tnnls.2023.3308900`

### 限流与通道记录（如实）

- `scholar` CLI：复杂查询返回 No results（字面匹配）；两次并行查询触发 **429 Too Many Requests**（/tmp/sch_imb.txt 留痕）。此后 scholar 仅低频使用，主通道切 OpenAlex。
- OpenAlex：本轮未遇 429，直连稳定。
- 本地混合索引：该工作树 auto-build 崩溃（`build.py:89` EmbeddingBackend device 参数缺陷），lexical/hybrid 均不可用；未修他人代码。
- WebFetch 对 arxiv.org 报域名校验失败；改用 curl+代理抓 arXiv HTML 成功。
- Zotero：Xie/DMAE 均无既有条目（zotero_search_items 零命中），无重复入库。

### FEC 补漏结果

- OpenAlex title_and_abstract 检索 `FEC continual learning`（1 条不相关）、`FEC replay memory`（0 条）、`forgetting evidence coreset continual`（仅命中本地已有的 Yoon OCS, arXiv 2106.01085）。**未能定位「FEC」缩写所指工作**——如 RGA 指特定论文请补全称再核。

### 未完成

（无——检查点 5 记录收口状态）

## 检查点 5（2026-10-15 17:4x，收口）

- 结构化笔记 ×4 已写入 `wiki/papers/attack-detection/lamda-related/`（Xie UGSR、DMAE、Aggarwal、Daniel）；全文转换件 ×4 同目录（`*-全文.md`，图片链接已剥离）。
- `wiki/papers/attack-detection/INDEX.md` 新增「LAMDA 第四章：标注×存储双预算联合配置的任务先例核查（2026-10-15 新增）」节（位于 RGA 节之后、方法学入口之前）。
- 报告已收口：`第四章任务先例核查报告.md`（裁决 (b)）；初稿两次生成损坏已逐段清理。
- 按协调方指示未再扩大检索：FEC 缩写未能定位（需 RGA 补全称）；Faber 进下载清单。
- 未 git 提交（工作树有并行任务改动）。
