# LAMDA 资格增量研究本地待核清单

日期：2026-09-08
输入：`LAMDA-2026-external-deep-research-raw.md`、`LAMDA-2026-qualification-followup-raw.md`、LAMDA v3 来源期/近时段诊断。
边界：只整理本地核验入口；不修改研究合同、Goal、恢复卡、DRIFT 主线、候选排序或任何运行。

## 结论

增量网页报告没有提供足以改变当前排序的新证据。可本地接受的最小结论仍是：官方全时期训练分片参与词表和方差筛选有明确代码依据，但这不等于测试标签进入监督训练；v3 聚合诊断证明近时段存在大幅退化，但仍受发布特征空间的未来协变量预处理疑点约束；本轮新增独立引用不能冒充 LAMDA 同制品、同协议复现。

## 核验矩阵

| 项目 | 网页候选 | 本地状态 | 必须核验的位置或动作 |
| --- | --- | --- | --- |
| LAMDA 官方预处理 | `vectorization_npz_creation.py` 汇集 2013、2014、2016-2025 年训练分片，`build_vocabulary(all_X_tr)` 后对 `all_X_tr` 拟合 `VarianceThreshold`；监督脚本再只训练 2013-2014。 | 已被本地稳定综述和旧数字账本独立接受。 | 固定 GitHub 修订 `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`；复核源码第 12-37、40-68、75-96 行及附录 G。继续使用“未来协变量预处理”，不得写成已证“标签泄漏”。 |
| IID 划分描述 | 论文 §4.1 称每年最后一个月；代码明确排除 `2013-12`、`2014-08` 作为 IID。 | 本地账本已记录代码事实；差异仍待版本解释。 | 对照 `anoshift_experiment_models_separate.py` 第 69-84 行和论文 §4.1，不自行把 `2014-08` 改成 `2014-12`。 |
| v3 脱敏诊断 | 完整视图 AP IID/2016/2017=`0.994404/0.937396/0.346236`，ROC-AUC=`0.994836/0.948836/0.545725`，FNR=`0.025211/0.222449/0.918489`。 | 本地 [metrics.json](../../../../thesis/experiments/llm_probe/runs/diagnostics/lamda-iclr2026-source-near-screening-budget1m-v3/metrics.json) 存在；仅具 `screening_only` 身份。 | 核 `effective-config.json`、`manifest.json` 与 `published_feature_space_uses_future_covariates=true`；报告未给 FPR、阈值来源、家族分组和不确定性，不能升级为低误报或未见家族结论。 |
| FreeMOCA | arXiv `2605.09664v2`；使用另一套 AZ 数据、2439 维 Drebin 特征，以 warm-start 和参数插值做无回放持续学习；不是 LAMDA 复现。 | 未发现本地独立 PDF 或全文笔记，保持网页全文候选。 | 入库后核 §4、表 1、附录 D 表 9、表 10、附录 F；核作者重叠、AZ 数据记录 `14537891`、A6000 成本和无不确定性边界。 |
| Sabbah 等自监督+RL 维护 | arXiv `2605.24294v1`；引用 LAMDA，但实验不是 LAMDA；§IV-F 的状态与奖励使用评价成绩，因此不是严格无标签适应。 | 已有 [原件](../../../../raw/papers/attack-detection/drift/2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf) 与 [结构化笔记](../../../../wiki/papers/attack-detection/2026-Sabbah-自监督强化学习漂移维护.md)。 | 回到 §IV-F、表 I 和题录作者顺序，核评价标签何时可用；不得把相对动作 cost 当墙钟、显存或能耗。 |
| CITADEL | 月标注预算 400 时 LAMDA F1/FNR/FPR=`77.7/24.0/2.3%`；同表 MORSE F1=`64.5%`。 | 已有 [原件](../../../../raw/papers/attack-detection/drift/2025-Haque-CITADEL-Semi-Supervised-Active-Learning-Drift.pdf) 与 [笔记](../../../../wiki/papers/attack-detection/2025-Haque-CITADEL半监督主动漂移适应.md)，不是本轮新增。 | 核表 IV 的标签预算、预处理继承、评价集合与不确定性；不得与零更新 v3 或严格源期协议直接排名。 |
| LAMDA 与 DRIFT | 两者标签语义、输入结构、时间轴、家族字段和资源不同；总分不能直接排序。 | LAMDA [原件](../../../../raw/papers/datasets/2026-Haque-LAMDA-Android-Malware-Concept-Drift.pdf)/[笔记](../../../../wiki/papers/datasets/2026-Haque-LAMDA-Android恶意软件长期漂移基准.md)与 DRIFT [原件](../../../../raw/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.pdf)/[笔记](../../../../wiki/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.md)均存在。 | 只比较公开协议：APK 静态向量对域名字符/子词、年度分片角色、family 字段、低误报指标和论文资源；不得把网页报告中的比较写成当前主备排序变更。 |
| 独立引用与复现版图 | 本轮核到 Sabbah 等独立引用；FreeMOCA 有作者重叠且使用 AZ；未核到独立团队同制品同协议复现。 | 这是检索结果，不是不存在性证明；Scite 未提供证据。 | 本地后续只补具体被引链和已知候选全文，不再开放式重搜；每项区分“引用”“使用 LAMDA”“同协议复现”。 |

## 运输与证据例外

- 网页报告称两份白名单文档返回 404；本机对应文件实际存在。该 404 只说明普通 ChatGPT 无法读取未公开或未同步的仓库路径，不是文档不存在或研究证据缺失。
- 增量报告自报 `actual_model=GPT-6 Astra Pro`、`actual_effort` 无可核档位、`used_apps=Sider Scholar, Consensus, GitHub`；Scite 没有提供引用语境。
- 两份网页报告均为外部候选。内部 `cite...` 或应用来源按钮不能替代本地 PDF 页码和固定源码链接。

## 最小下一步

1. 只读核 v3 的 `effective-config.json`、`manifest.json` 与 4561 维生成修订对应关系。
2. 只读核 FreeMOCA 原文；若与 LAMDA 无同制品实验，登记为迁移/参数保持近邻，不升级为 LAMDA 基线。
3. 用既有 Sabbah、CITADEL、LAMDA、DRIFT 本地全文核上表页码和协议；不启动新实验。
4. 未出现同协议独立复现前，保持“独立复现未核准”，不用搜索不命中声称不存在。
