# 检索笔记：C1 近邻论文入库（2026-10-14）

## 一、工具与通路的实测结论（**下次直接用，不要重试错的方式**）

| 通路 | 结果 | 备注 |
| --- | --- | --- |
| scholar CLI | ✗ 不可用 | 需 Chrome 调试端口，本会话无 |
| Semantic Scholar API | ✗ `429 Too Many Requests` | 重试两次均 429，无 key 不可用 |
| **OpenAlex API** | ✅ **可用，无需 key** | `https://api.openalex.org/works`，直连即可 |
| **arXiv API** | ✅ **仅 `https://` + `-x http://127.0.0.1:7890`** | `http://export.arxiv.org` 直连**静默返回空**（不报错）——差点被当成「论文不存在」 |
| arXiv abs 页面 | ✅ `https://arxiv.org/abs/<id>` + 代理 | 用于复核标题 |

**关键教训**：`http://export.arxiv.org/api/query` 直连**返回空字符串且 exit 0**，
我的解析器据此输出「未找到」——**包括本地已存全文的 MADCAT**。这是
「某工具取不到 ≠ 来源不可达」的又一次复发（检查点 §八已登记，仍复发）。
**凡解析器报「未找到」，必须先看原始返回字节数再下结论。**

**另一个错误**：OpenAlex 的 `search=` 是全文模糊匹配，按 `cited_by_count` 排序只会返回
高被引综述（实测首条是 SVM 综述，2365 次引用）。**正确用法是
`filter=title_and_abstract.search:<短语>` + `sort=publication_year:desc`。**

## 二、查询式与命中（逐条留痕）

| # | 查询式 | 命中 | 用途 |
| --- | --- | --- | --- |
| 1 | `title_and_abstract.search:android malware concept drift adaptation` | **16** | C1 空间全扫（最有效的一条） |
| 2 | `title_and_abstract.search:malware test-time adaptation` | 28 | MADCAT 同类 |
| 3 | `title_and_abstract.search:malware label noise temporal degradation detection` | **1** | C2 空间（几乎空） |
| 4 | `title_and_abstract.search:continual learning malware catastrophic forgetting domain incremental` | **5** | C3 空间 |
| 5 | `title_and_abstract.search:android malware label quality annotation reliability` | **0** | C2 空间的标签质量侧 |
| 6 | arXiv 标题含 ADAPT 且摘要含 pseudo-labeling 与 malware | 3 | 意外带出 LFreeDA |

## 三、三个候选空间占位（2026-10-14 实测，**同日同比**）

| 候选 | 空间规模 | 占位情况 |
| --- | --- | --- |
| **C1** 零/低标签时间泛化 | 16 条（含 8 篇 2025–2026 新作） | **拥挤**：SEED(预算半监督)、LFreeDA(无标签)、MADCAT(无标签 TTA)、CITADEL(主动学习 400)、HYDRA、MORPH、ADAPT |
| **C2** 标注管线时间退化 | **1 条**（且是 LLM few-shot，非时间退化） | **近乎无人**；但见 task_plan 的评价循环性风险 |
| **C3** Domain-IL 安全回归 | 5 条（MalCL、FreeMOCA、BinAdapter、Adapter-based） | 中等；本地已有 9 个否决实现铺在同路 |

**⇒ 与 2026-10-14 综述代理结论的直接冲突**：综述称 C1 的零标签端「是明确空位」，
**C2 未被占用只作「第二落点」**。实测是反过来——**C1 空位已被占，C2 的空间反而近乎无人**。
该冲突必须写回候选对照文档与综述索引（task_plan §二.4）。

## 四、下载台账（全部落 `raw/papers/attack-detection/`）

| 文件 | arXiv | 月份 | 大小 |
| --- | --- | --- | --- |
| `2026-Amalapuram-SEED-Semi-Supervised-Continual-Malware-Drift-Budget.pdf` | 2605.24903 | 2026-05 | 2.1M |
| `2026-Chen-HYDRA-Proactive-Android-Malware-Drift-Adaptation.pdf` | 2609.26352 | 2026-09 | 2.0M |
| `2026-Concept-Drift-Adaptation-Self-Supervised-Reinforcement-Learning-Android.pdf` | 2605.24294 | 2026-05 | 4.5M |
| `2025-Li-LFreeDA-Label-Free-Drift-Adaptation-Windows-Malware.pdf` | 2511.14963 | 2025-11 | 4.3M |
| `2025-McFadden-DRMD-Deep-Reinforcement-Learning-Malware-Drift.pdf` | 2508.18839 | 2025-08 | 324K |
| `2025-Alam-ADAPT-Pseudo-Labeling-Concept-Drift.pdf` | 2507.08597 | 2025-07 | 3.4M |
| `2024-He-Combating-Concept-Drift-Explanatory-Detection-Adaptation.pdf` | 2405.04095 | 2024-05 | 4.1M |
| `2024-Alam-MORPH-Automated-Concept-Drift-Adaptation.pdf` | 2401.12790 | 2024-01 | 3.4M |

**全部经 `file -b` 校验为真 PDF**（非 HTML 错误页）——下载后必须做这一步，
历史上出过 `hf download` 静默失败却报成功的事故。

## 五、待办

- [ ] MinerU 转全文（`pdf-converter`），中间文件写 `/tmp` 任务目录
- [ ] 8 份结构化笔记（frontmatter 八字段 + `source_pdf` + 页码）
- [ ] 更新 `wiki/papers/attack-detection/INDEX.md`
- [ ] **冲突写回**：候选对照文档 + `task-candidates.md` 的 C1 空位论断
- [ ] MADCAT 引用图：OpenAlex 记 `cited_by_count: 0`（2026-10-14）；S2 因 429 未取得，**待补**

## 六、全文抽取结果（2026-10-14 文献代理，供候选排序读取）

阅读源：`wiki/papers/attack-detection/<同名>-全文.md`（MinerU 转换），**逐篇读全文**。
证据等级统一为「在线全文已下载」。8 份结构化笔记落 `wiki/papers/attack-detection/`。

| # | 论文（笔记） | 实验数据集 | 特征表示 | 平台 | 监督设定 | 固定 FPR 工作点 | 评价指标 | 主结果数字（带章节号） | 与 LAMDA 的关系 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [[2024-Alam-MORPH自动概念漂移适应]] | AndroZoo + EMBER | 稀疏二值（16978 / 2381 维） | Android + Windows | 半监督自训练，无新标注；RQ2 叠加 100/月主动学习 | 无 | F1 / FPR / FNR | F1 +4.07%(AndroZoo)、+0.83%(EMBER)，FNR −14.78% / −5.74%（§6.2）；DE++ F1 23.3% vs 53.8%（§6.4） | 部件来源 + 仅对照 |
| 2 | [[2024-He-Dream解释性检测与漂移适应]] | Drebin + MalRadar | 稀疏二值 / MaMaDroid 包对 / Damd opcode 序列 | Android | 主动学习，标注预算 10/20/30/40/100 | 无 | AUC / F1 / Accuracy / CBP / DRR | 预算 10 时 F1 `0.805` vs 基线 `0.449`；0.9 精度需 19.54 样本 vs 99.12（§5.3、§5.5） | 仅对照 + 部件来源 |
| 3 | [[2025-Alam-ADAPT伪标签抗概念漂移]] | Drebin + APIGraph + BODMAS + EMBER + PDF | 稀疏二值（16978 / 1159 / 2381 / 950 维） | Android + Windows + PDF | 初始标注 + 伪标签（无新标注）；扩展 50/月主动学习；另有 source-free 变体 | 无 | F1 / FPR / FNR / Absolute Exposure / Wilcoxon | Drebin XGBoost+ADAPT F1 `57.1`、FPR `0.24`、FNR `56.6`；APIGraph `76.8`；BODMAS `99.6`；EMBER `93.5`（Table II） | 部件来源 + 仅对照 |
| 4 | [[2025-McFadden-DRMD强化学习恶意软件漂移]] | Transcendent + Hypercube | 稀疏二值（Drebin 10k / Ramda 379 维） | Android | 月度主动学习，预算 0/50/100/200/400 + 拒识 | 无 | AUT（基于 F1）/ 标注预算 / 拒识率 | 分类-仅平均 AUT +8.66、分类-拒识 +10.90（§1）；AL=400/Rej=400 时 AUT `84.66`（Table 1） | 仅对照 + 部件来源 |
| 5 | [[2025-Li-LFreeDA无标签漂移适应]] | MB-24+ + BIG-15 + MalwareDrift | 恶意软件图像 + CFG（PalmTree 嵌入） | Windows | **无标签适应**：源标注 + 目标无标签；对照 AdvDA 用 50/300/每类 10 目标标签 | 无 | Accuracy / macro-F1 / 伪标签准确率·覆盖率·ACS | MB-24+ 准确率 `82%`、F1 `79%`，低于全监督上界 2.8–4%；BIG-15 `98%`；MalwareDrift `52.9%`（§3.2.3、§4.2.3、§5.2.3） | **直接近邻** + 部件来源 |
| 6 | [[2026-Amalapuram-SEED预算半监督持续检测]] | BODMAS + AndroZoo + APIGraph | DREBIN 特征（1159 / 16978 维）/ PE 2381 维 | Android + Windows | 半监督持续学习：seen 任务 20% 标注，unseen 任务月度标注预算 50–250 | **有**：FPR = 10⁻¹ / 10⁻² / 10⁻³（§6.8） | PR-AUC / AUT / TPR@固定FPR | unseen-AUT(A) BODMAS `0.810`、AndroZoo `0.855`、APIGraph `0.930`（Table 3）；相对 HCL* +40%(BODMAS)/+14%(AndroZoo) | **直接近邻** + 部件来源 |
| 7 | [[2026-Chen-HYDRA分层图对比漂移适应]] | HiGraph + Drebin | 分层图 CFG + FCG（对照 Drebin 静态特征） | Android | 源标注 + 目标预算标注（50–400；留出 10–500）+ 伪标签 | 无 | F1 / Accuracy / FPR / FNR | Task A 预算 100：FNR `37.60`、FPR `0.67`、F1 `95.00`（Table 2）；较 DREAM 省 87.5% 标注（§4.3） | 仅对照 + 部件来源 |
| 8 | [[2026-Sabbah-自监督强化学习漂移维护]] | 模拟器 + 真机 Android（2008–2020 年度窗） | 静态特征 + 动态特征（两套） | Android | 标签可用周期维护（无主动学习预算） | 无 | 平衡准确率 / 宏F1 / 记忆集准确率 / 成本 的 AUT | real-dynamic RL 平均准确率约 `0.628`、成本约 `3.75`；real-static RL 宏 F1 约 `0.752`（Table II） | 仅对照 + 部件来源 |

### 与字段表冲突或意外的事实（文献代理自报）

1. **8 篇无一使用 LAMDA 数据集**：全部落在 AndroZoo / Drebin / HiGraph / Transcendent / BODMAS / EMBER / MB-24+ / BIG-15 / MalwareDrift 等公开集。SEED 虽属 CITADEL 同作者组，但用的是 AndroZoo/APIGraph 的 Chen et al. Drebin 特征，**不是** LAMDA。Sabbah 仅在相关工作里引用 LAMDA 作为漂移证据。
2. **只有 SEED 报告固定 FPR 工作点**（FPR=10⁻¹/10⁻²/10⁻³ 下的 TPR 轨迹，§6.8）；其余 7 篇都只报 F1/FPR/FNR 或 AUC/准确率数值，**无一是固定 FPR 运行点**。故对 LAMDA 的「FNR@固定FPR」轴，本轮只有 SEED 构成可对照读数，且它是**经验工作点**、不含有限样本证书。
3. **LFreeDA 把「无标签端」从空白推成已发表结果**（Windows，MB-24+），与 task_plan 记录的实测一致，进一步坐实「C1 零标签端已被占」。
4. **HYDRA 实为 ACM CCS 2026 论文**（DOI 10.1145/3830454.3832684，作者版含完整附录），DRMD 为 **AAAI 2026 扩展版**，SEED 页眉标注 **Accepted to ACM Transactions on AI Security and Privacy (June 2026)**；其余 5 篇取得版本为 arXiv 预印本，正式出处未在原件内页核到。
5. **`2026-Sabbah-自监督强化学习漂移维护.md` 在本次任务前已存在**（date 2026-09-08）。本次按「优先更新已有规范笔记」将其更新（date→2026-10-14、补统一字段表与五类分节、source_pdf 指向任务清单所列原件）；同一 PDF 另有副本 `raw/papers/attack-detection/lamda-related/2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf`。
6. **MORPH 存在负证据**：训练家族受限时 FPR 明显上升（§6.2），其前身性（ADAPT 早期形态）使其更适合当「负面对照 + 部件来源」而非基线。
7. **Dream 与 HYDRA 都做了诚实归因**：Dream 明说「多数适应收益来自更新机制而非漂移检测器」（§5.3），HYDRA 的 HYDRA† 消融显示策略本身也有增益（§4.3）。二者皆提示：C1 若主张「选样/检测」带来的增益，必须做交叉消融。
8. **本代理无 Bash 工具，无法执行 `git commit`**：8 份笔记 + INDEX.md + 本文件均已落盘，但**未提交**，需由主代理提交（提交信息建议：`docs(wiki): add C1 drift-adaptation paper notes`）。
