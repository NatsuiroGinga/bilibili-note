# notes：七族核验查询日志

证据等级图例：`本地全文`＝`wiki/papers/**` 已有 MinerU 全文笔记（原件在 `raw/papers/**`）；
`在线全文`＝已下载全文入 raw；`在线摘要`＝只取到摘要/题录；`外部候选`＝仅检索命中。
每条记录：查询式 / 来源 / 证据等级 / 命中 / 纳排理由。

---

## F0 复核「全空」（任务第一问）

**方法**：对 `wiki/papers/attack-detection/`（含 9 篇近邻全文与更广 attack-detection 语料）做关键词 `Grep`。

**结论：主代理的「全空」是 9 篇近邻子语料的关键词计数结果，不是仓库级或领域级事实。**
仓库 `wiki/papers/` 全域早已收录：
- F1 DRO：`methodology/2020-Sagawa-GroupDRO群体移位.md`、`2021-Duchi-分布鲁棒均匀性能.md`、`2021-Zhai-DORO异常值鲁棒分布优化.md`，以及 ranking/ 下大量 CVaR 篇（均 `本地全文`，原件在 `raw/papers/methodology/`）。
- F2 IRM/不变性：`methodology/2021-Ahuja-不变性与信息瓶颈.md`（IB-IRM）、`2021-Krueger-REx风险外推.md`（REx/VREx）。
- F3 课程：`methodology/2009-Bengio-课程学习.md`（原始）、`2020-Klink-自步深度强化学习.md`。
- F5 保形/NP：`methodology/2018-Tong-纽曼皮尔逊分类.md`、`2019-Tibshirani-协变量移位加权保形.md`、`2024-Angelopoulos-保形风险控制.md`、`2024-Farinhas-非交换保形风险控制.md`、`2025-Almeida-协变量移位高概率风险控制.md`。
- F6 博弈：`wiki/papers/game/` 整目录（Stackelberg 安全博弈原始线与近年 IDS 应用）。

**⇒ 判读**：9 篇近邻的「零命中」属实，但只能说明这 9 篇没提；**不能推断该族未被引入安全域**。真正的判据是下面对每一族的在线检索。

---

## F1 分布鲁棒优化（DRO）

**本地（`本地全文`）**：Sagawa ICML 2020（Group DRO 原始）、Duchi & Namkoong AoS 2021、Zhai DORO、ranking/ 下 CVaR 线（Prashanth 2019 集中不等式、Curi 2019 ADA-CVaR、Levy 2020、Zhu 2022 pAUC-DRO）。

**在线（`在线摘要`，WebSearch `distributionally robust optimization malware detection concept drift`）**：
- **命中：DRO 已进入恶意软件域（不止近邻 9 篇）**：
  1. *Distributionally Robust Deep Neural Network for Malicious App Software Dynamic Detection*（IEEE，document 10912979）——**Wasserstein 模糊集 + 面向未见恶意 App 的 DRO-DNN**，Lipschitz 上界近似。
  2. *Evaluating DRO for Zero-Day Malware Anomaly Detection*（IISE Annual 2026 摘要）——**零日恶意软件**上 Wasserstein DRO（= 正则化 ERM）。
  3. arXiv 2508.12402 —— Wasserstein DRO 检测器，对**误报率**加分布鲁棒机会约束，动机是扰动分布**非平稳／重尾／多峰**。**⇒ 与 P3（FPR 预算）最对口。**
- 纳排：均只取到摘要/题录（`在线摘要`/`外部候选`），升级需全文。

**判读**：F1 在恶意软件域**已被引入**；**Android 长期时间漂移上的 GroupDRO** 本次未命中。

---

## F2 不变性学习（IRM/VREx/IB-IRM）

**本地（`本地全文`）**：Ahuja IB-IRM、Krueger REx/VREx。
**缺失**：Arjovsky 2019 IRM 原始出处、Rosenfeld 2021 IRM 可辨识性批评（`Grep` 于 `wiki/` 零命中）。

**在线（`在线摘要`，WebSearch `invariant risk minimization Android malware temporal domain generalization`）**：
- **命中：TIF 直接占据该格位（确证）**：*TIF: Learning Temporal Invariance in Android Malware Detectors*，Zheng, Yang, Ngai, Jana, Cavallaro；arXiv:2502.05098；IEEE TSE 2026，DOI 10.1109/TSE.2026.3698484。
  - 自称**首个面向恶意软件检测的时间不变训练框架**；按**应用观察日期**构造环境；基于不变学习（环境不变约束 EIC）；两阶段：① 逐环境 ERM + 多代理对比学习 ② **不变梯度对齐 IGA**；可嵌入任意学习式检测器；基线含 V-REx、CLOv、IRM。
- 纳排：TIF 是**必须引用的直接近邻**；只取到摘要 + HTML 片段。

**判读**：F2 在 **Android 恶意软件时间漂移上已被 TIF 占据大半**。

---

## F3 课程学习

**本地（`本地全文`）**：`methodology/2009-Bengio-课程学习.md`（原始 Bengio 2009）、`2020-Klink-自步深度强化学习.md`；attack-detection 下 PINN 课程线 4 篇、`课程式对抗训练-在线视角`（Wasserstein 泛化界）、朱焱雷 2.3.3/3.5.1。

**在线（`在线摘要`，WebSearch `curriculum learning malware detection concept drift Android`）**：
- **命中：MalTutor 直接先例（确证）**：Li 等，*Understanding Model Weaknesses: A Path to Strengthening DNN-Based Android Malware Detection*，ISSTA/ACM SE 2025，DOI 10.1145/3728884。
  - **Android 恶意软件家族不均衡**（179 个 Drebin 家族 top5 占 57%）；用**预测不确定性**（自验证/交叉验证 + LSTM 自编码器聚类）把样本按**学习难度**分组，**单遍离散课程**由易到难；accuracy +31.0%、F1 +138.8%。
  - 该文的参考含概念漂移综述 Hu 等；但课程本身针对**家族不均衡／不确定性**，不是时间重排。
- 另命中：CCL 类别级课程（2022）、IoT 自适应课程 + XAI（2025，`外部候选`）。
- 纳排：属**家族不平衡侧**先例；**时间序课程**未命中。

**判读**：F3 在 Android 恶意软件域**已被引入**（MalTutor，家族不均衡面）；**与 P1–P4 时间漂移直接对口的课程未命中**。

---

## F4 核心集／数据剪枝

**本地**：`methodology/training-efficiency/` 有 safe screening / 稀疏反传，但**无 coreset 原始出处**（Toneva 遗忘样本、Sorscher scaling law 均未见）。attack-detection 侧 SEED/MORPH/ADAPT/HYDRA 等笔记含 "coreset" 一词（选样/记忆相关）。

**在线（`在线摘要`，WebSearch `coreset selection data pruning malware detection intrusion detection`）**：
- **命中：F4 已进入安全域（IDS 侧为主）**：
  1. **SSFSS**（Scientific Reports 2026，s41598-026-66614-x）—— 序贯子模特征-样本选择，IoT IDS；训练集降到 **5–15%** 仍保 97.5–99.5% 准确率，训练加速最高 70×。
  2. **CCS-CP 类比例核心集**（ICCV 2025W CDEL）—— 在 **CICIDS2017 / CTU13 / UNSW-NB15** 上证；CTU13 剪 90% 不掉点。
  3. *Beyond Learning Algorithms: The Crucial Role of Data in Robust Malware Detection*（IEEE S&P 2025）—— **保留数据集性质的核心集可增强恶意软件分类器韧性**。
  4. **ELFS** —— 无标签核心集选择（用伪标签难度分数）。
- 纳排：均为 IDS/恶意软件侧 `在线摘要`。

**判读**：F4 在安全域（尤其 IDS）**已被引入**；**Android 长期漂移上的核心集**未命中，但**同族（记忆选样）在本课题已被多轮否决**（角色记忆 M/O 四臂、MIR/GSS/PBR/CBRS 作近邻）。

---

## F5 保形预测 / 分布无关风险控制

**本地（`本地全文`）**：Tong NP 分类（Sci Adv 2018 原始）、Tibshirani 加权保形、Angelopoulos CRC、Farinhas 非交换 CRC、Almeida 协变量移位高概率风险控制。

**在线（`在线摘要`，WebSearch `conformal prediction Neyman-Pearson FNR control Android malware detection`）**：
- **命中：保形已进入 Android 恶意软件域**：
  1. *Android Malware Detection with Unbiased Confidence Guarantees*（Neurocomputing 280 (2018) 3–12）—— **标签条件 Mondrian 保形（LCMCP）** 给出**逐类有效**保证（恶意类单独可控误差），RF 骨干。**⇒ 与 P2/P3（类别条件误差）最对口。**
  2. *Operational Android Malware Filtering: Calibrated Probabilities and Distribution-Free Guarantees*（KJMR 2025-12）—— **15,036 个 Android 静态特征 App**；LR/RF/**XGBoost**；后验校准（Platt/Isotonic）+ 归纳保形，目标 α∈{0.10,0.05,0.01}，**RF/GBDT 排序最好**。**⇒ 与本课题 GBDT 观察直接一致。**
  3. DroidScribe（运行时行为 + CP，SVM）等。
- **NP 分类（专名 Neyman–Pearson）本次检索未命中** Android 恶意软件应用。

**判读**：F5 **已被引入 Android 恶意软件域**（保形/校准/分布无关保证），含 GBDT 骨干先例；**NP 专名版本未命中**。

---

## F6 博弈论

**本地（`本地全文`）**：`wiki/papers/game/` 整目录（Kiekintveld 2011 Stackelberg vs Nash 安全资源分配、Bayesian Stackelberg、MTD 安全博弈、近两年 SDN/IDS 博弈应用）；朱焱雷 3.5.2「Stackelberg 均衡收敛」（`本地全文`）。**且有 `.Codex/docs/2026-07-21-博弈论论文下载与精读*`、`2026-07-21-博弈论三目标协调文献审计.md` 等既有精读。**

**在线（`在线摘要`，WebSearch `Stackelberg game malware detector evasion temporal drift`）**：
- **命中：F6 已全面进入恶意软件+漂移域**：
  1. *A Stackelberg Approach to Federated Learning for Malware Detection*（CEUR-WS Vol-3962 paper36；另 UNIPA 0250）—— **服务器为 leader 奖励高质量数据、客户端为 follower**，证明**唯一 Nash 均衡收敛**，多年维持模型有效对抗漂移。
  2. *Adversarial Co-Evolution of Malware and Detection Models: A Bilevel Optimization Perspective*（2026）—— 防御-攻击迭代共演化，**双层优化**；基线逃逸率 90–96% → 降至 0–1.89%。
  3. *On concept drift, deployability, and adversarial selection in ML-based malware detection*（UMSL）—— 概念漂移 + 对抗选择。
  4. GameSec 2019 / DTIC：规避的**子博弈完美均衡**两玩家 Stackelberg。

**判读**：F6 在恶意软件漂移域**已被大量引入**。本课题边界：**M2/J06「双分布对手框架」曾被数学否决（目标精确分解）**，须如实记录；「生成器 vs 分类器」落点未命中但**塌缩风险最高**（见 families.md #18）。

---

## F7 平坦极小值（SAM）

**本地**：**无 SAM 原始出处**（`Grep Foret|Sharpness-Aware Minimization` 于 `wiki/` 零命中；"SAM" 命中均为后缀自动机等假阳性）。

**在线（`在线摘要`，WebSearch `sharpness-aware minimization SAM malware detection`）**：
- **命中：SAM 已进入恶意软件域（图像/家族分类侧）**：
  1. **MalFormer**（IEEE Access 2025）——ViT 恶意软件分析，**SAM 优化**，报告对**混淆**强鲁棒（DOAJ 8a66faf5a4164edb918226eaadd81153）。
  2. **Separable ViT + SAM**（KCI 2024）——灰度可视化恶意软件家族分类，SAM 优于 ResNet18/ViT/CrossViT；AndroDex 上对混淆有效。
  3. **Chai et al.**，IEEE TNSM 2022 —— **自适应 SAM** 用于**小样本恶意软件分类**。
  4. 网络安全另见学位论文评估 DNN 上 SAM/DRM vs ERM 对误标数据鲁棒性。
- 纳排：均图像/家族分类，非 Android 静态特征时间漂移；均 `在线摘要`。
- 关联：朱焱雷 3.5.3「平坦极小值泛化」（`本地全文`）＝中文学位论文已接受该套路。

**判读**：F7 在恶意软件域**已被引入**；Android 静态二值特征 + 年度漂移上的 SAM 未命中；**本地缺 SAM 原始出处**。

---

## 病灶 P1–P4 复核（对制品原文，2026-10-14）

### P1（E1 `metrics.json` per_year，`screening_only`，MPS，seed 42）——**证实**
逐年 AUROC：2016 `0.9458`、**2017 `0.5712`**（最小）、2018 `0.6423`、2019 `0.9549`、2020 `0.9562`、2021 `0.9460`、**2022 `0.9610`**（最大）、2023 `0.8821`、2024 `0.7817`、2025 `0.5958`。
⇒ 「0.5712(2017)–0.9610(2022)」为 min–max，**属实**。
**⚠️ 冲突披露**：路线总控 §二 引 stage-b 读数称「2025 AUROC 回升到 0.9851」，而 E1 同一 2025 得 `0.5958`。两读数来自不同运行与 panel（E1 为 `train_plus_test_combined`）。**同一 2025 年两个相反 AUROC，须先定权威制品再引用**。

### P2（E3 `metrics.json` pos_rate）——**证实**
2013 `0.513508`（51.35%）、2024 `0.016396`（1.64%）、2025 `0.000515`（0.05%）。⇒ 属实。

### P3（E1 group_a 源标定 vs group_b 目标年自校准）——**方向证实，量级区间需修正**
源阈值 `0.9929`(budget 0.001)/`0.8511`(0.01) 迁到目标年，group_a 实测 FPR 多数**远低于**预算（2022 `0.00069`、2024 `0.000042`、2025 `0`）⇒ **「过保守迁移」属实**。
自校准（group_b）降 FNR：0.001 档多为 2–26 点（2017 仅 `0.9909→0.9681`=2.3 点），0.01 档可达 **35–49 点**（2020 `0.7202→0.3714`、2021 `0.7867→0.3482`、2022 `0.7425→0.2484`）。
⇒ **「降 11–30 点」偏窄**（0.01 档有 35–49 点的年份）；**「但仍高」属实**（自校准后 FNR 多数仍 `0.25–0.97`）。

### P4（E3 标签共识）——**数值属实，但「随时间下降」为端点驱动，证据薄弱**
- `S2_pos_vt_median` 全序列：2013 `9`、2014 `11`、**2016 `12`**、2017 `6`、2018 `6`、2019 `10`、2020 `7`、2021 `7`、2022 `10`、2023 `6`、**2024 `5`**、2025 `5`。
  ⇒ 「12(2016)→5(2024)」取自**端点**；序列**非单调**（2019 与 2022 均为 `10`）。
- `S1_pos_frac_at_threshold`：2013 `0.0681`（6.8%）…2024 `0.4811`（48.1%）。⇒ 「6.8%→48.1%」同为**端点对比**，序列非单调（2019/2022 = `0.077`）。
- **判读：P4 的「随时间下降」不是稳健趋势，而是 2016/2013 端点与 2024 端点之差。** Spearman `+0.737 (n=10)` 无法从本制品复算年份集合，但**端点敏感 ⇒ 不可当因果**（与任务给定一致）。**该条作为机制依据应降级为「待验证」，不得单独支撑候选选择。**
- 补充（E3 实证到的事实，可替代 P4 表述）：`families_appearing_once/n_families`：2013 `1618/1765`、2020 `30858/31234`（近全单例）、2023 `6016/6148`、2024 `664/691`、2025 `21/23`——**单例家族爆炸**是本制品最显著的标签侧现象，比 vt 中位数更适合作为「标签管线时间退化」证据。

---
