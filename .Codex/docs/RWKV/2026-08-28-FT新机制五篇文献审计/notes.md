# 过程笔记：FT-Transformer 新机制全文与饱和检索审计

## 检查点 0：任务合同

- 预期决策：判定既有组件、协议修复与可形成“朱式改造”的 FT 专属机制，最终推荐两个主候选、两个备选与联合算法。
- 核心纳入：用户给定五篇原始 PDF；扩展纳入与数值嵌入、实体/时间历史、多实例学习、可微实体 AP/排序、漂移感知 tokenizer、因果前缀 token、KAN/PLR 改造直接相关的全文或官方源码。
- 排除标准：仅摘要主张、二手转述、未核页码数字、未公开实现的代码细节、只因“可能相关”而扩张的外围论文。
- 证据等级：`L1` 为本轮回到原 PDF 页码或官方源码核验；`L2` 为既有结构化全文笔记但本轮未逐页复核；`L3` 为题录或摘要候选；`L4` 为无法取得或无法解析全文。
- Zotero 状态：只记录实测状态；未调用时写“未操作”，不声称已导入。

## 查询记录

### 本地索引状态

- 初次直接使用系统 `python3` 失败：`ModuleNotFoundError: No module named 'yaml'`。按仓库规则改用 `uv run --project scripts/literature_search --locked`。
- 重建后：构建时间 `2026-08-28T02:55:46.128006+00:00`，论文笔记 `522` 篇，全文块 `39,756` 个，向量模型 `intfloat/multilingual-e5-small`，设备 `mps:0`，`stale=false`。
- 索引 SHA256：`22d499082f4a0adbd931650777b284726b13959916baeddbca5b07eb53c19c0d`。

### 本地混合查询第一组

作用域 `local`，实际返回论文集合；模式 `hybrid`；每式最多 10 项。

1. `FT-Transformer 实体历史 严格因果 前缀统计 字段 token 表格 Transformer`
2. `实体级 average precision 选轮 early stopping 可微 AP 排序 低误报 预算 校准`
3. `FT-Transformer 数值特征嵌入 PLR 周期 分段线性 KAN 矩阵驱动 tokenizer`
4. `分布漂移 感知 tokenizer 时间表格 entity history grouped multi-instance learning`

关键命中：

- `2022-Gorishniy-表格深度学习数值特征嵌入.md`：PLR、周期、分段线性与数值特征 embedding 的直接已占用边界；该工作只替换既有标量表示，不含历史、实体或因果前缀。
- `2025-Rubachev-TabReD工业级时间切分表格基准.md`：实体历史聚合作为普通表格列已非新事物；候选必须在角色化 token、严格过去状态和部署目标上给出差量。
- `2016-Pevny-神经网络形式化求解多示例问题.md`：实体可视为实例袋的构件证据，但不含 FT、加密流量、跨年度或低误报预算。
- 本地检索尚未命中“严格过去实体状态 token + FT”或“实体 AP/低 FPR 可微目标 + FT”的直接论文，形成扩展检索的两个主要缺口。

### 本地混合查询第二组

首次携带 `--no-auto-build` 查询时，索引因本任务文档和并行代理新增文档再次变旧，命令按门禁拒绝执行。重建后索引包含 522 篇论文笔记、39,823 个全文块，SHA256 为 `60afc85c6e3c2256839a6cdddaaaa4f3b9a294480574a6da16816a0cc7cb5d4d`。

查询式：

1. `causal prefix representation tabular transformer entity temporal history token`
2. `deep multiple instance learning transformer tabular bag level differentiable ranking`
3. `partial AUC optimization low false positive differentiable ranking neural network`
4. `distribution shift adaptive numerical embedding tokenizer tabular transformer`

关键命中：SAINT 行间注意力、TabR 检索增强、Ilse 注意力多示例学习、SOAP 直接 AP、MIDAM 多示例 AUC、大小不变对象损失、Tong 纽曼—皮尔逊阈值。它们分别占用跨行信息、检索、袋级池化、AP、AUC、等对象测度和低误报校准构件。

### 联网检索与饱和停止

只把 arXiv、PMLR、NeurIPS、ACM/IEEE 作者原件和官方 GitHub 当作技术证据。Google Scholar CLI 已安装，但本轮因无认证 Cookie 拒绝运行；没有用记忆补题录。

产生新直接近邻的查询组：

- `TabFormer tabular time series transformer transaction history`：发现 TabFormer。
- `differentiable average precision loss partial AUC low false positive deep learning`：确认 SOAP、深度 pAUC-DRO。
- `transformer entity memory cross attention transaction fraud tabular`：发现 FATA-Trans、Fieldy、STEP。
- `multi-instance partial AUC deep learning`：发现 NeurIPS 2023 已直接实现多示例双向部分 AUC。

达到饱和的最后两组：

1. `current event query past events cross-attention tabular`、`cross-attention entity history tabular transformer`、`online causal tabular sequence transformer memory bank`、`low false positive temporal multi-instance partial AUC`。
2. `prefix-consistent entity ranking false positive`、`current record cross-attention historical records tabular`、`entity-uniform false positive rate optimization sequence`、`causal prefix multi-instance partial AUC`。

这两组均未发现同时覆盖以下任一精确差量的直接论文：

- FT 当前流 `[CLS]` 单向查询严格 `t^-` 实体记忆，历史只能作 K/V，预测后才更新记忆；
- 以同一因果前缀部署分数为单位，执行实体均匀、源年冻结低误报预算的排序训练。

### Zotero 状态

- 本地 API 偏好已启用，但 Zotero Desktop 未运行，`127.0.0.1:23119` 拒绝连接；本轮未重启应用、未导入新条目。
- 既有条目：FT 原论文 `N4MRAEZF`、SOAP `MHNH9QBM`、MIDAM `N3WQX553`、Ilse 注意力 MIL 与其他既有笔记按原记录保留。
- 六篇新增强近邻统一标记“全文已归档，Zotero 未操作”，不得声称已同步。

## 原件核验台账

| 原件 | 纠正后题名与版本 | 页数 | 文本状态 | 既有全文笔记 | 本轮状态 |
| --- | --- | ---: | --- | --- | --- |
| `2012.06678v1.pdf` | *TabTransformer: Tabular Data Modeling Using Contextual Embeddings*，arXiv:2012.06678v1 | 17 | 可提取，已按页拆分 | 无 | `L1` 完成 |
| `2106.11959v5.pdf` | *Revisiting Deep Learning Models for Tabular Data*，arXiv:2106.11959v5；NeurIPS 2021 | 25 | 可提取，已按页拆分 | `wiki/papers/methodology/2021-Gorishniy-表格数据深度学习模型再审视.md` | `L1` 完成 |
| `3712285.3759853.pdf` | *FT-Transformer: Resilient and Reliable Transformer with End-to-End Fault Tolerant Attention*，SC 2025，DOI:10.1145/3712285.3759853 | 14 | 可提取，已按页拆分 | 无 | `L1` 完成；同名碰撞排除 |
| `electronics-15-02516.pdf` | *FT-Transformer-Based IoT Network Attack Detection and Cross-Dataset Generalization Analysis*，Electronics 2026, 15, 2516，DOI:10.3390/electronics15122516 | 31 | 可提取，已按页拆分 | 无 | `L1` 完成 |
| `Enhancing_FT-Transformer_With_a_Matrn-Driven_Kolmogorov-Arnold_Feature_Tokenizer_for_Tabular_Data-Based_In-Bed_Posture_Classification.pdf` | *Enhancing FT-Transformer With a Matérn-Driven Kolmogorov-Arnold Feature Tokenizer for Tabular Data-Based In-Bed Posture Classification*，IEEE Access 2025，DOI:10.1109/ACCESS.2025.3586365 | 15 | 可提取，已按页拆分 | 无 | `L1` 完成；文件名 `Matrn` 为重音字符丢失 |

## 全文证据摘记

### 论文一：TabTransformer

- 物理第 2–3 页公式（1）只把类别特征做列标识与取值 embedding，再经 Transformer 上下文化；连续特征 `xcont` 不进入 Transformer，而是与上下文化类别 embedding 拼接后送入 MLP。它不是 FT 的全字段 tokenizer，也没有数值 token、实体历史或时间前缀。
- 物理第 3 页公式（2）是标准自注意力；任务为 15 个公开二分类数据集，65/15/20 切分、五折、AUC、每折 20 次超参搜索（物理第 3–4 页）。
- 表 1 显示移除 Transformer 的 MLP 对照；15 个数据集中 14 个提升，平均 AUC 增益 1.0 点（物理第 4 页）。附录表 5–7 消融列 embedding、预训练替换比例与动态/静态替换（物理第 10–11 页）。
- 物理第 10 页称实现与精确超参数在代码和数据补充材料中，但 PDF 未给稳定仓库 URL；本轮尚未核到官方公开源码。
- 对本课题：只提供“字段身份 embedding 和字段间注意力”的基础构件。不能支持 M-A、M-B 或 M-E，也不能证明历史统计成为 token 后有效。

### 论文二：Revisiting Deep Learning Models for Tabular Data

- 物理第 4 页把 FT 明确定义为 `Feature Tokenizer + Transformer`。数值 token 为 `T_j=b_j+x_jW_j`，类别 token 为 `T_j=b_j+e_j^TW_j`，随后拼入 `[CLS]` 并经多层 Transformer；这确立了原生线性数值 tokenizer 的直接边界。
- 11 个公开表格数据集同时覆盖分类与回归，训练/验证/测试严格分离；验证集用于早停和调参，测试集只作最终评价（物理第 3、5–6 页）。最终每个调优配置跑 15 个种子，早停耐心为 16。
- 表 2 中 FT 平均排名 1.8，表 4 说明深度模型与 GBDT 无通用赢家（物理第 7–8 页）。表 5 对 AutoInt 和去除特征偏置做消融，说明偏置是 FT 构件的一部分（物理第 9 页）。
- 物理第 1、10 页给官方源码 `https://github.com/yandex-research/tabular-dl-revisiting-models`；既有 Zotero 条目键 `N4MRAEZF`。
- 对本课题：普通线性数值 token 是基座而非创新；论文没有实体、时间、严格因果历史、跨年度漂移、实体 AP 或低误报预算。

### 论文三：SC 2025 容错 FT-Transformer

- PDF 元数据与首页确认 “FT” 指 `fault-tolerant`，不是 `Feature Tokenizer`。任务是 GPU 注意力推理中的软错误检测与纠正。
- 方法包含端到端容错注意力、无跨线程通信的 strided ABFT、选择性神经元值约束和统一校验；公式与算法位于物理第 3–8 页，算法 1 在第 8 页。
- 实验使用随机生成的 Q/K/V 张量和 GPT-2、BERT-Base、BERT-Large、T5-Small 配置；表 2–4 与图 9–15报告最高 7.56 倍相对加速、平均 13.9% 容错开销、检测/纠正开销 4.7%/9.1%（物理第 9–11 页）。
- 第 13–14 页提供可复现实验制品 DOI `10.5281/zenodo.15881566`。
- 裁决：题名碰撞，和第三章 FT 表格模型、M-A、M-B、M-E 均无关。不得把其二次复杂度、长序列或容错动机转移到固定 84 token 项目。

### 论文四：Electronics 2026 的 FT-Transformer IoT 检测

- 物理第 5 页公式（1）把数值字段映射为 `t_i=x_iW_i+b_i+e_i`；第 6–7 页公式（2）至（8）为 `[CLS]`、注意力、分类和交叉熵；本质仍是普通字段 token。
- CICIoT2023 用于主任务，CICIoMT2024 用于外部验证；另用 NF-ToN-IoT→NF-BoT-IoT。第 7 页明确二分类按验证集攻击类 F1 选模，多分类按验证集宏 F1 选模，说明“部署目标相近的验证指标选轮”是协议设计，不是结构机制。
- 第 8 页公式（9）引入 `L_total=L_CE+λL_CORAL`，用未标注目标域样本做协方差对齐。第 26 页表 13 的 `λ=0.05` 提升部分外部 ROC-AUC，但这一路径若把 LSPR24 当目标域参与训练，违反本项目封印隔离，不能直接迁移。
- 第 19、21 页表 7–8 只消融 token 宽度、层数和头数；无 tokenizer 形式消融。第 24 页表 11 显示在 92 维特征并集协议下，FT 外部 ROC-AUC 跌到 `0.527226`，这是“表示对字段空间漂移敏感”的直接病灶证据，不是新 tokenizer 的效果证据。
- 第 29 页声明源码与处理数据仅可向通信作者申请，无公开仓库。基线预算也不完全统一：主二分类的 RF/XGBoost 最多只用 20 万训练与 10 万测试样本，而 FT 使用 42 万/12 万，故不得把其主表当严格共同预算比较。

### 论文五：MKAFT

- 物理第 3–4 页公式（1）至（7）从 KAN 与 B-spline 出发，用 Matérn 核替代 B-spline。第 5–6 页公式（8）至（11）给出完整 MKAFT：`B=SiLU(x)⊙W_b`、Matérn 核网格表示、核权重收缩 `G`，最终 `y=B+G`。
- 表 1 覆盖五个卧姿压力数据集；另评估 Covertype、ALOI、Higgs、Jannis、Helena、Adult。表 3 是 FT/KAFT/MKAFT 构件消融，表 5 是六个通用表格数据集结果（物理第 8、10、12 页）。
- 直接已占用边界：把 KAN、Matérn 核或所谓矩阵/张量权重 `W_m` 原样放入 FT tokenizer 已发表，不能作为本课题创新；PLR/周期/分段线性同理由 Gorishniy 2022 占用。
- 关键有效性缺陷：物理第 7 页明确“若测试准确率连续 16 个周期不提升则早停”，并在图 4 逐周期观察测试损失和测试准确率。该协议使表 3–5 的性能与收敛结论受到测试集反复访问污染，只能用于确认“组件已发表”，不能作为效果量级或公平优越性证据。
- PDF 未给公开源码或代码可用性声明；训练超参数还存在排版歧义（学习率显示为 `1×10^4`、Adam 的 `ε` 显示为 `10^8`，语义应核官方代码但代码不可得）。

## 扩展全文证据

### TabFormer：同实体层次序列 Transformer

- ICASSP 2021，arXiv `2011.01843v2`。物理第 2 页公式（1）把同一用户连续 `T` 行作为窗口，先做字段 Transformer，再做行序列 Transformer。
- 信用卡任务使用 10 条交易窗口；表 1 中原始 LSTM F1 为 `0.83`，加入 TabBERT 特征为 `0.86`（物理第 3 页）。
- TabBERT 用双向窗口，TabGPT 才是因果生成；没有当前流查询独立只读记忆。
- 官方源码：`https://github.com/IBM/TabFormer`。

### FATA-Trans：字段类型与时间感知

- CIKM 2023，DOI `10.1145/3583780.3614879`。物理第 3 页公式（1）–（3）定义同标识符连续窗口；第 4–5 页公式（4）–（10）分开静态/动态字段并注入时间间隔。
- 物理第 6 页已把历史均值、计数和频率当静态字段，说明“普通历史特征”已占用；但全文未给逐时点严格前缀拟合合同。
- 第 6–7 页按 2018 年前后切分信用卡数据并遮蔽标签；表 1/3 在第 7–8 页。
- 官方源码：`https://github.com/zdy93/FATA-Trans`。

### Fieldy：跨行跨列细粒度注意力

- KDD 2024 MiLeTS Workshop，arXiv `2406.15327`。物理第 3–4 页同时做行向、列向注意力，再用第二级 Transformer 关联全部字段。
- 贷款违约任务按客户历史分组并以 AP 评价；表 3 中等参数 Fieldy AP `0.48±0.06`，FT 与行式 TabBERT 均约 `0.44`，差值标准差较大（物理第 5 页）。
- 它直接占用跨历史字段注意力大类，但使用全窗口双向结构，不是单向因果记忆读取。

### STEP：因果自回归表格事件

- arXiv `2410.10648v3`，首页标注 `Preprint (Under Review)`。物理第 4 页公式（1）–（2）按用户分组、时间排序；第 5 页使用 decoder-only 因果遮罩。
- 信用卡任务按用户 98/2 切分，长度 10、无重叠窗口、不过采样，历史标签遮蔽（物理第 6–7 页）；表 1 在第 8 页。
- 它已经占用“因果实体历史 Transformer”大类。精确空白只剩 FT 当前字段路径、只读记忆方向和低误报联合训练。
- 官方源码：`https://github.com/alexstein0/event_prediction_step`。

### pAUC-DRO：深度低误报排序

- Zhu 等，ICML 2022。物理第 3 页公式（1）–（3）定义 one-way/two-way pAUC；第 4 页公式（7）–（10）以 CVaR/KL-DRO 聚焦顶部负样本。
- 第 5–6 页算法 SOPA/SOPA-s/SOTA-s；第 8 页采用“CE 预训练→重置分类头→pAUC 微调”，而不是 CE 与 pAUC 权重 1 并加。
- 第 9 页表 1–4 为图像与分子数据结果。官方实现进入 `https://github.com/Optimization-AI/LibAUC`。

### 多示例双向部分 AUC

- Hu、Zhu、Yang，NeurIPS 2023。物理第 8 页公式（8）–（9）直接定义 TPAUC，并把 `X_i` 扩展成多实例袋；均值池化之外还讨论平滑最大和注意力池化。
- 第 9 页表 2 比较 MIDAM、SOTAs 与 SONT；SONT(att)直接优化多示例 TPAUC。
- 因此“实体袋+低 FPR pAUC”本身也已占用。本文没有时间前缀、跨年度隔离或 FT 结构。

## 跨文献综合

### M-A：实体历史字段 token

- 五篇没有直接论文把“严格过去的实体统计”作为 FT 字段 token。TabTransformer 只上下文化当前样本的类别列；FT 原论文只对当前样本各字段做 token；Electronics 只对当前流量统计列做 token；MKAFT 只替换当前数值字段的映射函数。
- 构件证据成立：FT 允许每个数值字段成为独立 token；本地 TabReD 笔记证明历史聚合作为普通表格列已常见；因此创新差量不能是“首次使用历史特征”，只能是角色化、严格过去、实体条件化且与部署目标共同训练或决策。
- 严格因果可用量候选：`t` 之前的实体计数、距上次事件时间、指数衰减计数、既有合法数值字段的在线均值/方差、当前值相对过去分布的标准化偏差、既有类别值的过去频率。禁止未来窗口、标签派生统计、当前/未来实体标签、原始 IP 入模及任何由 LSPR24 选出的字段或窗口。

### M-B：实体 AP 选轮与校准

- 五篇中没有实体 AP 选轮。TabTransformer 与 FT 原论文按通用验证指标早停；Electronics 按攻击类 F1 或宏 F1 选模；MKAFT 错误地按测试准确率早停。
- 因此“把逐流 AP 换成源年实体 AP”只属于目标一致的选择协议，不能作为论文机制。要晋级，必须把实体袋级排序、部分 AUC 或低 FPR 风险写入可微训练目标或联合决策算法，并用“普通选轮 vs 实体 AP 选轮 vs 可微实体目标”三路消融区分。

### M-E：数值 token 编码

- 原生线性 token、周期/PLR/分段线性、KAN、Matérn/矩阵驱动 tokenizer 均已占用。原样替换全部属于照抄。
- 仍可能存在的任务化空白是：只用 LSPR23 严格过去实体状态驱动 tokenizer 的参数或路由，使同一当前数值在不同实体历史状态下得到不同表示；或者以源年可观测漂移病灶约束数值分区，但不得读取 LSPR24。
- 任何任务化版本必须对比：原生线性、已发表原组件、加入我方状态/约束后的改造。只有第三者相对第二者产生源年增益，才能证明“朱式改造”而不是原组件收益。

## 最终候选分层

### 主候选 D1：因果实体记忆交叉注意力

- 当前 FT 的 84 个 token 内部自注意力保持不变；当前 `[CLS]` 产生 query，严格过去的实体记忆只产生 key/value。
- 记忆必须在本次预测完成后才更新；原始 IP 只作实体分组键，不进入模型。
- 历史统计 token、PLR 或数值编码只负责构造记忆内容，是 D1 的实现组件，不单列创新。
- 直接近邻覆盖了序列、自回归、跨行/列和历史字段，但未覆盖这一单向接口，故新颖性高于其他候选；仍需 LSPR23 差量消融。

### 主候选 D2：因果前缀一致的实体均匀低误报排序

- 普通实体 AP 选轮只是协议。D2 必须进入训练目标，并使用与部署相同的严格过去前缀分数。
- 对每个实体先在冻结源年观察截止点形成一个分数，外层每实体等权；低误报部分只聚焦源年高分良性实体，预算在实验前冻结。
- SOAP、pAUC-DRO、MIDAM 和多示例 TPAUC 已覆盖基础数学。D2 的差量只在因果前缀、实体均匀测度、源年封印和 FT 联合算法，故新颖性风险高于 D1。
- 优先采用 pAUC 作为阶段二主目标，而不是以权重 1 叠加到已饱和的逐流交叉熵；C00 必须有等训练步数的交叉熵继续训练对照。

### 联合算法 D3：共享严格过去实体记忆

- D1 产生的同一实体记忆既为当前流跨注意力提供 K/V，也确定 D2 的因果前缀实体分数。
- 执行顺序为“读 `t^-` 记忆→当前流预测→形成前缀实体分数→计算低误报排序目标→更新模型→写入当前流到实体记忆”。
- 该顺序是显式算法差量，不是两个开关并列。

### 两个备选

1. **门控双读出**：用当前 `[CLS]` 与严格过去实体状态分别读出，再门控融合。成本低，但属于 D1 简化版，不足以单独支撑主创新。
2. **源年状态条件化 PLR**：用严格过去实体状态选择已发表 PLR 专家。只能作为 FT 骨干适配或 D1 组件，不能单列主创新。

## 遗留限制

- 本轮没有运行 LSPR23 机制实验；D1、D2、D3 均为“设计可行／实验待证”。
- STEP 仍是未正式发表预印本；其结果只用于近邻边界，不与正式论文同级支撑效果主张。
- MKAFT 的测试集早停污染其效果证据；只保留“组件已发表”事实。
- Zotero Desktop 未运行，六篇新增全文未导入 Zotero；仓库原件与全文笔记已完成。
- Electronics 的目标无标签对齐样本拆分和 MKAFT 的公开实现均无法由现有原件复核。
