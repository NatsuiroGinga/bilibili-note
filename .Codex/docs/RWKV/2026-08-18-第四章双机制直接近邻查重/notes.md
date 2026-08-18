# 第四章双机制直接近邻查重过程笔记

- **日期**：2026-08-18
- **代理映射**：`ch4_dual_mechanism_novelty_literature_resume_sol_max → gpt-5.6-sol → effort=max`
- **状态**：阶段二检查点 `2819dfb` 后续；前两批证据已提交为 `b71bf3b`、`7f8a027`。当前已全文核验 10 篇独立工作、11 份全文制品；第三批 DFM、SIM 标记 TDAE 与 Slips 的原件、知识层和 Zotero 条目已完成，待批次提交。

## 一、任务合同摘要

### 研究问题

核定目标前缀决策层适应（A）、实体全历史与有界近期窗口双通道（B）、源域折外选择到目标前缀标定再到冻结后段评价的统一算法合同（C）是否已被经典工作或 2016—2026 年直接近邻占用，并为第四章两个核心机制给出可追溯全文证据。

### 预期决策

- A、B 能否作为两个核心机制；
- C 应被表述为统一实验／部署合同、算法耦合，还是已被直接近邻占用；
- 每一部分可使用的最强措辞与禁止的更强措辞；
- 查重未关闭时需要补哪篇全文或哪组检索。

### 证据纪律

- 全文证据与摘要线索分开；
- 题录真实性与具体方法主张分别核验；
- 每篇都记录原件路径、SHA-256、页码／公式、支持点和不支持点；
- Zotero 只作馆藏、题录与附件管理，不能替代仓库 `raw → wiki` 证据链；
- 文献证据不能证明候选在 LSPR23／LSPR24 上有效。

## 二、既有项目证据与待核假设

以下仅是本地项目事实或待验证假设，不作为文献原创性结论：

1. 已有项目诊断显示，第三章上下文机制在长实体桶上显著有害，大型良性实体出现逐流假阳尖峰；该现象支持检索 B，但不能证明 B 有效。
2. 决策层指数的目标年作弊式桶内上界仍无法弥补长实体损失，说明 B 的查重应优先看表示层双时间尺度历史，而不是只看规模条件化池化。
3. 源年实体分组折外选择已在项目 XGBoost 路线中使用，但神经模型窗口选择信号尚待实验；文献查重要区分“项目已有工程做法”和“文献中已发表机制”。
4. A 中黑盒标签移位估计依赖条件可能失配；查重重点不是一般标签移位，而是条件诊断、失败回退和固定误报预算下冻结后段的组合。
5. C 的价值可能来自标签权限、时间顺序和冻结关系的严格耦合，而非新增独立统计估计器；必须寻找直接同构算法，不能只堆通用域适应论文。

## 三、概念词表与同义词

| 概念 | 英文检索词 | 判定备注 |
| --- | --- | --- |
| 目标因果前缀 | `target prefix`、`calibration window`、`initial target batch`、`burn-in` | 必须发生在后段评价之前 |
| 少量合法标签 | `few labeled target samples`、`supervised calibration`、`analyst-confirmed labels` | 记录标签预算和抽样单元 |
| 无标签预测 | `unlabeled target predictions`、`black-box shift estimation`、`quantification` | 不能暗用后段真值 |
| 实体级决策 | `host-level`、`entity-level`、`machine-level`、`account-level`、`bag-level` | 区分逐流／逐样本决策 |
| 固定误报预算 | `fixed FPR`、`false alarm budget`、`Neyman–Pearson`、`risk control` | 记录是否校准后冻结 |
| 全历史前缀 | `cumulative history`、`running statistics`、`long-term memory` | 必须按实体键且因果 |
| 有界近期窗 | `recent window`、`short-term statistics`、`sliding window`、`fast state` | 记录窗口选择域 |
| 双时间尺度 | `dual timescale`、`fast-slow`、`short-term and long-term` | 不能只因网络有多尺度卷积即判同构 |
| 实体分组折外 | `grouped out-of-fold`、`GroupKFold`、`leave-one-entity-out` | 选择窗长／变体而非报告分数即可 |
| 冻结后段 | `frozen evaluation`、`prospective holdout`、`prequential evaluation` | 记录是否持续在线更新 |
| 安全回退 | `fallback`、`abstention`、`safe adaptation`、`misspecification test` | 记录触发条件与回退基线 |

## 四、只读本地盘点记录

### 已知馆藏线索

待提交确认后补齐。优先盘点以下目录，但不据文件名推断全文内容：

- `raw/papers/attack-detection/`
- `raw/papers/methodology/`
- `raw/papers/methodology/multiple-instance/`
- `raw/papers/methodology/ranking/`
- `wiki/papers/attack-detection/INDEX.md`
- `wiki/papers/methodology/INDEX.md`

### Zotero 当前状态

- 本地接口与连接器已恢复；当前选中“我的文库”根层级。
- BBSE `V7UEB83M`、王世谦等 `SM7C8GX6`、İnan `9VG8ZBDJ`、PseudoCal `3K3ALH8S`、IW-GAE `6W5EVQE7`、Better Practices `2PK7SRWC` 已在前两批核验。
- 本批新增 DFM `XPQH2ENC`、SIM 标记 TDAE `A7W3F3TH`、Slips `G4VRGMXX`。前两者无子项；Slips 只有 BibTeX 说明笔记 `D9H475DC`，没有 PDF 附件。
- 不能声称 Zotero 已附全文；仓库 `raw` 与 `wiki` 是全文和论断证据源。

## 五、检索日志模板

每完成一组查询，追加一条：

```text
查询编号：
日期与时间：
数据库／站点：
查询式：
结果页或接口：
初始命中数：
去重后候选数：
新增 D2／D3 数：
关键命中：
排除概况：
下一条查询：
Zotero 状态：
```

## 六、候选论文登记模板

```text
题名：
作者：
年份：
来源／DOI／arXiv：
正式页面：
全文来源：
原件路径：
SHA-256：
全文页数：
证据位置：
支持点：
不支持点：
与 A／B／C 的关系：
直接同构级别：D0／D1／D2／D3
证据等级：E0／E1／E2／E3
纳入／排除：
理由：
wiki 笔记：
索引状态：
Zotero 条目／集合／附件状态：
允许措辞：
禁止更强措辞：
待办：
```

## 七、全文阅读笔记模板

```text
论文解决的问题：
任务单元与实体键：
源域／目标域定义：
时间顺序：
标签权限：
选择与调参发生在哪一段：
校准发生在哪一段：
评价发生在哪一段：
方法结构与公式：
阈值／先验／窗口机制：
固定误报预算：
失配检测与回退：
数据集与年份跨度：
指标：
关键结果：
消融：
作者自述局限：
本任务的同构判定：
```

## 八、查询家族与预期边界

### A 查询家族

1. 标签移位估计与先验修正；
2. 概率校准与阈值迁移；
3. 固定第一类错误／固定误报预算；
4. 入侵检测中的目标前缀、有监督／无监督标定；
5. 标签移位假设失配、诊断与回退。

### B 查询家族

1. 网络实体／主机的短期与长期行为画像；
2. 快慢状态、累积统计与滑动窗口并行；
3. 多示例学习中的包大小偏差和大包假阳；
4. 时间序列分类中的窗口长度选择；
5. 按实体分组的折外选择与时间因果评价。

### C 查询家族

1. 源域模型选择、目标小标定集与独立后段测试；
2. 前向／预序评价；
3. 测试时适应的“适应—冻结—评价”协议；
4. 安全适应、拒绝适应或失配回退；
5. 网络入侵检测跨年度或跨部署协议。

## 九、30 分钟检查点模板

```text
检查点时间：
已完成阶段：
已完成查询组／全文篇数：
当前候选数／去重数／纳入数／排除数：
新增 D2／D3：
下一篇全文或下一查询：
未关闭疑点：
无法取得原文：
raw／wiki 批次状态：
Zotero 状态：
精确阻塞：
```

## 十、第一轮本地馆藏盘点

### 规模与索引

- `raw/papers/`：433 个 PDF；
- `wiki/papers/`：495 个 Markdown 文件；
- 重点索引：`wiki/papers/methodology/INDEX.md`、`wiki/papers/attack-detection/INDEX.md`；
- 已有 A 相关原件：BBSE、JCPOT、协变量移位保形、最大似然标签移位校准、标签移位统一视角、在线异常阈值；
- 已有 B 相关原件／笔记：多示例实体聚合、随机大包池化、大小不变损失、服务器／主机级统计聚合、告警预算；
- 已有应用近邻：NetGuard 主动适应、TESSERACT 时间一致评价、TLS 阈值跨周失配、实体／主机粒度检测。

### 已确认的本地缺口

1. 标签移位最大似然、统一视角等原件已在 `raw`，但索引中仍有部分缺全文笔记，后续须补笔记而非重复下载；
2. NIDES 官方网页全文已核验，但 SRI PDF 端口不可达，尚无本地原件；
3. PseudoCal、IW-GAE、DFM 的正式／作者全文、笔记和 Zotero 条目已经补齐；
4. 王世谦等、SIM 标记 TDAE 与 Slips 的全文、笔记和 Zotero 条目已经补齐；
5. Zotero 已恢复，但本轮条目均未关联 PDF 子附件。

## 十一、第一轮联网检索日志

### Q-A1：目标域阈值、标签移位与固定误报预算

- **查询式**：`"network intrusion detection" "calibration" "false positive rate" target domain threshold host`；`"label shift" misspecification fallback robust calibration threshold`；`"fixed false positive rate" online calibration intrusion detection`。
- **来源**：PMLR、arXiv、OpenReview、出版社页面与官方项目页；检索日期 2026-08-18。
- **初步命中**：
  - BBSE 正文及补充材料：补充材料明确讨论标签移位假设不成立时可用核两样本检验判断近似是否合理；本地已有正文，补充材料待补；
  - 最大似然标签移位加偏差校正校准：本地已有原件，全文笔记待补；
  - 标签移位量化的分布特征匹配：明确研究标签移位假设失配与目标污染下的鲁棒性，待下载全文；
  - 无目标标签的标签移位校准：2024 年无标签后处理校准，待核正式题录与全文；
  - 目标域伪校准：2024 年无标签目标域后处理校准，待下载全文；
  - 纽曼—皮尔逊分类、在线异常阈值与 2026 年低误报入侵检测阈值：作为固定误报预算的 D1／D0 边界，待逐篇核验。
- **当前判断**：标签移位估计、校准、固定误报预算均已分别被占用；A 的可查重空间只可能来自实体级目标前缀、条件支路失配回退和冻结后段的具体耦合，不能把任一子机制写成首创。

### Q-B1：安全领域的短期／长期实体行为

- **查询式**：`("short-term" AND "long-term") host behavior intrusion detection sliding window`；`"recent history" "long-term" network intrusion detection host anomaly`；`"dual-timescale" anomaly detection user behavior security`。
- **来源**：SRI／技术报告入口、出版社页面、正式期刊页面、作者公开 PDF 入口；检索日期 2026-08-18。
- **初步命中**：
  - NIDES 经典统计组件：按用户／主体比较短期行为与长期画像，短期和长期记录数可配置；这是 B 的关键经典强近邻；
  - 自适应异常检测的演化连接系统：沿用短期／长期画像并用衰减更新历史，构成在线更新边界；
  - 移动通信欺诈用户画像：同时维护短期与长期概率画像并比较差异触发告警；
  - 邮件档案用户建模：以用户为实体，用短期窗口相对长期训练画像的变化触发异常；
  - 2024 年长期／短期特征用户异常检测：分别建模长期与短期用户行为后融合，构成近期 D2 候选；
  - 2022 年记忆增强内部威胁检测：窗口长度在长期弱信号与短期突变之间存在权衡，待核是否真正双通道。
- **当前判断**：B 的“实体短期／长期行为并用”至少已有三十余年谱系，不能作为原创；尚可查重的部分是全历史因果前缀与有界近期窗口同时进入表示、只在源域实体分组折外选窗，以及针对长实体假阳的任务化耦合。

### Q-C1：源域选择、目标校准与独立评价

- **查询式**：`"source domain" "target calibration" holdout evaluation`；`unsupervised domain adaptation target calibration source validation post-hoc calibration`；`"target calibration set" domain adaptation evaluate target test`。
- **来源**：PMLR、arXiv、OpenReview；检索日期 2026-08-18。
- **初步命中**：
  - 可迁移校准：用无标签目标数据作域适应后处理校准；
  - 伪校准：把无标签目标域转成伪标定集；
  - 重要性加权分组准确率估计：在无监督域适应中同时服务模型选择与校准；
  - 域适应最佳实践：明确指出使用目标测试标签做超参数选择属于坏实践；
  - 2026 年非平稳时间序列近邻：声称使用无泄漏划分、折外保序校准、因果滚动稳定化与固定 1% 告警预算，可能同时占用 C 的多个关系，须优先取得全文。
- **当前判断**：训练／校准／独立测试的时间合同本身是通用评价纪律，不宜作为独立原创贡献；C 只有在把源域实体折外选窗、目标前缀实体标定、条件性先验支路与冻结后段写成一套特定算法时，才可能形成任务化耦合。

### Q-B2：实体分组折外选择窗口

- **查询式**：`intrusion detection GroupKFold host window length`；`user anomaly detection cross-validation window size long-term short-term`；`entity-level anomaly detection out-of-fold window`。
- **结果**：命中分组交叉验证选模型超参数、按时间区域分组避免窗口泄漏、训练折外阈值校准和普通窗口长度交叉验证；尚未命中“按实体分组折外预测选择近期窗，同时目标后段冻结评价”的直接工作。
- **本轮新增 D2／D3**：0；该结果仅是第一轮，不能写成不存在。

## 十二、候选全文获取队列

### P0：直接决定占用边界

1. NIDES 统计组件或正式技术报告；
2. BBSE 正文与补充材料；
3. 标签移位量化的分布特征匹配；**已完成**；
4. 2024 年长期／短期特征用户异常检测；
5. 2026 年非平稳时间序列的折外校准、泄漏安全与固定告警预算论文；
6. 重要性加权分组准确率估计；
7. 伪校准；
8. 域适应最佳实践。

### P1：子机制谱系与边界

1. 最大似然标签移位加偏差校正校准；
2. 标签移位统一视角；
3. 无目标标签的标签移位校准；
4. 移动通信欺诈短期／长期画像；
5. 邮件档案用户建模；
6. 记忆增强内部威胁检测；
7. 在线异常阈值与低误报入侵检测阈值近邻。

## 十三、当前检查点

- **已完成**：任务合同、馆藏盘点、A／B／C 窄查询，以及 10 篇独立工作的全文裁决。DFM 下载阻塞已关闭；SIM 标记 TDAE 与 Slips 已完成原件、笔记和 Zotero 链。
- **下一步**：接收 NIDES 人工原件；追踪实体 OOF 选窗、实体预算与失配触发回退的两轮窄查询。
- **未关闭疑点**：是否存在 D3、长实体假阳直接机制、目标缓冲区与评价后段是否有严格时间隔离、NIDES 原件。

## 十四、第一批全文逐篇登记

### F1：基于长短周期特征的用户异常行为检测

- **题录**：王世谦、白宏坤、贾一博、卜飞飞、黄勇，2025，《郑州大学学报（理学版）》57(6)，65—73、参考文献续至82；DOI `10.13705/j.issn.1671-6841.2024077`。
- **原件**：`raw/papers/attack-detection/2025-Wang-LMIM-Long-Short-Period-User-Anomaly-Detection.pdf`；10页；SHA-256 `626da14439a62c1893b71588f0c905997fdb40f17e0defabc9613837b0bafaaa`。
- **证据**：物理第4至5页／印刷68—69页式（1）至（3）为周级长期多孤立森林；物理第5页式（4）至（7）为5、10、15分钟三个独立 GRU；物理第6页／印刷70页式（8）按两个模型各自准确率加权晚融合。
- **支持**：用户实体、长短周期并用、两个模型晚融合，B 为 D2。
- **不能支持**：长期仅在1—6周中选4周，不是全历史；窗口按普通实验选，不是源实体 OOF；数据以正常样本为主，10%异常由人工扰动合成，拆分的时间／实体隔离不清；无单独 LSPIF、MTWG、LMIM 完整融合消融。
- **知识与 Zotero**：`wiki/papers/attack-detection/2025-Wang-LMIM长短周期用户异常检测.md`；`SM7C8GX6`，无附件。

### F2：Proximity-based explainable anomaly detection for time-series data with calibration, leakage safety

- **题录**：Ebubekir İnan，2026，*Internet of Things* 37:101920；DOI `10.1016/j.iot.2026.101920`，PII `S2542660526000508`。
- **原件**：`raw/papers/attack-detection/2026-Inan-Proximity-Anomaly-Calibration-Leakage-Safety.pdf`；28页；SHA-256 `b6974fa21684ade2de4a3323e283d06e9ef9448b16ea3e32683c44381c50b38b`。
- **证据**：物理第4页式（2）至（3）为因果滚动 MAD；第5页式（11）至（13）为融合；第5至6页说明监督等渗／无标签经验分布标定；第9至11页用每序列连续70/15/15划分和1%告警预算；第26至27页算法给出完整流程。
- **关键边界**：标定集先决定 `k_fit`，后段再按全部后段分数重选恰好 `k_fit` 个；`τ_fit` 只作诊断。因此冻结的是告警数，不是可在线执行的数值阈值。
- **支持**：A、C 为 D2；独立标定、时序切分、固定预算和折外分数均已有强近邻。
- **不能支持**：无网络实体键、类别先验、BBSE 失配回退、源实体 OOF 选窗，也没有真正冻结的后段数值阈值。
- **知识与 Zotero**：`wiki/papers/attack-detection/2026-Inan-邻近异常检测校准与泄漏安全.md`；`9VG8ZBDJ`，无附件。

### F3：BBSE 正文与附录

- **题录**：Lipton、Wang、Smola，2018，ICML，PMLR 80:3122—3130；稳定标识 `pmlr-v80-lipton18a`。
- **原件**：正文 `raw/papers/methodology/2018-Lipton-BBSE-Label-Shift.pdf`，9页，SHA `f0b042df501321fc422fc14d733f857723df6e7e9d8635ef84c90d26d5480cee`；含附录版本 `raw/papers/methodology/2018-Lipton-BBSE-Label-Shift-Supplement.pdf`，11页，SHA `4ea2ca7b44133eaec9429351efc742b6b01a7c2d4bf14f12d46cd038e88be8fd`。
- **证据**：正文物理第2至3页给标签移位、支持集与混淆矩阵可逆假设及 `ŵ=Ĉ^{-1}_{ŷ,y} μ̂_ŷ`；正文第5页算法1独立拆分源数据。含附录版本物理第10页用重加权源特征与无标签目标特征的核均值差诊断标签移位近似，并提出最小奇异值选黑盒与数据复用偏差。
- **支持**：A 的无标签先验估计与条件诊断为 D1。
- **不能支持**：附录没有规定失配后自动切换的基线；无目标时间先导段、实体预算和冻结后段。
- **知识与 Zotero**：`wiki/papers/methodology/2018-Lipton-BBSE标签移位.md`；`V7UEB83M`，无附件。

### F4：PseudoCal

- **题录**：Hu、Liang、Wang、Foo，2024，ICML，PMLR 235:19304—19326；稳定标识 `pmlr-v235-hu24i`。
- **原件**：`raw/papers/methodology/2024-Hu-PseudoCal-Unsupervised-Domain-Calibration.pdf`；23页；SHA `0e19d94c0e7d51831dbde522efefb69bc231e5258ee0101176c0cfca8af97f47`。
- **证据**：物理第4页分解目标温度缩放损失并给跨伪标签簇混合公式；第5页固定域适应模型、默认 `λ=0.65`；第8页消融与模型质量边界；第9页局限；第14页算法1。
- **支持**：A 的无标签目标后处理校准为 D1。
- **不能支持**：使用整个目标域作传导式校准，无因果先导段、实体预算、类别先验、BBSE 回退和冻结后段。
- **知识与 Zotero**：`wiki/papers/methodology/2024-Hu-PseudoCal无监督目标域伪校准.md`；`3K3ALH8S`，无附件。

### F5：IW-GAE

- **题录**：Joo、Klabjan，2024，ICML，PMLR 235:22509—22529；稳定标识 `pmlr-v235-joo24a`。
- **原件**：`raw/papers/methodology/2024-Joo-IW-GAE-Calibration-Model-Selection.pdf`；21页；SHA `ed06be67071fd6426f9212ccfbbe2d3ae2a2ef49299363d33b8a7cc8bef7aace`。
- **证据**：物理第2页假设协变量移位且无概念移位；第3页式（2）按置信度分组并同时服务校准与选模；第5页式（8）至（13）优化重要性权重；第17页算法只显式拆源训练／验证；第21页承认非可识别性。
- **支持**：A 的无标签校准、C 的无标签选模＋校准均为 D1。
- **不能支持**：组是置信度组而非网络实体；无时间先导段、固定误报预算、标签移位诊断／回退或源实体 OOF。
- **知识与 Zotero**：`wiki/papers/methodology/2024-Joo-IW-GAE重要性加权组准确率.md`；`6W5EVQE7`，无附件。

### F6：Better Practices for Domain Adaptation

- **题录**：Ericsson、Li、Hospedales，2023，AutoML，PMLR 224:4/1—25；稳定标识 `pmlr-v224-ericsson23a`，arXiv `2309.03879`。
- **原件**：`raw/papers/methodology/2023-Ericsson-Better-Practices-Domain-Adaptation.pdf`；25页；SHA `681b18b0d6f886c6e9448c2dd8358ce8dd979e3e66c6629c66daa0366e15aa7a`。
- **证据**：物理第3页判目标测试标签调参为错误；第5、7页要求目标训练／验证／测试分离并显示独立验证更可靠；第8至10页显示适应可能低于源模型；第14页算法与60/20/20切分。
- **支持**：C 的独立评价纪律为 D1；为失配时保留源模型提供动机。
- **不能支持**：普通随机切分而非时间因果先导段；无 A／B 具体机制和确定性回退触发器。
- **知识与 Zotero**：`wiki/papers/methodology/2023-Ericsson-域适应更佳实践.md`；`2PK7SRWC`，无附件。

### F7：NIDES Statistical Component

- **题录**：Harold S. Javitz、Alfonso Valdes，1994，SRI International，*The NIDES Statistical Component: Description and Justification*；无 DOI；稳定官方页 <https://www.csl.sri.com/papers/2sri/>。
- **全文状态**：SRI 官方网页索引可读取 52 个物理页，PDF 精确入口 <https://www.csl.sri.com/papers/2sri/2sri.pdf>；本机 HTTP／HTTPS 均连接超时，raw、SHA、wiki 与 Zotero 待人工原件后补。
- **证据**：物理第5至8页说明按用户、组、远程主机和系统维护充分统计画像；第20至21页直接比较约200条记录的短期行为与30天半衰期长期画像；第41至42页说明历史从首次行为开始但以指数权重降低旧记录影响。
- **支持**：安全领域实体双时间尺度为 B 的 D2 强近邻。
- **不能支持**：长期画像不是未衰减全历史；窗口不由源实体 OOF 选择；无目标前缀冻结与长实体假阳实验。

### F8：SIM 标记网络流量的 TTL 时序深度自编码器

- **题录**：Babe Haiba、Najat Rafalia，2026，*Computers* 15(2):107；DOI `10.3390/computers15020107`。
- **原件**：`raw/papers/attack-detection/2026-Haiba-SIM-Tagged-TTL-Anomaly.pdf`；19页；SHA `ef72675dbcebca9df573cecadf1ed7772f03c0f1d938339a784f11b0430a96b5`；出版社 CC BY 静态原件。
- **证据**：物理第7页固定 `L=64`、步长16，Conv1D＋LSTM 在同一窗口内建模局部与较长依赖；第7—9页按合成 `SIM_tag` 做五折 GroupKFold；第7、9—10页从目标环境良性缓冲区按 `1-α` 分位数设 FAR 预算阈值；第14页允许漂移时滚动重标定；第15—16页给身份合成与数据面异常局限。
- **关键边界**：算法1先在测试窗计算分数，却没有把目标良性缓冲区列成独立输入或写明与最终评价窗的时间隔离；正文和表注声称“缓冲区标定后目标评价”。据此只能判为流程强近邻，不能认定实现了严格先导段与冻结后段。
- **支持**：A、B、C 均为 D2。它同时占用实体分组滑窗、源一类训练、目标良性缓冲区分位阈值和显式误报预算。
- **不能支持**：窗长固定而非源实体 OOF 选择；只有单一有界窗口而非完整历史＋近期双通道；阈值全局而非实体专属；无类别先验、BBSE 失配回退和冻结后段。
- **知识与 Zotero**：`wiki/papers/attack-detection/2026-Haiba-SIM实体分组窗与目标缓冲区阈值.md`；`A7W3F3TH`，无附件。

### F9：Slips 主机时间窗证据聚合

- **题录**：Sebastian Garcia 等10人，2026，`arXiv:2608.11979v1 [cs.CR]`；DataCite DOI `10.48550/arXiv.2608.11979`；尚未同行评审。
- **原件**：`raw/papers/attack-detection/2026-Garcia-Slips-Behavioral-Evidence-Aggregation.pdf`；12页；SHA `1db7c86a6708152ec0208ac8fe2066e2ce22026447049312d943af98f2a5d6f3`。
- **证据**：物理第2—3页按源IP建默认一小时画像；第5—6页分别给逐流 SGDClassifier、多流双向 GRU 与固定证据融合，`s_i=t_i c_i`、`S_{p,w}=Σ_i s_i`；第7页固定阈值15／小时；第10页表3给流级与画像窗级指标和局限。
- **支持**：B 为 D2，A 为 D1，C 为 D0。主机有界窗、多个独立检测器与画像窗级加性决策均明确已有。
- **不能支持**：无未衰减全历史通道、源实体 OOF 选窗、目标前缀标定、预算先验、冻结后段或融合消融；完整 PCAP 回放与晚到数据回填不证明严格因果输出冻结。
- **结果边界**：画像窗级 Slips `F1=0.3268`、召回率 `0.1953`，Suricata 为 `0.1925/0.1065`，二者 FPR 均为0；数据仅含两份恶意与一份良性 PCAP，作者明确称为架构演示。
- **知识与 Zotero**：`wiki/papers/attack-detection/2026-Garcia-Slips主机时间窗证据聚合.md`；`G4VRGMXX`，只有说明笔记子项，无 PDF。

### F10：DFM 稳健标签漂移量化

- **题录**：Dussap、Blanchard、Chérief-Abdellatif，2023，ECML PKDD Research Track，LNCS 14173:69—85；DOI `10.1007/978-3-031-43424-2_5`；arXiv `2306.04376v2`。
- **原件**：`raw/papers/methodology/2023-Dussap-DFM-Robust-Label-Shift.pdf`；30页作者预印本；SHA `7e608f675d458d02a495970d78935d4cf5106853019ece4b8404d31d3d60a96c`。
- **证据**：物理第5页式（P）定义分布特征匹配与 soft-DFM；第6页命题1证明 BBSE 是分类器独热输出映射下的特例；第7—8页定理1给精确标签漂移误差界；第9—10页定理2与推论1给失配／未知类污染边界；第10页明确不期待 BBSE 有一般污染稳健性；第11—14页给 QP、RFFM 与实验；第15页建议在控制数据上检查偏差／漂移。
- **支持**：A 为 D2，C 为 D1，B 为 D0。它直接支撑 PBC 的 BBSE 分支只能条件使用，并提供未知类污染的替代估计器压力基线。
- **不能支持**：没有可观测的预注册失配触发器、自动回退、实体先验／预算、时间先导段和冻结后段；softRFFM 只在污染表征远离源类等条件下更稳健。
- **知识与 Zotero**：`wiki/papers/methodology/2023-Dussap-DFM稳健标签漂移量化.md`；`XPQH2ENC`，无附件。

## 十五、第二轮查询与下载日志

### Q-A2：BBSE 失配、无标签目标校准与域适应选模

- **查询链**：BBSE 正文→官方补充材料→核均值失配；PseudoCal、IW-GAE 与 Better Practices 的正式 PMLR 页面、算法、附录和引用链。
- **结果**：新增 A 的 D1 三篇、C 的 D1 两篇；没有新增 D3。BBSE 提供诊断但不提供回退，PseudoCal 和 IW-GAE 使用完整无标签目标域而非因果先导段。
- **下一查询**：DFM 的目标污染／标签移位失配鲁棒保证；固定实体误报预算与拒绝适应。

### Q-B3：NIDES 与近期用户长短周期近邻

- **查询链**：SRI NIDES 官方报告、2025 年王世谦等全文，以及二者关于实体键、时间尺度、融合与窗口选择的直接比较。
- **结果**：新增 B 的 D2 两篇；“安全实体长短期画像”明确已有三十年谱系。仍未命中源实体分组 OOF 选近期窗、未衰减全历史与有界近期窗并行、长实体假阳三者同现。
- **下一查询**：从 NIDES 引用与近期内部威胁／邮件用户画像做前后向追踪；检索 entity-grouped OOF window selection。

### Q-A3／Q-B4：实体分组窗口与实体误报预算交叉查询

- **查询式**：`"entity-level" "false alarm budget" anomaly detection calibration threshold`；`"host-level" threshold calibration "false positive rate" intrusion detection`；`"GroupKFold" "window length" anomaly detection user behavior`；`"leave-one-user-out" window selection anomaly detection`。
- **来源**：MDPI 正式页、arXiv 正式页、作者／出版社开放 PDF；检索日期 2026-08-18。
- **命中与全文**：
  - Haiba、Rafalia 2026 的 SIM 标记 TDAE：按合成实体 GroupKFold，固定窗，目标良性缓冲区分位阈值与 FAR 预算；A／B／C 均新增 D2。
  - Garcia 等 2026 的 Slips：主机时间窗、逐流与多流模型、可追溯证据后期聚合；B 新增 D2，但属预印本 E2。
  - GUARDIAN 的留一用户身份验证窗、医疗／脑电的 GroupKFold 窗口、专利式主机 FPR 等因任务或证据等级不符排除，不进入强结论。
- **关键裁决**：GroupKFold 与实体窗同现已经有安全论文，但“用源实体折外预测选择候选窗长”仍未命中。目标环境良性缓冲区按误报预算取分位阈值也已出现，PBC 只能在实体专属预算／先验、严格时间隔离、失配回退和冻结上区分。
- **本轮新增 D2／D3**：D2 两篇，D3 为0；连续无新增计数重置为0。
- **下一查询**：精确检索 `GroupKFold`／`leave-one-device-out` 与 `window selection`／`history length selection` 同现且选择发生在源域；精确检索 target burn-in／pilot threshold frozen prospective evaluation。

### Q-A4：DFM 失配鲁棒引用链

- **查询链**：BBSE→DFM 正式 Springer 题录→arXiv v2 全文→标签漂移污染、未知类与核均值几何条件。
- **结果**：DFM 证明 BBSE 是分布特征匹配的特例，并明确其低维输出特征没有一般未知类污染稳健性；高斯核 softRFFM 的优势要求污染表征与源类近似正交。
- **本轮新增 D2／D3**：A 新增 D2 一篇，D3 为0。
- **关键裁决**：DFM 提供失配边界与替代估计器，而不是可直接部署的诊断触发回退。PBC 仍须自行冻结可观测门、失败阈值和不依赖标签漂移的回退。
- **下一查询**：寻找把失配统计量显式接到“采用／拒绝先验校正”分支、并在独立目标后段冻结评价的工作。

## 十六、恢复检查点（2026-08-18 20:20，历史；已由第十七节更新）

- **完成比例**：约65%。
- **全文计数**：7篇独立工作、8份全文制品；6篇已完整落仓库，NIDES 官方全文已读但 raw 待人工。
- **新增 D2／D3**：A 新增 D2 1篇（İnan）；B 新增 D2 2篇（NIDES、王世谦等）；C 新增 D2 1篇（İnan）；D3 为0。
- **raw／wiki／Zotero**：6篇有 raw，6篇有 wiki，6篇有规范 Zotero 条目；所有 Zotero 条目无 PDF 子附件。
- **精确阻塞**：NIDES SRI PDF 端口超时；DFM 下载尚未形成有效 PDF；第二轮实体折外选窗与实体预算引用链未完。
- **下一步**：完成 DFM，接收 NIDES 人工原件，继续两组边界检索；不等待文献任务完成即可运行第四章快速实验。

## 十七、恢复检查点（2026-08-18 20:40）

- **完成比例**：约82%。
- **全文计数**：10篇独立工作、11份全文制品；9篇已形成 raw＋wiki＋Zotero 链，NIDES 官方52页全文已读但原始文件待人工。
- **新增 D2／D3**：本检查点新增 Haiba（A／B／C 均D2）、Slips（B为D2）、DFM（A为D2）；累计 A 有3篇D2，B有4篇D2，C有2篇D2；D3为0。
- **raw／wiki／Zotero**：本批新增3份 raw、3份 wiki、2个方向索引与3个规范题录；DFM `XPQH2ENC`、Haiba `A7W3F3TH` 无子项，Slips `G4VRGMXX` 只有说明笔记而无PDF。
- **最新裁决**：PBC 的“目标良性缓冲区＋分位阈值＋显式FAR预算”已有直接网络实体强近邻；DTEP 的“实体分组＋固定窗”和“主机窗＋多检测器后期融合”均已存在。尚可区分的是精确的信息与选择合同，不是这些宽泛构件。
- **精确阻塞**：仅 NIDES 原始 PDF／SHA／Zotero 链需人工补齐；DFM 与 MDPI 403 已通过合法开放替代入口关闭。
- **下一步**：执行两轮更窄的 OOF 选窗与冻结回退检索；由于本轮新增 D2，停止条件计数从0开始。实验不等待本任务完成。
