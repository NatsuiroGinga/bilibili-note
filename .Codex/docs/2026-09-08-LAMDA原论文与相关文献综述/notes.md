# LAMDA 2026 原论文与相关文献证据台账

## 记录规范

每完成一组查询或一篇全文，立即记录：查询式、来源 URL、原件路径、证据等级、关键页码或公式、纳入或排除理由、与当前候选关系、待办和 Zotero 状态。

证据等级：

- `E3`：本地合法全文且已回到原始 PDF 页码核验。
- `E2`：在线合法全文已取得，尚未完成本地页码复核。
- `E1`：在线摘要或官方题录。
- `E0`：搜索结果、网页模型输出或未核传闻。

## 查询记录

### Q0：规则与安全边界

- 日期：2026-09-08
- 范围：根目录、`.Codex/docs/`、`raw/`、`wiki/`、RWKV 路由规则，以及 ChatGPT 交接、持久化计划、引用核验、MinerU、Zotero/Obsidian 技能。
- 结论：普通 ChatGPT 仅接收显式允许的公开 Markdown；不发送原始 PDF、私有路径内容、凭据、数据、权重或日志。网页输出必须由 Codex 独立复核。
- 待办：执行 `paper` 作用域本地混合检索，再执行 Zotero 语义检索。

### Q1：本地混合索引

- 日期：2026-09-08
- 查询式：`LAMDA Android malware temporal drift ICLR 2026`，作用域 `paper`，模式 `hybrid`；补充精确词 `LAMDA` 的 `lexical` 查询。
- 索引：构建时间 `2026-09-08T03:11:19Z`，论文集合 908 篇，向量模型 `intfloat/multilingual-e5-small` 固定修订 `614241f622f53c4eeff9890bdc4f31cfecc418b3`。
- 限制：并发任务持续写入导致状态检查显示 `stale=true`；自动增量构建后执行了最新索引查询，但精确 `LAMDA` 被同名对话模型和微调方法污染。
- 结果：未发现 LAMDA Android 恶意软件原论文全文笔记或 PDF。概念检索返回 MADCAT、TESSERACT、TRANSCENDENT 和 2026 漂移重训工作，均只作为近邻候选。
- 既有候选综述：`.Codex/docs/2026-09-07-跨年数据集替代调研/数据集比较综述.md` 含 LAMDA 数字，但其来源链未在该文档内展开，本任务不得直接升级这些数字。
- 证据等级：`E0`（索引候选）；必须回到全文。

### Q2：Zotero 去重

- 日期：2026-09-08
- 首次状态：Zotero 9.0.6 本地 API 已启用但应用未运行，查询返回 `Connection refused`；通过官方本地助手启动后 API 与连接器均返回 200。
- 语义查询：`LAMDA longitudinal Android malware dataset temporal drift ICLR 2026`。
- 精确结果：`LAMDA` 无题录命中，原论文未入库。
- 近邻已入库：MADCAT，条目键 `59GWHNT2`；TESSERACT，条目键 `F6KINRCT`；2026 漂移检测与自适应重训，条目键 `VQKRUFJV`。
- 证据等级：题录/摘要为 `E1`；是否有本地全文须逐项查附件和全文。
- 待办：核准 LAMDA 稳定标识后再次精确查重；只导入未入库条目。

## 论文证据记录

### P1：LAMDA 原论文

- 题名：*LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis*。
- 作者：Md Ahsanul Haque、Ismail Hossain、Md Mahmuduzzaman Kamol、Md Jahangir Alam、Suresh Kumar Amalapuram、Sajedul Talukder、Mohammad Saidur Rahman。
- 稳定标识：arXiv `2505.18551v1`；OpenReview `1FnCrZtBNQ`；ICLR 2026。
- 版本关系：arXiv v1 的作者单位与 OpenReview 会议版抬头存在差异；正式题名以 OpenReview 的 `Benchmark for Concept Drift Analysis` 为准。OpenReview PDF/API 直连均 403，本地保存的是 arXiv v1。
- 官方 URL：https://arxiv.org/abs/2505.18551、https://openreview.net/forum?id=1FnCrZtBNQ、https://iqsec-lab.github.io/LAMDA/。
- 原件：`raw/papers/datasets/2026-Haque-LAMDA-Android-Malware-Concept-Drift.pdf`，SHA-256 `26df883d075156abfe69d4def70e2b27614f63a53ba08dc82d0a284f3f3ed129`。
- 结构化笔记：`wiki/papers/datasets/2026-Haque-LAMDA-Android恶意软件长期漂移基准.md`。
- 证据等级：原始 PDF 已入库；arXiv 官方 HTML 全文已逐节核验；MinerU 未成功产出，PDF 物理页码待补。
- 关键位置：第 3 节数据构建；第 4.1 节/表 1；附录 C 表 7；附录 H 表 14；附录 J 表 15–16；附录 L。
- 纳入理由：本任务核心原论文。
- Zotero：`6THQM632`，题录已导入，无附件。
- 用户补充了 ICLR 2026 官方会议演示制品 `raw/papers/10011850_e9IemFB.pdf`，SHA-256 `37c1a03cc1ab3d01459695eb6855d109e10fbebe01c6824735fb0405a71f61dd`；该文件为 17 页横向演示文稿，第一页标注 `Presenter`，已建立 [[2026-Haque-LAMDA-ICLR2026官方演示版]] 笔记。它补充会议展示证据，不替代 arXiv v1 论文全文。

### P2：Chen 等，2023

- 题名：*Continuous Learning for Android Malware Detection*；USENIX Security 2023，1127–1144；arXiv `2302.04332`。
- 官方 URL：https://www.usenix.org/conference/usenixsecurity23/presentation/chen-yizheng。
- 原件：`raw/papers/attack-detection/lamda-related/2023-Chen-Continuous-Learning-Android-Malware.pdf`，SHA-256 `f15541d85dd4626b86fcb64f2034f68aeb1ccd80034e9c0e62525fd4f74259d4`。
- 结构化笔记：`wiki/papers/attack-detection/2023-Chen-Android恶意软件持续学习.md`。
- 证据等级：`E3`，USENIX 官方 PDF，MinerU 快速提取成功。
- 纳入理由：LAMDA 正文和参考文献 [17] 明确引用，是主动学习直接强基线。
- Zotero：`FJADHX96`，题录已导入，无附件。

### P3：CITADEL

- 题名：*CITADEL: A Semi-Supervised Active Learning Framework for Malware Detection Under Continuous Distribution Drift*；arXiv `2511.11979v3`，2026-02-14；只核为预印本。
- 官方 URL：https://arxiv.org/abs/2511.11979、https://github.com/IQSeC-Lab/CITADEL。
- 原件：`raw/papers/attack-detection/lamda-related/2025-Haque-CITADEL-Semi-Supervised-Active-Learning-Drift.pdf`，SHA-256 `ca2cf8f6cba43c34f8f1c1dcd0002bcff864ee87c497d9a86c8b330b0243341c`。
- 结构化笔记：`wiki/papers/attack-detection/2025-Haque-CITADEL半监督主动漂移适应.md`。
- 证据等级：`E2+`，原始 PDF 已入库、arXiv 官方 HTML 全文；MinerU 未产出。
- 纳入理由：直接使用并引用 LAMDA；给出半监督主动学习结果和课程学习附录。
- Zotero：`P86CK65V`，题录已导入，无 PDF 附件；BibTeX `note` 被导入为子笔记 `T4JYNA7A`。

### P4：McNdroid

- 题名：*McNdroid: A Longitudinal Multimodal Benchmark for Robust Drift Detection in Android Malware*；arXiv `2605.06894v1`。
- 官方 URL：https://arxiv.org/abs/2605.06894、https://doi.org/10.5281/zenodo.19969833。
- 原件：`raw/papers/attack-detection/lamda-related/2026-Kamol-McNdroid-Multimodal-Android-Malware-Drift.pdf`，SHA-256 `a61619af595c8b97f0eeebb93488daff78c387d1060922731d05c36539f8da14`。
- 结构化笔记：`wiki/papers/attack-detection/2026-Kamol-McNdroid多模态长期漂移基准.md`。
- 证据等级：`E2+`，原始 PDF 已入库、arXiv 官方 HTML 全文；MinerU 分页未产出。
- 纳入理由：同作者群明确称 LAMDA 为最近基准；补多模态，并明确只用 2013 训练词表。
- Zotero：`23DE8377`，题录已导入，无附件。

### P5：Sabbah 等，2026

- 题名：*Concept Drift Adaptation Using Self-Supervised and Reinforcement Learning in Android Malware Detection*；arXiv `2605.24294v1`。
- 官方 URL：https://arxiv.org/abs/2605.24294。
- 原件：`raw/papers/attack-detection/lamda-related/2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf`，SHA-256 `ce9f9f857872d9da76cfed3de93ff4949d7da1130f4347a4bc0d353ef8f74a27`。
- 结构化笔记：`wiki/papers/attack-detection/2026-Sabbah-自监督强化学习漂移维护.md`。
- 证据等级：`E2+`，原始 PDF 已入库、arXiv 官方 HTML 全文；MinerU 并发转换未产出。
- 纳入理由：直接提供 RL 状态/动作/奖励近邻并明确标签可用边界；引用 LAMDA 但未在 LAMDA 实验。
- Zotero：`DYVZDW5Z`，题录已导入，无附件。

### P6：Chow 等，2023

- 题名：*Drift Forensics of Malware Classifiers*；AISec 2023；DOI `10.1145/3605764.3623918`。
- 原件：`raw/papers/attack-detection/lamda-related/2023-Chow-Drift-Forensics-Malware-Classifiers.pdf`，SHA-256 `8d81cf75d27eaae8bbd92ff1feaa84eaae5bd937d94a92bfd5d0d823c10c4752`。
- 结构化笔记：`wiki/papers/attack-detection/2023-Chow-Android恶意软件漂移取证.md`。
- 证据等级：`E3`，作者公开 PDF，MinerU 快速提取成功。
- 纳入理由：LAMDA 参考文献 [18] 明确引用；提供家族组成与家族内演化的漂移根因分面。
- Zotero：`H4HNRY22`，题录已导入并用本地 API 查回，未自动附加 PDF。

### 直接近邻但本轮不新增原件

- MADCAT：本地已有原件和全文笔记，Zotero `59GWHNT2`；与 LAMDA 同日首发，LAMDA v1 未引用，属于问题近邻而非已证引用关系。
- TESSERACT：本地已有原件和全文笔记，Zotero `F6KINRCT`；是时间/空间评价协议基础。
- *Regression-aware Continual Learning for Android Malware Detection*：arXiv `2507.18313`，只作题录候选，不支撑稳定综述的效果量级。

### 网页增量候选：原件与笔记已入库（2026-09-09）

- FreeMOCA：原件 `raw/papers/attack-detection/lamda-related/2026-Asadi-FreeMOCA-Memory-Free-Continual-Malicious-Code.pdf`，SHA-256 `2665a1ee28de74058afcfe5842b6bbfb610efd29ee4ea1c6248e6788fca87d7f`；笔记 `wiki/papers/attack-detection/2026-Asadi-FreeMOCA无记忆恶意代码持续学习.md`。
- Regression-aware：原件 `raw/papers/attack-detection/lamda-related/2025-Ghiani-Regression-Aware-Continual-Learning-Android-Malware.pdf`，SHA-256 `b9578580d4eda18632a51a8f04bc4edcdd4b3cb1ddaecca7b42ac7f0041d9108`；笔记 `wiki/papers/attack-detection/2025-Ghiani-Regression-aware持续学习安全回归.md`。
- MADAR、GSS、MIR、PBR、CBRS、A-GEM 和 ECBRS/PAPA 主文及补充材料均已保存到 `raw/papers/attack-detection/lamda-related/`，并在 `wiki/papers/attack-detection/` 建立对应结构化笔记；各原件 SHA-256 见工作树文件清单和 Git 差异。
- 全文处理：MinerU 快速提取成功的条目使用 MinerU 输出辅助核验；其余长文因快速接口限制，使用本地 PDF 页码文本核对，笔记未把网页摘要当作全文证据。
- 入库边界：这些论文只补充方法来源、直接对照和创新边界，不改变 LAMDA 数据合同、阶段 A/B 的 `screening_only` 身份或候选存废裁决。

## 网页交接记录

- 出站包：`.Codex/docs/chatgpt-handoffs/lamda-2026-literature-deep-research-outbound.md`。
- requested：`model=auto`、`effort=high`、`mode=deep-research`；fallback=`GPT-5.6 Thinking`。
- 实际界面：普通 ChatGPT“聊天”，`GPT-6 Pro`；界面没有独立 effort 选择器，按深度研究执行。
- 已用应用：Sider Scholar、GitHub；没有默认全开 Consensus/Scite/Undermind/Zotero。
- 对话：https://chatgpt.com/c/6a9f912e-4abc-83ea-b7ba-3aa85cc61d6a；内部 WEB 标识 `96d34057-2cdd-4d89-b8d3-9773d7a1c827`。
- 完成：界面显示 33m14s；主报告自报 `GPT-6 Astra Pro`，但模型按钮显示 `6 Pro`，两者均原样记录；effort 无独立界面值。
- 模式：输入框显示“深度研究”，但主报告称未取得独立 Deep Research 作业状态；只能确认普通 ChatGPT 内完成多轮公开研究。
- 回收路径：`.Codex/docs/chatgpt-handoffs/inbox/LAMDA_v1_numeric_ledger_2026-09-08.md`、`LAMDA_artifact_manifest_2026-09-08.md` 和 `LAMDA-web-deep-research-receipt-2026-09-08.md`。
- 主回复导出：请求生成完整 Markdown 附件后网页返回空回复，没有附件；主回复保留在对话 URL，未伪造本地副本。

## Zotero 状态

- 去重前已有：MADCAT `59GWHNT2`、TESSERACT `F6KINRCT`、2026 漂移重训 `VQKRUFJV`。
- arXiv 批量导入失败：LAMDA 返回 429，其余四条读取超时，无条目创建。
- 本地 BibTeX 连接器导入成功：LAMDA `6THQM632`、Chen `FJADHX96`、CITADEL `P86CK65V`、McNdroid `23DE8377`、Sabbah `DYVZDW5Z`、Drift Forensics `H4HNRY22`。
- 六条均已用精确题名在 Zotero 9.0.6 本地 API 查回；均无 PDF 附件。仓库 raw 原件完整，不以 Zotero 附件替代原件层。

## 未关闭问题

- OpenReview 页面受挑战页拦截；接收状态已由 OpenReview PDF 抬头、作者仓库和官方项目页交叉确认，但 OpenReview 论坛讨论/修订历史未抓取。
- MinerU 对 LAMDA/CITADEL/McNdroid/Sabbah 未产出；这些笔记的精确 PDF 物理页码仍待补，当前只使用章节、表号和官方 HTML 全文。
- GitHub 代码仓库没有许可证文件；若要运行、修改或再分发代码，须先取得作者许可或新增官方许可声明。
- Zotero 条目没有 PDF 附件；如项目要求 Zotero 内也持有全文，需要后续手工关联本地合法原件。

## 网页报告增量：Replay 安全保持—适应取舍（2026-09-09）

- 外部报告的高层输出：`output/LAMDA 阶段 A：针对 Replay 安全保持—适应取舍的改造候选.md`；原始交接副本为 `.Codex/docs/chatgpt-handoffs/inbox/LAMDA-2026-qualification-followup-raw.md`。实际模式是普通 ChatGPT 对话内的只读全文研究，模型自报 `GPT-6 Astra Pro`，effort 无独立可核验值；Sider Scholar 与 Consensus 使用情况以报告开头为准，Scite 因额度耗尽未提供语境。
- 本地复核后保留的核心判断：阶段 A 的 Replay 只显示“旧恶意负向翻转下降、FPR 下降而 AP/FNR 略差”的取舍；阶段 B 的联合臂仅在 pooled FNR 与回溯翻转率上略降，FPR/AP/AUROC/F1 未全面占优，且代码筛选安全记忆的时点与配置声明不一致。网页报告不能替代这些本地制品。
- 候选一“只保护旧正确恶意决策”：有助于区分保持与修复，但单独属于已有回归约束的任务化损失，创新强度有限；必须与原式 PCT 和 Replay 对照。
- 候选二“类别／时间条件覆盖记忆”：CBRS、MADAR、GSS、MIR、PBR 等已有近邻覆盖了类别平衡、代表性、不确定性和干扰选择；只能作为强对照或记忆实现部件，不能只换采样器就宣称新算法。
- 候选三“决策角色条件记忆”：用已允许信息区分保护、修复、误报控制三种角色，并在总容量 200 下记录角色占用、margin、干扰和翻转变化；这是当前最值得先做的记忆候选，但仍是外部推论，未实验验证。
- 候选四“双侧风险约束下的修复式 Replay”：训练目标同时包含当前监督、回放、恶意修复和良性误报代理约束；保护集合只来自上一冻结模型已正确判恶意的历史记忆，不能用未来标签。这是最可能形成框架级主张的候选，但必须先与 PCT、A-GEM、普通蒸馏和同配额随机记忆区分。
- 最小因果骨架：固定容量原始 Replay（ER）／ER+角色记忆（M）／ER+双侧修复目标（O）／ER+M+O 四臂；另加原式 PCT、同配额随机角色记忆和 A-GEM 等直接近邻对照。当前只登记为待冻结实验方案。
- 已发现并核对入库：`Regression-aware Continual Learning for Android Malware Detection`（arXiv `2507.18313v2`）、`MADAR: Efficient Continual Learning for Malware Analysis with Diversity-Aware Replay`（arXiv `2502.05760v1`）、GSS（arXiv `1903.08671v5`）、MIR（arXiv `1908.04742v3`）、PBR（arXiv `2408.14976v1`）、CBRS（ICML 2020）、A-GEM（arXiv `1812.00420v2`）及 ECBRS/PAPA（NeurIPS 2023）。八组原件均位于 `raw/papers/attack-detection/lamda-related/`，对应 `wiki/papers/attack-detection/` 笔记的 `source_pdf` 可达，SHA-256 已在本轮复核；后续只需主代理审查其版本和方法映射，不重复下载或入库。
