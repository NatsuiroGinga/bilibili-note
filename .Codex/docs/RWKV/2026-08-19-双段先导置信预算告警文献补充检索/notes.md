# 双段先导置信预算告警文献补充检索笔记

- **日期**：2026-08-19
- **状态**：本轮精确检索与裁决完成；停止条件满足
- **已核验新增全文**：5 篇 E2 全文；另交叉引用 1 篇既有 E2 全文，不重复计数
- **已完成查询组**：5 组、16 条查询式
- **新增最高同构等级**：D2；D3 为 0
- **当前阻塞**：5 篇新增全文尚未进入 raw／wiki／Zotero；详见第五节

## 一、判定对象拆解

| 关系键 | 必须满足的含义 | 常见但不等价的近邻 |
| --- | --- | --- |
| R1 冻结树分数 | 树模型及其数值分数定义在目标使用前冻结 | 在线更新树、目标域重训、非树分数 |
| R2 时间因果选择段 | 只用目标时间前缀中已结束实体选择候选阈值 | 随机标定集、完整目标集、后段回看 |
| R3 独立确认段 | 与选择实体不交叉，专用于确认固定候选阈值 | 在同一批样本上选阈值并套固定阈值区间 |
| R4 实体假阳率预算 | 假阳率的统计单元是实体／主体，而非逐流或告警总量 | 逐样本假阳率、人工审查率、每窗告警率 |
| R5 单侧风险上界 | 对确认段良性实体的有限样本风险给出单侧上界，并处理有限候选选择 | 仅报告经验分位数、双侧区间、渐近误差棒 |
| R6 源阈值回退 | 没有可行候选、样本不足或上界不可算时恢复同预算源阈值 | 全量人工复核、拒绝预测、保持目标候选 |
| R7 冻结不相交评价 | 阈值封印后，只在首次晚于截止点的新实体上一次评价 | 后段重新取分位、`top-k`、持续重标定 |

`D3` 要求 R1—R7 在同一工作中同时明确出现。仅有训练／校准／测试三分、一般风险控制或一般回退不构成 `D3`。

## 二、既有文献排重清单

### 2.1 既有 21 篇树模型矩阵

1. Deng 等：时间序列森林。
2. Middlehurst 等：规范区间森林。
3. Middlehurst 等：多样表示规范区间森林。
4. Cabello 等：随机监督时间序列森林。
5. Zhou、Feng：深度森林。
6. Montiel 等：自适应 XGBoost。
7. Gomes 等：自适应随机森林。
8. Niculescu-Mizil、Caruana：监督学习概率校准比较。
9. Zadrozny、Elkan：排序分数到概率的变换。
10. Saerens 等：新环境类别先验调整。
11. Leistner 等：多示例森林。
12. Sigrist：GPBoost。
13. Mirsky 等：Kitsune。
14. Xu 等：Greedy Miser。
15. Chen 等：主机展平 XGBoost。
16. Pinchuk：时间聚合 XGBoost。
17. Lee 等：TreeText-CTS。
18. Asiaee、Aryan：TAP-GPPS。
19. Hung：物联网固定假阳率树阈值。
20. Anctil 等：批次隔离树分数校准。
21. Li 等：发布侧保形分诊审计。

### 2.2 既有 14 篇第四章双机制矩阵

1. 王世谦等：基于长短周期特征的用户异常行为检测。
2. İnan：带标定与泄漏安全的近邻时间序列异常检测。
3. Lipton 等：黑盒标签移位估计。
4. Hu 等：伪标定。
5. Joo、Klabjan：IW-GAE。
6. Ericsson 等：领域适应评价规范。
7. Javitz、Valdes：NIDES 统计组件。
8. Haiba、Rafalia：基于 SIM 标记网络流量的无监督异常检测。
9. Garcia 等：Slips 行为证据聚合。
10. Dussap 等：基于分布特征匹配的标签移位量化。
11. El-Hajj、Zeineddine：多尺度恶意软件检测与漂移监测。
12. Choi：标签移位校正的任意时点有效确认。
13. Choi：预指定预测校正的任意时点有效证据。
14. Clausen、Grov、Aspinall：CBAM。

## 三、查询记录

检索入口均为联网学术检索，题录随后回到 arXiv、OpenReview 或作者全文核验。查询只围绕已知缩写、作者和七关系组合，没有扩展到宽泛异常检测综述。

| 组 | 查询式数量与范围 | 主要返回与排重 | 全文动作 | 最高等级 | 下一步／停止判断 |
| --- | --- | --- | --- | --- | --- |
| Q1 | 4 条：COVCAL、C3R、SAFEVPR 精确缩写；Gurram＋FPR／置信界 | 命中 COVCAL、C3R、SAFEVPR；均不在既有 35 行 | 取得三份 arXiv 全文并分页 | D2 | 继续恢复 Gurram 与 Deng |
| Q2 | 4 条：Gurram＋纽曼—皮尔逊／假阳；Deng＋有限样本／风险控制 | 命中 Kalan、Deng 等 2511.06641；Gurram 返回项不唯一 | Deng 全文用 arXiv 版本核验 | D0（严格合同） | 用完整题意窄化 Gurram |
| Q3 | 4 条：Gurram＋文档抽取／选择风险／确认 | 唯一锁定 Gurram 2608.14639；与既有 35 行不重复 | 取得全文并分页 | D2 | 此项是最后一个新增 D2 |
| Q4 | 2 条：dev-then-cal＋Clopper–Pearson＋FPR；two-split＋source threshold | 零结果 | 无新增全文 | 无新增 D2／D3 | 连续停止组 1 |
| Q5 | 2 条：selection-untouched＋source threshold；frozen evaluation＋entity FPR budget | 仅返回术语碰撞的知识图谱、一般早期预警与非概率阈值材料；不满足双段风险合同 | 不扩读、不计候选 | 无新增 D2／D3 | 连续停止组 2，停止 |

计数口径：5 组、16 条查询式；网页打开与 PDF 下载不另计查询组。最后一个新增 D2 在 Q3，Q4、Q5 连续没有新增 D2／D3，满足预注册停止条件。

## 四、逐篇全文记录

### 4.1 COVCAL

- 题名：Risk-Controlled Lean-as-Judge for Natural-Language Mathematical Reasoning。
- 作者／年份：Pauline Bourigault、Xiaotong Ji、Matthieu Zimmer、Rasul Tutunov、Haitham Bou Ammar／2026。
- 标识符与入口：arXiv:2605.28365v1；<https://arxiv.org/abs/2605.28365>。
- 全文：17 个物理页；临时核验副本 /private/tmp/ch4-pilot-budget-lit-20260819/COVCAL.part.pdf；SHA-256 6b85b8f22dc138d315cf097a9b69b6766349fd23a566814c0000fcde8700e651；E2。
- 关键位置：物理第 4 页式（13）给 Bonferroni 网格上的单侧 Clopper–Pearson 上界，式（14）给 dev 选择后在独立 cal 上只检一次；物理第 5 页式（15）—（18）和定理 1—2 给同时网格保证与 dev-then-cal 保证；物理第 6 页报告 76／151／151 的 dev／cal／test 分账；物理第 14 页明确 fallback 输出不在选择风险证书内。
- 支持点：独立开发段选择固定候选、独立标定段确认、有限候选校正、无可行候选时 reject-all、完全隔离的测试诊断。
- 不能支持：基座不是树模型；样本是独立同分布问题而非时间前缀实体；控制的是已接受答案的选择风险而非实体假阳率；fallback 不是同预算源阈值且不受证书覆盖。
- R1—R7：R1 △（冻结完整流水线但非树）；R2 ✗；R3 △（角色隔离吻合，实体与时间单元不吻合）；R4 ✗；R5 ✓；R6 △（reject-all／一般 fallback）；R7 △（独立测试但非时间新实体）。
- 裁决：D2 强近邻，纳入。它直接占用“开发段选候选＋独立标定段单次确认＋单侧精确界”这组关系，但不占用本课题完整组合。
- Zotero：题名与 2605.28365 双路检索均零命中；未导入，仓库原件与笔记均无。

### 4.2 C3R

- 题名：Certified Domain Consistency for Multi-Domain Retrieval: Label-Free Per-Domain Contamination Control with Conformal Risk Guarantees。
- 作者／年份：Jayakumar Manoharan／2026。
- 标识符与入口：arXiv:2607.14157v1；<https://arxiv.org/abs/2607.14157>。
- 全文：25 个物理页；临时核验副本 /private/tmp/ch4-pilot-budget-lit-20260819/2026-Manoharan-C3R-Certified-Domain-Consistency.pdf；SHA-256 66cefd96d2a6d6747f5c18648089f9292440b570da3fd9ef449f2545374e57d4；E2。
- 关键位置：物理第 5 页式（1）定义每域检索污染率；第 6 页明确 D1／D2 两个不相交标定集、冻结探针和分割独立性，定理 1 式（2）给真域风险转移界；第 7 页式（3）反解目标预算并在不可行时 abstain；第 8 页算法 1 给 D1 的 Clopper–Pearson、D2 的 Hoeffding–Bentkus 风险控制与服务规则，并报告 70% 标定、30% 评价；第 9 页明确严格预算下大面积 abstain。
- 支持点：冻结基础检索栈；三个数据角色隔离；有限样本单侧界与 3C+1 个陈述的 Bonferroni 校正；不可行时不静默违约；独立评价。
- 不能支持：D1 估路由误差、D2 直接选阈值，不是“先选阈值、再独立确认固定阈值”；随机重采样不是时间因果段；风险是每域 top-K 污染而非实体 FPR；回退是空输出而非源年度阈值；基座不是树。
- R1—R7：R1 △；R2 ✗；R3 △；R4 ✗；R5 ✓；R6 △；R7 △。
- 裁决：D2 强近邻，纳入。它占用“冻结栈＋两分割有限样本风险＋不可行 abstain”的一般安全合同，但缺当前候选最关键的阈值选择／确认语义与源阈值回退。
- Zotero：题名与 2607.14157 双路检索均零命中；未导入，仓库原件与笔记均无。

### 4.3 SAFEVPR

- 题名：SAFEVPR: Patch-Based Conformal Verification for Safe Cross-Condition Sequence Visual Place Recognition。
- 作者／年份：Ha Sier、Jiaqiang Zhang、Zhuo Zou、Xianjia Yu、Tomi Westerlund／2026。
- 标识符与入口：arXiv:2605.28048v1；<https://arxiv.org/abs/2605.28048>。
- 全文：8 个物理页；临时核验副本 /private/tmp/ch4-pilot-budget-lit-20260819/2026-Sier-SAFEVPR.pdf；SHA-256 9b715f2f146dcaf69d7a0c84cce7361069181bbdad5fa9957599d54a635b7772；E2。
- 关键位置：物理第 1—2 页明确跨条件破坏交换性，因此不声称任意漂移下的正式保证；第 3 页式（1）定义接受集合 FDR，式（2）定义冻结 DINOv2 补丁匹配分数，随后给每箱 Bonferroni-LTT、Clopper–Pearson 阈值、τ=+∞ abstain 以及小样本时回退 vanilla LTT；第 4 页给带空间缓冲的标定／测试隔离和整条件留出评价。
- 支持点：冻结基础检索器与非训练验证分数；有限候选 Bonferroni 单侧风险检验；无可行阈值时 abstain；有缓冲的隔离测试。
- 不能支持：没有独立选择段和确认段；控制的是已接受匹配的 FDR 而非实体 FPR；跨条件结果只有经验有效性；回退是 vanilla LTT，不是源阈值；非树、非时间新实体。
- R1—R7：R1 △；R2 ✗；R3 ✗；R4 ✗；R5 ✓（只在交换性条件下）；R6 △；R7 △。
- 裁决：D2 协议近邻，纳入但必须附交换性限制。它不能支撑“跨年度漂移下仍有名义 FPR 保证”。
- Zotero：题名与 2605.28048 双路检索均零命中；未导入，仓库原件与笔记均无。

### 4.4 Gurram

- 题名：Valid Per-Field Selective Risk Control for Document Extraction: Three Failure Modes, a Validity Ladder, and When Conditioning Pays。
- 作者／年份：Bhaskar Gurram／2026。
- 标识符与入口：arXiv:2608.14639v1；<https://arxiv.org/abs/2608.14639>。
- 全文：14 个物理页；临时核验副本 /private/tmp/ch4-pilot-budget-lit-20260819/Gurram.part.pdf；SHA-256 d230c8f6b9331b774c4db6e14ed24eecaa1b2faf91adbc3789d866dce48bf9a0；E2。
- 关键位置：物理第 3 页说明一次冻结的真实文档输出、HGB 树融合与 selection-untouched 确认捕获；第 4 页给文档级 50／50 标定／测试和 add-one 阈值；第 5 页要求 fit／val 文档隔离，并用精确二项尾、Holm 与固定序列控制有限候选；第 6—7 页分别给 field-iid 与 doc-iid PAC 保证及选择乘数纪律；第 8 页给预先冻结配置在未参与选择的新捕获上的一次确认。
- 支持点：明确揭示同一数据拟合分数和阈值会泄漏；分离 fit、val、test；精确二项尾和家族错误率校正；选择未触碰确认；不可认证时 review-all／零覆盖。
- 不能支持：随机文档切分而非时间因果段；HGB 分数仍在目标文档上拟合，不是源年度冻结树；风险是字段选择风险而非实体 FPR；没有同预算源阈值回退；独立确认验证整套配置，不是专门确认选择段产生的固定阈值。
- R1—R7：R1 △；R2 ✗；R3 △；R4 ✗；R5 ✓；R6 △；R7 △。
- 裁决：D2 强近邻，纳入。它使“选择与确认隔离、精确二项有限候选校正、未触碰确认”都不能作为单项原创。
- Zotero：题名与 2608.14639 双路检索均零命中；未导入，仓库原件与笔记均无。

### 4.5 Kalan、Deng 等

- 题名：Neyman-Pearson Classification under Both Null and Alternative Distributions Shift。
- 作者／年份：Mohammadreza M. Kalan、Yuyang Deng、Eitan J. Neugut、Samory Kpotufe／2025 预印本；OpenReview 元数据标为 ICLR 2026 已发表。
- 标识符与入口：arXiv:2511.06641v1；<https://arxiv.org/abs/2511.06641>；OpenReview 论文页对应 pHckxhmBlI。
- 全文：22 个物理页；临时核验副本 /private/tmp/ch4-pilot-budget-lit-20260819/Deng.part.pdf；SHA-256 19d4ab51cdf5467a1164109d2716412fd21858093774c2bd757ab9f850fc2fda；论断锚点来自 arXiv 全文，按 E2 计。
- 关键位置：物理第 2 页给利用源类 0、源类 1 的两阶段学习；第 3 页式（1）定义目标 Type-I 约束下最小化 Type-II；第 4 页式（3）—（7）给自适应源约束和交集为空时的 target-only 分支；第 6 页定理 1 给高概率目标 Type-I／Type-II 界并说明无信息源时避免负迁移。
- 支持点：在零类和一类分布均漂移时显式控制目标 Type-I；源有用时迁移、无用时匹配 target-only；这是纽曼—皮尔逊约束与安全迁移的一手近邻。
- 不能支持：重新学习分类器而非冻结树分数；需要目标两类标签；没有时间段、实体单位、阈值选择／独立确认、Clopper–Pearson 有限候选校正或冻结评价；安全分支是 target-only，不是源阈值回退。
- R1—R7：R1 ✗；R2 ✗；R3 ✗；R4 △（Type-I 但非实体 FPR）；R5 △（一般化高概率界而非指定二项上界）；R6 △（避免负迁移但回退方向相反）；R7 ✗。
- 裁决：严格合同 D0，作为纽曼—皮尔逊迁移方法链纳入，不作为 D2 直接同构。
- Zotero：题名与 2511.06641 双路检索均零命中；未导入，仓库原件与笔记均无。

### 4.6 既有全文交叉引用，不计新增

- Choi，Anytime-Valid Evidence for Prespecified Predictive Corrections，arXiv:2608.08174v1，既有原件 raw/papers/methodology/2026-Choi-Anytime-Valid-Predictive-Corrections.pdf，既有笔记 wiki/papers/methodology/2026-Choi-预指定预测校正的双边序贯证据.md，Zotero 键 32WRX9MB。
- 物理第 4 页式（1）、第 9—10 页财富过程、第 19—22 页双边确认／回退、第 25—31 页标签移位与容忍区特例已完成既有核验。它占用“预指定校正＋后续证据＋反驳后回到源预测”，但需要后续标签，且无实体 FPR 阈值或独立最终评价；保持 D2，不重复计入本轮 5 篇。

## 五、阻塞清单

本轮没有全文访问付费墙；五篇均取得公开全文并完成论断核验。但父任务限定只写独占三文档，未执行 raw／wiki／索引／Zotero 写入，因此以下是明确的持久化补链清单，而不是“全文不可得”：

| 论文 | 稳定标识 | 建议原件名 | 当前原件／笔记／Zotero |
| --- | --- | --- | --- |
| COVCAL | arXiv:2605.28365 | raw/papers/methodology/2026-Bourigault-COVCAL-Risk-Controlled-Lean-as-Judge.pdf | 三者均缺；临时全文可读 |
| C3R | arXiv:2607.14157 | raw/papers/methodology/2026-Manoharan-C3R-Certified-Domain-Consistency.pdf | 三者均缺；临时全文可读 |
| SAFEVPR | arXiv:2605.28048 | raw/papers/methodology/2026-Sier-SAFEVPR-Conformal-Verification.pdf | 三者均缺；临时全文可读 |
| Gurram | arXiv:2608.14639 | raw/papers/methodology/2026-Gurram-Per-Field-Selective-Risk-Control.pdf | 三者均缺；临时全文可读 |
| Kalan、Deng 等 | arXiv:2511.06641 | raw/papers/methodology/2026-Kalan-Deng-NP-Classification-Distribution-Shift.pdf | 三者均缺；arXiv 全文可读；OpenReview PDF 自动下载 403 |

临时副本位于 /private/tmp/ch4-pilot-budget-lit-20260819/，不视为仓库持久原件。后续若获准补链，必须按 raw/AGENTS.md 与 wiki/AGENTS.md 执行原件、结构化笔记、INDEX 和 Zotero 四步，不得只复制 PDF。

## 六、恢复检查点

- 已完成：规则与路线恢复；提交 3266e5f 与三检查点恢复；5 组 16 条精确查询；5 篇新增 E2 全文逐页定位；R1—R7、纳入／排除、Zotero 双路查重；两组停止查询。
- 最终裁决：4 篇 D2 协议／方法强近邻，1 篇严格 D0 的纽曼—皮尔逊方法链；D3 为 0。未发现冻结树分数、目标时间因果选择段、独立确认段、实体 FPR、有限候选单侧界、同预算源阈值回退和冻结新实体评价七项同现。
- 未关闭项：只有 raw／wiki／索引／Zotero 持久化补链；不是科学裁决或 Q0 阻塞。
- 与实验关系：本调研只收缩原创措辞，候选仍为设计可行、实验待证；不得因文献整理暂停已经满足门禁的 Q0。
