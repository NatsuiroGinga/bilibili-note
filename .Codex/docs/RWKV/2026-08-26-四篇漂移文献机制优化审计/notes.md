# 四篇漂移文献机制优化审计过程笔记

## 恢复入口

- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`
- 核心提交：`3fad1f87d44f803504ecaa804e835236e380f840`
- 研究契约：`.Codex/docs/RWKV/2026-08-25-第三章机制改造研究契约/`
- 证据输出：本目录 `证据矩阵.md` 与 `审计结论.md`

## 阶段一检查点

- 完成时间：2026-08-26。
- 核心文献目标：4 篇；全文回核目标：4/4。
- 构件近邻上限：4 篇。
- 核心裁决对象：`Lp + max` 多算子实体聚合、O11 逐流分数上的决策层因果前缀统计。
- 禁止升级：文献可试性不得写为本项目实验有效。
- Zotero：沿用既有材料登记的条目状态，本任务不重新导入，也不在未调用本地接口时声称已复核。

## 阶段二检查点：检索与收集

### 本地索引

- 规定入口：`uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`。
- 首次状态：索引存在，但因新增/修改来源而 `stale=true`；旧索引含论文笔记 `500` 篇。
- 增量重建：`built_at=2026-08-26T03:57:06.662285+00:00`，论文笔记 `504` 篇，总笔记 `1846`，向量 `38149` 个，模型 `intfloat/multilingual-e5-small@614241f...`，设备 `mps:0`。
- 复查：`stale=false`、`stale_reasons=[]`，索引 SHA-256 `6562fd7508d3534701c63c39c96d587f37439e220ae335d74ed506204e66ffa5`。
- 离线查询式：`concept drift encrypted malicious traffic aggregation causal prefix online score`，作用域 `paper`，模式 `hybrid`，`offline=true`。首位命中 MalMoE，第 3 位命中 Berruz，第 9 位命中 MADCAT；Wasswa 由冻结核心清单直接纳入，不按排名排除。
- 本轮未联网新增候选，也未调用 Zotero 本地接口；研究契约记录的 Zotero 键只视为既有状态，本轮不声称重新核验或写入。

### 核心 PDF 完整性

| 文献 | 原件路径 | 页数 | SHA-256 | 状态 |
| --- | --- | ---: | --- | --- |
| Roh et al., MADCAT | `raw/papers/attack-detection/2025-Roh-MADCAT-TTA-Malware-Concept-Drift.pdf` | 8 | `1ef1b99f9c7bf5da908f14be2f23bc211dd97ff9a8f7ceb270a92144be0e0eff` | 未加密、文本可抽取 |
| Wasswa & Lynar | `raw/papers/attack-detection/2025-Wasswa-IoT-Botnet-Latent-Space-Alignment-Drift.pdf` | 6 | `5d6d7e768ba7a16aaab41e577e173339e5c0ffa56e758238c525111aef296bf9` | 未加密、文本可抽取 |
| Berruz et al. | `raw/papers/attack-detection/2026-Berruz-Concept-Drift-Detection-Adaptive-Retraining.pdf` | 39 | `851ff060009a02077d9e445218897282c16826e4ad8ad0a333e6222e8f3b31bb` | 未加密、文本可抽取 |
| Tan et al., MalMoE | `raw/papers/attack-detection/encrypted/2026-Tan-MalMoE-Graph-Drift-MoE.pdf` | 10 | `01c932b849269518843873cd84992c1bb180f59c86ff49e116ed8673f677df00` | 未加密、文本可抽取 |

- 四篇共 `63` 个物理页，已逐页抽取到 `/tmp/four-drift-audit-20260826/<paper>-pNNN.txt`，临时文件不进入仓库。
- MalMoE 物理 p.8 已以 `160 ppi` 渲染并视觉核对表 II、表 III，排除文本列错位。

## 阶段三检查点：筛选与分类

| 文献 | PDF | 全文笔记 | 回核状态 |
| --- | --- | --- | --- |
| Tan et al., MalMoE, 2026 | 可读 | `wiki/papers/attack-detection/encrypted/2026-Tan-MalMoE图漂移专家混合检测.md` | 核心方法；同域多算子与门控直接近邻 |
| Wasswa et al., 潜空间对齐, 2025 | 可读 | `wiki/papers/attack-detection/2025-Wasswa-IoT僵尸网络潜空间对齐抗漂移.md` | 核心边界；表示对齐正交路线 |
| Roh et al., MADCAT, 2025 | 可读 | `wiki/papers/attack-detection/2025-Roh-MADCAT自监督测试时适应.md` | 核心边界；测试时训练竞争路线 |
| Berruz et al., 漂移检测与自适应重训, 2026 | 可读 | `wiki/papers/attack-detection/2026-Berruz-漂移检测触发自适应重训.md` | 核心边界；按批统计触发重训与评价设计 |
| Pevný & Somol, 2016 | 原件指针当前缺失 | `wiki/papers/methodology/2016-Pevny-神经网络形式化求解多示例问题.md` | 构件近邻；均值或最大池化选择、嵌入后聚合 |
| Ilse et al., 2018 | 原件指针当前缺失 | `wiki/papers/methodology/2018-Ilse-基于注意力的深度多示例学习.md` | 构件近邻；嵌入级聚合位置 |
| MIDAM, 2023 | 原件指针当前缺失 | `wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化.md` | 构件近邻；完整实体目标与小包非线性偏差 |
| ForkMerge, 2023 | 可读 | `wiki/papers/methodology/2023-Jiang-ForkMerge辅助任务负迁移.md` | 构件近邻；辅助更新过滤，只约束后续训练实验 |

### 纳入与边界

- 核心纳入 `4/4`，重复 `0`，缺失核心全文 `0`，仅摘要 `0`。
- 构件近邻纳入 `4/4`。Pevný、Ilse、MIDAM 只按既有全文笔记使用，不据此声称本轮重新查看其原件。
- MalMoE 是唯一直接同时涉及加密恶意流量、图漂移、实体/节点聚合和推理期路由的核心论文。
- Wasswa、MADCAT、Berruz 不因“未直接支持两个方向”而完全排除；它们作为放置层、因果性和最终测试隔离的边界证据。
- Berruz 的测试集预言机调参绝对数字从本项目基线和效果量级比较中排除，只保留方法流程与作者明确披露的相对关系。

## 阶段四逐篇全文记录

### Tan et al. 2026，MalMoE

- 物理 p.1：论文定义 `Drift 1` 为流统计漂移、`Drift 2` 为图规模漂移；明确写出 AVG 对图规模稳健、DEG 对流统计稳健，二者对另一类漂移敏感。
- 物理 p.3：AVG-DEG 直接拼接的两个失败理由是数值尺度偏置，以及任一漂移下拼接向量总有一部分发生漂移；其替代方案是按流硬选择较优专家，而不是把两算子直接并联后共同分类。
- 物理 p.4，式（1）－（5）：`h_avg` 为 IP 邻接流边特征均值，`h_deg` 为入出边计数；两个专家分别训练，分类任务仍是逐边/逐流二分类。
- 物理 p.5，式（6）－（10）：门控使用当前整张图上的 readout，最简实现为所有流嵌入的均值；门选择专家。它不是逐流分数的因果前缀统计，也未给出曝光序递推。
- 物理 p.6：两阶段训练先训专家后训门；作者明确说专家稳健性主要来自节点特征。HyperVision/NetVigil 阈值在测试集上最大化 `TPR-FPR`，仅作对基线有利的理论上界。
- 物理 p.8，表 II 视觉复核：`AVG F1 0.9710→0.4822` 是**合成数据集、无漂移列到 Drift 1（流统计漂移）列的下降**；`DEG F1 0.9817→0.2811` 是**无漂移列到 Drift 2（图规模漂移）列的下降**。两个箭头都表示退化，不是跨方法提升，也不是 Overall 列。
- 物理 p.8，表 II 同时显示：AVG 在 Drift 2 为 `0.8610`，DEG 在 Drift 1 为 `0.9630`；AVG-DEG 直接拼接 Overall F1=`0.7939`，低于 AVG-AUG `0.9112`、DEG-AUG `0.9252` 和 MalMoE `0.9444`。
- 初步等级：表格和公式事实为 `D1`；迁移到 `Lp + max` 是 `D3`，因为算子、任务粒度与组合方式均不同。

### Roh et al. 2025，MADCAT

- 物理 pp.2－3：机制是测试时训练；每个新样本被随机掩码，编码器用重建损失更新一步，再与冻结分类头完成检测。没有实体、池化或逐流分数前缀。
- 物理 p.3：2015－2018 数据按月分组，每月再分 `70%` 测试时训练与 `30%` 验证；原文未说明月内是否按时间排序，不能宣称严格因果。
- 物理 p.3，图 3 与正文：静态基线逐月退化，MADCAT 的 F1 更稳定；这只约束“固定模型任意跨度免适应”的正文措辞，不证明本项目方向有效。
- 物理 p.4：置信度分数只用于伪标签样本筛选/平衡，不作为最终告警的因果前缀统计。
- 初步等级：测试时训练流程为 `D1`；对 O11 分数层因果前缀只构成“未覆盖/不可据此支持”的边界。

### Wasswa & Lynar 2025，潜空间对齐

- 物理 pp.1－3：历史 VAE＋GAT 分类器一次训练；当前域另训 VAE 和 MLP 对齐器，只更新对齐模块。式（1）只匹配潜空间均值与标准差。
- 物理 p.3：预处理显式删除 `Timestamp`；方法没有实体聚合、曝光序或逐流分数前缀。
- 物理 p.4：召回率公式误写为 `TP/(TP+TN)`，且跨域对齐仅报告一个方向；绝对数字不作为本项目效果依据。
- 物理 p.5：作者自陈尚未集成漂移检测器，未来才研究何时更新对齐模型。
- 初步等级：表示层对齐路线为 `D1`；对两个目标方向均为正交边界，不构成机制支持。

### Berruz et al. 2026，自适应重训

- 物理 p.4：作者因恶意软件场景通常拿不到准确率、精确率、召回率和 F1 等反馈而选择无标签数据分布式漂移检测。这支持“在线量应无需目标标签”的设计约束，不指定量必须来自模型分数。
- 物理 pp.6－8：MK-Means 使用相邻重叠批的轮廓系数变化；OCSVM 使用离群/内点比；MMD 使用相邻批两样本检验。三者输入均为样本特征分布，不是分类器逐样本分数。
- 物理 pp.11－12：样本按时间戳从旧到新排序并切连续批，存在因果批序；但每个批是 `50` 个样本的块级统计，不是实体内逐流曝光前缀。
- 物理 pp.13－15，式（2）－（5）与算法 1：检测器的唯一动作是选择哪些批次重训分类器；最终样本告警打分方式不变。因此它属于训练流程层，不属于分数决策层。
- 物理 pp.16－17，式（6）：每个分类器在对应测试子集上直接调超参数；作者明确称这是预言机式上界而非真实部署。绝对准确率不得作为本项目基线。
- 初步等级：无标签、按时序批统计为 `D1`；迁移成 O11 逐流分数上的因果前缀是 `D3`，还缺输入量、实体键、更新公式与告警作用的直接证据。

## 查询与核验记录

下一检查点先核对四篇构件近邻对“聚合算子”“聚合位置”“完整实体目标”“训练更新过滤”的精确支持边界，再形成跨文献证据矩阵。
