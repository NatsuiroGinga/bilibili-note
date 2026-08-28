# XGBoost 与相近树模型结构改造文献审计过程笔记

- **日期**：2026-08-19
- **代理映射**：`xgboost_tree_adaptation_literature_sol_max → gpt-5.6-sol → effort=max`
- **研究路线**：`RESEARCH_ROUTE=RWKV`
- **当前状态**：累计 21 篇候选全文已逐页或逐节核验，完成 17 组查询；T1、T2 均满足停止条件，最高均为 `D2`，未发现 `D3`。

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

## 十三、直接同构窄查询日志

### Q5：T1 第一轮——二进窗与网络实体 XGBoost

- **查询式**：`"powers of two" "XGBoost" time series classification`；`"dyadic windows" XGBoost classification`；`"multi-scale" XGBoost network intrusion host history`；`"AfterImage" XGBoost network intrusion`。
- **结果**：没有新增 T1 `D2／D3`；命中多为深度时序模型、普通静态 XGBoost 或图模型。Kitsune／AfterImage 仍是网络实体多尺度特征器，不是原论文中的 XGBoost 方法。
- **Zotero 状态**：只读去重，无写入。

### Q6：T1 第二轮——实体尾随窗与多分辨率聚合

- **查询式**：`("XGBoost" OR "gradient boosting") "multi-window" temporal features entity`；`XGBoost "sliding windows" "network intrusion detection" host feature`；`XGBoost "multiple time windows" network traffic classification`；`XGBoost "multi-resolution" temporal aggregation entity history`。
- **新增 `D2`**：Pinchuk（2026）。该文明确使用多个实体键、无前视尾随窗口聚合和 XGBoost；因此重置 T1 的连续无新增计数。
- **排除**：普通滑窗切分、神经网络编码器后接 XGBoost、没有实体截止时间的静态统计。

### Q7：T1 第三轮——无前视实体历史

- **查询式**：`"no-lookahead" XGBoost "entity history" windows`；`"entity history" XGBoost multi-scale windows`；`"trailing windows" XGBoost device_id history`；`dyadic temporal features "gradient boosted trees"`。
- **结果**：仅重复命中 Pinchuk（2026），没有新增 T1 `D2／D3`；这是其后的第一轮无新增。

### Q8：T1 第四轮——固定幂次尺度

- **查询式**：`"1, 2, 4, 8, 16" XGBoost window history`；`"2, 4, 8, 16" XGBoost temporal aggregation`；`"time aggregation" XGBoost "network intrusion"`；`2025 2026 XGBoost host history "strictly before"`。
- **新增 `D2`**：TreeText-CTS（2026）。该文以患者为实体，在 `{1,2,4,8,16,32,48}` 小时尺度生成统计并通过冻结 XGBoost；因此再次重置 T1 的连续无新增计数。
- **边界线索**：Cotroneo 等网络检测延迟研究比较 5 秒至 30 分钟单一聚合间隔并分别训练 XGBoost／Extra Trees；不是并列多尺度实体前缀，暂不升级为直接近邻。

### Q9：T2 第一轮——树分数、标签漂移与目标约束

- **查询式**：`XGBoost "label shift" EM calibration target`；`random forest "prior probability shift" unlabeled target calibration`；`tree classifier scores target pilot prior correction fallback`；`XGBoost threshold calibration "false positive budget" target`。
- **新增 `D2`**：TAP-GPPS（Asiaee 与 Aryan，2026）。它在校准源模型上用无标签目标数据估计组条件先验、修正后验并选择满足目标人口统计平等约束的分组阈值；实验明确包含 XGBoost。
- **不能支持**：没有时间因果先导、实体告警预算或自动失配回退。

### Q10：T2 第二轮——先导／校准期与固定假阳率

- **查询式**：`"pilot period" XGBoost threshold calibration`；`"calibration period" random forest "false positive rate" threshold`；`XGBoost "held-out calibration" "false positive rate" threshold`；`"unlabeled target" XGBoost "prior shift"`。
- **新增 `D2`**：Hung（2026）。正式全文明确用验证集选择固定假阳率阈值，再在隔离的未见攻击族测试集评价 XGBoost／随机森林；因此重置 T2 的连续无新增计数。
- **边界线索**：OULAD 早期预警工作用容量 `Top-x%` 固定工作量，但最终模型为直方图梯度提升且无目标适应；TAN-IDS 用 5% 带标签目标样本微调 XGBoost，但随机拆分且改变模型。二者不升级为 T2 直接近邻。

## 十四、增量全文核验：直接近邻

### 14.1 Pinchuk（2026），实体时间聚合＋XGBoost

- **题录／全文**：Mykola Pinchuk，*Time Aggregation Features for XGBoost Models*，[arXiv `2601.10019`](https://arxiv.org/abs/2601.10019)，v1，2026-01-15；工作副本 `/tmp/manifold-pdf-extract/xgb-tree-audit/2026-TimeAggregationXGB.pdf`，17 页，E2。
- **页码与公式**：物理 p.2 规定滚动尾部训练／验证／测试和无前视约束，小时 `H` 的特征只用 `<H` 的数据；物理 p.3 以 `device_ip`、`device_id`、`app_id`、`site_id` 为实体，按实体／窗口生成 `log(1+impressions)` 与平滑点击率 `(C+α)/(I+α+β)`，其中 `α=1,β=10`。物理 p.4 表 2 给 `(1,6,24)`、`(1,3,6,12,24)`、`(1,6,24,48,168)` 和 `(1,2,4,8,16,24,48,96,168)` 小时窗，表 3 比较尾随、隔一小时、桶化、日历和事件计数窗；物理 p.12 重列聚合公式。
- **支持点**：实体时间截止、多组固定尺度统计和单一 XGBoost 已在同一方法中出现，是 T1 最直接的表格树近邻之一。
- **不能支持点**：点击率特征依赖延迟标签；物理 p.11 说明同一折中验证／测试时点可使用更早小时的点击标签。最大窗口组不是纯二进序列；尺度组由同一数据集两折结果比较，不是源实体折外选择后跨域冻结；任务不是网络安全。
- **裁定**：T1 `D2`，T2 `D0`。只用计数的无前视多窗 XGBoost 属同信息强基线；点击率版本必须单列为“延迟标签可用”层级。Zotero 未入库。

### 14.2 Lee 等（2026），TreeText-CTS

- **题录／全文**：Kwanhyung Lee 等，*TreeText-CTS: Compact, Source-Traceable Tree-Path Evidence for Irregular Clinical Time-Series Prediction*，[arXiv `2605.20292`](https://arxiv.org/abs/2605.20292)，v1，2026-05-19；工作副本 `/tmp/manifold-pdf-extract/xgb-tree-audit/2026-TreeTextCTS-v1.pdf`，27 页，E2。
- **页码与公式**：物理 pp.3—4 以患者为实体，在预测时点 `t` 的 `[t-W,t]` 窗内计算最近值、均值、标准差、最小值、最大值、计数、净变化、距最近观测时间和缺失率；每个 `W` 单独训练 XGBoost，式（2）的叶分数只由训练集估计。物理 p.5 指定 `W={1,2,4,8,16,32,48}` 小时，并把树清单、谓词与缓存对验证／测试冻结；式（6）说明 XGBoost 与缓存固定，选择器和语言模型继续学习。物理 p.7 表 3 给多窗口 XGBoost 均值／最大值控制项；附录物理 p.12 表 A2／A4 给任务观察期与患者级拆分。
- **支持点**：患者实体、多尺度统计、仅训练集拟合并冻结的 XGBoost 和验证／测试冻结清单同现；固定幂次尺度与树模型不能再单独主张新颖。
- **不能支持点**：每个窗口是独立 XGBoost，最终预测器为证据选择器与语言模型，不是把所有尺度统计拼接给一个 XGBoost；保留全部尺度，未做源实体折外尺度子集选择；临床任务而非网络逐流。
- **裁定**：T1 `D2`，T2 `D0`；其多窗口 XGBoost 均值／最大值是结构强基线，完整语言模型组件不属于同预算树基线。Zotero 未入库。

### 14.3 Asiaee 与 Aryan（2026），TAP-GPPS

- **题录／全文**：Amir Asiaee 与 Kaveh Aryan，*Fairness Under Group-Conditional Prior Probability Shift: Invariance, Drift, and Target-Aware Post-Processing*，[arXiv `2602.05144`](https://arxiv.org/abs/2602.05144)，v1，2026-02-05；工作副本 `/tmp/manifold-pdf-extract/xgb-tree-audit/2026-TAP-GPPS.pdf`，15 页，E2。
- **页码与公式**：物理 p.3 定义组条件先验漂移 `P_t(X|Y,A)=P_s(X|Y,A)`；物理 pp.5—6 的式（20）—（21）用组内新旧先验比校正后验，第 5.2 节用 EM 或 BBSE 从无标签目标估计组先验，第 5.3 节按目标接受率／人口统计平等约束选择组阈值。物理 p.7 算法 1 串联源模型校准、目标先验估计、后验修正、二分阈值和约束风险选择；实验包括逻辑回归、XGBoost、MLP，并把源模型、无修正阈值和带标签目标 oracle 分开。物理 p.8 的局限明确承认保证依赖 GPPS 与敏感属性。
- **支持点**：校准源树、无标签目标先验、目标约束阈值和隔离测试在同一框架中出现；树特定的无标签先验校正与目标阈值约束不是空白。
- **不能支持点**：预算是群体接受率／公平约束，不是网络实体告警或假阳率预算；无因果时间先导、失配诊断与自动回退，且目标漂移为受控构造。
- **裁定**：T1 `D0`，T2 `D2`；已校准 XGBoost＋TAP-GPPS EM／BBSE 与无修正阈值是强基线，敏感属性不可用时只作条件性基线。Zotero 未入库。

### 14.4 Hung（2026），IoT 树分数固定假阳率阈值

- **题录／全文**：Ruei-Jan Hung，*An Explainable XGBoost-Based Framework for IoT Attack Detection with Unseen Attack Family Evaluation*，*Sensors* 26(10):3005，DOI [`10.3390/s26103005`](https://doi.org/10.3390/s26103005)，PMC `PMC13210460`；[PMC 正式全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC13210460/)，E3。工作副本为 `/tmp/manifold-pdf-extract/xgb-tree-audit/2026-Sensors-IoT-XGB.xml`；正式 JATS 不提供连续物理页码，故以章节锚定。
- **章节与协议**：第 3.4 节把每轮 200 万训练预算拆为 170 万拟合、30 万验证，验证集用于阈值校准，并审计拟合／验证／测试零重叠；第 3.6 节以验证宏平均 F1、MCC 和近似 `FAR=0.01` 共同选择 XGBoost 配置，明确不使用最终未见攻击族测试标签；第 4.4 节在每轮验证集选择接近目标假阳率的阈值，再用于隔离的未见攻击族测试，目标覆盖 `0.001—0.05`；第 4.5 节另以验证集假阳性／假阴性代价选择阈值。
- **支持点**：XGBoost／随机森林分数、固定假阳率预算、独立验证阈值和隔离测试已在网络安全正式全文中同现，是 PBC 的直接决策层强基线。
- **不能支持点**：验证集是同一基准内随机划分，不是部署目标域的因果时间先导；未估目标先验，没有条件失配诊断或源阈值回退；第 5 节明确实部署仍需持续校准监测。
- **裁定**：T1 `D0`，T2 `D2`；验证固定假阳率 XGBoost／随机森林是强预算基线，但不能据此声称目标先导适应或真实部署假阳率保证。Zotero 未入库。

## 十五、19 篇全文组恢复检查点

- **完成量**：累计 19 篇全文；E3 为 10 篇，E2 为 9 篇。四篇新增文献的题名、作者、版本／DOI 与全文位置均已由 arXiv、PMC 或出版社元数据核验。
- **T1 最高等级**：`D2`，无 `D3`。Pinchuk 最接近“实体历史多窗统计＋单一 XGBoost”，TreeText-CTS 最接近“固定幂次尺度＋训练集冻结 XGBoost”；尚缺网络逐流严格前缀、源实体折外尺度选择／冻结和同一最终树骨干的完整同现。
- **T2 最高等级**：`D2`，无 `D3`。TAP-GPPS 占用无标签目标先验＋目标约束阈值，Hung 占用树分数＋固定假阳率验证阈值＋隔离测试；尚缺目标因果先导、实体工作量预算、失配诊断／预注册回退和冻结后段的联合合同。
- **人工补件**：无。MDPI 页面限流与 PMC PDF 下载挑战已由 Europe PMC／PMC 正式全文 XML 解锁，不影响全文级裁决。
- **下一查询**：以 TreeText-CTS 与 Hung 为最新 `D2` 起点，T1、T2 各执行两轮新的直接短语与同义词查询；若连续两轮无新增 `D2／D3`，即满足扩展停止条件。

## 十六、停止条件窄查询与新增全文

### Q11：T1 第五轮——冻结多尺度窗口 XGBoost

- **查询式**：`"frozen XGBoost" "multi-scale" window summaries entity`；`"per-window XGBoost" multiscale time series`；`"powers-of-two windows" XGBoost patient entity`；`"fixed multi-resolution" XGBoost causal history`。
- **结果**：只重复命中 TreeText-CTS；另有时序预测、混合深度模型和单窗工作，均未新增 T1 `D2／D3`。这是 TreeText-CTS 后第一轮无新增。

### Q12：T1 第六轮——网络实体严格因果幂次窗

- **查询式**：`"1 2 4 8 16 32" XGBoost network intrusion`；`dyadic XGBoost host profile network security`；`"strictly causal" multiwindow XGBoost entity history`；`site:arxiv.org XGBoost multiscale entity history 2025 2026`。
- **结果**：只重复命中 Pinchuk、主机展平 XGBoost 和 VAE–GRU–XGBoost 等既有／边界项；没有新增 T1 `D2／D3`。这是连续第二轮无新增，T1 检索满足停止条件。

### Q13：T2 第三轮——固定假阳率、标签漂移与因果校准窗

- **查询式**：`"validation-based threshold calibration" XGBoost "fixed-FAR" held-out test`；`"target pilot" XGBoost "false alarm rate" fallback`；`"source-only" XGBoost EM BBSE threshold label shift`；`"causal calibration window" tree classifier unlabeled target`。
- **结果**：重复命中 Hung 与 TAP-GPPS；未新增 T2 `D2／D3`。这是 Hung 后第一轮无新增。

### Q14：T2 第四轮——先导前缀、部署校准与源阈值回退

- **查询式**：`"pilot prefix" classifier prior correction freeze`；`"deployment calibration window" XGBoost alert budget`；`"fallback to source threshold" XGBoost shift`；`"time-disjoint" XGBoost threshold calibration`。
- **新增 `D2`**：Anctil、Hauguel 与 Noel（2026）。其批次隔离校准协议对 XGBoost 原始分数拟合等渗回归，在校准批次选固定特异度阈值，再原样应用于未见测试批次。
- **不能支持**：批次随机留出而非目标时间先导；校准需要癌症／对照标签；无目标先验估计、失配诊断或源阈值回退。因此只刷新同类 D2，不触及 D3。

### 16.1 Anctil、Hauguel 与 Noel（2026），批次隔离树分数校准

- **题录／全文**：Nicolas Anctil、Pierrick Hauguel 与 Louis-Philippe Noel，*Metabolomic Profiling of Dried Blood Spots for Breast Cancer Detection: A Multi-Classifier Validation Study in 2,734 Participants*，medRxiv，DOI [`10.64898/2026.04.24.26351695`](https://doi.org/10.64898/2026.04.24.26351695)，v1，2026-04-27；工作副本 `/tmp/manifold-pdf-extract/xgb-tree-audit/2026-Metabolomic-XGB-Calibration.pdf`，26 页，E2。
- **页码与协议**：物理 pp.8—9 的第 3.7—3.8 节给 22 棵、深度 2 的正则化 XGBoost，并规定每次把 20% 分析批次留作测试，再从其余训练批次拿 30% 作同时与拟合／测试批次隔离的校准分区；在校准分数上拟合等渗回归并选择目标特异度阈值。物理 p.14 第 4.5 节把阈值原样迁移到未见测试批次，表 4 同列 XGBoost、逻辑回归与固定 95% 特异度下的灵敏度；同时把测试集选阈值的 oracle 明确标成乐观上界。
- **支持点**：XGBoost 原始分数、组／批次隔离的带标签等渗校准、固定特异度预算和未见组测试在同一预印本中出现；为 PBC 提供比普通随机验证更严格的树分数预算基线。
- **不能支持点**：校准批次来自训练候选池且随机留出，不是部署目标域的时间因果先导；依赖校准标签，不估先验，不设失配诊断／源阈值回退，也没有实体告警工作量。
- **裁定**：T1 `D0`，T2 `D2`；作为“带标签、组隔离固定特异度”强基线，不能与无标签 PBC 放在同一信息预算层。Zotero 未入库。

## 十七、20 篇全文组恢复检查点

- **完成量**：累计 20 篇全文；E3 为 10 篇，E2 为 10 篇。
- **T1**：最高 `D2`、无 `D3`，TreeText-CTS 后连续两轮无新增，扩展检索已停止。
- **T2**：最高 `D2`、无 `D3`；最新近邻为 Anctil 等的“树分数＋组隔离校准＋固定特异度＋未见组测试”，还需连续两轮无新增查询。
- **人工补件**：无。新增预印本可由 medRxiv 官方 PDF 逐页核验。
- **下一查询**：只继续 T2，聚焦“时间有序目标校准段／先导段＋冻结树＋固定 FAR 或 Top-k＋失配回退”，并避免重复普通验证阈值文献。

## 十八、PBC 强近邻增量核验

### Q15：T2 第五轮——时间校准期、冻结分数与先导标签角色

- **查询式**：`"time-ordered calibration period" XGBoost "false positive rate"`；`"deployment pilot" XGBoost threshold calibration intrusion`；`"frozen classifier" "pilot window" prior shift threshold`；`"calibration prefix" XGBoost held-out future`。
- **新增 `D2`**：Li 等（2026）。其目标队列不是时间顺序，但在同一目标队列内严格拆分先验修正、保形校准和留出评价三种标签用途；源模型、源逻辑校准和目标修正均在下一环节前冻结，并定义阳性标签不足时的全审查安全回退。
- **边界**：未命中 XGBoost／随机森林基座；回顾性随机分区不能冒充部署因果前缀；论文明确称其不是无标签实时适应。

### 18.1 Li 等（2026），先验漂移下的发布侧保形分诊审计

- **题录／全文**：Chengze Li 等，*A Deployment Audit of Release-Side Risk in Conformal Triage under Prevalence Shift*，[arXiv `2605.20956`](https://arxiv.org/abs/2605.20956)，v2，2026-08-04；工作副本 `/tmp/manifold-pdf-extract/xgb-tree-audit/2026-Conformal-Triage-Audit.pdf`，20 页，E2。
- **页码与公式**：物理 pp.5—6 的第 3.1—3.2 节固定源风险模型，把目标 `C1／C2／T` 分别用于修正、校准和评价；式（1）—（2）在带标签 `C1` 上用单参数 logit 平移匹配目标先验，之后冻结。物理 pp.7—9 的式（3）—（12）把保形集合映射为发布、标记或延迟人工审查，并定义人工审查率、事件覆盖与错误发布风险；物理 p.10 的式（14）和表 1 给出事件标签过少时 `ny≤⌈1/α⌉−2` 的无限阈值安全回退。物理 p.11 说明目标队列回顾性随机拆为 `31／31／61`，使用冻结源预测；物理 pp.12—14 表 2—3 与图 4联合报告工作量—错误发布风险。
- **支持点**：冻结源分数、带标签目标先导角色、先验匹配、阈值校准、工作量预算、显式数据稀缺诊断、安全回退和不重用标签的留出评价几乎完整同现；这显著压缩 PBC 的宽泛组合原创空间。
- **不能支持点**：全文没有 XGBoost、GBDT 或随机森林实例，只称 Clinical／Radiomics 风险模型；目标 `C1／C2／T` 是回顾性随机分区，不是按到达时间的因果先导／后段；回退是全部纳入人工审查，而不是恢复源阈值；校准依赖延迟目标标签，论文明确否认无标签实时适应。
- **裁定**：T1 `D0`，T2 `D2`，是目前机制关系最接近 PBC、但缺树基座与时间合同的强近邻。可直接借鉴标签用途分账、工作量—漏放风险曲线和稀缺性安全回退；不能作为无标签同预算方法。Zotero 未入库。

## 十九、21 篇全文组恢复检查点

- **完成量**：累计 21 篇全文；E3 为 10 篇，E2 为 11 篇。
- **T1**：最高 `D2`、无 `D3`，扩展检索已停止。
- **T2**：最高 `D2`、无 `D3`；Li 等刷新“先导角色隔离＋预算／风险＋安全回退”的机制近邻，但仍缺树基座、时间因果前缀和源阈值回退。
- **人工补件**：无。
- **下一查询**：从 Li 等重新计两轮，只查“树模型／XGBoost＋时间有序目标 pilot／prefix＋prior／budget＋fallback／defer”；若均无新增 `D2／D3`，即停止扩展。

## 二十、T2 终止窄查询

### Q16：带标签目标先导、树分数与保形分诊

- **查询式**：`XGBoost "labeled pilot" prevalence correction conformal`；`"random forest" "labeled pilot" threshold calibration held-out`；`"frozen source-trained" XGBoost target calibration release review`；`"target pilot" XGBoost conformal triage`。
- **结果**：只重复命中 Li 等（2026）及普通目标域重训练／术语歧义条目，没有新增 T2 `D2／D3`。搜索结果中的 VTOL “target pilot”指飞行员个体，且方法在目标个体数据上重训 XGBoost，不符合冻结源树与时间先导合同，按 D0 初筛排除，不进入技术证据矩阵。
- **计数**：这是 Li 等之后第一轮无新增。

### Q17：源阈值回退、时间前缀与告警预算

- **查询式**：`"source threshold" fallback XGBoost target calibration`；`"time-ordered pilot" classifier "alert budget" freeze`；`"causal pilot window" XGBoost calibration`；`"target prefix" tree scores prior correction held-out`。
- **结果**：没有新增 T2 `D2／D3`。Zendal 等（2026，DOI `10.3390/app16147263`）的初筛元数据／摘要涉及源阈值迁移失效与本地重校准，但基座为联邦逻辑模型，且未形成树分数、目标时间先导、不相交后段和预注册源策略回退的联合关系；跨课程、跨数据集阈值工作同样只作检索边界。因最终裁决不依赖这些条目的技术细节，未用摘要升级证据等级或写入逐篇矩阵。
- **计数**：这是 Li 等之后连续第二轮无新增；T2 满足停止条件。
- **Zotero 状态**：只读去重，无写入；没有新增需入库的全文。

## 二十一、最终综合

### 21.1 核心论文清单与直接同构等级

| 机制族 | 核心论文 | 证据等级 | 直接等级 | 本任务中的定位 |
| --- | --- | --- | --- | --- |
| 二进／随机区间统计 | TSF／`interRF`、CIF、DrCIF、r-STSF | E2 | T1 `D2` | 固定幂次、随机或监督选区间＋森林已经存在 |
| 多粒度窗口森林 | gcForest | E3 | T1 `D2` | 多窗口扫描进入森林已有，但不是实体因果历史 |
| 网络在线多尺度 | Kitsune／AfterImage | E3 | T1 `D2` | 网络实体／通道的因果五尺度统计基础 |
| 实体多窗 XGBoost | Pinchuk（2026） | E2 | T1 `D2` | 实体截止、多组尾随窗与单一 XGBoost 的最直接表格近邻 |
| 固定幂次窗 XGBoost | TreeText-CTS（2026） | E2 | T1 `D2` | 患者实体、幂次尺度、训练集冻结的逐窗 XGBoost 强近邻 |
| 分数校准 | Niculescu-Mizil—Caruana；Zadrozny—Elkan | E3 | T2 `D1` | 逻辑校准与等渗回归标准部件 |
| 无标签先验修正 | Saerens 等 | E3 | T2 `D2` | 冻结分数、无标签先验、诊断与不修正回退 |
| 目标先验与约束阈值 | TAP-GPPS（2026） | E2 | T2 `D2` | XGBoost 实例、无标签组先验与约束阈值 |
| 树分数固定误报预算 | Hung（2026）；Anctil 等（2026） | E3／E2 | T2 `D2` | 固定假阳率／特异度、隔离校准与测试 |
| 发布侧分诊与安全回退 | Li 等（2026） | E2 | T2 `D2` | 冻结源分数、目标标签分账、工作量—风险与稀缺回退的最强机制近邻 |

**直接同构结论**：21 篇全文中没有 T1 或 T2 的 `D3`；两个对象的最高等级均为 `D2`。该结论受本轮操作化定义、合法来源与 17 组查询范围约束，不能改写成“全球首创”。

### 21.2 可直接借鉴的结构改造

1. **历史表示**：借鉴 AfterImage 的按实体／通道在线常数时间更新，但把衰减尺度改成预注册的因果尾随窗；每个事件只允许读取其之前的同实体状态。
2. **尺度与窗口选择**：以 `interRF` 的二进区间、CIF／DrCIF 的随机区间和 r-STSF 的监督选区间作为替代尺度搜索；任何监督选择只用源实体折外预测完成，并在目标数据出现前冻结。
3. **树的组织方式**：同时比较“所有尺度拼接到单一 XGBoost”和 TreeText-CTS 式“每窗 XGBoost 后均值／最大值”；Pinchuk 的计数-only 多窗 XGBoost用于同信息强对照。
4. **实体聚合**：若标签确为袋级，可用 MIForests；若只是组内相关，GPBoost 是统计部件。二者都不能替代逐流严格前缀合同。
5. **分数与先验**：先在源实体折外分数上比较逻辑校准／等渗回归，再用 Saerens EM、BBSE／DFM 或条件可用的 TAP-GPPS 估计目标先验；诊断不通过时保留源策略。
6. **预算与回退**：借鉴 Hung 的固定假阳率、Anctil 的组隔离固定特异度、Li 的标签用途分账与稀缺安全回退；部署评价同时报告误报／漏报、实体告警量、人工审查率和回退触发率。
7. **信息权限分层**：无标签先导、少量带标签先导、持续标签在线更新分别成层；AXGB／ARF 与带标签率特征只能作为上界或独立层，不能与冻结无标签方案直接横比。

### 21.3 强基线与基础部件

| 层级 | 应纳入方法 | 使用条件 |
| --- | --- | --- |
| DTEP 必做同骨干 | 原始 XGBoost；固定单窗统计＋XGBoost；Pinchuk 式计数-only 无前视多窗 XGBoost；TreeText 式逐窗 XGBoost 均值／最大值 | 同字段、同实体历史、同训练与推理预算 |
| DTEP 强结构 | `interRF`／TSF、CIF、DrCIF、r-STSF；AfterImage＋XGBoost | 必须改造成同一因果实体输入，公开额外计算量；AfterImage＋XGBoost 是构造组合而非 Kitsune 原模型 |
| PBC 必做 | 源阈值；源实体折外逻辑校准／等渗；Saerens EM、BBSE／DFM；Hung 固定假阳率 | 同一冻结树分数、同一先导长度和标签权限 |
| PBC 条件性强基线 | TAP-GPPS；Anctil 式组隔离等渗＋固定特异度；Li 式保形发布／标记／延迟 | 分别要求敏感属性、目标标签或人工审查通道，须单列信息／人力预算 |
| 标签可达上界 | AXGB、ARF、带标签目标 oracle、Pinchuk 标签率特征 | 只作独立权限层，不参与无标签同预算排名 |
| 基础部件／非主基线 | gcForest、MIForests、GPBoost、Greedy Miser、经典校准公式 | 仅在计算预算、袋标签语义、组内相关或特征成本问题实际出现时启用 |

### 21.4 DTEP 与 PBC 的原创边界

- **DTEP 已被占用的宽泛表述**：多窗／多尺度统计、固定幂次尺度、实体无前视聚合、网络在线多尺度特征、冻结 XGBoost 和监督／随机选窗均已有直接来源，不能单独作为原创点。
- **DTEP 可保留的任务化边界**：面向网络逐流的同实体严格历史前缀；尺度选择只用源实体折外预测并冻结；固定二进尺度进入同一、共同预算 XGBoost；跨年份／跨时间且实体隔离评价；冷启动与超长实体的预注册回退。是否产生收益必须由共同预算强基线、消融和多种子实验裁决。
- **PBC 已被占用的宽泛表述**：冻结模型上的目标先验修正、阈值预算、数据角色隔离、工作量分诊、显著性“不修正”与稀缺安全回退均已有来源，不能单独作为原创点。
- **PBC 可保留的任务化边界**：冻结树分数；只用按到达时间截取的目标因果先导段；明确无标签或少标签预算；在同一合同中联合先验失配诊断、实体告警量／假阳率预算和回到源策略；随后冻结并只在时间不相交后段评价。Li 等的随机回顾分区和全审查回退没有占用“时间因果＋源策略回退”这两项。
- **表述纪律**：最终只能写“本轮未发现 D3 直接近邻”，不能写“首次提出”；没有真实实验制品前，DTEP 与 PBC 均标为“设计可行、实验待证”。

### 21.5 人工补件与写入边界

- **人工补件清单：无。** 21 篇最终纳入文献均有合法公开全文，技术裁决均落到物理页码、公式、算法、表格或正式章节。
- MDPI 限流和 PMC PDF 挑战已由 Europe PMC／PMC 正式 JATS 全文解决，不是阻塞。
- 本任务未改 `raw/`、`wiki/`、Zotero、RWKV 总控／恢复卡、论文正文、代码或实验制品。
