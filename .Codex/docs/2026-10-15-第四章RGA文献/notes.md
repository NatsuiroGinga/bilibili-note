# notes：RGA 文献核实过程记录

## 检索式清单（随用随记）

1. Zotero 语义：「active learning budget-constrained annotation malicious malware detection ranking」
2. 本地混合：「active learning budget ranking precision@k acquisition」
3. 本地混合：「CITADEL semi-supervised active learning concept drift intrusion」
4. 本地混合：「continual learning replay memory buffer budget limited storage class-incremental」
5. scholar：「precision at top k active learning acquisition budget ranking」→ BatchBALD(NeurIPS 2019)、Deep AL survey(Ren, ACM CS 2021)、B-ACT(arXiv:2604.15173)
6. scholar：「active learning concept drift malware detection」→ Chen-Wagner(USENIX Sec 2023)、Dream(CCS 2025)、Li 2024(arXiv:2407.13918)
7. scholar：「active learning for concept drift in malware detection」→ CITADEL 确认 arXiv:2511.11979、ActDroid(C&S 2025)、CALMDROID(IEEE/ACM 2025)、Guerra-Manzanares&Bahsi(JCV 2024)、FALCON(IEEE 2026)
8. scholar：「Faber drift adaptation data stream active learning conference 2022」→ 0 结果（查询过长）
9. scholar：「active learning combined replay memory continual learning limited storage」→ **Faber DSAA 2022 命中**（"Active lifelong anomaly detection with experience replay", IEEE doc 10032405, cites 21）＋ Isele&Cosgun(AAAI 2018, 732 cites)、Brignac(WACV 2023)、Teal(arXiv:2407.00673)、Nie 2023、Daniel 2025、Ho 2024、Szűcs 2025、Das 2023(arXiv:2305.06408)

## 第二批检索（2026-10-15）

10. scholar：「top-k ranked list precision gate threshold active labeling positive yield」→ FunnelAL(arXiv:2607.25276)、**annotation yield 预测**(BMC Med Inform 2025)、Active testing(Nguyen&Ramanan, ICML 2018)
11. scholar：「rare category detection extreme class imbalance active learning survey」→ He&Garcia(TKDE 2009, 15495 cites)、Branco et al.(ACM CSUR 2016, 1932 cites)、Tharwat&Schenck(Mathematics 2023, 311 cites)、Deep AL survey(Li, IEEE 2024, 284 cites)
12. scholar：「technology assisted review recall at k effort stopping active learning systematic review」→ **TAR 停止判据家族**：SWIFT-Active Screener(Howard, 2020, 182)、Callaghan&Müller-Hansen(Syst Rev 2020, 155)、SAFE(Boetje&van de Schoot 2024, 210)、**Li&Kanoulas(ACM TOIS 2020, 58)**、Di Nunzio(ECIR 2018, 38)、Ferdinands(Syst Rev 2023, 113)
13. scholar：「labeling budget feasibility ranking model lift high precision screening fraud detection」→ **Deep anomaly detection under labeling budget constraints(Li, Qiu, Kloft, Smyth, Mandt, ICML 2023, PMLR v202, 27 cites)**、**Cost-Sensitive Top-K Review for Capacity-Constrained Fraud Screening(IEEE 2026)**、Amaretto(IEEE 2022, 86)、Carcillo 2018 流式欺诈主动学习

### 判读要点（与 RGA 的差量，初步）

- TAR 停止判据家族用**运行中已观察的 yield** 决定「何时停止」；RGA 是**事先可行性门**（能否开始/是否退化为被动）＋「预算门×排序门」两道独立门结构。同族但角色不同。
- ICML 2023（Li et al.）显式以标注预算约束做异常检测主动学习——budgeted acquisition 家族强代表作。
- IEEE 2026 Cost-Sensitive Top-K Review 在容量受限筛查下做成本敏感 top-k——与「排序头部×预算」概念最接近，需取原文核。

- **Faber et al., "Active lifelong anomaly detection with experience replay", DSAA 2022**（IEEE 10032405）——主动标注+回放的组合，任务指定的重点对象
- **CITADEL, Haque et al., arXiv:2511.11979**——本地已有 PDF，待核
- **Chen, Ding, Wagner, "Continuous learning for android malware detection", USENIX Security 2023**（cites 182）——对比学习+主动学习+样本选择
- **Guerra-Manzanares & Bahsi, "Experts still needed", JCV 2024**
- **ActDroid, Muzaffar et al., Computers & Security 2025**
- **CALMDROID, Dong et al., 2025**（core-set 主动学习）
- **Isele & Cosgun, "Selective experience replay", AAAI 2018**（存储受限回放代表作）
- **Brignac & Lobo, "Improving replay sample selection and storage", WACV 2023**（显式做存储预算）
- **Das et al., "Accelerating batch active learning using continual learning techniques", arXiv:2305.06408**

## 本地查重结果（2026-10-15，Zotero 语义检索 + 本地混合索引）

- 本地已有漂移侧全文笔记：Transcend（2017 Jordaney）、TESSERACT（2019 Pendlebury）、CADE（2021 Yang）、INSOMNIA（2021 Andresini）——均属漂移检测/拒识族，**不涉及**「排序头部作为获取可行性的门」。
- 本地已有排序方法论文笔记（`wiki/papers/methodology/ranking/`）：SoRR（Hu, JMLR 2022, arXiv:2106.03300）、ATk loss（Fan, NeurIPS 2017, arXiv:1705.08826）、AP-GeM（Revaud, ICCV 2019）——排序侧成熟家族的本地锚点。
- 本地已有 `raw/papers/attack-detection/lamda-related/2025-Haque-CITADEL-Semi-Supervised-Active-Learning-Drift.pdf`（CITADEL 原件在库，待核内容）。
- 查询「continual learning replay memory buffer budget」在本地无「预算受限主动标注 + 存储受限持续学习」组合工作命中；该组合需在线检索确认。
- Zotero 命中 `4N4DE8HP`（Gupta 2025, Generative Active Adaptation for Drifting and Imbalanced NID）——主动适应近邻候选，待在线定位原文。

## 候选与证据等级

（待填）

## 无法获取原文清单

（待填）

## 全文核验判读（2026-10-15，证据等级=本地全文已转换）

### CITADEL（Haque et al., arXiv:2511.11979，21 页，MinerU 全文转换）

- 机制：FixMatch 改造 SSL（Bernoulli bit flip / feature mask 增强）+ 监督对比损失 + 多判据 AL 选择（softmax margin、Lp 范数距离、低置信度，统一打分取 **top-k**；原文 Algorithm 2 第 11 行 `Q ← top-k samples in D_u by score(·)`）。
- 预算角色：外生固定量（50/100/200/400 每期），**从不检验获取是否值得**；无任何「排序头部 lift → 主动获取正收益」的门。
- 与 CL 的关系：原文第 2 节明确「CL addresses a different problem setting and is out of the scope of this work」——**不含存储受限回放**。
- 结论：RGA 的「排序门」与「双预算」命题在 CITADEL 中均不存在；CITADEL 只覆盖「预算受限主动标注（SSL 侧）」。

### Chen, Ding, Wagner（USENIX Security 2023，19 页，MinerU 全文转换）

- 机制：层级对比学习 + 伪损失不确定性选样，每月固定标注量（200/月），warm start 重训。
- 关键原文证据：相关工作段「Rahman et al. have studied continual learning methods for malware detection given storage and training limitations… **Retiring training samples is out of scope in this paper**」——主动标注与存储管理在该文明确是两个分开的问题。
- 结论：同样无排序门；其贡献面是「更便宜的不确定性度量」，不是「获取可行性的前置判据」。

### Li, Qiu, Kloft, Smyth, Mandt, Rudolph（ICML 2023，PMLR v202，29 页，MinerU 全文转换）

- 机制：SOEL——预算约束下的查询策略（k-means++ 多样性覆盖）+ 半监督 AD + 污染率估计。
- 定理 1（第 2.4 节）：标注查询集以半径 δ 覆盖数据、Lipschitz 打分函数以足够 margin 正确排序已标注样本 ⇒ 未标注样本排序正确。**这是「排序泛化」的条件，不是「排序头部 lift 决定获取是否值得」**；δ 是空间覆盖量，α_s 是 ROC 恒等式的提升倍数，二者数学对象不同。
- 预算角色：给定 K 选查询点；无「标注量临界条件 ℓ_c = 1/(α_s p_s)」式的可行性形式化。
- 结论：是 budgeted acquisition 家族强代表作，但不构成 RGA 排序门的先例。

## 未关闭疑点

1. **Faber DSAA 2022 全文未取得**：IEEE 付费墙 + Semantic Scholar/Google Scholar 限流，无法核其「主动标注×回放」的耦合细节（它是否把标注预算与存储预算放进同一形式化，只能等全文后判读）。已进用户手动下载清单。
2. **「排序头部作为获取可行性门」的直接先例检索受限于 scholar 限流**（第 15、16 轮查询被 429 拦截）：annotation yield 预测与 lift-curve 家族未能完成在线核验。基于已核 3 篇全文 + TAR 家族题录层判读，结论为「本轮检索所及范围内未发现直接先例」，非穷尽证明。
3. 「排序头部作为获取可行性门」与「标注产出（yield）预测」家族的关系（BMC Med Inform 2025 题录提示存在该方向）待取原文后补判。

## 无法获取原文清单（已交用户手动下载）

- **Faber, Corizzo, Sniezynski, Corizzo 等，"Active lifelong anomaly detection with experience replay"，IEEE DSAA 2022**（IEEE 文档号 10032405）。相关原因：检索到的唯一同时做「主动标注 × 回放」组合的安全/异常检测侧工作，是 RGA 双预算命题的直接近邻，其耦合方式（标注与存储是否共享一个预算形式化）决定 RGA 的新颖性边界。已尝试：scholar 检索定位（成功）→ IEEE getPDF 直下（空文件）→ Semantic Scholar API openAccessPdf（429 限流）→ arXiv API（无该文）。建议获取路径：IEEE Xplore 校园网/个人订阅，或联系通信作者（Corizzo，American University）要 author 版。

## 修正与风险登记

- 2026-10-15 第 13–16 轮 scholar 查询被 429 限流，annotation yield 与 lift-curve 两个补充方向未完成在线核验；对应结论范围收窄为「已核全文 + 题录层判读」。
- Chen 2023 笔记初稿曾误写 source_pdf 路径为 `lamda-treated`（实际 `lamda-related`）并误留 `key_fingding_note` 占位字段，同轮已修正。
