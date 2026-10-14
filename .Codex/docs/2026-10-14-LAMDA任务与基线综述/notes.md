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

## 查询式登记

（每跑一组查询立即在此追加：日期、入口、查询式、命中数、关键命中路径）

### S1（2026-10-14）本地混合索引 status
- 待跑。

### S2（2026-10-14）本地混合索引 query
- 待跑。

## 待办

- [ ] 本地混合索引检索（强制第一步）
- [ ] Zotero 语义检索
- [ ] 在线：引用 LAMDA / IQSeC-Lab/LAMDA 的工作
- [ ] 在线：任务家族方法与效果量级
- [ ] literature-survey.md
- [ ] task-candidates.md
- [ ] baselines.md
