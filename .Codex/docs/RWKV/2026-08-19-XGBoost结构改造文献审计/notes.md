# XGBoost 与相近树模型结构改造文献审计过程笔记

- **日期**：2026-08-19
- **代理映射**：`xgboost_tree_adaptation_literature_sol_max → gpt-5.6-sol → effort=max`
- **研究路线**：`RESEARCH_ROUTE=RWKV`
- **当前状态**：首批 15 篇候选全文已逐页核验；继续 T1／T2 直接同构窄查询与近期补漏。

## 一、既有证据的去重边界

### 1.1 已由 XGBoost–CPA–ELP 审计关闭的部分

- Lee 与 Stolfo（2000）：过去时间窗的同主机／同服务计数、比例、均值作为当前连接特征；因果跨流统计不是空白。
- Bilge 等（2012）：按服务器实体聚合 NetFlow 统计后输入随机森林；“实体聚合原始流＋树模型”不是空白。
- Hindy 等（2021）：把整束统计回填逐流行；证明跨流特征回填已有先例，也构成未来信息泄漏反例。
- Gehri 等（2023）：随机森林逐流分数按主机恶意流计数形成告警；树分数到实体后处理已有直接安全先例。
- Dijk 等（2026）：无向 2-IP、时间排序与最长 128 流构造有来源；同文 XGBoost 仍只用原始逐流特征。
- Gülçehre、Revaud 与 Gulrajani／Lopez-Paz：幂平均公式、可学习幂次与源域模型选择已占用；本轮不重做。

### 1.2 已由第四章双机制查重关闭的部分

- DTEP 宽泛部件已有：NIDES 长短期画像、王世谦等长短周期晚融合、Haiba 实体 GroupKFold 固定窗、Slips 主机时间窗证据、El-Hajj 多尺度滚动与 LOEO 嵌套选择、CBAM 主机短上下文。
- PBC 宽泛部件已有：BBSE／DFM 先验估计与失配边界、PseudoCal 与 IW-GAE 无标签校准、Haiba 目标良性缓冲区分位阈值、CBAM 每主机阈值、Choi 的独立先导冻结与反驳回退。
- 原有查重未命中 D3；尚未关闭的是树模型特定的固定二进尺度输入、源实体折外选尺度、树分数在目标先导段完成预算／先验校正并冻结回退的完整组合。

## 二、本轮优先文献家族

| 家族 | 预期作用 | 先验候选 |
| --- | --- | --- |
| 区间／多分辨率森林 | 树模型如何选择窗口、尺度和统计 | Time Series Forest、Canonical Interval Forest、DrCIF、随机化监督时间序列森林 |
| 多粒度扫描森林 | 多窗口序列切片如何直接送入森林 | gcForest／deep forest |
| 自动实体历史特征 | 关系实体与时间截止下的聚合特征 | Deep Feature Synthesis、关系树／统计特征学习 |
| 纵向／分组树模型 | 同一实体重复观测与随机效应 | MERF、LongBoost、GPBoost |
| 多示例树模型 | 实例到实体袋的直接树学习 | MIForests、MI-Boosting、树结构多示例方法 |
| 数据流与漂移树 | 窗口更新、漂移检测和模型替换 | Adaptive Random Forest、Adaptive XGBoost、Mondrian Forest |
| 树分数校准 | 逻辑校准、等渗回归、概率偏差 | Zadrozny–Elkan、Niculescu-Mizil–Caruana |
| 先验／标签漂移校正 | 冻结树分数的目标域先验修正 | Saerens 等、BBSE／DFM 已有证据的树分数实例化 |
| 预算约束树 | 固定代价、特征预算或误报约束 | Greedy Miser、纽曼—皮尔逊阈值与树分数后处理 |
| 网络多尺度统计 | 与固定二进历史最接近的领域特征器 | Kitsune／AfterImage、多半衰期统计＋树分类近邻 |

## 三、初始假设与待证边界

1. 固定多尺度统计作为树输入很可能已有大量先例；原创空间不能落在“多窗统计＋XGBoost”这一宽泛组合。
2. 二进窗只是工程离散化，除非与实体严格因果前缀、源实体折外尺度选择、长实体失败面和冻结跨年合同共同出现，否则不足以构成独立研究贡献。
3. 目标先导段对树分数做等渗／逻辑校准、分位阈值或先验修正均可能是标准后处理；PBC 的可保留空间只可能是实体预算、条件诊断、预注册回退和不相交后段的联合合同。
4. Adaptive Random Forest／Adaptive XGBoost 属于持续在线更新模型，若 DTEP–PBC 冻结骨干与后段，它们应作为强漂移基线或反例，而非直接机制来源。
5. 时间序列森林与多粒度扫描森林若直接处理原始序列，可能是比“固定统计＋XGBoost”更强的结构基线；是否能在统一字段、实体、历史和预算下复现仍需工程审计。

## 四、检索台账模板

每完成一组查询立即追加：

```text
查询编号：
日期：
数据库／站点：
查询式：
初始命中：
去重后候选：
新增 D2／D3：
纳入：
排除：
下一查询：
Zotero 状态：
```

## 五、逐篇全文模板

```text
题名／作者／年份：
DOI／arXiv／正式页：
本地原件或合法全文：
Zotero：
证据位置：
任务与样本／实体单元：
输入历史与时间因果：
窗口／尺度选择：
树模型角色：
实体聚合：
校准／漂移／预算：
支持点：
不能支持点：
T1／T2 同构等级：
强基线／基础部件／边界：
纳入／排除理由：
```

## 六、初始检查点

- **已完成**：规则恢复；既有两份文献审计全量阅读；T1／T2、D0—D3 与 E0—E3 冻结。
- **下一步**：本地 `raw/wiki` 与 Zotero 只读盘点；随后检索时间序列森林、多粒度扫描、Adaptive XGBoost、树分数校准和网络多尺度统计。
- **未关闭疑点**：是否已有固定二进窗口的网络实体 XGBoost；是否已有目标因果先导段对树分数完成预算／先验诊断回退并冻结评价。
- **无法取得原文**：暂无新增项；继承的 NIDES 与 DCS 阻塞只在确有必要时交叉引用，不重复登记为本轮新增。
- **写入状态**：本轮仅创建三份指定过程文档；尚未改 `raw/wiki/Zotero`。

## 七、本地与 Zotero 盘点

### 7.1 本地去重

- 以文件名和 wiki 正文精确检索 TSF／CIF／DrCIF、gcForest、Adaptive XGBoost、Adaptive Random Forest、Mondrian Forest、MIForests、Mixed-Effects Random Forest、GPBoost、经典树分数校准、Saerens 先验修正与 Deep Feature Synthesis，均未发现可确认的原件或规范笔记。
- `wiki/papers/datasets/data-protocol/2022-Arp-安全机器学习十大陷阱.md` 已有一项可复用边界：Kitsune Mirai 数据上，仅用 10 秒滑窗包频率的箱线图基线在低误报区间优于 Kitsune。它支持“简单固定窗必须列强基线”，不支持多尺度 XGBoost 或 DTEP 有效。

### 7.2 Zotero 只读状态

- Zotero Desktop `9.0.6`，本地 API 与连接器均返回 `200`；本轮未写入馆藏。
- 对 `Time Series Forest`、`Canonical Interval Forest`、`Deep Forest`、`Adaptive XGBoost`、`Adaptive Random Forest`、`Predicting Good Probabilities with Supervised Learning`、`Adjusting the Outputs of a Classifier to New a Priori Probabilities`、`MIForests` 的精确题名搜索均返回空列表。
- 空列表只表示本轮精确题名未命中，不能据此声称馆藏绝对不存在同题异名条目。

## 八、联网检索日志

### Q1：区间森林与多分辨率树

- **查询式**：`"A Time Series Forest for Classification and Feature Extraction" paper pdf`；`"The Canonical Interval Forest" paper`；`"Diverse Representation Canonical Interval Forest" paper`；`"A Randomized Supervised Time Series Forest" paper`。
- **正式候选**：
  - Deng 等 2013，TSF，DOI `10.1016/j.ins.2013.02.030`，arXiv `1302.2277`；随机区间上的均值、标准差、斜率进入树节点候选。
  - Middlehurst 等 2020，CIF，DOI `10.1109/BIGDATA50022.2020.9378424`，arXiv `2008.09172`；把 TSF 的三统计扩为 catch22 子集并支持多变量。
  - Middlehurst 等 2021，HIVE-COTE 2.0／DrCIF，DOI `10.1007/s10994-021-06057-9`，arXiv `2104.07551`；原始序列、一阶差分和频谱三种表示上随机抽区间和统计。
  - Cabello 等 2023，r-STSF，DOI `10.1007/s10618-023-00978-w`；监督区间提取与随机化森林。
- **初筛**：TSF、CIF、DrCIF 对 T1 均至少是 D2 候选，因为“多区间／多表示统计＋树”已同现；但它们以固定长度完整序列为样本，不按网络实体产生逐事件因果前缀，也不是 XGBoost。r-STSF 是否需要纳入取决于全文中尺度选择与因果边界。
- **新增 D2／D3**：待全文核验；当前不作强结论。

### Q2：多粒度扫描与在线漂移树

- **查询式**：`"Deep Forest: Towards An Alternative to Deep Neural Networks" official paper pdf`；`"gcForest" multi-grained scanning paper arxiv`；`"Adaptive Random Forests for Evolving Data Stream Classification" paper pdf`；`"Adaptive XGBoost for Evolving Data Streams" paper`。
- **正式候选**：
  - Zhou 与 Feng 2017，gcForest，IJCAI，DOI `10.24963/ijcai.2017/497`，arXiv `1702.08835`；多粒度扫描用多个滑窗把序列／图像局部块变成森林类向量，再进入级联森林。
  - Gomes 等 2017，Adaptive Random Forest，DOI `10.1007/s10994-017-5642-8`；每棵树配置漂移监测器，预警时训练后台树，漂移时替换。
  - Montiel 等 2020，Adaptive XGBoost，arXiv `2005.07353`；按小批持续新增 XGBoost 成员，固定最大集成大小，并比较替换／推入及显式漂移检测策略。
- **初筛**：gcForest 是 T1 的 D2 结构近邻，但窗口经完整样本扫描且默认多个尺度并行，不是实体前缀 XGBoost。ARF／AXGB 是标签可达且持续更新模型的漂移强基线，也是 PBC“冻结树模型、只改决策层”的 D0 边界。
- **2026 近期线索**：LAX-Reg（DOI `10.1155/int/1759600`）用动态滑窗和选择性增删树处理流回归，只作近期边界候选；任务是回归，且持续更新骨干。

### Q3：树分数校准、先验修正与实体袋学习

- **查询式**：`"Predicting Good Probabilities with Supervised Learning" pdf`；`"Transforming classifier scores into accurate multiclass probability estimates" pdf`；`"Adjusting the outputs of a classifier to new a priori probabilities" pdf`；`"MIForests" multiple-instance learning randomized trees paper pdf`；`"Gaussian Process Boosting" GPBoost JMLR paper`。
- **正式候选**：
  - Niculescu-Mizil 与 Caruana 2005，DOI `10.1145/1102351.1102430`；直接比较决策树、袋装树、提升树，给出逻辑校准与等渗回归的树分数校准依据。
  - Zadrozny 与 Elkan 2002，DOI `10.1145/775047.775151`；以保序等渗回归把任意排序分数转成概率，并给多类组合。
  - Saerens 等 2002，*Neural Computation* 14(1):21—41；用期望最大化从无标签目标输出估计新先验并校正后验，另讨论先验变化检验。
  - Leistner 等 2010，MIForests，ECCV，DOI `10.1007/978-3-642-15567-3_3`；把袋内实例标签作为隐变量，迭代训练随机森林，并给在线扩展。
  - Sigrist 2022，GPBoost，JMLR 23(232):1—46；把树提升与分组随机效应／高斯过程联合，放松独立观测假设。
- **初筛**：树分数校准与先验修正均是 PBC 必须面对的 D1 强基线；MIForests 证明“实体袋监督直接改造随机森林”已有；GPBoost 证明“树提升＋实体相关结构”已有，但都不覆盖目标时间先导、实体误报预算和回退。

### Q4：网络多尺度统计与 XGBoost 补漏

- **查询式**：`Kitsune AfterImage damped incremental statistics multiple time windows paper PDF`；`"AfterImage" network traffic statistics half-life paper`；`"Kitsune: An Ensemble of Autoencoders" USENIX PDF`；`XGBoost AfterImage features network intrusion`；另对 XGBoost、滑窗、多时间窗与网络入侵作官方论文页定向查询。
- **正式候选**：Mirsky 等 2018，Kitsune，NDSS，DOI `10.14722/ndss.2018.23204`，arXiv `1802.09089`；其特征提取器按网络通道在线维护大量统计，是否使用多个衰减尺度须回原文核验。
- **排除／边界线索**：2025 年 VAE–GRU–XGBoost 只是神经时序编码器后接 XGBoost，模型与数据协议需进一步审计；大量普通 XGBoost 入侵检测工作只有静态表格特征，不符合纳入标准。
- **当前未命中**：首轮尚未找到同时满足固定二进多尺度、网络实体严格前缀和 XGBoost 输入的论文；这不是停止结论，必须继续窄查询。

## 九、首轮联网检查点

- **已完成查询组**：4 组；候选原论文 15 篇，尚未全部全文核验。
- **当前最强方向**：TSF／CIF／DrCIF 占用“多区间统计＋森林”；gcForest 占用“多窗口扫描＋森林”；AXGB／ARF 占用“漂移时持续更新树”；经典校准与 Saerens 占用“冻结分数后处理”。
- **下一篇全文**：TSF、DrCIF、gcForest、AXGB、Niculescu-Mizil–Caruana、Saerens、MIForests、GPBoost；Kitsune 仅核对多衰减尺度。
- **未关闭疑点**：T1 是否有网络／实体 XGBoost 直接近邻；T2 是否有树分数＋目标先导预算／先验诊断回退的完整链；区间森林能否在统一实体历史合同下成为可执行强基线。
- **人工补件**：暂无新增；所有首批核心候选已有公开全文入口。

## 十、全文核验检查点：区间、多粒度与漂移树

### 10.1 Deng 等（2013），Time Series Forest

- **题录／全文**：Deng, Runger, Tuv, Vladimir，*A Time Series Forest for Classification and Feature Extraction*，*Information Sciences* 239:142—153，DOI `10.1016/j.ins.2013.02.030`；[arXiv 全文](https://arxiv.org/abs/1302.2277)，工作副本 `/tmp/manifold-pdf-extract/xgb-tree-audit/2013-TSF.pdf`，E2。
- **页码与公式**：物理 p.5 的式（1）—（3）定义区间均值、标准差和最小二乘斜率；同页明确写明 Rodríguez 等只考虑长度为 2 的幂的区间，把候选空间从 `O(M²)` 降为 `O(M log M)`。物理 pp.13—14 的表 2 明确将 `interRF` 定义为“500 棵随机森林作用于长度为 2 的幂的区间特征”。
- **支持点**：固定二进区间统计与随机森林已在同一正式工作中出现，且有可直接复现的比较项；TSF 自身则在每个树节点随机采样 `O(M)` 个区间候选。
- **不能支持点**：每个样本是等长完整时间序列，不是同一网络实体的逐事件严格历史前缀；分类器不是 XGBoost；没有源实体折外选尺度、跨域冻结或决策回退。
- **裁定**：T1 `D2`，T2 `D0`；`interRF` 是必须纳入的结构强基线。Zotero 未入库。

### 10.2 Middlehurst 等（2020），Canonical Interval Forest

- **题录／全文**：*The Canonical Interval Forest (CIF) Classifier for Time Series Classification*，IEEE Big Data 2020，DOI `10.1109/BIGDATA50022.2020.9378424`；[arXiv 全文](https://arxiv.org/abs/2008.09172)，工作副本 `2020-CIF.pdf`，E2。
- **页码与算法**：物理 pp.1—2 说明 TSF 的三种区间统计并引入 catch22；物理 p.3 的算法 1 对每棵树随机抽取 `k` 个区间，并从 25 个候选特征中随机选 `a=8` 个，默认 `r=500` 棵树、`k≈√(d·m)`。
- **支持点**：随机窗、统计特征子集和多变量维度选择可直接借鉴为“树前窗口／尺度选择”基线。
- **不能支持点**：区间依赖完整样本的相位位置，不是实体在线历史；无固定二进尺度、XGBoost、域冻结或预算校正。
- **裁定**：T1 `D2`，T2 `D0`；在统一历史输入与计算预算可实现时属于强结构基线。Zotero 未入库。

### 10.3 Middlehurst 等（2021），DrCIF／HIVE-COTE 2.0

- **题录／全文**：*HIVE-COTE 2.0: a new meta ensemble for time series classification*，*Machine Learning*，DOI `10.1007/s10994-021-06057-9`；[arXiv 全文](https://arxiv.org/abs/2104.07551)，工作副本 `2021-HC2-DrCIF.pdf`，E2。
- **页码与算法**：印刷 pp.11—13 的第 3.2 节与算法 3：DrCIF 在原始序列、一阶差分和周期图三种表示上各取随机区间，以 7 个基本统计加 catch22 构成 29 个候选特征池；每棵树选 `a=10` 个特征，默认 `r=500`。
- **支持点**：多表示、多区间、多统计与森林在一个模型中联合；比只用均值／方差／斜率的 TSF 更强。
- **不能支持点**：完整定长序列分类；不保证实体因果前缀，不是 XGBoost，不含目标先导适应。
- **裁定**：T1 `D2`，T2 `D0`；若统一数据合同和预算可行，属于强结构基线。Zotero 未入库。

### 10.4 Cabello 等（2023），r-STSF

- **题录／全文**：*Fast, Accurate and Interpretable Time Series Classification Through Randomization*，*Data Mining and Knowledge Discovery*，DOI `10.1007/s10618-023-00978-w`；[arXiv 全文](https://arxiv.org/abs/2105.14876)，工作副本 `2023-rSTSF.pdf`，E2。
- **页码与算法**：物理 pp.13—17 的第 4 节及算法 1—2：在原始、周期图、导数和自回归四种表示上，用九种聚合函数；随机切点递归搜索子区间，以 Fisher 分数监督选择区间特征，再训练随机化树集成。
- **支持点**：监督式窗口选择与多表示聚合已经是成熟的树模型时间序列结构，不可把“自动选窗＋统计＋树”作为新颖表述。
- **不能支持点**：用训练标签搜索完整序列区间；不是网络实体严格历史、固定二进尺度或 XGBoost，也不涉及跨域冻结。
- **裁定**：T1 `D2`，T2 `D0`；强结构基线，尤其用于检验固定二进尺度是否只是较弱离散化。Zotero 未入库。

### 10.5 Zhou 与 Feng（2017），gcForest

- **题录／全文**：*Deep Forest: Towards an Alternative to Deep Neural Networks*，IJCAI 2017，DOI `10.24963/ijcai.2017/497`；[会议正式页](https://www.ijcai.org/proceedings/2017/497)，工作副本 `2017-gcForest.pdf`，E3。
- **页码与算法**：会议印刷 pp.3554—3555／物理 pp.2—3：多粒度扫描把多个滑窗中的原始特征送入随机森林和完全随机森林，每个窗口输出类别向量；示例窗长 100／200／300，默认尺度为特征维数的 `⌊d/16⌋、⌊d/8⌋、⌊d/4⌋`；级联深度按验证性能停止。
- **支持点**：多窗序列片段到森林类别向量的结构已存在。
- **不能支持点**：窗口扫描整个样本，不是实体时间前缀；不是 XGBoost；验证停止也不是源实体折外尺度合同。
- **裁定**：T1 `D2`，T2 `D0`；计算预算允许时为次强结构基线。Zotero 未入库。

### 10.6 Montiel 等（2020），Adaptive XGBoost

- **题录／全文**：*Adaptive XGBoost for Evolving Data Streams*，[arXiv `2005.07353`](https://arxiv.org/abs/2005.07353)，工作副本 `2020-AXGB.pdf`，E2。
- **页码与公式**：物理 pp.2—3：非重叠小批缓冲区训练新的弱树成员；集成满时采用推入或替换策略。式（5）令训练窗大小按 `W(i)=min(W_min·2^i,W_max)` 倍增；ADWIN 监测分类准确率并在漂移时重置窗口及替换成员。
- **支持点**：XGBoost 在数据流中可通过动态训练批窗与成员替换适应漂移；“二进增长窗口”不是特征历史尺度。
- **不能支持点**：需要持续标签和模型更新；与冻结骨干、无标签先导、冻结后段评价冲突。
- **裁定**：T1 `D1`，T2 `D0`；只可作为标签可达的漂移上界／独立信息预算基线。Zotero 未入库。

### 10.7 Gomes 等（2017），Adaptive Random Forest

- **题录／全文**：*Adaptive Random Forests for Evolving Data Stream Classification*，*Machine Learning*，DOI `10.1007/s10994-017-5642-8`；[DOI 正式页](https://doi.org/10.1007/s10994-017-5642-8)，作者稿工作副本 `2017-ARF.pdf`，E3。
- **页码与算法**：物理 pp.2—3 说明每棵树配置预警／漂移监测器；物理 pp.7—8 的算法 1—2 采用测试后训练、Poisson(6) 在线袋装，预警时生长后台树，确认漂移时替换主树，并按在线准确率加权投票。
- **支持点**：标签漂移检测、后台树和模型替换是成熟的持续在线树适应机制。
- **不能支持点**：每个实例标签在线可用且骨干持续改变，不满足 PBC 的信息权限与冻结合同；没有历史尺度特征。
- **裁定**：T1 `D0`，T2 `D0`；仅在单列“目标标签可用”层级中作为漂移强基线。Zotero 未入库。

## 十一、全文核验检查点：校准、先验、实体与预算

### 11.1 Niculescu-Mizil 与 Caruana（2005），树分数校准

- **题录／全文**：*Predicting Good Probabilities with Supervised Learning*，ICML 2005，DOI `10.1145/1102351.1102430`；作者公开全文工作副本 `2005-Calibration.pdf`，E3。
- **页码与公式**：物理 p.2 的式（1）—（2）给逻辑校准的 S 形映射与似然目标，式（6）给等渗回归；两者均要求与训练数据独立的带标签校准集。物理 pp.3—8 表明提升树分数常呈 S 形失真；小校准集下逻辑校准更稳，数据足够时等渗回归追平或超过。
- **支持点**：XGBoost／提升树必须与标准逻辑校准、等渗回归比较，且校准数据应隔离。
- **不能支持点**：不能支撑无标签目标校准、先验估计、实体预算或诊断回退。
- **裁定**：T1 `D0`，T2 `D1`；强概率校准基线。Zotero 未入库。

### 11.2 Zadrozny 与 Elkan（2002），等渗回归概率映射

- **题录／全文**：*Transforming Classifier Scores into Accurate Multiclass Probability Estimates*，KDD 2002，DOI `10.1145/775047.775151`；[DOI 正式页](https://doi.org/10.1145/775047.775151)，工作副本 `2002-ZadroznyElkan.pdf`，E3。
- **页码与算法**：物理 pp.3—4：对排序分数以 PAV 算法学习单调分段常数映射；模型若在训练集过拟合，映射应在独立带标签样本上训练；无排序信息时只能退化到基率。
- **支持点**：任意树排序分数到概率的标准非参数基线。
- **不能支持点**：不处理无标签目标先验、因果先导、预算和条件回退。
- **裁定**：T1 `D0`，T2 `D1`；强概率校准基线。Zotero 未入库。

### 11.3 Saerens、Latinne 与 Decaestecker（2002），无标签新先验修正

- **题录／全文**：*Adjusting the Outputs of a Classifier to New a Priori Probabilities: A Simple Procedure*，*Neural Computation* 14(1):21—41，DOI `10.1162/089976602753284446`；[DOI 正式页](https://doi.org/10.1162/089976602753284446)，作者公开全文工作副本 `2002-SaerensPriorShift.pdf`，E3。
- **页码与公式**：物理 p.5 的式（4）以新旧先验比重加权冻结分类器后验并归一化；物理 pp.7—8 的式（9）从训练先验初始化，在无标签新数据上以 EM 交替估计后验与新先验；物理 pp.9—10 的式（12）—（13）定义似然比检验。物理 pp.18—19 明确指出，仅在先验变化显著时才应执行重调，否则可能降低准确率。
- **支持点**：冻结模型、无标签目标样本、先验校正、条件诊断和“不修正”回退已在一个经典方法中同现；该方法与分类器家族无关，可直接实例化到已校准的树分数。
- **不能支持点**：假设类条件分布不变且模型后验足够准确；没有目标时间因果先导段、实体告警预算、参数冻结后在不相交后段评价，也没有树模型专属设计。
- **裁定**：T1 `D0`，T2 `D2`，是本轮最强 PBC 直接近邻和必须实现的先验校正强基线。Zotero 未入库。

### 11.4 Leistner 等（2010），MIForests

- **题录／全文**：*MIForests: Multiple-Instance Learning with Randomized Trees*，ECCV 2010，DOI `10.1007/978-3-642-15567-3_3`；[DOI 正式页](https://doi.org/10.1007/978-3-642-15567-3_3)，作者稿工作副本 `2010-MIForests.pdf`，E3。
- **页码与算法**：物理 pp.4—5 将袋内实例标签视为隐变量，以确定性退火迭代训练随机森林；式（1）—（2）规定正袋至少一个正实例，袋预测可取实例后验最大值。物理 p.8 的算法 1 反复重估实例标签；p.9 给顺序袋的在线扩展。
- **支持点**：实体／袋标签可直接进入随机森林训练，而非只能先手工聚合。
- **不能支持点**：袋关系不是时间历史；“正袋至少一正例”未必符合主机／实体攻击标签；无多尺度、XGBoost 或目标先导校正。
- **裁定**：T1 `D1`，T2 `D0`；仅在实体标签语义满足多示例假设时作为条件性基线。Zotero 未入库。

### 11.5 Sigrist（2022），GPBoost

- **题录／全文**：*Gaussian Process Boosting*，JMLR 23(232):1—46；[JMLR 正式全文页](https://jmlr.org/papers/v23/20-322.html)，工作副本 `2022-GPBoost.pdf`，E3。
- **页码与公式**：物理 pp.1—4；式（1）以 `y=F(X)+Zb+ε` 联合树提升和分组随机效应／高斯过程，表 1 对比混合效应树、MERF 与相关方法。
- **支持点**：树提升显式建模同一组／实体相关性已有成熟统计路径。
- **不能支持点**：主要目标是回归／概率混合效应，不把严格历史、多窗统计送入 XGBoost，也不做目标先导预算校正。
- **裁定**：T1 `D1`，T2 `D0`；相关结构的基础部件，不是当前任务的直接强基线。Zotero 未入库。

### 11.6 Mirsky 等（2018），Kitsune／AfterImage

- **题录／全文**：*Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection*，NDSS 2018，DOI `10.14722/ndss.2018.23204`；[NDSS 正式页](https://www.ndss-symposium.org/ndss-paper/kitsune-an-ensemble-of-autoencoders-for-online-network-intrusion-detection/)，工作副本 `2018-Kitsune.pdf`，E3。
- **页码与公式**：物理 pp.5—7。式（6）定义衰减 `d_λ(t)=2^{-λt}`；增量统计按来源 MAC-IP、来源 IP、双向 IP 通道和套接字聚合。表 2 明确每个时间窗 23 个统计，并在 100 ms、500 ms、1.5 s、10 s、1 min 五个尺度重复，合计 115 维；每个新包在线更新，复杂度 `O(1)`。
- **支持点**：网络实体／通道的严格在线多尺度统计不是空白；均值、方差、计数、抖动、协方差和相关性等可作为树前特征器。
- **不能支持点**：尺度是指数衰减而非固定二进窗；下游为自动编码器集成，不是 XGBoost；没有源实体折外尺度选择或目标决策校正。
- **裁定**：T1 `D2`，T2 `D0`；`AfterImage 特征＋XGBoost` 应作为明确标注的“组合强基线”，不能误称为该论文原方法。Zotero 未入库。

### 11.7 Xu 等（2012），Greedy Miser

- **题录／全文**：*Greedy Miser: Learning under Test-time Budgets*，ICML 2012；[会议公开全文](https://icml.cc/2012/papers/661.pdf)，工作副本 `2012-GreedyMiser.pdf`，E3。
- **页码与公式**：物理 pp.1—3；式（3）把树评估成本与首次特征获取成本纳入测试代价，式（4）在预算 `B` 下优化损失，式（5）把特征获取成本写入树分裂目标。
- **支持点**：若不同历史尺度具有明确提取成本，可借鉴为成本感知的尺度／特征选择。
- **不能支持点**：预算是推理计算与特征成本，不是误报率、实体告警量或目标先导分位预算；无漂移回退。
- **裁定**：T1 `D1`，T2 `D0`；只属成本约束基础部件。Zotero 未入库。

### 11.8 Chen 等（2023），主机特征展平＋XGBoost

- **题录／全文**：*A Host-Based Network Intrusion Detection System with Feature Flattening and a Two-stage Classifier*，[arXiv `2306.09451`](https://arxiv.org/abs/2306.09451)，工作副本 `2023-HostFlatteningXGB.pdf`，E2。
- **页码与算法**：物理 pp.6—11：将 BERT 得到的主机事件／消息矩阵展平并与流特征拼接，以抽样和主成分分析减维；用 XGBoost 比较矩阵尺寸并选择 `15×50`，再以两阶段 XGBoost 完成二分类和多分类。
- **支持点**：主机侧表示与流特征拼接后进入 XGBoost 已有实例。
- **不能支持点**：矩阵是静态主机日志表示，不是同一实体历史统计、固定多尺度或严格因果先导；未做预算／先验校正。
- **裁定**：T1 `D0`，T2 `D0`；只作边界证据，不列核心强基线。Zotero 未入库。

## 十二、15 篇全文组恢复检查点

- **完成量**：15／15 篇候选全文已取得、转文本并逐页定位；按本任务证据定义，E3 为 9 篇，E2 为 6 篇。E2 均为可核验预印本，未与 E3 混写。
- **T1 最高等级**：`D2`。`interRF` 占用固定二进区间统计＋随机森林；Kitsune 占用网络实体／通道＋因果在线五尺度统计；r-STSF／CIF／DrCIF 占用监督或随机区间、统计与森林。尚无一篇同时满足实体严格前缀、固定二进尺度、XGBoost、源实体折外选择与冻结。
- **T2 最高等级**：`D2`。Saerens 等占用冻结分类器、无标签新数据、先验校正、显著性诊断与不校正回退；尚缺目标因果先导、实体告警预算、后段隔离和冻结评价。
- **人工补件**：无；未遇到必须依赖付费全文才能裁决的候选。
- **持久化边界**：本任务不拥有 `raw/`、`wiki/` 或 Zotero 写权限，故仅记录公开全文入口、工作副本和“未入库”状态；不把临时工作副本冒充仓库原件。
- **下一查询**：T1 直接检索 `powers of two／dyadic windows＋XGBoost＋entity／network history` 与 `AfterImage＋XGBoost`；T2 直接检索 `tree scores／XGBoost＋unlabeled target prior correction／pilot period／false-positive budget／fallback`，并单独覆盖 2025—2026。
