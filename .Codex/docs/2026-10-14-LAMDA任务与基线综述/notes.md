# 过程笔记：LAMDA 任务与基线综述（2026-10-14）

每完成一组查询或读一篇全文立即追加。证据等级沿用既有规范：
`E3` 本地全文已核页码／`E2` 在线全文已取得／`E1` 在线摘要或官方题录／`E0` 搜索结果未核。

## 本地已读材料登记（步骤 2）

### M1：LAMDA 原论文与相关文献证据台账（2026-09-08）

- 路径：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/.Codex/docs/2026-09-08-LAMDA原论文与相关文献综述/notes.md`
- 证据等级：`E3`（其内各论文均有 raw 原件与 wiki 笔记）
- 已入库并核验的 LAMDA 相关论文（全部有本地原件）：
  - **P1 LAMDA** 原论文：arXiv `2505.18551`，ICLR 2026，OpenReview `1FnCrZtBNQ`；Zotero `6THQM632`
  - **P2 Chen 2023** *Continuous Learning for Android Malware Detection*，USENIX Security 2023；Zotero `FJADHX96`（主动学习直接强基线）
  - **P3 CITADEL**：arXiv `2511.11979v3`，同作者群，半监督主动学习，直接用 LAMDA；Zotero `P86CK65V`
  - **P4 McNdroid**：arXiv `2605.06894v1`，多模态长期漂移基准，同作者群；Zotero `23DE8377`
  - **P5 Sabbah 2026**：arXiv `2605.24294v1`，SSL+RL 漂移维护，引用 LAMDA 但未在 LAMDA 实验；Zotero `DYVZDW5Z`
  - **P6 Chow 2023** *Drift Forensics of Malware Classifiers*，AISec 2023；Zotero `H4HNRY22`
  - 近邻：MADCAT（`59GWHNT2`）、TESSERACT（`F6KINRCT`）、FreeMOCA、Regression-aware（Ghiani）、MADAR、GSS、MIR、PBR、CBRS、A-GEM、ECBRS/PAPA、PCT、Cotter Proxy-Lagrangian、Kumar ICO、TERM、IWMS、DGR

### M2：第三章 LAMDA 候选方案统一筛选台账

- 路径：`thesis/methods/第三章-LAMDA候选方案统一筛选台账.md`
- **已试并被否的方向**（避免重复）：L2 PCT/Focal Distillation、L3 缺口感知修复、L4 条件双侧门控、
  L5 联合、L7 四角色记忆、L8 双侧风险损失、L9 仅调阈值、L11 双玩家约束（v1 乘子发散、v2 无介入）、
  L28 尾锚约束（E1 oracle 否决：受损良性不在冻结高分尾，损伤为全局表征漂移）
- **有信号但只作安全基线**：L1 ER（FPR 与旧恶意翻转下降，AP/FNR 略差）、
  L6 A-GEM 双风险投影（FPR 0.0131→0.0122、翻转 0.0521→0.0320，但 FNR 0.0595→0.0703）
- **待跑**：L29 受限参数修复（head-only + CUR）
- **关键实测数字**（screening_only，v3 探针，MPS 513.6 s）：IID AP `0.9944`，2016 AP `0.9374`/FNR `0.2224`，
  **2017 AP `0.3462`/FNR `0.9185`**
- **核心取舍病灶**：修复当前恶意漏判 ⇒ FPR 大增（0.0595→0.1386）；保护旧决策/压 FPR ⇒ 恶意修复受抑。

### M3：LAMDA 第三章恢复卡

- 路径：`.Codex/docs/LAMDA/LAMDA第三章恢复卡.md`
- 数据合同：到达流 `2013→2014→2016→2017→2018`；开发面板 2016/2017/2018 test；封印 2019–2023；
  2024/2025 恶意样本枯竭（794/23）只作探索性。
- hash/label 审计：总行数 `1,008,381`，无哈希重复、无跨年标签冲突；`year_month` 覆盖不均
  （2025 仅 1 个月）。
- 病灶画像：E1 显示修复损伤为**全局表征漂移**（良性 P90 整体 0.025→0.844），非薄尾被穿。

## 初步工作假设（待文献证据检验，均标"推论"）

- H1：**「2017 年级的时间退化」是 LAMDA 上最强且可统计的病灶**（AP 0.3462、FNR 0.9185，样本量足够），
  而非 2024/2025（那是正例率崩塌导致的数据退化，不可作模型缺口）。
- H2：本地修复-保护线（任务化损失/记忆/投影/博弈）在 2017 病灶上系统受挫，提示病灶可能不在
  「更新策略」而在「表示层/特征空间的年际结构」——文献里该家族是否有表示侧做法（特征演化、
  马尔科夫漂移定位、分布对齐）需要检索确认。
- H3：LAMDA 上引用者极少（2026-02 上线），任务设定（跨年泛化协议、家族迁移、漂移归因）仍有空位；
  需要实查确认。

## 协调者更正（2026-10-14，已确认）

1. **范围放宽**：不只找「用了 LAMDA 的论文」，检索主轴改为**任务**。LAMDA 数据卡自述可用于
   概念漂移分析、时间泛化、家族分类、鲁棒长期恶意软件检测、持续学习。对每条任务轴分别综述
   「已发表工作占到哪一步」：
   - 轴 1：时间泛化／概念漂移适应（Android 或更广序列分类器）
   - 轴 2：持续学习／域增量学习（允许新数据更新，区别于静态外推）
   - 轴 3：家族分类／未见家族泛化
   - 轴 4：鲁棒的长期恶意软件检测（含对抗与规避）
   - 轴 5：低误报／固定告警预算下的检测（DRIFT 主线同款，Android 家族若有已发表工作须报——
     它是潜在可迁移机制来源）
2. **相近宿主数据集**：任何「Android 恶意软件／恶意软件序列分类」长期时间基准（McBndroid、
   AndroZoo 派生基准、Drebin 时间重划等），每个给时间跨度、样本量、是否公开、正例率是否随时间
   崩塌、是否有人报告过时间退化。
3. **索引阻塞**：本工作树 literature_search 是旧版（`EmbeddingBackend.__init__() got an unexpected
   keyword argument 'device'`），不得修它。**改用 drift 工作树索引**（exists=true、stale=false、
   1,934 笔记／154,662 chunks）：
   `cd /Users/bilibili/personal/note/.worktrees/ch3-drift-20260908 && uv run --project scripts/literature_search --locked python -m scripts.literature_search query "<查询式>" --scope local --mode hybrid --json`
   只在该树跑查询命令，不在该树写文件。

## 查询式登记

（每跑一组查询立即在此追加：日期、入口、查询式、命中数、关键命中路径）

### 第二轮更正（2026-10-14，用户）

「不要只盯时间泛化/概念漂移方法，看 HF 界面与数据集论文的介绍」。综述与候选改从
**LAMDA 官方 8 条任务轴**出（协调者已从 HF 数据卡、原论文与 ICLR 演示版笔记核出，直接引用）：

| # | 任务 | 已有官方/已发表读数 | 余量线索 |
| --- | --- | --- | --- |
| 1 | 二分类+时间泛化（IID/NEAR/FAR） | LightGBM F1 `47.24±27.33`／MLP `47.59±25.30`／SVM `41.86±22.55`／XGBoost `42.75±25.86`；CADE（APIGraph）F1 `0.4407`/FNR `0.4734`/FPR `0.1729` | FAR FNR `64–70%` |
| 2 | Domain-IL 持续学习 | 2025 平均 F1：Joint `88.52±0.46` vs Naive `72.71±0.83` | **15.8 点间隙** |
| 3 | Class-IL（154 家族，测试家族样本数>10） | 附录 J | 该定义让测试标签参与任务定义（缺陷已标注） |
| 4 | Task-IL | 演示版 p.14–15 | 待查 |
| 5 | 家族分类 | 全库 1,380 恶意家族、150,604 单例、2,985 未知家族 | 长尾极重 ⇒ 真余量 |
| 6 | 主动学习/半监督适应 | 演示版展示 Chen-AL | 待查 |
| 7 | 标签漂移/弱标签时间版本 | 附录 F 表 13：2017 年 5.19% 原恶意样本当前被判良性 | 标签本身随时间变 |
| 8 | 表示学习对比（静态二值 vs 图/多模态） | CADE/APIGraph 对比 | 待查 |

**优先深挖：轴⑤家族分类（150,604 单例长尾）与轴② Domain-IL（15.8 点间隙）**。
轴①⑦次优先（FAR FNR 64–70%、2017 5.19% 标签翻转是可统计病灶）。
宿主数据集综述改为回答「各轴在别的宿主上做到哪一步」。基线清单按轴分组。

### S1–S2（2026-10-14）本地混合索引（drift 工作树，scope=local/paper，mode=hybrid）

- 索引：ch3-drift-20260908 工作树，1,934 笔记，向量模型 intfloat/multilingual-e5-small。
- 查询 1「Android malware concept drift temporal generalization」→ Top6：MADCAT-TTA 全文、
  TRANSCENDENT、Berruz 漂移重训、El-Hajj 多尺度 LOEO、Chow 漂移取证。
- 查询 2「Android malware family classification few-shot open set」→ Top6：**TRANSCENDENT**（保形评价）、
  Lichy RF-Beats-CNN、El-Hajj LOEO、CBSeq、Berruz、Chow。
- 查询 3「malware family classification long tail imbalanced」→ Lichy、CBSeq、MADCAT、TRANSCENDENT、
  El-Hajj、Anderson。
- 查询 4「continual learning Android malware detection replay」→ **Chen 2023 持续学习**、TRANSCENDENT、
  MADCAT、CBSeq、**NetGuard 主动适应 NIDS**、**Nguyen 极端 FPR 恶意软件检测**。
- 查询 5「active learning malware detection labeling budget」→ NetGuard、TRANSCENDENT、Nguyen 极端 FPR、
  Inan 校准泄漏安全、El-Hajj、MADCAT。
- 查询 6「malware detection label noise weak labels VirusTotal」→ **Nguyen 极端 FPR**、TRANSCENDENT、
  El-Hajj、Prasse 加密流量 LSTM、Anderson、BAYWATCH。
- 判读：本地库在轴①②⑥上已较厚（Chen/CITADEL/MADCAT/回放家族全有全文笔记）；
  **轴⑤家族分类/少样本/开集是本地最薄的轴**，只有 TRANSCENDENT（保形/拒识）与若干间接命中；
  轴⑤需要重点外部检索。
- 既有领域综述（`wiki/papers/malware/LAMDA-2026-原论文与时间漂移相关工作综述.md`）已登记四个
  研究空白任务（P0 无泄漏静态时间泛化基准、P1 源期多域静态稳健训练、P1 延迟标签主动/半监督维护、
  P1 标签版本与家族不确定性），本任务综述须与它们对齐并检验外部占用情况。

### S0（2026-10-14）本工作树索引状态
- 入口：`uv run --project scripts/literature_search --locked ... status --json`（LAMDA 工作树）
- 结果：`exists=false, stale_reasons=["missing_index"]`，当前笔记 1,770 篇未建索引。
  → 证实阻塞，切换 drift 工作树索引。

## 待办

- [ ] 本地混合索引检索（强制第一步）
- [ ] Zotero 语义检索
- [ ] 在线：引用 LAMDA / IQSeC-Lab/LAMDA 的工作
- [ ] 在线：任务家族方法与效果量级
- [ ] literature-survey.md
- [ ] task-candidates.md
- [ ] baselines.md
