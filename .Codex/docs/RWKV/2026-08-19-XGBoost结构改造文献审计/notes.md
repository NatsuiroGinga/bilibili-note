# XGBoost 与相近树模型结构改造文献审计过程笔记

- **日期**：2026-08-19
- **代理映射**：`xgboost_tree_adaptation_literature_sol_max → gpt-5.6-sol → effort=max`
- **研究路线**：`RESEARCH_ROUTE=RWKV`
- **当前状态**：规则与既有审计恢复完成；开始本地与 Zotero 去重盘点。

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
