# 查证笔记：对抗与漂移联合框架

> 本文件按查询组即时落盘，不攒到最后。

## 记录格式

每条：查询式 | 来源/URL | 原件路径 | 证据等级 | 关键页码 | 纳入/排除理由

---

## 2026-10-14 查询日志

### S1 本地混合索引 · Q1 组（入口：ch3-drift-20260908 工作树，索引 built 2026-10-14T03:16Z，1934 notes）

| 查询式 | Top 命中 | 等级 | 纳入/排除 |
| --- | --- | --- | --- |
| `adversarial robustness concept drift malware` | 1. Roh 2025 MADCAT（TTA 对概念漂移，无对手）；2. El-Hajj 2026（表 1 含 Drift exploitation 维度） | 本地结构化全文笔记 | MADCAT 归漂移侧单独做（B 类证据）；El-Hajj 仅威胁模型分类表，非联合优化，纳入待核 |
| `joint adversarial distributional robustness malware temporal` | 1. El-Hajj 2026 2.2.4 表 1 | 本地结构化全文笔记 | 纳入：El-Hajj 表 1 把 Drift exploitation 列为对抗维度，防御栏写 Drift detection——是分类学列举 |
| `robust malware detection temporal drift adversarial` | El-Hajj 2026、Barbero 2022 Transcendent、Berruz 2026、MADCAT、MalMoE 2026 | 本地结构化全文笔记 | 全部漂移侧；无一含主动对手 |
| `adversarial training distribution shift malware` | Barbero 2022、Curi 2019 ADA-CVaR、Ganin 2016、**El-Hajj 3.3 节引 Sandor et al. 2024** | 本地结构化全文笔记 | **重大线索**：Sandor 2024 ICCP |
| `evasion attack temporal generalization Android malware` | El-Hajj、MADCAT、Barbero、CBSeq、Berruz | 本地结构化全文笔记 | 无联合工作；Android 侧无命中 |

### S1 重大线索（Q1 的 A 类候选）

- **Sandor, M., Portase, R., Colesa, A. (2024). "Enhancing ML model resilience to time-evolving data in malware detection systems with adversarial learning." 2024 IEEE 20th International Conference on Intelligent Computer Communication and Processing (ICCP), Cluj-Napoca, IEEE, pp. 1–7. DOI: 10.1109/ICCP63557.2024.10793037**
  - 二手转述（El-Hajj 2026 全文笔记行 242，本地）：「combined adversarial training to reduce drift-induced accuracy drop to 9.1%, but training time increases by 300%, and the approach requires known attack patterns」
  - 证据等级：**在线摘要（本地综述转述）**，未回原件。待在线核验。
  - 若成立：这是「对抗训练 × 时间演化数据」的**直接联合**——Q1 落 A 类（已有人联合做过），C4 需差异化。
- **El-Hajj & Zeineddine 2026**（Front. Artif. Intell. 9:1811692，本地全文笔记）：表 1（行 150）把对抗维度列为 Evasion / Data poisoning / Model poisoning / **Drift exploitation** 四列，Drift exploitation 的能力是 $\mathcal{P}_t$ manipulation、防御是 Drift detection；行 156 给出漂移加速公式 $\mathcal{P}_{t+1} = \mathcal{P}_t \oplus \Delta\mathcal{M}$。
  - 性质：威胁模型**分类表**，防御分开设计（漂移检测触发重训）；**非**最坏情形联合优化框架。
  - 行 180：攻击面表把 Drift exploitation 定义为「Trigger false drift detection」。
- 漂移侧单独做的本地证据（B 类支撑）：MADCAT 2025（TTA）、Barbero 2022 Transcendent（保形评估）、Berruz 2026（漂移检测+重训）、MalMoE 2026（图流量时间泛化）、Alam 2024 MORPH、Darem 2021。

### S1 本地混合索引 · Q3 组

| 查询式 | 关键命中 | 等级 | 结论 |
| --- | --- | --- | --- |
| `Android malware feature space attack realizable constraint` | **2019-Cortellazzi-问题空间对抗攻击与约束.md**（本地结构化全文笔记，含页码锚点） | 本地结构化全文笔记 | 纳入：Q3 核心文献 |
| `problem space evasion attack Android Drebin mapping` | 同上（rank 1） | 本地结构化全文笔记 | 同上 |
| `adversarial examples Android malware feasibility constraint reversibility` | Cortellazzi；El-Hajj 2.2.3（对抗能力含 feasibility constraint $\Phi(x+\delta_x)$） | 本地结构化全文笔记 | El-Hajj 也有可行性约束形式化，作旁证 |

**Q3 本地核到的核心事实（Cortellazzi/Pierazzi arXiv:1911.02142v3，36 页扩展版，PDF 在 `raw/papers/attack-detection/2019-Cortellazzi-Problem-Space-Adversarial.pdf`）**：

- 四类问题空间约束 Γ={可用变换 T、保持语义 Υ、合理性 Π、预处理鲁棒性 Λ}，定义 8–12，**p.7–8**
- **特征空间攻击投影到问题空间后，攻击置信度必然不高于原特征空间攻击**，**p.9**（单调性结论）
- 副效应特征 η：为满足约束被迫附带改动、不沿梯度方向（定义 13，**p.8–9**）
- Android 案例的攻击算法：**贪心搜索 + `check_feasibility` 过滤（经验规则：最多新增 1 个权限、不新增危险权限）**，§3.6，**p.15**；攻击对象是 **DREBIN 特征 SVM**（§5）
- 「可用变换」的具体含义：注入良性应用完整字节码切片（软件移植）；保持语义=恒 False 谓词包裹（§3.2–3.5，p.12–15）
- 模型硬化：对抗重训 ASR 恒 >95%（p.21）；问题空间样本做对抗训练 ≫ 特征空间样本，鲁棒性 +10–60%（p.21–22）
- **该笔记本体限制**：本地 PDF 是 arXiv 扩展版；引用正式版（IEEE S&P 2020）须回核

### S1 本地混合索引 · Q4 组

| 查询式 | 关键命中 | 等级 | 结论 |
| --- | --- | --- | --- |
| `LAMDA dataset adversarial evaluation android malware benchmark` | 1. LAMDA 2026 原论文结构化笔记；2. McNdroid 2026（另一纵向基准）；3. Sabbah RL/SSCL | 本地结构化全文笔记 | 命中均无对抗评价 |
| `LAMDA malware dataset time decay adversarial` | 同上 | 本地结构化全文笔记 | 无对抗评价命中 |

**LAMDA 证据记录**：`wiki/papers/datasets/2026-Haque-LAMDA-Android恶意软件长期漂移基准.md`（Evidence ID `LAMDA-E1`）、`wiki/papers/malware/LAMDA-2026-原论文与时间漂移相关工作综述.md`（14 条 LAMDA 引用核验）。待读该两份笔记核对「有无对抗评价」。

### S1 本地混合索引 · Q2 组

| 查询式 | 命中 | 结论 |
| --- | --- | --- |
| `projected adversarial training convergence malware` | 无 PAD 命中（GAN/多任务/漂移文献混杂） | 本地索引无 PAD 2023 TDSC 原件 |
| `provable robustness guarantees malware classifier convergence` | RS-Del、Barbero、Duchi-Namkoong | 本地索引无 PAD |
| `PAD projected adversarial dissonance TDSC` | 仅 Ganin 的 PAD 缩写冲突（Proxy A-Distance） | 本地索引无 PAD 2023 TDSC |

**本地综述对 PAD 的声称位置**：`thesis/methods/第三章-LAMDA主任务与机制裁决.md` 行 48；`thesis/methods/第三章-LAMDA任务与方案筛选矩阵.md` 行 160。声称内容：「PAD 2023（TDSC）已占『恶意软件对抗训练的收敛保证』⇒ 对抗训练类不作主轴」。**本地综述未附原件路径，须在线核。**

### S3 在线核验日志（2026-10-14 15:20 前后）

#### Q2 PAD 2023 题录核验——目前**无法证实**，且发现多次搜索引擎拼编

| 动作 | 结果 | 证据等级 |
| --- | --- | --- |
| arXiv API `all:"Convergence of Adversarial Training in Deep Learning Classifier for Malware Detection"` | 0 结果 | API 直核 |
| WebSearch #1 给出题录：题名含 "Classifier"，作者 Damera/Maglaras/Venkatesan 等 6 人，DOI `10.1109/TDSC.2023.3271837`，IEEE doc 10133857 | Crossref `works/10.1109/TDSC.2023.3271837` → **404**；`doi.org` 同 DOI → **404** | 在线题录核验失败 |
| WebSearch #2 给出另一题录：题名含 "Deep Neural Networks"，作者 V. Damera/Panigrahy/Ali/Gokhale/Srivastva，DOI `10.1109/TDSC.2022.3175541`，TDSC 20(5):4351–4364，doc 9757818 | Crossref `works/10.1109/TDSC.2022.3175541` → **404**（`/tmp/pad_cref3.json` 内容 "Resource not found."）；Crossref 标题检索无此题 | 在线题录核验失败 |
| WebSearch 声称 arXiv:2509.25848 是「PAD: Protected Adversarial Detection for Malware Classifiers」 | **直接抓取 arxiv.org/abs/2509.25848 实为 VLM 推理论文**（"More Thought, Less Accuracy?"）——WebSearch 转述不可信 | API 直核（反例） |
| Google Scholar 精确短语 `"Convergence of Adversarial Training in Deep Neural Networks for Malware Detection"` | **did not match any articles** | Scholar 直核 |
| Google Scholar 精确短语 `"Provable Adversarial Detection"` + malware | **did not match any articles** | Scholar 直核 |
| Google Scholar 短语 `"convergence of adversarial training"` + malware | **did not match any articles** | Scholar 直核 |
| Google Scholar `PAD malware adversarial "Dependable and Secure Computing"` | 10 条命中均非 PAD 缩写论文；顶部命中 Zainab/Dyrmishi/Bostani/Cavallaro 2026（Windows 问题空间对抗鲁棒性系统评价，arXiv）——归 Q3 | Scholar 直核 |

**Q2 中间结论（待最终定稿，不下裁决）**：
1. 「PAD 2023（TDSC）」这一题录**尚未在任何权威索引（Crossref/Scholar/arXiv/S2）核到**；两次 WebSearch 给出的题录互相矛盾且 DOI 均未注册。
2. 本地综述「PAD 2023（TDSC）已占恶意软件对抗训练的收敛保证」目前**查无实据**——该声称本身可能是未经核验的外部候选（早期网页综述残留）。
3. IEEE Xplore 站内搜索被 bot 检查挡住（HTTP 202 空响应），`dblp` 同样；S2 API 429 限流。**未穷尽**：OpenAlex 未试直连（此前经代理 429）、S2 未重试、IEEE 站内未试 POST 搜索。
4. **在核到原件前，任何关于 PAD 的威胁模型/保证类型/是否涉漂移的转述都不得使用**——包括 WebSearch 给出的「EMBER 数据集」「bounded adversarial budget」「closed-form convergence point」等描述（来源与不存在/错拼题录绑定，视为污染）。

#### Q1 Sandor 线新证据

- Google Scholar `convergence adversarial training malware detection` 命中 **`http://www.hit.bme.hu/~buttyan/publications/SandorKB2026cscs.pdf`**（J Sándor, B Kovács, L Buttyán，2026，CSCS 会议）——Sandor 团队在 2024 ICCP 之后有续作，摘要片段含「consistent and rapid convergence pattern (see Figure 1)」。**待抓全文核它与 ICCP 2024 的关系及是否涉漂移**。
- ICCP 2024 原件（DOI 10.1109/ICCP63557.2024.10793037，出自 El-Hajj 参考文献行 1573）仍**未取得全文**；IEEE 被挡。BME Buttyán 主页可能有副本——待查 `hit.bme.hu`。

#### Q3 新线索（Scholar 检索副产物）

- **Ferdous, Islam, Mahboubi, Islam (2026, arXiv)**：「a systematic feature-space adversarial robustness evaluation with adversarial ...」——系统性的特征空间对抗鲁棒性评价，**待取全题录与全文**。
- **Zainab, Dyrmishi, Bostani, Cavallaro (2026, arXiv)**：「Breaking Windows Malware Detection: A Comprehensive Evaluation of Problem-Space Adversarial Robustness」——Windows 恶意软件问题空间对抗鲁棒性系统评价。**待取全文**。
- 以上两条都是「特征/问题空间攻击 + 真实约束评价」的**已发表（预印本）实践证据**，与 Cortellazzi 2019 一起支撑 Q3 的「可实施、且必须带约束」结论。

#### 工具状态记录

- `scholar` CLI 无认证 cookie（`scholar auth` 需 Chrome 调试端口，未启动）；改用 curl 抓 scholar.google.com HTML，可用。
- WebFetch 对 researchgate.net 报「Unable to verify if domain is safe to fetch」；IEEE/SciSpace/dblp/DDG/Bing 经代理均被 bot 挑战（HTTP 202/挑战页）。
- Semantic Scholar API 429（限流，无 key）；OpenAlex 经代理 429（共享 IP 日预算耗尽）——**待试 OpenAlex 直连**。
- 可用通路：arXiv API（直连）、Google Scholar HTML（经代理）、Crossref API（经代理）、站点直抓。

### 检查点 1（2026-10-14 ~15:25）

- Q1：**部分完成**。已核本地侧全貌（漂移侧工作多、无一含主动对手）；A 类候选 Sandor ICCP 2024 已定位题录与二手转述，原件未取得；Sándor 2026 续作待抓。
- Q2：**部分完成**。PAD 2023 题录核验全面失败（Crossref/Scholar/arXiv/di.org 均查无），WebSearch 两次给出矛盾题录且混编 arXiv 编号。结论方向：该「已占」声称查无实据；仍差 OpenAlex 直连与 S2 重试两步收尾。
- Q3：**大部分完成**。Cortellazzi/Pierazzi 全文笔记已核页码（四约束 p.7–8、投影单调性 p.9、Android 可行性规则 p.15、硬化结果 p.21–22）；新增两条 2026 系统评价线索待取全文。**「改一个二值特征对应什么真实操作」的正面页码证据已在 Cortellazzi 笔记内（注入良性字节码切片+权限经验规则），待补一句「删除不存在的权限不可实现」的直接文献表述。**
- Q4：**部分完成**。本地侧（LAMDA 原文笔记+14 条引用核验综述）无对抗评价；待在线 arXiv 引用面补查。

## 检查点 2（2026-10-14 ~15:45）· Q2 已核清

### 先记录一次已推翻的误判（留档，防复发）

**误判**：检查点 1 中「PAD 2023 题录核验全面失败 ⇒ 查无实据，可能是网页综述残留」。
**推翻依据**（主代理核到，本代理复核确认）：
1. 真 DOI 是 `10.1109/tdsc.2023.3265665`（此前 WebSearch 给的 `...2023.3271837` 与 `...2022.3175541` 都是错的题录——404 证明的是「那个 DOI 不存在」，不是「这篇论文不存在」）。
2. OpenAlex 直连（无代理）`api.openalex.org/works/doi:10.1109/tdsc.2023.3265665` 返回完整记录（本代理已复核）：题名 **PAD: Towards Principled Adversarial Malware Detection Against Evasion Attacks**，2023，**IEEE TDSC**，被引 40，作者 Deqiang Li, Shicheng Cui, Yun Li, Jia Hao Xu, Fu Xiao, Shouhuai Xu；OA PDF = `arxiv.org/pdf/2302.11328`。
3. **答案早就在本地**：`.Codex/docs/2026-10-14-理论算法家族综述/raw-queries/openalex/abs_PAD.json` 存有完整 OpenAlex 记录。动手查网前应先 `rg` 本地 `raw-queries/`。
4. 教训：IEEE bot 拦截+Crossref 404+Scholar 无 cookie 三个工具失败叠加 ≠ 来源不存在；**OpenAlex 直连可用，走代理反而 429**。

### Q2 正式答案：PAD 2023（TDSC）到底占了什么（已回全文，arXiv:2302.11328v2 HTML）

- **威胁模型**（§III-A）：白盒规避攻击——攻击者通过搜索**非功能性指令**集合 $\delta_z$ 修改恶意软件样本 $z$，拥有对检测器 $f$ 与对抗检测器 $g$ 的完全知识（引 Kerckhoffs 原则）；鲁棒性评估用灰盒（知道 $f$ 不知道 $g$）。
- **攻击**：特征空间 box 约束扰动 $\mathbf{x}'\in[\underline{u},\overline{u}]$（**明确不用 norm 球约束**：「the defender should resist semantics-based attacks rather than small perturbations」）；实现为 **SMA（Stepwise Mixture of Attacks）**——多种梯度攻击的混合。数据集 **Drebin 与 Malscan**（二值静态特征）；实验称 PAD-SMA 对 Drebin 16 个攻击、Malscan 13 个攻击保持 ≥85% 准确率。
- **保证类型**：**对抗训练的优化收敛保证**——内层最大化可解析求解（凹损失），外层 SGD 收敛率 **$\mathcal{O}(1/\sqrt{N})$**（Theorem 2，正文行 339：「the convergence rate of the adversarial training is $\mathcal{O}(1/\sqrt{N})$」）；前提是检测器光滑（convex measurement $\psi_\vartheta$ 使损失对输入凹）。此外用 Wasserstein 距离把扰动解释为分布鲁棒优化（式 9：$\max_{\mathbb{P}': W(\mathbb{P}',\mathbb{P})\le\varepsilon}\mathbb{E}_{x'\sim\mathbb{P}'}\mathcal{F}$）。
- **「收敛」是否涉及分布漂移：不涉及。** 全文 rg 检索 `concept drift|temporal|distribution shift|time-evolv` **零命中**。PAD 的「distribution-wise」指**扰动球**（训练分布邻域内的对抗扰动分布），数据分布本身固定；时间维完全缺席。
- **对 C4 的含义（仅陈述事实，不下裁决）**：PAD 占据的是「**固定数据分布 + 扰动球内层最大化**的对抗训练收敛保证」；C4 若把最坏情形同时放在「输入扰动 × 时间切片选择」上，其最坏情形集合与 PAD 的 Wasserstein 扰动球是**不同对象**——差异化空间存在，但差异是否足够构成章级创新，须由主代理结合其他三问答裁。

### Q1 补充：Sándor 2026 续作与 ICCP 2024 原件

- Scholar 命中 `hit.bme.hu/~buttyan/publications/SandorKB2026cscs.pdf`（Sándor, Kovács, Buttyán, CSCS 2026）——**已证伪关联**：BME 的 Sándor 是 János Sándor（与 Kovács/Buttyán 合作），与 ICCP 2024 的 **Marian Şandor**（与 Portase/Coleşa，克卢日）**不是同一人**；该 PDF 与本任务无关。
- ICCP 2024 原件已经 **OpenAlex 直连 DOI 查询核到**（`api.openalex.org/works/doi:10.1109/ICCP63557.2024.10793037`）：题名 **Enhancing ML Model Resilience to Time-Evolving Data in Malware Detection Systems with Adversarial Learning**，2024，IEEE ICCP，被引 1，作者 Marian Şandor, Radu Marian Portase, Adrian Coleşa。
- **ICCP 2024 摘要全文（OpenAlex 倒排重建，在线摘要级）**：「ML efficacy degrades over time as malware evolves. We propose **combining feature engineering and adversarial training** to enhance model resilience. By **generating training data mutations**, our method helps models better recognize true malware indicators, **maintaining high performance over time**.」
  - 性质：**对抗训练 × 时间演化数据的联合工作**（防御侧），形态是「训练数据变异 + 特征工程」，不是最坏情形联合优化；无 IEEE OA PDF（被挡），页码未取得，细节只有 El-Hajj 2026 的二手转述（漂移致精度降 9.1%、训练时间 +300%、需已知攻击模式）。

### S3 续：Q1 联合工作专项检索（Scholar）

- Scholar 查询 `"adversarial training" "concept drift" malware`，10 条命中逐一判读：
  - **TAH-GAN（2026 预印本，Research Square，DOI 10.21203/rs.3.rs-10821022/v1）**：「Time-Aware Hybrid Generative Adversarial Network for Robust Android Malware Evasion」。Crossref 摘要直核：「Existing **adversarial generators rarely model temporal change**…We introduce a **time-aware** hybrid GAN…for **drift-aware robustness assessment**. 评估在 **KronoDroid 与三个 AndroMD 特征视图**」。**性质：攻击侧的「对抗 × 时间」联合（生成器建模时间变化以做漂移感知鲁棒性评价）**；预印本（未经同行评审）；非 LAMDA。
  - REPLICANT（arXiv:2608.28499，2026）：deep RL 学「真实规避策略」，强调**现实攻击者建模**（无特权信息）；摘要未见时间维。
  - HYDRA（arXiv 2026）：漂移适应（图对比学习），无对手。
  - 「Evasion Attacks on Cost-Utility-Based Adversarial Training for Online AutoML in IoT」（arXiv 2026）：在线学习+对抗训练，IoT AutoML 场景，相邻非同题。
  - 其余为纯漂移侧或纯对抗侧，无第三篇直接联合。

### S3 续：Q4 LAMDA 引用面全扫（S2 API，2026-10-14）

- S2 `paper/arXiv:2505.18551`（LAMDA）**被引 14 条，逐条标题判读**：
  - Stress-Testing Structure-Aware Calibration…Type Shift（校准/型移）、Cross-Environment Systematic Review、Research Methodologies Narrative Review、Sabbah SSCL+RL（漂移）、FreeMOCA（持续学习）、PLCDroid（伪标签+漂移）、Binary-30K（数据集）、CITADEL（主动学习）、**DeepTrust**、Feature-Centric Survey、OOD Robustness Graph Benchmark（2508.06734）、Regression-Aware Continual Learning、Beyond the Tesseract（数据集清洗）、Drift-Aware Federated Continual Learning。
- **唯一对抗向引用 = DeepTrust（arXiv:2510.12310；DOI 10.1016/j.eswa.2026.132961，ESWA 已发表）**。已抓 arXiv HTML 全文核验：
  - 全文 `rg LAMDA` **零命中**——DeepTrust **引用 LAMDA 但不在 LAMDA 上做实验**。
  - 它的对抗评价在 **ELSA-RAMD 基准（ELSA European Lighthouse on Secure and Safe AI）+ SaTML'25 竞赛**（`benchmarks.elsa-ai.eu`，`ramd-competition.github.io`，DeepTrust 参考文献 [10][11]），Track 1 = **Adversarial Robustness to Feature-space Attacks**，DREBIN 特征 $x\in\{0,1\}^d$（$d=1{,}461{,}078$）。
  - 竞赛基线：DREBIN、Sec-SVM、SVM-CB（用 Temporal Feature Stability 裁剪不稳定特征权重——**时间信息用于特征选择而非最坏情形联合**）、C-PCT、DeepTrust；DeepTrust 拿 SaTML'25 金牌。
- **Q4 中间结论：未发现 LAMDA 上的对抗评价。** 检索途径：本地两份 LAMDA 笔记（`rg adversar` 双零命中）+ S2 全部 14 条引用标题判读 + DeepTrust 全文核验（唯一对抗向引用不在 LAMDA 实验）。「没有」不写成「不存在」——本结论只覆盖 2026-10-14 可检索面。

### S3 续：Q3 补充证据

- **Zainab, Dyrmishi, Bostani, Cavallaro (arXiv:2609.34456, 2026)**「Breaking Windows Malware Detection: A Comprehensive Evaluation of Problem-Space Adversarial Robustness」——Windows PE 问题空间（证书/UPX/节区），全文已抓。关键句（§讨论，行 2035）：「enforcing **executability** substantially reduces the measured effectiveness of some attacks…the Gamma-section attack suffers a dramatic drop in ASR once **non-executable samples are removed**」——**可实施性约束大幅压低表观攻击成功率**的直接实测证据。
- **Demetrio et al.（arXiv:1901.03583）**「Explaining Vulnerabilities of Deep Learning to Adversarial Malware Binaries」——Windows PE，特征归因+真实注入（SecML Malware 线起点）。摘要已核。
- **ELSA-RAMD（SaTML'25）**：把「DREBIN 二值特征上的特征空间攻击」制度化为**正式竞赛赛道**——特征空间攻击在二值静态特征上的**可实施性与接受度**的最强社区证据。

### 工具通路更新（2026-10-14 ~16:30）

- **OpenAlex 直连（无代理）DOI 单条查询可用**；但 `filter=title_and_abstract.search` 检索接口限流（共享 IP 日预算）。DOI 直查绕过该限制。
- arXiv API 偶发 >120s（转后台重试成功）；arXiv HTML 全文（`arxiv.org/html/<id>`）直连可用且快。
- S2 API 间歇 429，重试可用。





