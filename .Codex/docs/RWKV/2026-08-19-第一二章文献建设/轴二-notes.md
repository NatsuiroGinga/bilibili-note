# 轴二 — 工作笔记（滚动落盘，不事后补写）

RESEARCH_ROUTE=RWKV。建立：2026-08-19。

---

## CP-B01（S0–S3 完成）

已读：根 `AGENTS.md`、`thesis/AGENTS.md`、`raw/AGENTS.md`、`wiki/AGENTS.md`、
`.Codex/docs/RWKV/AGENTS.md`、本任务目录 `task_plan.md` 与 `notes.md`、
`.Codex/docs/RWKV/2026-08-19-第三章引注核验报告.md`（241 行，全读）、
`.Codex/docs/2026-08-18-实体粒度部署证据调研/候选证据清单.md`（531 行，全读）。

候选池实测命令：

```
awk -F'\t' '$1=="B"{printf "%s\t%s\n",$2,$3}' 原件分轴清单.tsv | sort -t/ -k3
→ 99 行
```

### 已定分组框架（框架先于选文献）

四段，逐段与第三章机制一一对应，见 `轴二-task_plan.md` 表。

### 已从前序继承的可复用条目（去重后落轴二的）

E1 Pevný、E2 Bilge、E3 Yen、E4 Hu BAYWATCH、E5 Cui（B）、E6/E11 Ho Hopper、
E7 Dainotti、E8 Alahmadi、E9 Zhang ACSAC、E14 Li Sensors、E15 Garcia（B）、
E20 Anderson、E21 El Mahdaouy（B）、E25 Dijk（B，已占第三章 `[2]`）、
E19 Lee & Stolfo（已占第三章 `[10]`）、E22 Gehri（已占第三章 `[1]`/`[3]`）。

### 本轮新发现（骨架报告称「缺失」但实际本机有原件）

- **`raw/papers/attack-detection/drift/2019-Pendlebury-TESSERACT-Space-Time-Bias-Malware.pdf` 存在。**
  骨架交付的 `gaps` 写「漂移检测经典族整族缺失：TRANSCEND / TRANSCENDENT / CADE / INSOMNIA」，
  但**未提 TESSERACT**。TESSERACT 正是时间偏置的规范出处，直接支撑段一。
  该条纠正骨架结论：段一的时间偏置论证**本机有 A 级原件，不必联网**。
- `raw/papers/attack-detection/drift/2023-Malekghaini-DL-Encrypted-Traffic-Classification-Data-Drift.pdf` 存在。

待办：S4 逐篇核验。

---

## CP-B02（段一核验，实测）

### TESSERACT（Pendlebury 等）

- 原件 18 页。首页文本层为 `arXiv:1807.07838v4 [cs.CR] 12 Sep 2019`，
  **首页无出版载体行**。正式载体（USENIX Security 2019）与页码**须联网核**，本轮不写。
- PDF p.6：三条约束原文标题 `C1) Temporal training consistency`、
  `C2) Temporal gw/mw windows consistency`、`C3) Realistic malware-to-goodware ratio in testing`；
  同页明写 `we are the first to propose C2 and C3`。
- PDF p.9 图 5 与正文：`AUT(F1 , 24m)` 为 ALG1 0.58、ALG2 0.32、DL 0.64；
  正文原句 `the AUT(F1 , 24m) is lower than 10-fold F1`。
- PDF p.10–12 §5「Delaying Time Decay」：三种缓解一律需要新标签或新目标数据——
  增量重训（incremental retraining）、主动学习（uncertainty sampling）、带拒识的分类。
  **表 3 行 `No update` 对应 AUT 0.577 / 0.317**，即不更新时无任何挽回手段。
- 段一角色：时间偏置与时间衰减评价协议的规范出处。
- 短板证据：p.10–12，其全部对策落在「延迟」而非「消除」，且都要求获得测试期的标签或样本。

### Malekghaini 等（Computer Networks 2023）

- 题录从首页与 PDF 元数据核出：*Deep learning for encrypted traffic classification in the face of
  data drift: An empirical study*，Computer Networks 225 (2023) 109648，doi:10.1016/j.comnet.2023.109648。
  16 页。**同行评议正式发表（A）。**
- PDF p.6：训练与目标数据相隔两年时，`the accuracy of the UCDavis CNN model decays by 49.6%,
  compared to 43.9% for UW-H in service-level classification`。
- PDF p.9：两个月间隔亦有约 50% 掉点（`roughly 50% drop in classification accuracy`）。
- PDF p.12–13 §5.2.3「Best practices」：其对策是按**目标数据集规模**调整架构
  （masking 层、dropout 值、学习率）并在目标数据上重训。
- 段一角色：加密流量分类在真实 ISP 两年数据上的漂移实测。
- 短板证据：p.12–13，对策以取得目标年数据为前提。

### Bartos 等（USENIX Security 2016）——落段三

- 题录从首页核出：Karel Bartos、Michal Sofka（Cisco Systems）、Vojtech Franc（CTU Prague）。
  *Optimized Invariant Representation of Network Traffic for Detecting Unseen Malware Variants*，
  Proceedings of the 25th USENIX Security Symposium，August 10–12, 2016, Austin, TX，ISBN 978-1-931971-32-4。
  **印刷页码实测**：PDF p.2 页脚 `25th USENIX Security Symposium 807`，
  PDF p.17 页脚 `822 25th USENIX Security Symposium` → **pp. 807–822**。（A 级，题录完整。）
- PDF p.3（印刷 p.808）：`Bag representation of samples – Instead of classifying flows individually,
  we propose to group flows into bags`；袋 = 同一用户与同一 hostname/域的全部通信；
  表示对特征平移缩放、**袋内置换与袋大小变化**不变；参数由训练数据学习。
- PDF p.2（印刷 p.807）摘要：在大型企业网部署检出 2,090 个新且未见的恶意软件变体，精确率 90%。
- 段三/段四角色：**「把判定对象由单条流换成一组相关流、并把聚合表示的参数学出来」的最早同类工作**，
  是本课题两个机制在文献中最接近的先行工作，必须显式对比。


---

## CP-B03（段二核验 + 两项硬阻塞，实测）

### 硬阻塞一：两个原件 PDF 损坏，无法核验

```
pdfinfo raw/papers/methodology/2019-Azizzadenesheli-RLLS.pdf
  → Syntax Error: Invalid XRef entry 0 / Couldn't read xref table  (346,638 bytes)
pdfinfo raw/papers/methodology/2020-Garg-Unified-Label-Shift.pdf
  → Syntax Error: Invalid XRef entry 0 / Couldn't read xref table  (319,697 bytes)
raw/papers/methodology/2020-Garg-Unified-View-Label-Shift-Estimation.pdf → Pages: 21（正常）
```

`2020-Garg-Unified-Label-Shift.pdf` 损坏在 `2026-08-19-第三章引注核验报告.md` `[5]` 条已记录；
**`2019-Azizzadenesheli-RLLS.pdf` 损坏为本轮新发现。**
两篇均落轴二段二，**在重新取得可读原件前不得进入正式条目**。

### 段二逐条

| 来源 | 载体（原件核出） | 等级 | 关键位置与原文 |
| --- | --- | --- | --- |
| Ben-David、Luu、Lu、Pál《Impossibility Theorems for Domain Adaptation》 | AISTATS 2010，Chia Laguna Resort, Sardinia；`Volume 9 of JMLR: W&CP 9`（原件 p.1 页脚） | A | p.1 摘要：`Our negative results hold with respect to any domain adaptation learning algorithm, as long as it does not have access to target labeled examples`；并证明协变量移位假设「rather weak」，不能免除其他假设 |
| Ganin 等《Domain-Adversarial Training of Neural Networks》 | `Journal of Machine Learning Research 17 (2016) 1-35`，Submitted 5/15; Published 4/16（原件 p.1 页眉） | A | 题录完整，卷期页码原件可读，**无须联网** |
| Lipton、Wang、Smola《Detecting and Correcting for Label Shift with Black Box Predictors》 | ICML 2018（第三章 `[5]` 已核；PMLR 卷期页码原件文本层不可读） | A | 已占第三章 `[5]` |
| Alexandari、Kundaje、Shrikumar《Maximum Likelihood with Bias-Corrected Calibration is Hard-To-Beat at Label Shift Adaptation》 | 原件 p.1 页脚：`Proceedings of the 37 th International Conference on Machine Learning, Vienna, Austria, PMLR 119, 2020`。11 页 | A（页码待联网补） | p.1 摘要：Saerens 等的极大似然校正 `does not require model retraining`，但要求 `p(y|x)` 已校准，而现代神经网络不满足；BBSL 与 RLLS `require model retraining with importance weights` |
| Han 等《Anomaly Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation》 | 原件 p.1 页脚：`Network and Distributed System Security (NDSS) Symposium 2023`，`https://dx.doi.org/10.14722/ndss.2023.24830`。18 页 | A | 摘要与 §IV-C 全篇围绕**降低人工标注开销**；正文多处 `manual labeling is required`、`labeling overhead`。其适应仍以取得目标期样本并人工标注一部分为前提 |
| Kim、Park、Choo《When Model Meets New Normals: Test-Time Adaptation for Unsupervised Time-Series Anomaly Detection》 | PDF 元数据 `Subject: The Thirty-Eighth AAAI Conference on Artificial Intelligence (AAAI-24)`，首页页眉同。9 页 | A（页码待联网补） | 摘要：提出基于趋势估计与自监督的**测试期**适应策略，「during inference」学习新常态 |
| Layeghy、Baktashmotlagh、Portmann《DI-NIDS: Domain Invariant Network Intrusion Detection System》 | 原件 p.1：`arXiv:2210.08252v1 [cs.CR] 15 Oct 2022`。11 页 | **B（预印本）** | 摘要原句：`the state-of-the-art domain adaptation approaches have had limited success`（限定语境为网络入侵检测）。是段二共同短板的**领域内直接自述**，但出自预印本，须单列标注 |

### 段三／段四增补核验

| 来源 | 载体 | 等级 | 位置与要点 |
| --- | --- | --- | --- |
| Bartos、Sofka、Franc | USENIX Security 2016，**pp. 807–822**（页脚实测） | A | 见 CP-B02 |
| Zhu 等《Provable Multi-instance Deep AUC Maximization with Stochastic Pooling》 | PDF 元数据 `Proceedings of the International Conference on Machine Learning 2023`。23 页 | A（PMLR 卷期页码待联网补） | §2：`smoothed-max pooling interpolates between the max pooling (with τ = 0) and the mean pooling (with τ = ∞)`；§3 指出 `requires processing all instances in the bag`，为大袋提出方差缩减随机估计。**与本课题幂平均池化同属「用一个连续参数在 max 与 mean 之间插值」的算子族，必须显式对比** |
| Lo 等 E-GraphSAGE | 原件 p.1 脚注：`accepted for publication in IEEE/IFIP Network Operations and Management Symposium, Budapest, Hungary, April 2022`（即 NOMS 2022）；本机为作者版 `arXiv:2103.16329v8` | A（页码待联网补） | 逐流边分类，图结构只提供邻域特征，判定单元仍是流 |

### 载体存疑（原件文本层无据，文件名标注不可采信）

- `2017-Prasse-…-ECML.pdf`：全文 `rg -i 'ECML|PKDD|LNCS|Lecture Notes'` **在正文与页眉页脚零命中**，
  仅参考文献中出现 Springer。**文件名标的 ECML 无原件依据**，须联网核定，否则按预印本著录。
  与第三章 `[8]` Gulcehre「文件名标 ECMLPKDD 但原件未见」属同型缺陷。
- `2016-Pevny-Discriminative-Models-Tree-Structure-MIL-AISec.pdf`：p.1 为 `arXiv:1703.02868v1`，
  版权行为未填模板 `Copyright 20XX ACM X-XXXXX-XX-X/XX/XX`。**文件名标的 AISec 无原件依据**，
  与前序调研 E1 的「正式会议与页码待核」一致，本轮确认仍未关闭。

---

## CP-B04（联网补齐，实测；已按 raw/wiki 规则完成落盘与笔记）

联网可用。本轮新增 5 篇原件，**每篇均已写全文笔记并更新 INDEX**（`raw/AGENTS.md`「下载即写笔记」）。

| 查询式 | 命中来源 URL | 落盘原件 | 笔记 | 等级 |
| --- | --- | --- | --- | --- |
| `Azizzadenesheli "Regularized Learning for Domain Adaptation under Label Shifts" ICLR 2019 arXiv pdf` | https://arxiv.org/pdf/1903.09734 | `raw/papers/methodology/2019-Azizzadenesheli-RLLS-arXiv1903.09734.pdf`（26 页） | `wiki/papers/methodology/2019-Azizzadenesheli-RLLS标签移位正则化学习.md` | A（首页印 `Published as a conference paper at ICLR 2019`） |
| `Yang "CADE ..." USENIX Security 2021 arXiv pdf` | https://www.usenix.org/system/files/sec21-yang-limin.pdf | `raw/papers/attack-detection/drift/2021-Yang-CADE-Concept-Drift-USENIXSec.pdf`（19 页） | `wiki/papers/attack-detection/2021-Yang-CADE漂移样本检测与解释.md` | A，pp. 2327-2344（页脚实测） |
| （直接取 USENIX 稳定路径） | https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-jordaney.pdf | `raw/papers/attack-detection/drift/2017-Jordaney-TRANSCEND-Concept-Drift-USENIXSec.pdf`（20 页） | `wiki/papers/attack-detection/2017-Jordaney-TRANSCEND漂移检测与共形评价.md` | A，pp. 625-642（页脚实测） |
| `Andresini "INSOMNIA" ... AISec 2021 arXiv` | https://pure.royalholloway.ac.uk/ws/files/43612548/insomnia_camera_ready.pdf | `raw/papers/attack-detection/drift/2021-Andresini-INSOMNIA-Concept-Drift-NIDS-AISec.pdf`（12 页） | `wiki/papers/attack-detection/2021-Andresini-INSOMNIA网络入侵检测漂移鲁棒.md` | A（AISec Workshop），DOI 10.1145/3474369.3486864，**卷内页码 camera-ready 未印，须回 ACM DL 核定** |
| `加密恶意流量检测 综述 软件学报 OR 通信学报 OR 计算机学报 2023 2024 概念漂移` | http://cjc.ict.ac.cn/online/onlinepaper/czh-2023512164928.pdf | `raw/papers/attack-detection/chinese-surveys/2023-陈子涵-…-计算机学报.pdf`（26 页） | `wiki/papers/attack-detection/2023-陈子涵-互联网加密流量检测分类与识别研究综述.md` | A，计算机学报 2023, 46(5): 1060-1085（页眉实测 PDF p.2 = 印刷 1061） |

### 一次误下载已自查并纠正（记录以防复发）

凭记忆写 arXiv 编号 `2111.09319` 取 INSOMNIA，实际下到高能物理论文
`Techni-Composite Higgs models with (a)symmetric dark matter candidates`（DESY-21-196）。
**已删除该误下载文件**（本轮自建，非既有原件），改从 Royal Holloway 机构库取 camera-ready。
教训与仓库既有两起同型事故一致：**标识符不得凭记忆写，必须先检索确认再下载，下载后必须开首页核对题名。**

### INSOMNIA 表 1 关键数字（PDF p.7，实测抄录）

| σ | 方法 | F1(%) | AUT(F1) |
| --- | --- | ---: | ---: |
| — | No-Update | **0.0019** | 0.035 |
| — | Kitsune | **0.0113** | 0.009 |
| 50% | INSOMNIA | 80.88 | 42.39 |

这是段一最强的一条量化证据：时间一致划分下不更新的深度 NIDS **检出率实际归零**。

### 中文缺口已开口

骨架盘点判定「中文文献储备为零」。本轮已补入 1 条 A 级中文条目（计算机学报 2023）。
该文 §5 的概念漂移四问题（印刷 p.1076-1077）**不含判定单元与跨流上下文**，
构成本课题两个机制在中文侧的现状空白证据。
