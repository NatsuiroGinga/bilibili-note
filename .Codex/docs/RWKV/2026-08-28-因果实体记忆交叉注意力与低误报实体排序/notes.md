# 调研笔记：因果实体记忆交叉注意力与低误报实体排序

- 日期：2026-08-28
- 代理：`ft_causal_memory_lowfpr_theory_sol_max`
- 模型：`gpt-5.6-sol`
- 推理强度：`max`
- 研究状态：设计可行／实验待证

## 一、任务边界与当前裁决

- 章级机制固定为结构级“因果实体记忆交叉注意力”和训练级“低误报实体排序训练”。
- 数值 tokenizer、历史 token、角色或类型嵌入只属于 FT 骨干适配或机制一实现细节，不单列为创新机制。
- 普通实体 AP 选轮和 C00 双选轮只属于源年选择协议，不是模型或训练机制。
- 本任务不修改代码、配置、恢复卡、研究问题卡、正文、`raw/`、`wiki/`、Zotero 或服务器。
- 文献只证明构件来源、直接近邻和可试性；没有 LSPR23 共同预算实验时，任何效果与原创性结论都不得高于“实验待证”。

## 二、工程病灶与源码证据

| 病灶 | 已核事实 | 证据 |
| --- | --- | --- |
| 裸 FT 对实体过去零感知 | 字段注意力只在一条流的 `83+1` 个 Token 内执行；训练前把 `N×T` 展平为 `N·T` 条独立流。`E23/T23` 只用于源年切分，不进入裸 FT 前向 | `thesis/experiments/llm_probe/tools/ch3_ft_transformer_field_token_protocol_a.py:2423-2456,3003-3023` |
| 旧 CPA 含当前流 | `context32=torch.cumsum(representation32)/counts` 没有右移，时刻 `t` 的上下文包含 `representation_t`；随后与当前表示拼接融合 | 同工具 `:2460-2480` |
| 旧 CPA 跨片段断裂 | 每次只对独立采样的长度 128 张量做 `cumsum`，调用方没有读取上一片段状态；严格过去 MLP 虽在片内右移，仍没有跨片段 carry | 同工具 `:3484-3492`；`tools/ch3_full_mlp_strict_past_cpa_protocol_a_q0.py:212-223` |
| 逐流目标与实体部署错位 | 训练主损失为逐流 BCE，原 FT 选轮指标为源年逐流 AP；应用主裁决同时要求实体 AP、实际整数 FP 预算完整曲线和首次告警曲线 | FT 工具 `:3531-3543`；配置 `configs/ch3-ft-transformer-field-token-protocol-a-seed42-v1.json:465`；`.Codex/docs/RWKV/2026-08-20-可微神经骨干替代XGBoost目标合同.md:126-144` |
| 固定辅助权重可能夺权 | 旧配置将 `auxiliary_loss_weight` 固定为 `1.0`；只有 ELP 格把序列级 BCE 加到逐流 BCE，梯度共同进入骨干、融合层和 `p_log` | 配置 `:459-460`；FT 工具 `:3497-3502,3527-3543` |
| 概率空间饱和会破坏低 FPR 排序 | 既有校准事故已确认 FP32 `sigmoid` 可把高 logit 压成精确 `1.0`，导致大并列块改变实际 FP/FPR | `.Codex/docs/RWKV/2026-08-27-D0验收与D1D2病灶诊断报告.md:275-281` |

### 统一接口的既有最小合同

既有审计已提出 `entity-segment-sequence/v1`：

- 模型输入面：`flow_indices`、`valid_mask`、`entity_id`；
- 状态链接面：`segment_ordinal`、`previous_segment_row`、`is_entity_start`、`role_id`；
- 时间与溯源面：逐流 `available_ns`、稳定 `source_record_id`；
- 收据面：模式、来源、顺序和语义哈希。

证据位于 `.Codex/docs/RWKV/2026-08-21-RWKV跨片段实体连续状态候选/notes.md:115-126`。现有 `I23/M23/E23/T23` 可作底层来源，但不能证明 `T23` 就是 83 个字段全部可用的部署时刻，也不含上一片段指针、角色边界和稳定原始记录标识。因此仅凭这四个数组不得宣称部署严格因果。

完整训练实体袋还需要一个只供调度器使用、禁止送入模型的控制面清单：同一切分内的实体到片段行列表、实体训练标签、片段覆盖哈希和完整性收据。最终实体长度、剩余片段数和未来时间不得成为模型张量。

## 三、本地混合检索检查点

### 3.1 索引状态

- 入口：`uv run --project scripts/literature_search --locked python -m scripts.literature_search`。
- 2026-08-28 03:25 UTC 重建后：`522` 篇论文笔记、`39,896` 个文本块、向量设备 `mps:0`，索引 SHA256 为 `2a3119f0231947059abed985e53bd1a3ef6bacdd2068de5b4133f7a483a841ba`。
- 并发代理随后修改过程文档，状态再次显示 `source_changed`；核对 `collection_diffs.papers` 为新增 `0`、修改 `0`、删除 `0`，论文集合仍为 `522` 篇。部分后续查询因此被 CLI 拒绝，但已成功完成的 `paper/hybrid` 查询有效。

### 3.2 查询与命中

| 查询式 | 作用域／模式 | 关键命中 | 处理 |
| --- | --- | --- | --- |
| `实体历史 严格过去 时间有序 多示例学习 实体袋 注意力聚合` | `paper/hybrid` | Ilse 2018、TabReD 2025、Pevný 2016 两篇、MIDAM 2023 | 回读结构化全文笔记与原始 PDF |
| `低误报 部分AUC pAUC 排序损失 top negative 实际FPR` | `paper/hybrid` | MIDAM 2023、安全机器学习低 FPR 方法论、ForkMerge 2023 | 追加读取 Narasimhan 2013、Zhu 2022 与 Hu 2023 原始 PDF／官方 PDF |
| `纽曼皮尔逊 分类 类型一错误 低假阳性率 约束 分类器` | `paper/hybrid` | Tong 2018、Wang 2024、Vovk 2012、CBAM 2021 | Tong 作为源域低 FPR 校准强基线，不作为训练损失 |
| `多任务学习 梯度冲突 辅助损失 权重 梯度投影 负迁移` | `paper/hybrid` | 并发索引变更使该次 CLI 拒绝；精确 `rg` 命中 ForkMerge、AuxiNash、Recon | 回读全文笔记，并在线核验 PCGrad 与 GradNorm 官方 PDF |
| `MalMoE 上下文门控 图漂移 专家混合 加密流量` | `paper/hybrid` | 并发索引变更使该次 CLI 拒绝；精确 `rg` 命中 MalMoE 全文笔记 | 回读 10 页原始 PDF 与全文笔记 |

五篇文献审计代理随后扩展了顺序表格近邻：TabFormer、FATA-Trans、Fieldy、Stein 等 2024 自回归表格 Transformer；低 FPR 近邻扩展到 Zhu 2022 深度 pAUC 与 Hu 2023 多示例 TPAUC。主代理已用 arXiv、ACM、PMLR、NeurIPS 官方页交叉核验题录和关键结论。

## 四、全文证据台账

证据等级定义：`E3` 为本地原始 PDF 与结构化全文笔记均可回溯；`E2` 为官方论文页和官方 PDF 已核、尚未写入本地全文笔记；`E1` 只允许候选发现。本任务只用 `E3/E2` 支撑承重论断。

| 文献 | 等级与原件 | 承重位置 | 可支持 | 不能支持 |
| --- | --- | --- | --- | --- |
| Gorishniy 等 2021，FT-Transformer | `E3`；`raw/papers/2106.11959v5.pdf`，SHA256 `f2faa3...63478d` | 物理第 4 页，FT 数值／类别 token 与 `[CLS]` | FT 对当前样本字段做 token 化和字段内自注意力 | 实体历史、跨片段状态、实体 AP、低 FPR |
| Huang 等 2020，TabTransformer | `E3`；`raw/papers/2012.06678v1.pdf` | 物理第 2-3 页公式（1）（2） | 当前行类别列的上下文化嵌入 | 数值全字段 FT、实体历史或因果前缀 |
| Gorishniy 等 2022，数值特征嵌入 | `E3`；`raw/papers/methodology/2022-Gorishniy-On-Embeddings-Numerical-Features-Tabular.pdf`，SHA256 `22b976...a0d8` | 第 3-5 页公式（1）（2） | PLE／周期嵌入及逐特征独立编码 | 把 tokenizer 原样替换称为章级创新；实体时序机制 |
| Rubachev 等 2025，TabReD | `E3`；`raw/papers/methodology/2025-Rubachev-TabReD-Tabular-Benchmark-Pitfalls.pdf` | 第 16-17 页 | 历史聚合量作为普通表格列已是工业常态 | “首次使用实体历史特征” |
| Padhi 等 2021，TabFormer | `E2`；[arXiv:2011.01843](https://arxiv.org/abs/2011.01843) 与作者代码 | 物理第 2 页公式（1）、图 2，第 3 页表 1 | 同一用户连续行的字段层与序列层 Transformer | 全窗口双向 TabBERT 等于当前 query 读取严格过去只读记忆 |
| Zhang 等 2023，FATA-Trans | `E2`；[ACM DOI](https://doi.org/10.1145/3583780.3614879) 与作者 PDF | 第 3-5 页公式（1）-（10），第 6-8 页 | 同 ID 顺序窗口、静态／动态字段与时间感知表示 | 历史静态量逐时刻严格前缀已获证明；独立 K/V 记忆 |
| Azorin 等 2024，Fieldy | `E2`；[arXiv:2406.15327](https://arxiv.org/abs/2406.15327) | 第 3-6 页图 2、表 3-4 | 行向、列向细粒度时序表格注意力 | 单向因果实体记忆；当前流 FT 保持 84 Token 的结构 |
| Stein 等 2024，自回归表格 Transformer | `E2`；[arXiv:2410.10648v3](https://arxiv.org/abs/2410.10648) | 第 4-8 页公式（1）（2）、表 1 | 按实体分组、时间排序和因果语言模型 | “首次因果实体历史 Transformer”；FT 字段 query 对独立记忆的差量 |
| Dai 等 2019，Transformer-XL | `E2`；[ACL Anthology](https://aclanthology.org/P19-1285/) 与官方 PDF | 物理第 3-4 页，式中 `SG(memory)` | 跨片段缓存过去隐藏状态、当前段查询、跨段截断梯度 | 按实体隔离的 FT 字段交叉注意力；低误报目标 |
| Ilse 等 2018，注意力 MIL | `E3`；`raw/papers/methodology/multiple-instance/2018-Ilse-Attention-Deep-Multiple-Instance-Learning.pdf`，SHA256 `9da16d...5b199` | 第 2-4 页公式（7）-（9） | 袋级置换不变聚合和门控注意力 | 有序因果实体链、跨片段恢复、低 FPR |
| Zhu 等 2023，MIDAM | `E3`；`raw/papers/methodology/multiple-instance/2023-Zhu-MIDAM-Stochastic-Pooling-ICML.pdf`，SHA256 `3b0b6d...e87` | 第 3-6 页公式（1）-（8）、算法 1 | 大袋随机子包代入非线性池化会有偏；需状态跟踪或偏差边界 | 部分 AUC、实际整数 FP 预算、严格因果实体链 |
| Narasimhan 与 Agarwal 2013，pAUC | `E3`；`raw/papers/methodology/2013-Narasimhan-Partial-AUC.pdf`，SHA256 `3181ad...51b` | 第 1-5 页，经验 pAUC 与 `[0,β]` 最高分负例 | 左端 ROC／top-negative 排序目标与全 AUC 不等价 | 深度实体袋、RankNet softplus、跨片段状态 |
| Zhu 等 2022，When AUC Meets DRO | `E2`；[PMLR 官方页](https://proceedings.mlr.press/v162/zhu22g.html) 与 PDF | 第 3-4 页公式（5）-（10），第 8 页训练协议 | CVaR 精确 top-negative pAUC、KL 平滑近似、随机负例的无偏子梯度；CE 预训后 pAUC 微调 | “深度 pAUC”或 top-negative 本身是本课题创新；逐流 BCE 等权联合有原文先例 |
| Hu 等 2023，NSWC FCCO | `E2`；[NeurIPS 官方页](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1160792eab11de2bbaf9e71fce191e8c-Abstract-Conference.html) 与 PDF | 第 8-9 页公式（8）（9）、表 2 | 多示例袋、均值池化与两向 pAUC 已直接组合 | “实体袋+pAUC”本身具有新颖性；严格过去 FT 部署分数 |
| Burges 等 2005，RankNet | `E2`；[ICML 官方 PDF](https://icml.cc/Conferences/2005/proceedings/papers/012_LearningToRank_BurgesEtAl.pdf) | 第 2 页公式（1）-（3） | 成对逻辑斯蒂排序损失 `log(1+exp(score_diff))` | pAUC top-negative 选择、实体袋或实际 FP 保证 |
| Tong 等 2018，NP 分类 | `E3`；`raw/papers/methodology/2018-Tong-Neyman-Pearson-Classification.pdf`，SHA256 `ff679e...66e3` | 第 2-4 页命题 1、算法 1 | 独立保留负例的次序统计阈值与源分布类型一错误控制 | 目标年同保证、可微训练目标、排序改善 |
| Yu 等 2020，PCGrad | `E2`；[NeurIPS 官方页](https://proceedings.neurips.cc/paper/2020/hash/3fe78a8acf5fda99de95303940a2420c-Abstract.html) 与 PDF | 第 2-3 页 | 冲突梯度法向投影；梯度量级差与高曲率共同导致干扰 | 主任务天然优先、验证泛化不退化 |
| Chen 等 2018，GradNorm | `E2`；[PMLR 官方页](https://proceedings.mlr.press/v80/chen18a.html) 与 PDF | 第 2-3 页公式（1） | 直接控制任务梯度量级 | 无超参数的主任务保护；低 FPR 或实体袋 |
| Jiang 等 2023，ForkMerge | `E3`；`raw/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移.pdf`，SHA256 `597e00...9de` | 第 3-6 页公式（5）-（8）、算法 1 | 梯度夹角不足以判断负迁移；主验证性能可过滤辅助更新 | 本项目一阶投影必然防止泛化退化；低成本 |
| Shamsian 等 2023，AuxiNash | `E3`；`raw/papers/game/2023_Shamsian_Auxiliary_Learning_as_an_Asymmetric_Bargaining_Game.pdf` | 第 4-6 页主张 4.1、命题 4.2 | 主任务与辅助任务应非对称分配训练权力 | 本项目提出的投影与范数上限公式已由原文给出 |
| Tan 等 2026，MalMoE | `E3`；`raw/papers/attack-detection/encrypted/2026-Tan-MalMoE-Graph-Drift-MoE.pdf`，SHA256 `01c932...df00` | 第 3-6 页公式（1）-（10） | 加密流量中上下文聚合、图级门控和硬专家选择是可行构件 | 当前 30 秒图上下文等于严格过去实体记忆；FT 结构或低 FPR 排序 |

## 五、检索综合与边界

1. “因果实体历史 Transformer”大类已被 Stein 等自回归表格 Transformer 占用；“顺序表格跨行注意力”又有 TabFormer、FATA-Trans 和 Fieldy。因此机制一不能声称首次建模实体历史，只能主张待验证的 FT 专属差量：保留当前流 84 Token 字段自注意力，以当前字段表示为 query，只读同实体严格 `t^-` 记忆的 K/V，经零门可退化残差后预测，并跨片段恢复。
2. “深度 pAUC”“top-negative”“实体袋+pAUC”分别被 Zhu 2022 和 Hu 2023 直接占用。因此机制二的差量只能是 LSPR 任务化组合：完整因果实体分数、等实体训练测度、来自冻结实际整数 FP 预算的多预算 CVaR，以及主任务优先的受控联合梯度。
3. tokenizer、普通历史列、MIL 注意力、Transformer-XL 递归、RankNet、PCGrad、GradNorm、ForkMerge 和 NP 校准均已发表。论文必须用“原组件→任务病灶→我方改造→差量消融”证明必要性，不能把拼接本身写成原创。
4. 截至当前检索，没有全文证据直接给出两个章级机制的完整同构组合；这只说明当前范围内未定位。不得写成“首次”“唯一”或“已证明原创”。

## 六、尚未冻结的数值与工程阻塞

- 记忆槽数 `R`：无直接文献精确值，也没有本机 MPS／服务器 CUDA 的状态内存实测；必须由 LSPR23 实体长度诊断和资源收据冻结。
- 完整实体袋批量：现有 FT 有效批为 64 个序列；改成完整实体袋会改变批单位和数据呈现，必须为四格共同重设并增加原 C00 采样器控制，不能静默沿用。
- 正式随机种子数与置信水平：现有单种子 `seed42` 只适合筛选；正式数量须由 LSPR23 方差或功效分析冻结，不能引用快照中的 `1×SE` 作为硬门。
- NP 置信参数：Tong 的 `α/δ` 是方法参数；若进入对照，须从既有告警合同和源负实体规模推导，不能默认抄 `0.05`。
- CVaR 的每预算阈值状态、实体袋吞吐和双梯度反向成本需本机真实数据资源探测；文献的图像批量和 FPR 网格不得搬用。

## 七、Zotero 与写回状态

- 本任务未读取、写入或修改 Zotero。
- FT 原论文已有本地 Zotero 键 `N4MRAEZF`；其他 Zotero 状态只沿用既有全文笔记记录，不作本轮新增事实。
- 本任务未新建或修改任何 `raw/`、`wiki/` 条目；主仓库中存在但当前工作树尚未同步的原件只按绝对路径只读核验。
