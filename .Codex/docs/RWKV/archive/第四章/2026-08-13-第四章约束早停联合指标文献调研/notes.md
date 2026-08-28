# 调研笔记：第四章约束早停联合指标

## 恢复入口

- 任务计划：`task_plan.md`
- 路线总控：`.Codex/docs/RWKV/RWKV路线总控.md`
- 当前恢复卡：`.Codex/docs/RWKV/RWKV当前恢复卡.md`
- 会话交接：`.Codex/docs/RWKV/2026-08-13-会话交接文档.md`
- 更正台账：`.Codex/docs/RWKV/2026-08-13-实验结论更正台账.md`
- v2 脚本：`thesis/experiments/llm_probe/tools/ch4_v2.py`
- v2 原始日志：`thesis/experiments/llm_probe/runs/diagnostics/ch4-drift-v2/run.log`
- v2 聚合结果：`thesis/experiments/llm_probe/runs/diagnostics/ch4-drift-v2/ch4_drift_v2.json`

## 本地实验事实基线

### `ch4-drift-v2` 可用事实

- 源年度与目标年度决策单元统一为无向 `2-IP` 实体。
- 源年度按“是否含恶意流 × 实体流数分位”分层留出 `20%` 实体，只用留出区做阈值校准与混淆矩阵估计。
- 源留出阈值迁移：源留出 `FPR=0.0400, DR=0.9787`；迁移目标年后 `FPR=0.0153, DR=0.5505`；目标标签 oracle 在 `FPR=0.0400` 时 `DR=0.6157`。目标阈值与源阈值相差 `9.60×`，冻结迁移损失 `0.0652`。
- BBSE 使用目标年前 `10%` 无标签流前缀：前缀逐流先验 `0.0447008424`，全年逐流先验 `0.0257073138`。
- 九个源工作点中，`0.001/0.005/0.01/0.02/0.20/0.30` 六点出现 `q<FPR_s`，未经截断的先验估计为负；`0.05` 点对前缀真值相对误差 `4.54%`，`0.10` 点误差 `55.53%`，`0.50` 点虽未标记 `q<FPR_s`，截断估计仍为零、误差 `100%`。
- 因此可支持的最窄结论是：漂移问题存在；BBSE 在至少一个事后选出的工作点有信号；纯标签移位不在全工作点成立；无目标标签工作点选择仍未解决。
- 前缀分位数校准得到 `FPR=0.0614, DR=0.6529`，高检出来自多用误报预算；在 `FPR≤0.04` 合同下属于违约，而不是排序性能差。

### 不可使用的事实

- `runs/diagnostics/ch4-drift/` 下 v1 的全部数字与结论作废。
- v2 的 `pos_weight=18.9877` 与第三章 C11 的 `8.9438` 不同，v2 绝对指标不得与第三章横排。
- 目标标签 oracle 和事后最佳 BBSE 工作点只能用于诊断与评价，不能参与候选选择。

## 待建立的数值依据台账

| 数值／超参数 | 当前来源状态 | 外部依据待查 | 敏感性要求 | 允许用于选择的数据 |
| --- | --- | --- | --- | --- |
| `FPR≤4%` | v2 与第三章固定操作点；业务依据未知 | Dijk、LSPR、朱焱雷、FIRMBOUND、Prasse、Neyman–Pearson 文献 | 至少源预注册网格，目标仅一次报告 | 源年度标签；目标前缀仅无标签量 |
| 目标前缀比例 `10%` | v2 诊断设定 | 标签移位与在线风险控制文献 | 比例／流量双口径 | 源数据与无标签目标前缀 |
| BBSE 工作点九点网格 | v2 诊断网格 | BBSE 条件数、广义矩估计、工作点集成文献 | 源可识别性与目标无标签一致性门 | 源留出标签＋目标无标签预测 |
| 约束违约置信度 | 未冻结 | 保形风险控制、Neyman–Pearson、二项上界 | 置信水平敏感性 | 源校准或合法在线无标签代理；不得用目标标签调参 |
| 观察流量／告警时延权重 | 未冻结 | 早期分类、最优停止、成本敏感决策 | 报帕累托前沿，不事后选单点 | 源年度或外部业务成本 |

## 初步机制假设（尚未裁决）

候选不应直接“混合九个 BBSE 先验估计”，因为六个不可行估计暴露的是条件分布漂移，而非纯估计方差。更可检验的方向是：把每个源工作点视为一个矩条件／专家，仅使用源留出的可识别性、无标签目标前缀的可行性与跨前缀稳定性做资格筛选；对通过资格的工作点形成预注册混合，并对最终告警策略施加实体级误报率上置信界。该方向是否只是广义矩估计、分布鲁棒优化或保形风险控制的组合，须经全文查重后再决定。

## 查询记录

### 本地库盘点组 L1（2026-08-13）

- 查询方式：分别以 `lipton|bbse|label shift`、`conformal risk|nonexchangeable`、`firmbound|earliest|prasse|optimal stopping`、`neyman|pearson|fixed fpr`、`dijk|lspr|朱焱雷`、`selective|risk coverage|reject`、`nash|multi objective|pareto|distribution robust|cpo` 搜索 `raw/papers/` 与 `wiki/papers/`。
- 已定位本地核心原件：Lipton 2018 BBSE、Angelopoulos 2024 保形风险控制、Farinhas 2024 非交换保形风险控制、Ebihara 2025 FIRMBOUND、Prasse 2017 ECML、Tong 2018 Neyman–Pearson 分类、Geifman 2019 SelectiveNet、Achiam 2017 CPO、Redko 2019 JCPOT、Sagawa 2020 GroupDRO、Duchi–Namkoong 2021 分布鲁棒优化、Navon 2022 Nash-MTL、Shamsian 2023 AuxiNash、Dijk 2026、朱焱雷学位论文。
- 纳入理由：这些原件直接覆盖本任务的六类方法与三类博弈判别；先精读，随后联网查重近年同构机制。
- 初步排除：一般网络安全 Stackelberg／Nash 防御论文不直接处理无标签工作点选择、固定误报预算或外生轨迹早停，只在博弈概念边界需要时抽样核验。
- 下一步：逐页核验各原件的假设、目标、保证、工作点与局限，尤其搜索 `FPR / false positive / 0.04 / 4% / delay / coverage / constraint`。

### `FPR≤4%` 依据追溯组 F1（2026-08-13）

- Gehri 等 2023 原件：`raw/papers/datasets/locked-shields-related/2023-Gehri-Towards-Generalizing-ML-C2-Detection-CyCon.pdf`。
- 全文位置：第 6.2 节，第 12–14 页，尤其第 13 页。作者把“检测主机”定义为至少涉及 `n={1,5,10,100}` 条预测恶意流的 IP，并在 `n=1` 的结果叙述中报告各年主机级 `FPR<4%`；结论另报告恶意通信超过 100 次的主机 `DR>90%` 且 `FPR<4%`。
- 证据属性裁决：**这是模型在既定 `n` 下的事后报告结果，不是作者预先指定的 `4%` 评价点，也不是部署时要求满足的操作约束。** 原文没有给出告警处理容量、成本函数、法规或“超过 4% 会淹没安全运营中心”的依据。
- 可迁移边界：该结果可以支持把 `4%` 当作与同源 Locked Shields 主机级研究对比的经验工作点；不能支持把它写成普适安全上限或业务可承受阈值。
- Dijk 2026 原件：`raw/papers/methodology/2026-Dijk-Learning-from-the-Past-Guiding-the-Future.pdf`。全文以平均精确率为不平衡数据主指标；出现的 `0.04` 是图表数值或平均精确率差异，不是固定误报率工作点。**不支持 `4%`。**
- 朱焱雷学位论文原件：`raw/` 中既有论文 PDF。全文只出现定性“误报极低”等表述，没有 `FPR≤4%` 操作合同。**不支持 `4%`。**
- FIRMBOUND 原件：`raw/papers/methodology/2025-Ebihara-FIRMBOUND.pdf`。正文把误分类惩罚与采样成本合为贝叶斯风险，并通过后向递推求早停；附录讨论序贯概率比检验的期望误报／漏报上界，但没有给出 `4%`。**支持早停成本建模，不支持该数值。**
- Prasse 等 2017 原件：`raw/papers/methodology/multiple-instance/2017-Prasse-Malware-Detection-Encrypted-Network-Traffic-Neural-Networks-ECML.pdf`。作者指出即使误报率看似较小，在良性基数巨大时绝对误报告警仍可能远多于恶意检测，并报告精确率、固定精确率召回、误报率和检测时间；没有采用 `4%`。**支持同时报告绝对误报负担与时延，不支持该数值。**
- 当前结论：项目的 `4%` 应改称“预注册主工作点”，其外部来源是同源数据上的经验可比性，而非业务安全标准。

### 约束博弈与多目标议价本地全文组 G1（2026-08-13）

- Cotter 等 2019，官方 PMLR 页面：`https://proceedings.mlr.press/v98/cotter19a.html`；官方 PDF 已保存为 `raw/papers/methodology/2019-Cotter-Two-Player-Games-Constrained-Optimization.pdf`，SHA-256 为 `c3a8f4728e10dc41a1463c1582bcf329770d87c71b2e552160506a13a165ca1f`。
- Cotter 全文第 1–4 节：普通拉格朗日可解释为模型玩家最小化目标、乘子玩家最大化约束违约的二人零和博弈；代理拉格朗日允许模型玩家用可微代理约束更新，而乘子玩家仍按原始、可不连续的比例／率约束更新。均衡输出通常是随机分类器；后处理可将支持集压到至多 `m+1` 个模型，其中 `m` 为约束数。
- 对本章的占用：把“检测收益对抗误报率／时延约束”命名为零和博弈，或输出若干阈值策略的随机混合，本身已被拉格朗日／代理拉格朗日理论覆盖；除非目标数据资格集、实体前缀矩条件或失败回退机制有实质改造，否则没有新的博弈论贡献。
- Achiam 等 2017 CPO 全文：约束马尔可夫决策过程内直接求奖励最大且成本约束满足的策略，并给出每次更新近似约束满足的界。冻结轨迹上的阈值／停时选择不含动作影响未来状态，直接套 CPO 会增加与问题无关的强化学习外壳。
- Navon 等 2022 Nash-MTL 全文：纳什议价解决多个训练任务梯度方向／尺度冲突，求对任务损失梯度的比例公平联合更新并收敛到帕累托驻点。它没有把误报率当作必须满足的硬约束，也不解决无标签目标年度的阈值可识别性。
- 初步裁决：平均精确率、检出率与时延直接做纳什议价，会把硬误报约束降格为可交换效用，而且这些评价指标不是现成的同一训练参数上的平滑任务损失。除非重新定义多任务训练合同并证明每项梯度含义，该路线不适合作为最小候选。

### 早期分类直接近邻查询组 E1（2026-08-13）

- 查询对象：Qiu、Zhao、Zheng，*Optimizing Detection Time and Specificity: Early Classification of Time Series with Sensitivity Constraint*。
- 正式题录页：`https://neurips.cc/virtual/2024/98926`；OpenReview 论坛：`https://openreview.net/forum?id=PXVqsZlxEa`。
- 搜索索引与正式题录可确认其问题直接联合早期检测时间、特异度／误报和灵敏度约束，并以帕累托／Neyman–Pearson 形式求解；这已占用“把早分类写成检出约束下的误报－成本多目标优化”这一宽泛创新表述。
- 全文状态：官方 OpenReview PDF 与 API 在当前环境均返回 `403`；按仓库证据规则，公式、命题和实验细节暂不用于最终强论断。已登记人工下载，待取得原件后补页码级核验。
- 与候选关系：即便基础公式被该文占用，针对 LSPR 的“跨年度、实体级、目标标签不可见、多个 BBSE 矩条件大面积失效时的资格化与失败回退”仍可能构成实质改造；必须用原方法、仅加资格门、完整改造三档消融验证，不能声称一般早期分类框架首创。

## 缺失全文清单

- Qiu、Zhao、Zheng，*Optimizing Detection Time and Specificity: Early Classification of Time Series with Sensitivity Constraint*，NeurIPS 2024 Workshop。人工动作：从 `https://openreview.net/forum?id=PXVqsZlxEa` 下载官方 PDF，保存到 `raw/papers/methodology/`，随后核验问题公式、命题 2.1、约束方向、训练／评价数据选择和实验工作点。当前阻塞：OpenReview PDF 与公开 API 均返回 `403`，本机没有可用浏览器会话。

## Zotero 状态

- 本机 Zotero `9.0.6`，本地 API 与连接器均正常，API 版本 `3`。
- 已命中：Angelopoulos 保形风险控制、Farinhas 非交换保形风险控制、Almeida 2025 协变量漂移高概率风险控制、Tong 2018 Neyman–Pearson 分类、Geifman 2019 SelectiveNet。
- 精确题名查询暂未命中：BBSE、FIRMBOUND、Nash-MTL；可能是条目题名或同步差异，后续以作者／arXiv 标识再查。
- 本轮尚未写入 Zotero；只有联网查重新增且确认有用的论文才按稳定标识导入并核验附件。

## 下一检查点

1. 全文核验 BBSE、Neyman–Pearson、保形风险控制和非交换风险控制的可识别性／保证边界。
2. 全文核验 Cotter、分布鲁棒优化、GroupDRO、Nash-MTL 和早停近邻，形成三类博弈比较表。
3. 检索多工作点标签移位的矩估计／集成近邻，判断“无标签工作点对手”是已有估计器换名还是可形成 LSPR 特有实质改造。
4. 将 Cotter 原件补入结构化笔记、方向索引与 Zotero；Qiu 保持人工下载阻塞，不以摘要替代全文。
