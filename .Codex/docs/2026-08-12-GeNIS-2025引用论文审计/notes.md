# GeNIS-2025 引用论文审计滚动证据

## 检查点 0：任务启动

- 时间：2026-08-12。
- 代理配置：`genis2025_citation_literature_sol_max → gpt-5.6-sol → effort=max`。
- 已读规则：仓库根、`raw/`、`wiki/`、`.Codex/docs/`。
- 已读既有证据：GeNIS 原始论文研读计划、证据笔记、规范化数据集笔记与旧未分类占位笔记。
- 已知数据论文：Silva 等，`GeNIS: A modular dataset for network intrusion detection and classification`，`Data in Brief` 60 (2025) 111487，DOI `10.1016/j.dib.2025.111487`。
- 已知数据发布：Zenodo DOI `10.5281/zenodo.14919237`，仍需通过 DataCite/Zenodo 核验其概念 DOI、具体版本 DOI 和版本历史。
- 父任务指定优先候选：`Binary and Multiclass Cyberattack Classification on GeNIS Dataset`（arXiv:2511.08660）；`Machine Unlearning for the XGBoost Model with Network Intrusion Datasets`。
- 下一步：本地 `raw/`、`wiki/`、`.Codex/docs/` 与 Zotero 去重；随后锁定官方版本链并建立候选全集。

## 查询与候选台账

| 编号 | 查询式或来源 | 命中 | 初分 | 全文状态 | Zotero 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| Q0 | 本地仓库与 Zotero 去重 | 待执行 | 待定 | 待定 | 待定 | 扩展检索前门禁 |

## 检查点 1：本地、Zotero 与插件首轮检索

- 本地 `raw/`、`wiki/`、`.Codex/docs/` 按 `GeNIS`、数据 DOI、论文 DOI、两篇 arXiv 标识和题名检索：扩展检索前没有两篇使用论文的原件或笔记。
- Zotero 语义检索未命中新使用论文；精确 `GeNIS` 只命中数据论文的两个重复书目条目与一个笔记；`2511.08660`、`2606.19220` 均未命中。因此两篇使用论文不是 Zotero 重复项。
- Sider Scholar 的 OpenAlex 搜索因返回条目中存在空题名而触发结构化输出校验错误；Google Scholar 式简称查询产生大量 `genis/genistein` 同名噪声，精度不足。
- Scite 插件返回月度调用额度已用尽，无法执行本轮检索；这是服务额度阻塞，不表示没有引用。
- SciSpace 精确命中数据论文与 `Binary and Multiclass Cyberattack Classification on GeNIS Dataset`，其余 8 项均为语义近邻或时间上不可能引用的噪声。
- Consensus 命中数据论文和 `Binary and Multiclass...`；其他结果需要逐条抓取并以全文引用确认，不能直接纳入。
- 插件可用性更正：Sider Scholar、Scite、SciSpace、Consensus 均有可调用工具；此前“暂未发现显式工具”只是在首次工具列表展开前的临时状态，已撤回。

| 编号 | 查询式或来源 | 命中 | 初分 | 全文状态 | Zotero 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| Q0 | 本地仓库与 Zotero 去重 | 数据论文重复条目 2；新使用论文 0 | 去重门禁完成 | 数据论文已有全文 | 两篇新论文未入库 | Zotero 键 `33735EHP`、`FX9SE29U` |
| Q1 | Sider OpenAlex：`GeNIS cyberattack classification` | 工具结构校验失败 | 阻塞 | 不适用 | 不适用 | 返回空题名触发错误 |
| Q2 | Sider Google Scholar 式：`"GeNIS" network intrusion dataset` | 主要为同名噪声 | C 候选 | 不读取 | 不适用 | 需用题名/DOI精确查询替代 |
| Q3 | Scite：`"GeNIS" AND (intrusion OR cyberattack OR XGBoost)` | 未执行 | 阻塞 | 不适用 | 不适用 | 月度 5 次额度耗尽，2026-09-01 UTC 重置 |
| Q4 | SciSpace：谁引用或使用 GeNIS | 数据论文、2511.08660 + 8 个语义近邻 | A 候选 1；C 8 | 2511 已取得全文 | 待入 | 近邻项不因语义相关而算引用 |
| Q5 | Consensus：GeNIS modular network intrusion dataset | 数据论文、2511.08660 + 若干近邻 | A 候选 1；待核验若干 | 2511 已取得全文 | 待入 | 命中必须再 `fetch` 后才可引用 |

## A1：Binary and Multiclass Cyberattack Classification on GeNIS Dataset

- 身份：Miguel Silva、Daniela Pinto、João Vitorino、Eva Maia、Isabel Praça、Ivone Amorim、Maria João Viamonte。
- 预印本：arXiv `2511.08660v1`，2025-11-11，17 页，CC BY 4.0。
- 正式版本：FPS 2025 会议论文，Springer LNCS 16402，第 335–351 页，2026-05-01 在线，DOI `10.1007/978-3-032-20018-1_18`。Springer 正式 PDF 需订阅；arXiv 开放全文的题名、作者、章节和正式页面预览一致，尚无证据表明实验表发生变化。
- 原件：`raw/papers/datasets/published-baseline/2511.08660v1-GeNIS-binary-multiclass-classification.pdf`。
- SHA-256：`2650407346007c4b24df2398fdd96c4bacd0ee331a23f857ab03038d56731138`。
- 证据等级：A 类、开放预印本全文；正式版本元数据由 Springer 核验，正式 PDF 受订阅限制。
- 数据：明确采用 60 秒流版本；表 1（PDF 第 6 页）给出训练 294,844、测试 73,712，即 80/20。二类恶意 92.63%、良性 7.37%；四类 DoS 80.22%、Recon 7.52%、Benign 7.37%、Bruteforce 4.89%。
- 字段：原始 125 字段，其中 3 个标签；手工预处理与 `State`、`Flags`、`Protocol` 独热编码后 87 个输入。排除 Argus 标识字段、`Ssaddr/Sdaddr` 及地址/MAC/VLAN 等拓扑字段。
- 特征选择：信息增益、卡方、递归特征消除、平均绝对偏差、离散比；归一化后相加，取 16 项、约 70% 累计重要度。二分类字段见表 7（PDF 第 10 页），多分类字段见表 10（PDF 第 12 页）。
- 模型：RF、XGB、LGBM、LSTM、MLP。树模型在完整和缩减字段上用 5 折交叉验证网格调参；神经网络从训练数据再取 70/30 训练/验证，早停。论文未说明随机种子、分层函数细节、缩放器/选择器是否仅在训练折拟合，也未给源码。
- 二分类最好结果：表 8（PDF 第 11 页），完整 87 字段 RF 与 XGB 并列 F1 99.9949%、准确率 99.9905%、召回 100%、精确率 99.9897%、FPR 0.1289%；XGB 训练/推理 4.78/0.06 秒，明显快于 RF 的 29.09/0.15 秒。最快训练为 LGBM 完整字段 3.37 秒，F1 99.9905%。
- 多分类最好结果：表 11（PDF 第 13 页），F1/召回/精确率均为宏平均。完整字段 RF 与 XGB 并列宏 F1 99.9817%、准确率 99.9919%；RF 宏召回 99.9700%、宏精确率 99.9933%、FPR 0.0921%，训练/推理 25.6/0.21 秒；XGB 宏召回 99.9724%、宏精确率 99.9910%、FPR 0.1105%，训练/推理 9.51/0.10 秒。
- 缺失：没有每类召回、混淆矩阵、跨种子分布、置信区间、场景/日期/捕获留出、跨数据集验证或公开源码。
- 可比边界：只与相同 60 秒版本、相同发布训练/测试文件、同 87 或逐项相同 16 字段、同宏平均口径严格可比。不同流间隔、不同字段、场景留出或时间前向协议只能分表。
- 泄漏/天花板判断：随机行级协议下 F1 已近 100%，但同源捕获、相邻/累计流和同一攻击运行可能跨分区；`SrcTCPBase`、`DstTCPBase`、`SrcWin`、`DstWin` 等连接指纹进入 16 字段。该分数只证明发布随机协议近饱和，不能证明未知场景泛化饱和。
- 源码：全文、arXiv、Springer 和一般 GitHub 题名查询均未找到作者源码；CatalyzeX/第三方页面的“Github”入口不能替代可验证仓库。

## A2：Machine Unlearning for the XGBoost Model with Network Intrusion Datasets

- 身份：Diana Magalhães、Eva Maia、João Vitorino、Isabel Praça；arXiv `2606.19220v1`，2026-06-17，12 页，WorldCist'26 会议稿。
- 原件：`raw/papers/datasets/published-baseline/2606.19220v1-XGBoost-machine-unlearning-GeNIS.pdf`。
- SHA-256：`9e0d74e7a7d1a72ca451c7dc1436e66b4c09fb28ef6485ddc666397edb864bc3`。
- 证据等级：A 类、开放预印本全文。
- 任务：XGBoost 的机器遗忘；GeNIS 仅用于二分类模型效用、遗忘效率和遗忘质量，不是提出更强检测器。
- 数据：表 1（PDF 第 6 页）给出 GeNIS 2,806,168 条、训练 2,244,934、测试 561,234、14 特征、2 类。总数精确对应官方 5 秒流版本，故“5 秒”是由官方版本计数推定；论文没有字面声明文件名或 DOI 版本。
- 划分：80/20 数量；没有说明随机/分层/场景、随机种子或 14 个字段名称。0.01% 训练样本用于遗忘，并被有意集中到单一分片；5 个分片，每个使用 1 或 3 个切片。
- 模型：完整 XGBoost（XGB-T）、去除遗忘集后全重训（XGB-R）、XGBoost-Forget 训练/遗忘后（XGB-FT/XGB-FU），以及使用两层全连接网络的 SISA。
- 表 5（PDF 第 9 页）：XGB-T F1 99.978031%、准确率/召回 99.978084%、精确率 99.978057%；XGB-R F1 99.978389%、全重训 3.9892 秒；XGB-FU 5 分片/3 切片 F1 99.978023%、0.5014 秒，约为全重训的 7.96 倍加速；1 切片 0.7361 秒。SISA F1 约 99.09%，运行 17.5142–34.5388 秒。
- 表 6（PDF 第 9 页）：感染分片的 ASR 从 XGB-FT 100% 降至 XGB-FU 1.5749%/1.5840%；全分片聚合在遗忘前已只有约 1.57%–1.62%，因此聚合稀释了后门信号。
- 表 7（PDF 第 10 页）：JSD 约 `7e-6` 至 `1e-5`，作者明确判定未呈现预期模式，可能因仅遗忘 0.01% 而不适合该设置。
- 缺失：没有字段表、XGBoost 超参数、随机种子、指标平均方式、每类召回、FPR、置信区间或源码。
- 效率边界：作者明确承认，若遗忘样本分散到多个分片，受影响分片都会重训，效率会趋近全重训；当前约 7.96 倍加速是在有利的单分片放置条件下，不可外推到任意删除请求。
- 与 A1 的严格可比性：不严格可比。A2 使用 5 秒/14 字段/未披露平均方式，A1 使用 60 秒/87 或 16 字段，并报告二分类 F1 与多分类宏 F1。
- 源码：全文和一般 GitHub 题名查询未发现可验证作者仓库；CatalyzeX 页面显示 `Request Code`，应记为源码未公开。

## 初步“基线是否饱和”裁决

- **发布随机行级协议：近乎饱和。** A1 的最好二分类 F1 距 100% 仅 0.0051 个百分点，多分类宏 F1 距 100% 仅 0.0183 个百分点；A2 的 5 秒二分类 XGB 也约 99.978%。继续只替换模型、只报准确率/F1 的绝对提升空间极小。
- **真实泛化：实验待证，而非饱和。** 现有论文没有原始捕获、攻击运行、场景、日期或端点分组留出；没有逐类召回和跨种子不确定性；特征选择与标准化的拟合边界也未完整披露。
- **研究承接方式：双表。** 表 A 忠实复现 A1 的 60 秒官方发布划分，以证明同协议可比；表 B 使用捕获/场景/时间分组防泄漏协议，以检验未知运行泛化。表 B 不能用更低或更高分数直接声称超越表 A。

## 未关闭疑点（更新）

- Springer 正式 FPS PDF 受订阅限制；需比较可访问的作者稿与正式元数据，确认是否存在表格修订。
- A2 的正式 WorldCist'26 DOI/论文集版本是否已上线。
- 两篇论文是否存在未被一般网页索引捕获的作者代码仓库。
- 除 A1、A2 外，是否有仅在参考文献、代码、学位论文或未规范元数据中使用/引用 GeNIS 的作品。

## GeNIS 任务机会矩阵（工作版）

证据边界：以下“可构造性”来自 GeNIS 原始论文和官方数据结构；“未饱和”表示尚无已核验 GeNIS 论文给出该严格任务的结果，不表示方法必然有效。正式结果仍需真实实验裁决。

| 任务 | 可构造性与冻结单元 | 正式强基线 | 主指标 | 当前饱和度 | 已知缺陷/不可比较项 | 创新空间 | 最小证伪实验 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 普通随机行级二分类 | 官方 5/60 秒预处理训练/测试文件可直接使用 | A1 的 RF/XGB/LGBM；A2 的 XGB | F1、ACC、FPR、训练/推理时延 | **近饱和**：F1 99.995% / 99.978% | 不证明新场景泛化；5 秒与 60 秒、14/16/87 字段不可混比 | 仅剩效率、压缩或校准，不宜把微小 F1 增量作为主创新 | 原样复现 A1；若同种子误差不能稳定下降且 CI 重叠，停止模型替换路线 |
| 普通随机行级四类分类 | A1 的 60 秒 `CategoryLabel` 及其 80/20 文件 | RF、XGB、LGBM，完整 87 字段和论文 16 字段 | 宏 F1、宏召回、每类召回、FPR | **近饱和**：宏 F1 99.9817% | A1 未报每类召回/混淆矩阵；DoS 占 80.22% | 仅逐类诊断或效率有空间；不适合作为唯一论文任务 | 复现 RF/XGB；若最弱类召回也接近 100% 且无显著误差结构，否决继续堆模型 |
| 开放集/未知攻击识别 | 用 `SubCategoryLabel` 或完整攻击场景留一类；所有同源捕获只进一个分区。13 子类可做留一攻击族/留一子类 | 闭集 RF/XGB 阈值；OpenMax/能量分数；一类分类器；已入库开放集 NIDS 基线 | 未知 AUROC/AUPR、OSCR、已知宏 F1、FPR@TPR、拒识率 | **未评估** | 子类样本极不均衡，`recon-dns` 仅 20；不能随机拆同一运行 | 分层标签与顺序攻击步骤使未知类协议可解释 | 选择一个中等样本子类整类留出；RF/XGB 最大概率阈值与能量/距离基线比较；若未知 AUPR 不高于类先验或已知性能崩溃则否决 |
| 跨场景泛化 | `3-scenarios`、PCAPNG、采集日、攻击机位置与顺序步骤可作为组；整场景/整日留出 | RF/XGB/LGBM；域不变 ERM；组分层仅用于训练内验证 | 留出场景宏 F1、最坏组召回、良性 FPR、跨组方差 | **高度未饱和；优先级最高** | 8 个攻击场景、良性仅 3 类，独立组数少；不同场景可能对应不同攻击类型 | 从“记住捕获”转向“跨运行泛化”；可研究行为字段与连接指纹消融 | 先做按原始捕获/场景 GroupKFold 或留一场景；若所有模型掉分小于预设可测量门槛且无最坏组差异，缩小该方向 |
| 持续学习 | 按 2025-02-06 至 02-12 时间顺序或攻击链阶段形成任务流；只允许过去训练未来测试 | 逐批重训 XGB；在线/增量树；回放 MLP；朴素微调 | 平均准确率、遗忘量、前向迁移、时间加权 F1、更新成本 | **未评估** | 只有约 7 天且标签/日期强相关；一次采集不能证明长期概念漂移 | 研究有限场景流中的更新/遗忘权衡，不可夸大为长期生产漂移 | 固定 3–5 个时间任务，比较全量重训与回放；若简单全重训在预算内且无遗忘优势，否决复杂持续学习 |
| 机器遗忘 | A2 已构造 5 秒、14 字段、5 分片、1/3 切片，遗忘 0.01% | 全重训 XGB、SISA、XGBoost-Forget | 删除后效用、RT/加速比、ASR、成员推断、分布距离 | **效用指标近饱和；遗忘质量未饱和** | A2 将删除点集中单分片，JSD失效；超参/字段/种子未披露 | 随机多分片删除、类别/场景删除、可验证遗忘与成本曲线 | 将相同 0.01% 均匀撒到 1/2/5 分片；若加速随分片数迅速消失且 ASR/成员推断不接近全重训，否决“通用高效遗忘”主张 |
| 投毒恢复 | 在训练集注入可审计触发器/标签翻转，保持测试净集；按场景与分片控制污染 | 干净重训 XGB、A2 的 XGBoost-Forget、数据过滤+重训、SISA | 干净宏 F1、ASR、恢复时间、误删率、恢复后校准 | **未饱和** | A2 全分片聚合在遗忘前已稀释 ASR，可能制造假安全；人工触发器代表性有限 | 研究定位污染分片与恢复，而不只报平均准确率 | 对全局与单分片分别注入同预算触发器；若未遗忘集成已自然压低 ASR，改用不被投票稀释的污染，否则否决该设置 |
| 选择性预测/拒绝 | 任何分类器输出概率/集成分歧；严格测试集上按置信度拒绝 | 温度缩放 RF/XGB/MLP；深度集成；保序校准；选择性风险阈值 | 风险-覆盖曲线、AURC/E-AURC、固定覆盖错误率、选择性宏 F1 | **未评估** | 随机协议几乎无错，无法区分方法；必须在场景留出或未知类上评估 | 将不确定性用于人工复核/拒识，适合与开放集结合 | 在场景留出上比较最大概率、熵与校准阈值；若 AURC 不优于随机拒绝或覆盖稍降即无错误，则不支持复杂方法 |
| 校准/告警预算 | 概率输出与良性测试流可构造；按单位时间或每千良性流定义告警预算 | 未校准 RF/XGB；Platt、温度、保序；成本敏感阈值 | ECE、Brier、NLL、每小时/千流误报、预算下召回 | **未评估；比随机F1更有空间** | 现有论文只报 FPR，且随机拆分 FPR 低；没有生产流量基率 | 从排序分数转向受约束告警运营；可按良性用户/管理员/背景分面 | 在验证集定阈值满足固定误报预算，只在场景留出测试；若校准不改善 Brier/NLL 或预算召回，否决校准模块 |
| 早期检测 | PCAPNG 与 5/10/30/60 秒多间隔流、攻击步骤时间表可构造截断观测 | 5 秒 RF/XGB；只用首 N 包/首 T 秒；累积流投票 | 检测时延、TTD CDF、早期宏 F1、预算FPR、提前量 | **未评估** | 四个间隔来自同源 PCAP，不能跨分区；现有聚合流可能含完整窗口未来信息 | 速度—准确率曲线、分阶段最短证据、在线更新 | 同一捕获先分区再生成 5/10/30/60 秒视图；若 5 秒简单 XGB 已在固定 FPR 下达到目标时延，否决复杂序列模型 |
| 攻击链阶段识别 | 八场景中 DNS→NMAP→具体攻击有显式阶段与约 5 分钟间隔；`1-packets/3-scenarios` 可映射阶段 | 逐流 RF/XGB；HMM/CRF；轻量时序模型；阶段多数类 | 阶段宏 F1、序列编辑距离、阶段转移准确率、检测提前量 | **未评估** | `CategoryLabel` 不是阶段标签，必须由场景表和时间对齐重新标注；DNS 仅 20 流 | GeNIS 特有的顺序场景优势，区别于静态分类 | 选 2–3 个阶段完整场景，建立确定性对齐门禁；若标签对齐不唯一或静态 RF 已完全区分，则缩小为阶段转移/提前量问题 |
| 解释与机制审计 | 125 字段、类型分组、SHAP 与场景标签可用；可做字段族/身份字段消融 | A1 SHAP；Permutation；组消融；稳定性选择；反事实 | 解释稳定性、跨折Jaccard、忠实度、性能下降、最坏组差异 | **SHAP展示已有，可靠性未饱和** | A1 只汇总字段类型重要度；相关特征下 SHAP 可不稳定，不能等同因果 | 连接指纹/拓扑依赖审计、跨场景解释稳定性 | 多种子/场景折上比较 SHAP 排名；若排名低稳定且删身份字段大幅掉分，则证明现有模型依赖捷径；若稳定且组消融无影响则否决捷径主张 |
| 主动学习 | PCAP/场景流可作为未标注池，按捕获组逐轮查询；场景表提供真值回放 | 随机采样；不确定性；分歧采样；分层/多样性采样 | 标注量—宏 F1 曲线、AULC、最弱类召回、查询多样性、运行成本 | **未评估** | 同源相邻流冗余极高，行级采样会夸大收益；需要组/片段级查询 | 用场景级或时间片级查询降低冗余，结合开放集发现 | 固定场景留出，按时间片而非行查询；若不确定性采样不优于分层随机或只重复查询相邻流，则否决复杂策略 |

### 初步优先级

1. **P0：跨场景泛化 + 校准/告警预算**。直接修复现有随机协议无法回答的现实问题，且可用 RF/XGB 强基线。
2. **P1：早期检测 + 攻击链阶段识别**。利用 GeNIS 特有的多间隔、PCAP 和顺序阶段，避免在近饱和静态分类上挤微小增量。
3. **P1：开放集 + 选择性预测**。未知攻击与拒识可组成一套协议，但必须避开极少样本 `recon-dns` 的不稳定留出。
4. **P2：机器遗忘/投毒恢复**。已有 A2，可承接点是多分片、非有利删除和更强遗忘验证，而非再报 99.97% 检测 F1。
5. **P2：持续学习/主动学习/解释审计**。可构造，但独立时间跨度和场景数有限，先用最小实验验证是否存在足够信号。

## 可恢复检查点：会话中断前

### 完成度与分类计数

- 当前完成度：约 45%；尚未达到“查全”停止条件。
- A 类：2 篇，均已取得并阅读全文。
  1. `Binary and Multiclass Cyberattack Classification on GeNIS Dataset`，arXiv `2511.08660v1`；正式 FPS 版本 DOI `10.1007/978-3-032-20018-1_18`。
  2. `Machine Unlearning for the XGBoost Model with Network Intrusion Datasets`，arXiv `2606.19220v1`。
- B 类：当前已确认 0 篇。Consensus 等插件返回的相邻作品尚未完成全文引用核验，不能预先计作 B 类。
- C 类：SciSpace 首轮返回中明确有 8 个语义近邻或时间上不可能引用的作品；Sider Google Scholar 式检索还有大量 `genis`、`genistein` 同名噪声，未逐条计数。最终 C 类数量尚未封口。
- 全文核验数：A 类 2 篇；加上任务前已经完整核验的 GeNIS 数据论文，证据面共 3 篇全文。

### 原件、wiki 与 Zotero 状态

- 已新增原件：
  - `raw/papers/datasets/published-baseline/2511.08660v1-GeNIS-binary-multiclass-classification.pdf`
  - `raw/papers/datasets/published-baseline/2606.19220v1-XGBoost-machine-unlearning-GeNIS.pdf`
- 原件 SHA-256 已分别记录为 `2650407346007c4b24df2398fdd96c4bacd0ee331a23f857ab03038d56731138` 与 `9e0d74e7a7d1a72ca451c7dc1436e66b4c09fb28ef6485ddc666397edb864bc3`。
- wiki：两篇新全文的规范论文笔记尚未创建，`wiki/papers/datasets/published-baseline/INDEX.md` 尚未更新；因此 raw→wiki→索引闭合仍未完成。
- Zotero 去重：扩展检索前两篇均不存在；数据论文已有两个重复书目条目（`33735EHP`、`FX9SE29U`）。
- Zotero 规范导入：`zotero_add_items_by_arxiv` 与 identifier 导入因 HTTP 429/超时失败。
- Zotero 降级状态：已保存两个弱源网页条目，`2511.08660` 对应 `SS6IHSUE`，`2606.19220` 对应 `CN7XAI2P`；未附 PDF，不能声称论文条目闭合。

### 最后完成的查询

- DataCite 官方记录确认：`10.5281/zenodo.14919237` 为 GeNIS `1.0.0` 版本 DOI，创建于 2025-02-24，关系为 `IsVersionOf 10.5281/zenodo.14919236`。
- Zenodo 官方记录确认：记录 `14919237` 的 `conceptdoi` 为 `10.5281/zenodo.14919236`、`conceptrecid` 为 `14919236`，版本为 `1.0.0`，发布日期为 2025-02-24；记录于 2026-02-05 更新，但版本号未变。
- 随后请求 `https://zenodo.org/api/records/14919237/versions?page=1&size=100` 以枚举完整版本链时，受限网络返回 `Could not resolve host: zenodo.org`。该失败之后已按指令停止新增检索。

### 未关闭候选与疑点

- Consensus 首轮除数据论文和 A1 外返回若干可能只在综述/方法中引用 GeNIS 的作品；必须逐条 `fetch`、核验出版时间、参考文献或全文，才能判 B/C。
- 正式 FPS PDF 受 Springer 订阅限制；开放 arXiv 稿与正式页面的题名、作者、摘要、章节和页数范围一致，但尚未逐表比较排版后的正式 PDF。
- A2 的 WorldCist'26 正式 DOI/论文集版本尚未定位。
- 两篇 A 类均未发现可验证作者源码；一般 GitHub 题名查询只返回论文页、`Request Code` 或无关仓库，仍需作者/机构/GitHub 精确链最终封口。
- A2 的 5 秒版本依据 2,806,168 总流数推定，论文未字面声明文件名、数据 DOI 版本或 14 个字段名称。
- A1 未说明随机种子、分层实现，以及特征选择器/标准化器是否仅在训练折拟合；这些是复现与泄漏审计缺口，不可擅自补猜。

### 精确阻塞

1. Scite：月度 MCP 调用额度耗尽，2026-09-01（UTC）重置。
2. Sider OpenAlex：返回空题名导致结构化输出校验错误；Google Scholar 式简称检索精度极低。
3. Zotero 规范 arXiv 导入：HTTP 429 与读取超时；当前只有网页条目。
4. Springer 正式 FPS PDF：订阅墙；直接 PDF 端点返回 HTML 访问页面。
5. Zenodo 版本枚举：最后一次调用 DNS 解析失败；基础记录已成功取得。

### 唯一下一动作与目标交付

- 恢复时先完整重读 `task_plan.md` 与本文件，然后只执行一个动作：重试 Zenodo 官方版本列表端点，封口概念 DOI、版本 DOI 和版本历史；完成或记录持续阻塞后，再恢复论文引用链查全。
- 最终目标：`.Codex/docs/2026-08-12-GeNIS-2025引用论文查全审计.md`。
- 禁止修改：实验源码、路线总控、恢复卡、候选登记册。
- 代理映射：`genis2025_citation_literature_sol_max → gpt-5.6-sol → effort=max`。

## 检查点 2：Zenodo 版本链封口

- 恢复后先完整重读 `task_plan.md` 与本文件，再按冻结动作请求官方版本端点。
- 受限网络首次仍无法解析 `zenodo.org`；经受控联网重试，`size=100` 返回 HTTP 400。该错误来自分页参数，不是记录不存在。
- 改用 `https://zenodo.org/api/records/14919237/versions?page=1&size=10` 成功。官方返回 `hits.total = 1`，唯一版本为：
  - 记录：`14919237`
  - 版本 DOI：`10.5281/zenodo.14919237`
  - 概念 DOI：`10.5281/zenodo.14919236`
  - 概念记录：`14919236`
  - 版本：`1.0.0`
  - 发布日：2025-02-24
  - 创建：2025-02-24T17:30:11Z
  - 更新：2026-02-05T14:49:41Z
- 裁决：截至 2026-08-12，官方公开版本链中只有 `1.0.0` 一个具体版本。2026-02-05 是记录更新时间，不是新版本发布日期。后续论文若只写“GeNIS”而未写 DOI，只能标为“与唯一公开版本相容”，不能擅自声称作者明确绑定 `1.0.0`。
- 当前完成度约 50%；下一动作转为多源引用全集封口。

## A 类逐篇证据模板

每篇记录：题名、作者、年份、稳定标识、原件路径、源码 URL、GeNIS 数据版本、数据目录/流间隔、样本量、类别、特征、预处理、拆分、模型、调参、指标、最好结果、全文页码/章节、源码核验、作者披露缺陷、本课题发现的复现缺口、可比与不可比项。

## 未关闭疑点

- 两篇优先候选是否都已正式发表，是否公开全文与源码？
- 是否存在只在参考文献、代码依赖或数据路径中出现而未被学术索引捕获的实际使用作品？

## 检查点 3：恢复后版本链复核与规范入引并集

- 恢复后再次请求 Zenodo 官方 `records/14919237/versions?page=1&size=10`；受限网络首次 DNS 失败，经受控联网后返回成功，仍为 `hits.total = 1`。因此检查点 2 的版本链裁决被独立复核，且 `14919237` 明确是具体版本记录，不是概念记录。
- OpenAlex 以数据论文作品 `W4408724424` 反向查询 `cites`，返回 4 项：
  1. `A Multi-Head Attention and Residual Dense Network with Dynamic Sampling for Fine-Grained Network Intrusion Classification`，DOI `10.1109/ICUMT67815.2025.11268763`，A 类候选，正式版本非开放获取。
  2. `A Novel Synthetic Dataset for JavaScript Malware Detection`，DOI `10.1109/AIIA68273.2025.11383680`，B 类候选，正式版本非开放获取。
  3. `Machine Unlearning for the XGBoost Model with Network Intrusion Datasets`，正式 DOI `10.1007/978-3-032-32026-1_14`；这解决了 A2 正式版本标识疑点，正式版本非开放获取，开放全文仍以 arXiv 作者稿为证据。
  4. `Engineering cyber ranges and security testbeds: a survey of technologies, use cases, and research trends`，DOI `10.1007/s10207-026-01298-y`，B 类候选，开放正式全文。
- 语义学术搜索的反向引用接口返回 4 项，其中三项与 OpenAlex 重合，并额外返回：`Generalizing across Networks: Evaluating Model Transferability for Intrusion Detection`，DOI `10.5220/0015002100004103`，A 类候选，标为开放获取、CC BY-NC-ND。
- 规范入引并集暂为 6 个作品族：既有 A1、A2，加上 `Multi-Head`、`Generalizing`、`JavaScript Malware` 与 `Cyber Ranges Survey`。OpenAlex 与语义学术搜索各漏收至少一项，不能单独作为查全依据；下一步须以开放引文语料库、Crossref 数量、全文参考文献和题名/作者/GitHub 链交叉封口。
- 当前完成度约 58%；A 类已全文确认 2 篇，新增 A 候选 2 篇，B 候选 2 篇。候选尚未全文核验，因此当前 A/B 最终计数不变。

## 用户补充：本地数据下载状态（验收前）

- 2026-08-12 用户报告：GeNIS Zenodo 记录 `14919237` 除 `1-packets.zip` 外均已下载。
- 此处严格记为用户声明，不预先声称文件有效、完整或可供实验使用。
- 历史初步定位曾命中 `~/Downloads/0-info.zip`、`2-flows.zip`、`3-scenarios.zip`、`4-preprocessed.zip` 以及已解压的 `0-info/`；没有命中 `1-packets.zip`。随后主进程按用户授权移入规范原件路径，`Downloads` 原路径已消失。
- 下一门禁：官方字节数/MD5 → ZIP 完整性 → 顶层目录及关键清单 → 任务可构造性。未通过全部相关门禁前，只能称“已定位候选文件”。

## 检查点 4：本地 GeNIS 数据文件门禁与 `4-preprocessed` 专项核验

### 官方清单与本地验收

| 文件 | 官方字节数 | 官方 MD5 | 本地 SHA-256 | ZIP 完整性 | 状态 |
| --- | ---: | --- | --- | --- | --- |
| `0-info.zip` | 3,308 | `432ada3813f0261ac8b5e371ea4d729e` | `7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc` | 通过 | 已验收 |
| `1-packets.zip` | 1,028,741,083 | `5afbceaadfe3c3476f54723434d59b4a` | 未定位 | 未执行 | **缺失** |
| `2-flows.zip` | 380,755,720 | `063b7a2ec6e6b73cc302151d2b3ba6d7` | `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` | 通过 | 已验收 |
| `3-scenarios.zip` | 491,738,368 | `7c560f37af540c9e65abae813bdacab4` | `8a56adc70d4400786b774012c69af1d5264d6733986d5a6d5d500e66b57cf246` | 通过 | 已验收 |
| `4-preprocessed.zip` | 599,956,349 | `1856f231354cf4928e40ba606080a9b2` | `50c696a8ccbc4320a559711d58092e1f5552e6971725eeb208cd2398e6cf7db8` | 通过 | 已验收 |

规范路径为 `raw/datasets/GeNIS-2025/0-info/`、`raw/datasets/GeNIS-2025/2-flows.zip`、`raw/datasets/GeNIS-2025/3-scenarios.zip`、`raw/datasets/GeNIS-2025/4-preprocessed.zip`。其中 `0-info/` 内含 `genis-features.csv` 与 `genis-ground-truth.csv`；`2-flows.zip` 含 5/10/30/60 秒按活动类型分开的完整 125 列流表；`3-scenarios.zip` 含四种间隔下 8 个顺序攻击场景；`4-preprocessed.zip` 含四种间隔各一对训练/测试 CSV。原 `~/Downloads` 只作为历史来源位置，不再是规范路径。

### `4-preprocessed.zip` 的内容与复现角色

- 压缩包共有 8 个 CSV。含表头行数分别为：5 秒训练/测试 `2,244,935/561,235`；10 秒 `1,203,348/300,838`；30 秒 `486,347/121,588`；60 秒 `294,845/73,713`。扣除表头后恰对应各间隔总量的 80/20。
- 5/10 秒文件各 85 列，30/60 秒文件各 87 列；每份最后三列均是 `BinaryLabel`、`CategoryLabel`、`SubCategoryLabel`。列数差异来自各间隔中独热编码后实际出现的协议/标志/状态取值不同，不能把“所有间隔均 87 输入特征”当作官方事实。
- 该层从 `2-flows` 的 125 列完整流表中删除显式标识、地址、时间等字段，对协议、标志和状态作独热编码，并提供发布方打乱、分层的 80/20 文件。它是**已预处理的同协议主入口**，但不含验证集，也不保留可直接执行场景/捕获分组所需的全部身份列。
- A1 的 60 秒表 1 计数与 `4-preprocessed` 的 60 秒训练/测试完全一致，故 A1 的发布协议可直接从该层复现；A2 的 5 秒总数与训练/测试计数也完全一致，但 A2 又声称 14 特征且未披露字段名，因此 `4-preprocessed` 只能复现其样本划分规模，不能从现有披露唯一重建 14 字段输入。
- `2-flows` 是完整 125 列、按单活动类型分开的上游；`3-scenarios` 复用同类完整流字段，把攻击步骤与对应时段良性流组合成 8 条攻击链。两者适合重新冻结时间、活动、捕获与场景组；`4-preprocessed` 则适合忠实复现发布方随机行级结果，三者不能互相替代。

### 可启动与阻塞任务

- 可立即支持：发布方随机行级二/多分类复现（`4-preprocessed`）；字段选择、身份字段消融和机器遗忘（`2-flows` 或 `4-preprocessed`）；按流时间前向、按活动类型/场景留出、攻击链阶段、校准/告警预算、开放集、持续/主动学习（`0-info + 2-flows + 3-scenarios`，仍须先写确定性分组清单）。
- 部分可支持：多时间间隔的**聚合流级**早期检测，可比较 5/10/30/60 秒统计，但四层来自相同底层捕获，必须先按捕获/场景划分再比较，不能将不同间隔当独立样本。
- 当前阻塞：逐包重提取、首 N 包/首 N 字节、包级检测时延、PCAP 重放、换 HERA 参数或更换流导出器、验证同一 PCAP 在不同导出器下的字段一致性。上述任务均需要缺失的 `1-packets.zip`。
- 数据门禁：正式实验前还需建立不可跨分区的原始活动/场景/时间组键，验证标签连接唯一性，冻结字段排除清单，并检查同一 `FlowID` 的累计/相邻输出是否跨分区；ZIP 与哈希通过只证明文件完整，不证明实验划分有效。

## A3：Generalizing across Networks: Evaluating Model Transferability for Intrusion Detection

- 身份：Miguel Silva、João Vitorino、Daniela Pinto、Ivone Amorim、Eva Maia、Isabel Praça；SECRYPT 2026 正式论文，第 701–711 页；DOI `10.5220/0015002100004103`；CC BY-NC-ND 4.0。
- 原件：`raw/papers/datasets/published-baseline/2026-Silva-Generalizing-across-Networks-GeNIS.pdf`；SHA-256 `6e4e5c0aa6d09d0c0403725631658ed5c19e9cb07faed71dd66d5cae1375d687`；11 页正式全文。
- 任务：GeNIS、HIKARI-2021、CICIDS2017、UNSW-NB15 的同域二分类与跨数据集迁移，另比较三数据集联合训练后对第四个未见数据集的预测。
- 数据与字段：从四套原始 PCAP 统一用 HERA 生成 60 秒流；分层 70/30。删除协议、服务、端口等类别字段、缺失率超过 10% 的列与仍含缺失的行，保留 40 个行为字段（PDF 第 3 页）。GeNIS 训练良性/恶意 `19,005/238,984`，测试 `8,145/102,422`（表 1，PDF 第 4 页）。
- 特征选择：信息增益、卡方、递归特征消除、平均绝对偏差、离散比；每数据集前十的并集形成 21 字段。GeNIS 前十为 `Offset`、`SrcLoad`、`Load`、`DstLoad`、`Ssaddr`、`DAppBytes`、`Rate`、`RunTime`、`SrcRate`、`Sum`（表 6，PDF 第 5 页）。
- 模型：LGBM、RF、XGB、LSTM。树模型五折交叉验证选择网格参数；LSTM 64 单元加 32 单元全连接，把每行当单步序列，训练集再 80/20 验证，最多 30 轮、早停耐心 3（PDF 第 3–4 页）。
- 同域：GeNIS 40 字段的 LGBM/RF/XGB 均 F1 100%、FPR 0；LSTM F1 99.97%、FPR 0.16（表 7，PDF 第 7 页）。
- 单源迁移：GeNIS→HIKARI/CICIDS/UNSW 的 RF F1 为 `67.95/86.21/0`；LGBM、XGB 在 UNSW 也为 0（表 7）。21 字段时 GeNIS→HIKARI 的 RF 为 67.91%，GeNIS→CICIDS 的 RF 降为 46.04%，GeNIS→UNSW 的树模型近 0（表 8，PDF 第 7 页）。
- 未见 GeNIS 联合训练：训练集排除 GeNIS 时，40 字段在 GeNIS 上最好 RF F1 66.34%、FPR 0；21 字段最好 XGB F1 67.05%、FPR 0.21（表 9–10，PDF 第 9 页）。只要组合中包含 GeNIS，GeNIS 留出又几乎达 100%。
- 关键裁决：该文直接证明同域随机协议近饱和不等于迁移饱和。当前最适合承接的是跨场景/跨网络泛化，而不是继续挤压随机行级 F1。
- 缺口：没有源码、随机种子、重复运行、置信区间、每类结果或校准。`Offset`、`Ssaddr` 等潜在源文件/连接指纹进入字段；未说明特征选择是否在每个训练域内独立完成，四数据集前十并集是否包含未见测试域的信息。
- 本地边界：该文从 PCAP 统一重提取，当前缺 `1-packets.zip`，不能严格重放其 GeNIS PCAP 协议；现有 `2-flows` 只支持流级近似或场景内重划分。

## B1：Engineering cyber ranges and security testbeds: a survey of technologies, use cases, and research trends

- 身份：Klaus Mayer、Max Landauer、Florian Skopik、Markus Wurzenberger；`International Journal of Information Security` 25:140，2026-08-10；DOI `10.1007/s10207-026-01298-y`；CC BY 4.0。
- 原件：`raw/papers/datasets/2026-Mayer-Engineering-cyber-ranges-survey.pdf`；SHA-256 `4d7a07dda03707fff2192f28f300f46617608291190a7598021bb48dd6227df1`；109 页正式开放全文。
- 全文核验：正文只在 PDF 第 25 页把 GeNIS 作为 Airbus CyberRange 云端仿真平台生成企业拓扑攻击、良性和背景流量的实例；参考文献第 166 项在 PDF 第 107 页给出数据论文 DOI。
- 分类：**B 类**。全文没有用 GeNIS 样本训练或评测模型，也没有版本、字段、拆分、指标或结果。

## 用户人工下载清单：付费墙与正式版本补件

以下清单是当前无法从合法开放来源取得的 GeNIS 相关全文。用户如有机构订阅，可从官方出版页下载并放入建议路径；不得使用不可信镜像。

### 必须补件：影响 A/B 最终分类或实验协议核验

1. **中文题名：采用动态采样的多头注意力与残差密集网络细粒度入侵分类**  
   原题名：`A Multi-Head Attention and Residual Dense Network with Dynamic Sampling for Fine-Grained Network Intrusion Classification`  
   作者：Neha Shukla、Rakesh Chandra Joshi、Radim Burget、Martin Rosa、Malay Kishore Dutta；2025。  
   DOI：`10.1109/ICUMT67815.2025.11268763`。  
   官方出版页：<https://ieeexplore.ieee.org/document/11268763>。  
   所需版本：IEEE ICUMT 2025 正式出版 PDF，第 266–271 页。  
   建议文件名：`2025-Shukla-GeNIS-MHSA-RDB-dynamic-sampling.pdf`。  
   目标路径：`raw/papers/datasets/published-baseline/2025-Shukla-GeNIS-MHSA-RDB-dynamic-sampling.pdf`。  
   已有替代稿：无；ResearchGate 只有“请求全文”，机构网页和 IEEE 页面只有摘要。  
   仍缺证据：四种间隔逐项样本量、训练/验证/测试拆分、字段及预处理、动态采样比例、完整网络/超参数、对照基线、13 子类逐类召回、宏 F1、误报率、效率、随机种子与源码。当前只能列 A 类候选，不能用摘要补猜协议。

2. **中文题名：用于 JavaScript 恶意软件检测的新型合成数据集**  
   原题名：`A Novel Synthetic Dataset for JavaScript Malware Detection`  
   作者：Hind Ikni、Alaa Eddine Belfedhal；2025。  
   DOI：`10.1109/AIIA68273.2025.11383680`。  
   官方出版页：<https://ieeexplore.ieee.org/document/11383680>。  
   所需版本：IEEE AIIA 2025 正式出版 PDF。  
   建议文件名：`2025-Ikni-JavaScript-malware-synthetic-dataset.pdf`。  
   目标路径：`raw/papers/datasets/citation-only/2025-Ikni-JavaScript-malware-synthetic-dataset.pdf`。  
   已有替代稿：无；ResearchGate 只有“请求全文”。  
   仍缺证据：GeNIS 在正文或参考文献中的精确位置与语境。题名和摘要显示实验对象为 JavaScript 恶意软件，故目前只列 B 类候选，尚不能全文确认其仅引用。

### 建议补件：已有完整作者稿，正式 PDF 用于版本对照

3. **中文题名：GeNIS 数据集上的二分类与多分类网络攻击分类**  
   原题名：`Binary and Multiclass Cyberattack Classification on GeNIS Dataset`  
   作者：Miguel Silva、Daniela Pinto、João Vitorino、Eva Maia、Isabel Praça、Ivone Amorim、Maria João Viamonte；正式出版年 2026。  
   DOI：`10.1007/978-3-032-20018-1_18`。  
   官方出版页：<https://link.springer.com/chapter/10.1007/978-3-032-20018-1_18>。  
   所需版本：FPS 2025/LNCS 16402 正式出版 PDF，第 335–351 页。  
   建议文件名：`2026-Silva-GeNIS-binary-multiclass-formal.pdf`。  
   目标路径：`raw/papers/datasets/published-baseline/2026-Silva-GeNIS-binary-multiclass-formal.pdf`。  
   已有替代稿：完整开放作者稿 `raw/papers/datasets/published-baseline/2511.08660v1-GeNIS-binary-multiclass-classification.pdf`，已足以支撑当前逐表审计。  
   仍缺证据：正式排版版是否对表格、页码、措辞或勘误作过修改。补件是**建议项而非当前结论的必要条件**。

4. **中文题名：面向网络入侵数据集 XGBoost 模型的机器遗忘**  
   原题名：`Machine Unlearning for the XGBoost Model with Network Intrusion Datasets`  
   作者：Diana Magalhães、Eva Maia、João Vitorino、Isabel Praça；2026。  
   DOI：`10.1007/978-3-032-32026-1_14`。  
   官方出版页：<https://link.springer.com/chapter/10.1007/978-3-032-32026-1_14>。  
   所需版本：WorldCist'26/LNNS 正式出版 PDF，第 150–162 页。  
   建议文件名：`2026-Magalhaes-XGBoost-machine-unlearning-formal.pdf`。  
   目标路径：`raw/papers/datasets/published-baseline/2026-Magalhaes-XGBoost-machine-unlearning-formal.pdf`。  
   已有替代稿：完整开放作者稿 `raw/papers/datasets/published-baseline/2606.19220v1-XGBoost-machine-unlearning-GeNIS.pdf`，已足以支撑当前逐表审计。  
   仍缺证据：正式版是否补充或修改 14 字段、参数、表格与局限性。补件同样是建议项，不阻断现有审计。

### 补件后的唯一后续动作

- 用户放入文件后，先核对 DOI、页数、许可证与 SHA-256，再全文定位 GeNIS 用法；随后创建或更新对应 wiki 笔记、方向索引和 Zotero 附件。
- 在两篇必须补件到位前，最终审计会保留“未决候选”而不会虚假封为 A/B 确认项。

### 补件状态更新

- 两篇“必须补件”已由主进程从合法 IEEE 来源核验并归档；前述人工下载阻塞已经解除。清单保留为过程记录，不再是当前待办。
- `2025-Shukla-GeNIS-MHSA-RDB-dynamic-sampling.pdf`：6 页，SHA-256 `45b6c2f0483273a8358109e408bdbf860b5f774040a6228a350b0110f9e6f173`；已完成全文核验，升级为 A4。
- `2025-Ikni-JavaScript-malware-synthetic-dataset.pdf`：6 页，SHA-256 `e8788fef603636ad1a6d7cfba632f84a1807d483d75d216a5195890bf63dcb35`；已完成全文核验，确认为 B2。

## A4：A Multi-Head Attention and Residual Dense Network with Dynamic Sampling for Fine-Grained Network Intrusion Classification

- 身份：Neha Shukla、Rakesh Chandra Joshi、Radim Burget、Martin Rosa、Malay Kishore Dutta；ICUMT 2025，第 266–271 页；DOI `10.1109/ICUMT67815.2025.11268763`。
- 原件：`raw/papers/datasets/published-baseline/2025-Shukla-GeNIS-MHSA-RDB-dynamic-sampling.pdf`；6 页；SHA-256 见上。
- 数据：明确使用 GeNIS `4-preprocessed` 四种时间间隔，13 个 `SubCategoryLabel` 子类。删除 IP/MAC/端口等非数值或冗余字段，编码类别字段、最小—最大缩放，称通常约 80 输入字段，但未给逐间隔精确清单（PDF 第 2–3 页）。
- 重采样：训练期间组合 SMOTE、随机过采样、随机欠采样与逆频率类别权重；没有目标类数、SMOTE 邻居数、随机种子或可审计流水线，未明确缩放/重采样是否只在训练折拟合；验证集比例也未披露。
- 模型：输入投影 512 维，3 个八头注意力块、头维 64，两个残差全连接块 256/128，dropout 0.3/0.2，13 类 softmax；Adam、交叉熵、200 轮、批 256、早停耐心 25、学习率平台下降（式 1–9，PDF 第 3–4 页）。
- 结构疑点：作者把 512 维投影重排成 `(1,512)` 再自注意力；若实现确为单 token，注意力权重会退化，难以建立跨特征依赖。无源码可核对实际张量轴。
- 汇总结果（表 II–III，PDF 第 5 页）：标称 5/10/30/60 秒的所提模型 F1 为 `0.9805/0.9894/0.9909/0.9900`；对应 RF 为 `0.9772/0.9850/0.9713/0.9796`。所提模型最好标称宏 F1 为 30 秒 0.9909；5 秒上 RF 准确率 0.9992 高于所提 0.9989。
- 每类结果（表 IV，PDF 第 6 页）：攻击子类几乎全为 0.9989–1.0000，最低为标称 30 秒 `benign-admin` 0.8724；`recon-dns` 每列仅 4 个测试样本，F1 1.0 不稳定。
- **表格错误裁决**：表 IV 表头标称 5/10/30/60 秒的总样本为 `121,587/73,712/561,234/300,837`，但官方真实 5/10/30/60 秒测试数是 `561,234/300,837/121,587/73,712`。其实际列顺序是 30/60/5/10 秒。表 II–III 的所提模型数值又与表 IV 的宏平均/准确率按错位列相同，因此公开结果的窗口标签不可直接信任；“10 秒峰值准确率 99.89%”也不是唯一峰值。
- 缺失：没有消融、训练/推理时间、参数量、FPR、校准、固定告警预算、场景/捕获/时间留出、跨数据集评价、随机种子、置信区间或源码；跨数据集被明确列为未来工作（PDF 第 6 页）。
- 创新占用判断：已占用“四间隔随机行级十三分类 + MHSA/RDB + 重采样”组合；**没有占用跨场景/跨网络泛化、域移位校准、固定告警预算或最坏组风险控制**。因此不改变当前方案一的首选排序，只把 A4 加入同协议强基线与复现审计。

## B2：A Novel Synthetic Dataset for JavaScript Malware Detection

- 身份：Hind Ikni、Alaa Eddine Belfedhal；AIIA 2025；DOI `10.1109/AIIA68273.2025.11383680`。
- 原件：`raw/papers/datasets/citation-only/2025-Ikni-JavaScript-malware-synthetic-dataset.pdf`；6 页；SHA-256 见上。
- 引用语境：PDF 第 2 页将 GeNIS 与另一数据论文并列，说明传统网络入侵/异常数据通过在受监控环境中模拟真实攻击场景来产生网络包，且数据构建依赖具体物理或虚拟基础设施；参考文献第 6 项在 PDF 第 6 页列 GeNIS 数据论文。
- 实际实验：完全使用生成的 9,780 条 JavaScript 脚本与 Sschumat 数据集训练/评价 CodeBERT；没有读取 GeNIS 文件或报告 GeNIS 结果。
- 分类：**B 类仅引用**，不是 GeNIS 实际使用。

## Zotero 闭合状态

- A1 正式 DOI 条目 `297YNSZD`，附件 `S2JY6EHD` 为 arXiv 开放作者稿。
- A2 正式 DOI 条目 `V2USVDU7`，链接附件 `CU8TAQZV` 指向 arXiv 开放作者稿。
- A3 正式 DOI 条目 `WR5TBHG7`，链接附件 `SBMHM5VP` 指向 SciTePress 正式开放全文。
- A4 正式 DOI 条目 `49Z3ITRB`，链接附件 `IUEKA27R` 指向 IEEE 正式出版页；本地正式 PDF 已归档。
- B1 正式 DOI 条目 `YX4RTA7R`，PDF 附件 `GF49VVX6` 为 Springer 正式开放全文。
- B2 正式 DOI 条目 `TUU6S5IT`，链接附件 `8QAU5VSK` 指向 IEEE 正式出版页；本地正式 PDF 已归档。
- 早期降级网页条目 `SS6IHSUE`、`CN7XAI2P` 仍是潜在重复项；本轮未获删除授权，故不做破坏性清理，只在最终报告建议用户在 Zotero 中合并。

## 检查点 5：IEEE 正式全文封口后中断保存

### 精确状态

- 截止时间：2026-08-12；完成度 **82%**；任务仍未完成，已停止新增检索。
- 规范引用并集：6 篇；A 类实际使用 4 篇，B 类仅引用 2 篇，当前并集内未决候选 0 篇。
- C 类：8 个已经逐条初筛排除的语义近邻；此外还有未逐条计数的 `genis`、`genistein` 同名噪声。该 8 只表示有记录的排除项，不能解释为全网 C 类总数。
- 全文：六篇引用作品全部逐页或逐表核验；若计入原始 GeNIS 数据论文，证据面共 7 篇全文。
- 当前没有继续进行的查询。最后完成的新增证据批次是两篇 IEEE 正式 PDF 的逐页核验、分类、wiki/索引/Zotero 写回；用户中断指令后未再启动检索。

### A/B 封口清单

| 类别 | 作品 | 正式标识 | 全文与结论 |
| --- | --- | --- | --- |
| A1 | `Binary and Multiclass Cyberattack Classification on GeNIS Dataset` | `10.1007/978-3-032-20018-1_18`；arXiv `2511.08660` | 开放作者稿全文已核验；60 秒官方 80/20，二分类 RF/XGB F1 最高 99.9949%，四分类宏 F1 最高 99.9817%；无分组划分、源码或逐类召回。 |
| A2 | `Machine Unlearning for the XGBoost Model with Network Intrusion Datasets` | `10.1007/978-3-032-32026-1_14`；arXiv `2606.19220` | 开放作者稿全文已核验；GeNIS 5 秒计数、80/20、未披露的 14 字段；0.01% 单分片删除时 F1 99.978023%，约 7.96 倍于全量重训；多分片删除收益趋近重训。 |
| A3 | `Generalizing across Networks: Evaluating Model Transferability for Intrusion Detection` | `10.5220/0015002100004103` | 正式开放全文已核验；60 秒、HERA 40/21 字段、70/30；GeNIS 同域树模型 F1 100%，排除 GeNIS 的联合训练对 GeNIS 最好 F1 67.05%，直接证明随机同域饱和不等于跨网络饱和。 |
| A4 | `A Multi-Head Attention and Residual Dense Network with Dynamic Sampling for Fine-Grained Network Intrusion Classification` | `10.1109/ICUMT67815.2025.11268763` | IEEE 正式全文已核验；四间隔、13 类、约 80 字段、MHSA/RDB 与动态重采样；标称最好宏 F1 0.9909，但表 II–IV 的窗口标签与官方样本量发生 5/10/30/60 对 30/60/5/10 的错位，窗口结论不可直接采用。 |
| B1 | `Engineering cyber ranges and security testbeds: a survey of technologies, use cases, and research trends` | `10.1007/s10207-026-01298-y` | 正式开放全文已核验；PDF 第 25 页只将 GeNIS 作为网络靶场生成数据实例，未实验使用。 |
| B2 | `A Novel Synthetic Dataset for JavaScript Malware Detection` | `10.1109/AIIA68273.2025.11383680` | IEEE 正式全文已核验；PDF 第 2 页和参考文献第 6 项只介绍 GeNIS 的网络流量生成语境；实际实验是 9,780 条 JavaScript 脚本与 CodeBERT。 |

### IEEE 两篇处理状态与方案裁决

- A4 原件：`raw/papers/datasets/published-baseline/2025-Shukla-GeNIS-MHSA-RDB-dynamic-sampling.pdf`，6 页，SHA-256 `45b6c2f0483273a8358109e408bdbf860b5f774040a6228a350b0110f9e6f173`。对应 wiki：`wiki/papers/datasets/published-baseline/GeNIS-多头注意力残差密集网络动态采样.md`；Zotero 正式条目 `49Z3ITRB`，出版页附件 `IUEKA27R`。
- B2 原件：`raw/papers/datasets/citation-only/2025-Ikni-JavaScript-malware-synthetic-dataset.pdf`，6 页，SHA-256 `e8788fef603636ad1a6d7cfba632f84a1807d483d75d216a5195890bf63dcb35`。对应 wiki：`wiki/papers/datasets/GeNIS-JavaScript恶意软件论文仅引用核验.md`；Zotero 正式条目 `TUU6S5IT`，出版页附件 `8QAU5VSK`。
- A4 已占用“四间隔随机行级十三分类 + MHSA/RDB + 重采样”，但没有组/场景留出、跨网络泛化、概率校准、固定告警预算或最坏组风险控制；其窗口标签错误反而要求审计式复现。因此首选方案仍是**跨场景/跨网络泛化 + 固定告警预算与校准**，没有因 A4 改变排序。

### 已落盘制品计数

- 新增引用论文原件：6 份，A 类 4 份、B 类 2 份；原始数据论文原件为任务前既有证据。
- 新增全文 wiki：6 篇；方向索引已更新 `wiki/papers/datasets/published-baseline/INDEX.md` 与 `wiki/papers/datasets/INDEX.md`。
- Zotero：6 个规范 DOI 条目。A1、B1 有可直接读取的全文附件；A2、A3、A4、B2 以规范条目加开放作者稿或官方出版页链接登记，本地 `raw/` 原件是全文核验事实源。
- 数据门禁：`raw/datasets/GeNIS-2025/0-info/`、`2-flows.zip`、`3-scenarios.zip`、`4-preprocessed.zip` 已通过官方大小、MD5 和完整性核验；`1-packets.zip` 缺失。

### 未完成项与精确阻塞

- 未完成专题证据矩阵：组分布鲁棒泛化、CVaR/DRO/REx 或更贴近入侵检测的跨网络领域泛化；域移位校准与选择性预测；Neyman–Pearson 或固定误报率/告警预算风险控制；跨数据/跨网络入侵检测；组簇统计与最坏组评价。每类仍需原论文公式、可观测量、假设、失败条件、已占原创点和 GeNIS 最小迁移机制。
- 未完成本地朱论文第三章结构与工作量证据参照；只允许提取结构和证据要求，不机械复制提升门槛。
- 未完成题名、简称、DOI、作者、数据文件名和 GitHub 引用链的最终封口叙述，以及多源交集解释和最终审计文档。
- Scite 月度额度已耗尽，2026-09-01（UTC）前不能补该源；这必须作为来源局限披露，但不阻断基于 OpenAlex、语义学术搜索、OpenCitations、Crossref 计数、正式全文反向引用和插件交集的当前六篇并集。
- A1/A2 正式出版社 PDF 仍可由用户补作版本对照，但完整作者稿已经足以支撑当前实验审计，不是终稿阻塞。
- Zotero 弱网页重复项 `SS6IHSUE`、`CN7XAI2P` 未获删除授权；只建议用户在 Zotero 中合并，不能由代理擅自删除。
- `1-packets.zip` 缺失只阻断逐包、首 N 包、PCAP 重放和重新导出类实验；现有流、场景、时间、遗忘、校准和告警预算方案均可由现有文件设计，正式实验前仍需冻结分组键与防泄漏门禁。

### 唯一恢复动作

完整重读 `task_plan.md` 与本文件后，**只先完成并写回“跨场景泛化 + 固定告警预算专题证据矩阵（含朱论文第三章结构参照）”**；该矩阵落盘前不扩展其他候选，也不开始最终审计结论。矩阵完成后再依次写最终引用并集封口说明与 `.Codex/docs/2026-08-12-GeNIS-2025引用论文查全审计.md`。

代理映射：`genis2025_citation_literature_sol_max` → `gpt-5.6-sol` → `effort=max`。

## 检查点 6：理论矩阵恢复卡（2026-08-12）

- 主制品：`.Codex/docs/2026-08-12-GeNIS跨场景泛化与固定告警预算/理论与已发表改进空间矩阵.md`。
- 精确状态：引用审计总任务 `82%`；主理论矩阵约 `48%`。矩阵在本检查点前为 `135` 行，已形成完整章节骨架，但仍有 `16` 处明确“待补”，不能视为交付完成。
- 已冻结章节：文档状态与证据口径；结论先行；第二节 A 类四篇实际使用工作表、同协议饱和度裁决、不能重复声称原创的机制。
- 未冻结章节：第三节七类通用理论证据；第四节推荐双机制；第五节轨 A；第六节轨 B；第七节两类基座适配；第八节消融和最小证伪；第九节朱论文结构参照；第十一节来源索引。第十节人工下载状态已有骨架但仍需终检。
- 子代理状态：`genis_core_theory_literature_reviewer_sol_max`（`gpt-5.6-sol`，`effort=max`）负责八篇本地全文的公式、假设和失败条件；中断时仍在运行，已要求停止新增联网检索并先保存独立证据卡。尚未收到并验收交付，不得把其内容记作主矩阵完成。
- 最后查询：PMLR 偏 AUC 原论文、Ben-David 类域风险界和未见场景分布匹配。只有检索页元数据，尚未取得/全文核验新论文；一次命令行下载因网络域名解析失败而退出，目标原件不存在，因此没有进入 raw/wiki/Zotero 流程。
- 无关事实排除：矩阵严格只使用 GeNIS 真实四时间间隔、八场景/活动及本地字段审计和通用方法全文；没有把任何无关数据集的成员数、每成员捕获数或困难域设定带入 GeNIS。最终必须按用户给定模式对整个 GeNIS 任务目录做零命中检查；通用风险界也必须改写并绑定轨 A/轨 B 的 GeNIS 合同。
- 精确阻塞：子代理证据卡尚未落盘/验收；两篇新检索结果没有全文，不能作为论断证据。它们不是实验启动的硬阻塞，恢复时不得先扩展它们。
- **唯一恢复动作：**重读本检查点与主矩阵，读取并验收子代理证据卡；直接补完第三、四节，冻结独立支持单元、固定告警预算尾部排序、簇级有限候选界、场景差异过大时保证失效和交叉拟合阈值的公式/假设/失败条件。
- 预计剩余：核心合同约 `25` 分钟，完整矩阵与本地检查约 `45–55` 分钟。
