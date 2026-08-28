# LSPR24 流式行为检测任务方案册

- **文档状态**：自包含实施交接包；设计可行，实验待证
- **适用日期**：2026-08-12
- **唯一数据集**：LSPR24
- **冻结数据合同**：`lspr24-g0-v5-staged`
- **合同 SHA-256**：`877488f3529c6c862b060a74782d1904aae81512ea1169c713ba20d8c3f31a0e`
- **方案编制代理**：`/root/rwkv_application_transfer_patterns_sol_max`
- **模型与推理强度**：`gpt-5.6-sol`，`effort=max`
- **本册边界**：只定义当前窗口的因果流式检测，不实现代码、不启动实验、不读取最终 20%

## 1. 执行结论

本任务应优先验证“**强字段基座 + 有界 RWKV 历史残差**”，而不是再做一个用 RWKV 完全替换强树模型的普通序列分类器。推荐顺序如下。

| 排名 | 候选 | 本册裁决 | 主要理由 |
| --- | --- | --- | --- |
| 1 | `SBD-1` 强字段基座 + 有界 RWKV 历史残差 | **主候选** | 保留 LSPR24 当前窗口字段交互的强路径，只让 RWKV 证明因果历史的独立增益；残差有显式幅度上界，可直接做机制消融 |
| 2 | `SBD-2` 行为码协议语言模型 + 监督检测头 | **条件候选** | PLM-NIDS 提供最直接安全先例，但离散化、码本和正常似然均增加数据工程；只有连续字段主候选失败且行为码门禁通过时才进入正式比较 |
| 3 | `SBD-3` 完整任务化 RWKV 因果分类器 | **必要架构基线** | 能判断完整 RWKV 是否足以完成任务，但“RWKV 用于入侵检测”已被 PLM-NIDS 覆盖，不能单独构成原创贡献 |
| 4 | 频域、多尺度图、在线目标适应、博弈或最优停止包装 | **当前否决** | LSPR24 的 `H<=32` 尚无稳定周期、图关系或决策动作证据；这些模块增加第三章工作量，却不能修复当前已见的弱骨干问题 |

本册的“流式”含义是：在每个 5 秒窗口完成时，以同一受保护端点的因果状态立即输出当前窗口标签概率。它**不是**攻击发生前的未来风险预测，也不是带停止动作和时延代价的最优停止问题。

### 1.1 既有结果如何使用

下列数字来自跨年度 `LSPR23→LSPR24` 的既有诊断，只说明“用较弱序列骨干叠加复杂时间、状态或风险包装”曾经失败，**不得**作为本任务的训练数据、模型选择结果、通过门槛或 LSPR24 单年度性能先验：

| 既有跨年度方法 | AP | 相对 XGBoost 的下降 |
| --- | ---: | ---: |
| XGBoost | 0.03890259 | — |
| 候选 B 最佳 | 0.01920596 | 50.63% |
| C12 最佳 | 0.01697728 | 56.36% |
| R1 最佳 | 0.01287790 | 66.90% |
| C12-R 最佳上界 | 0.00927448 | 至少 76.16% |

由这些结果得到的仅是**本课题推论**：新方案必须保留强字段交互基座，并让历史模块接受可证伪的增量检验。跨年度结果不是本任务的可比较实验结果；本任务只按后文的 LSPR24 严格时间前向协议产生新证据。

## 2. 唯一任务与数据合同

### 2.1 任务定义

设 `x_t` 为受保护端点在窗口 `t` 结束时可见的合法 LSPR24 字段，`m_t` 为合法字段的缺失与质量掩码，历史长度 `H∈{1,4,16,32}`。模型在 `window_end_t` 时刻输出：

```text
p_t = P(window_label_t = 1 | x_[t-H+1:t], m_[t-H+1:t])
```

其中：

- 主节拍固定为 5 秒；1 秒仅能在主方案、字段、超参数和主结果冻结后作为敏感性分析。
- 序列只在同一 `protected_endpoint_id`、同一连续段和同一分区内构造。
- `window_label_t=max(flow_label)`，表示该窗口是否与冻结标签定义下的红队基础设施或横向活动相关。
- 该标签不等于攻击家族、攻击是否成功、资产是否受损，也不支持“提前多少秒发现尚未发生攻击”的表述。
- 模型只能使用 `mTimestampLast` 之前已完整观测的信息；身份、端口、绝对时间、标签、IDS 输出、样本标识和路径信息不得进入张量、路由、采样权重或阈值。
- 分区边界、隔离带、端点重置或连续段重置后的状态必须清空；不得跨边界携带 RWKV 状态或手工历史。

### 2.2 精确 60/20/20 与前 60 内部 40/10/10

切分按**活动秒时间秩**完成，不按流行数、窗口数、端点数或标签比例完成。

| 数据区间 | G0 v5 名称 | 唯一用途 | 禁止事项 |
| --- | --- | --- | --- |
| 0%–40% | `train-fit` | 归一化与词表拟合；模型训练；训练内诊断 | 不得用后续区间拟合任何变换 |
| 40%–50% | `architecture-selection` | 仅种子 42 的架构、`H` 和超参数选择 | 不得反复回看后改变搜索空间 |
| 50%–60% | `dev-validation` | 候选冻结后的种子 42/43/44 一次性开发验证 | 不得把结果送回调参或补种子 |
| 60%–80% | `calibration` | 骨干完全冻结后的概率校准与告警阈值冻结 | **只允许校准**；不得重训、选架构、选字段或改损失 |
| 80%–100% | `final-test` | 所有方法与评价程序冻结后的唯一最终评价 | 当前方案实施进程零访问、零统计、零哈希、零成员信息 |

高层上，前 60% 是开发选择区，60%–80% 仅校准，最后 20% 完全封存。`G0-D` 放行不表示 `G0-F` 已准备，也不授权访问最终区。

### 2.3 合法输入与统一支持区间

所有候选与基线必须由以下 G0-D 制品派生，并共享同一字段、历史样本、非重叠推断锚点、评价簇和分数清单：

- `<LSPR24_G0_RUN_ROOT>/views/development-windows.parquet`
- `<LSPR24_G0_RUN_ROOT>/views/history-samples.parquet`
- `<LSPR24_G0_RUN_ROOT>/manifests/field-manifest.json`
- `<LSPR24_G0_RUN_ROOT>/receipts/field-lineage-and-tensor-probe.json`
- `<LSPR24_G0_RUN_ROOT>/manifests/inference-anchor-manifest.parquet`
- `<LSPR24_G0_RUN_ROOT>/manifests/evaluation-clusters.parquet`
- `<LSPR24_G0_RESTRICTED_ROOT>/development-labels.parquet`，只能经受限加载接口连接

建模进程不得直接扫描原始 LSPR24 Parquet，不得解析 `attack_narratives.json`，不得自行生成最终区成员清单。若 G0-D 缺少本任务所需合法视图，必须请求数据生产进程扩展 G0 制品，不能在任务代码中旁路重扫原始数据。

### 2.4 前 80% 的标签可构造性

| 所需信号 | 前 80% 是否可合法构造 | 合法来源与用途 |
| --- | --- | --- |
| 当前窗口 `window_label_t` | **可以** | 受限开发标签侧车与冻结窗口连接规则；用于 0%–60% 的监督训练／评价，以及 60%–80% 的冻结校准 |
| 同端点因果历史 | **可以** | `history-samples.parquet`；只在同一连续段与分区内连接，边界处清空 |
| 当前检测的评价簇 | **可以** | `evaluation-clusters.parquet` 与非重叠锚点；用于前 60% 的选择和一次开发验证 |
| 未来攻击标签／提前量 | **本任务不需要，也不得派生** | 本册不定义未来风险或早期预警，不从后续窗口反标当前样本 |
| 最终 20% 标签与性能 | **当前不可以** | 只能由 G0-F 在全部方法冻结后一次性解封评价 |

上述“可以”以真实 G0-D 放行收据和对应制品存在为前提；方案文字不能替代数据门禁。

## 3. 已核验文献事实与移植矩阵

下表中的“文献事实”只说明既有机制如何被移植，不代表其在 LSPR24 上有效。

| 工作 | 保留的 RWKV 机制 | 替换的输入／输出 | 新增任务模块与目标 | 是否完整使用原生 RWKV | 对本任务的事实边界 |
| --- | --- | --- | --- | --- | --- |
| RWKV 原论文与官方实现 | 时间混合、通道混合；并行训练、固定大小递归状态推断 | 文本词元输入，下一词元输出 | 因果语言建模交叉熵 | **是** | 证明训练／推断接口，不证明安全检测有效 |
| RWKV-7 Goose | 向量衰减、移除键、动态状态更新与可学习状态演化 | 仍以语言建模为主 | 下一词元目标 | **完整层使用时是**；只抽取状态核时不是 | 提供现代 RWKV 状态核与官方源码参照；不能把抽取的核写成“完整 RWKV-7” |
| PLM-NIDS | RWKV-4 因果语言模型和逐序列状态 | 将三、四层包元数据离散为协议词元；输出下一词元分布或分类概率 | 良性序列交叉熵、困惑度异常分数；可加监督分类头 | **使用完整 RWKV-4 骨干，但任务已改造** | 直接证明 RWKV 可进入网络入侵检测；只在 CIC-IDS-2017、攻击先验高且缺强树模型对照，不能证明 LSPR24 有效 |
| RWKV-TS | 时间混合与通道混合 | 将文本嵌入替换为实例归一化、分块数值序列；接预测、分类、填补或异常头 | 不同任务的回归、分类或重建目标 | **完整任务化 RWKV 块** | 证明数值时序适配可行；其异常检测平均 F1 83.89，低于 TimesNet 85.24，不能宣称普遍最优 |
| TLS-RWKV | 因果时间状态与 RWKV 层 | 视频特征序列输入；逐帧动作类别输出 | 全连接分类头、时间标签平滑、逐帧交叉熵，并改用 Laplace 激活 | **任务化层，非原生语言模型** | 提供“每个时间点即时分类”的跨域先例；不是网络安全或提前预警证据 |
| FRWKV+ | RWKV 式状态分支 | 数值频域输入与预测输出 | 零初始化、信任门控、幅度上界 0.20 的有符号校正 | **否** | 提供有界残差的结构先例；其周期预测收益不能外推为流量检测收益 |
| RWKV-CVM | RWKV-TS 时序骨干 | 多变量时间序列 | 带恒等跳路的轻量跨变量门控 | **否，RWKV 前增加任务模块** | 只支持“小幅保守注入可训练”；论文增益约 1.8% 且并不普适 |
| Vision-RWKV、RWKV-SAM、RWKV-UNet | 将 RWKV 用于全局或长程混合 | 图像块／特征图输入；分割或重建输出 | 保留卷积、U-Net 或任务解码器；部分工作删除冗余通道混合 | **否** | 支持“保留强局部任务路径，只让 RWKV 负责全局历史”的移植原则；不是安全效果证据 |
| STWGRL | D-RWKV 时序编码 | 多变量传感器序列与异常分数 | 去噪、自学习有向图和图稀疏正则 | **否** | 图模块并非天然增益；在 MSDS 上移除图稀疏正则后 F1 反而由 94.68 升至 95.92，故无图证据时不应照搬 |

### 3.1 文献事实与本课题推论的分界

**文献事实：**RWKV 可以保留因果递归状态，同时替换输入编码器、任务头和训练目标；成功的任务迁移经常保留强局部任务模块，并把 RWKV 限定为长程混合器；有界、零初始化校正已有时间序列结构先例。

**本课题推论：**LSPR24 当前窗口字段交互可能比长历史更重要，因此应以强字段模型为锚点，只让 RWKV 学习受限的历史增量。这个推论必须由同一 LSPR24 支持集上的基线、状态置乱和残差消融验证。没有新实验前只能标记为“实验待证”。

## 4. 主候选 `SBD-1`：强字段基座 + 有界 RWKV 历史残差

### 4.1 机制

对每个合法窗口构造当前字段向量 `x_t` 和预注册的因果历史统计 `a_t^(H)`。强字段锚点是一次拟合的 XGBoost 或在 `architecture-selection` 胜出的等价强树配置：

```text
b_t = logit(clip(f_tab([x_t, a_t^(H)]), 1e-6, 1-1e-6))
e_t = FieldEncoder(x_t, m_t)
h_t = RWKV(h_(t-1), e_t)
r_t = w_r^T [h_(t-1), e_t]
g_t = sigmoid(w_g^T [h_(t-1), e_t, q_t] + c_g)
delta_t = epsilon * tanh(r_t / epsilon)
ell_t = b_t + g_t * delta_t
p_t = sigmoid(ell_t)
```

其中 `q_t` 只含字段清单允许的缺失、截断、历史覆盖率与重置质量信息。`w_r` 零初始化，使训练起点精确退化为强字段锚点。`epsilon`、门控形式和所有候选值必须在首次读取 `architecture-selection` 预测前进入搜索预算清单。

该构造具有可审计的结构性质：

```text
|ell_t - b_t| <= epsilon
```

若两个样本的基座 logit 间隔大于 `2*epsilon`，单个有界残差不能翻转二者排序。这个结论只限制修改幅度，**不保证** AP、召回率或校准一定改善。

### 4.2 训练目标

```text
L_cls = weighted_BCE(y_t, p_t)
L_anchor = mean((ell_t - b_t)^2)
L_gate = mean(g_t * (1 - history_coverage_t))
L = L_cls + lambda_anchor * L_anchor + lambda_gate * L_gate
```

- `weighted_BCE` 的类别权重只能在 `train-fit` 冻结；AP 评价仍使用原始分布。
- `L_anchor` 不能替代幅度上界，只用于抑制无必要的校正。
- `L_gate` 只约束历史不完整时的门值；不得以标签、端点身份或后续统计控制门。
- 每个联合配置中的树模型只拟合一次；不得为残差堆叠额外进行未登记的折外树拟合。
- 神经模型固定有效批量 256、最多 30,000 次已提交更新，只保留第 30,000 次检查点；数值发散和显存超限计入配置预算。

### 4.3 为什么不是“完整原生 RWKV”

`SBD-1` 保留 RWKV 的因果状态更新，但输入是数值字段编码，输出是二分类有界残差，并保留外部强树锚点。因此它是**RWKV 状态核的任务化混合模型**，不能描述成完整原生 RWKV。完整官方 RWKV 层必须作为单独基线，防止把外部锚点收益误归因于 RWKV。

## 5. 条件候选与明确不采用方向

### 5.1 `SBD-2`：行为码协议语言模型 + 监督头

所有量化边界和码本只在 `train-fit` 拟合。令 `c_t` 为去身份窗口行为码：

```text
s_lm,t = -log P(c_t | c_[t-H:t-1])
L_lm = 1[输入历史与目标窗口标签均为0] * CE(c_t, c_hat_t)
L_joint = L_cls + lambda_lm * L_lm
```

当前检测分数只能使用上一窗口结束时已经产生的 `c_hat_t` 与刚完成的 `c_t`，不能用 `c_(t+1)`。该候选必须与固定阶 `n` 元语法、马尔可夫链和连续字段 RWKV 比较；若码本坍缩、身份可反推或下一码预测不优于 `n` 元语法，则立即否决。

### 5.2 `SBD-3`：完整任务化 RWKV 分类器

使用官方 RWKV 层、数值字段编码和二分类头直接优化 `weighted_BCE`。它承担两个作用：

1. 判断完整 RWKV 是否能在相同字段与预算下达到强基线；
2. 判断 `SBD-1` 的收益来自 RWKV 历史状态，还是只来自强树锚点。

即使 `SBD-3` 胜出，也只能声称 LSPR24 严格时间前向协议下的实证改进，不能声称首次将 RWKV 用于网络入侵检测。

### 5.3 当前不采用

- **频域／物理时间分支**：既有跨年度候选未产生可信增益，LSPR24 G0 也禁止绝对时间进入模型；训练区未证明稳定周期前不增加快速傅里叶变换分支。
- **图模块**：受保护端点视图没有冻结、无捷径的实体图；STWGRL 的图正则存在负消融，不能仅凭概念加入。
- **在线目标适应**：会改变校准区和未来分布的信息预算，破坏“骨干冻结、60%–80% 只校准”的合同。
- **GroupDRO、尾风险或博弈包装**：当前跨年度结果低于 XGBoost；应先证明基础历史状态有增量，再讨论风险目标。
- **最优停止／强化学习**：本任务没有未来预警标签、停止动作、误报代价和时延奖励，不得把静态阈值包装成决策问题。
- **长精确召回混合器**：`H<=32`，尚无需要 GoldFinch、RWKV-X 等长上下文精确检索的证据。

## 6. 共同预算强基线

所有基线必须消费相同合法字段、相同 `H`、相同非重叠锚点和相同评价簇；不得通过缩小树模型历史或扩大 RWKV 字段集制造优势。

| 基线组 | 必须具备的能力 | 它回答的问题 |
| --- | --- | --- |
| 常数先验、随机排序 | 反映开发区类别先验与 AP 下界 | 模型是否超过无信息预测 |
| XGBoost、HGB、随机森林，`H=1` | 强当前字段非线性交互 | 历史是否真的必要 |
| XGBoost、HGB，`H∈{4,16,32}` | 相同历史的展平向量与预注册滚动统计 | RWKV 是否优于强手工历史树模型 |
| 逻辑回归／字段 MLP | 受控当前字段锚点 | 非线性字段交互贡献有多大 |
| GRU、TCN／因果一维卷积 | 因果递归与有限感受野 | RWKV 状态是否优于常见轻量序列模型 |
| 轻量因果 Transformer | 窗内精确注意力 | RWKV 是否以状态效率换取可接受精度 |
| Mamba | 另一类选择性状态空间模型 | 收益是否为 RWKV 特异 |
| 完整官方 RWKV、RWKV-TS 式分类器 | 原生状态核与数值时序适配 | 混合候选是否真正优于完整 RWKV |
| `SBD-1` 去残差、去门、去上界变体 | 同一锚点下的控制变量 | 每个任务模块是否有独立贡献 |
| 固定阶 `n` 元语法／马尔可夫链 | 仅用于 `SBD-2` 行为码分支 | 语言模型收益是否超过简单计数记忆 |

搜索预算固定遵守 G0-A13：每个模型 1–12 个完整枚举配置；神经配置种子 42、有效批量 256、30,000 次更新、单检查点；种子 42 通过后才以同配置运行 43、44，不补种子。

## 7. 可观测量、评价指标与最小消融

### 7.1 主评价

- **主指标**：非重叠推断锚点上的 AP。
- **辅助检测指标**：ROC-AUC、F1、恶意召回率、良性端点小时固定误报率下的召回率。
- **校准指标**：Brier 分数、期望校准误差；只能在 60%–80% 拟合校准器后报告冻结校准结果。
- **统计单位**：以 `evaluation_cluster_id` 做成簇配对自助法，报告三种子和 95% 置信区间；全窗口指标只能作描述性结果。
- **部署指标**：单窗口延迟、每秒窗口数、峰值显存、单端点状态字节、重置耗时。

### 7.2 机制可观测量

必须逐配置保存以下开发区诊断，不能只保存最好 AP：

- `|ell_t-b_t|` 最大值、分位数与超界计数；数值容差固定为 `1e-6`。
- 门值 `g_t` 的分位数、低于 0.05 与高于 0.95 的比例。
- 残差导致的排序翻转比例、基座错误与残差方向的相关性。
- RWKV 状态范数、非有限值计数、端点／分区／隔离带重置次数。
- 每个 `H` 的历史覆盖率、有效锚点数和 AP 增量。
- 状态时间置乱、端点内历史置乱和全状态清零后的 AP 变化。
- 身份探针与绝对时间探针必须无法从模型张量发现禁入字段；这不是“去身份效果”，只是合法性门禁。

### 7.3 最小消融矩阵

| 编号 | 模型 | 唯一目的 |
| --- | --- | --- |
| A0 | XGBoost `H=1` | 当前字段强基线 |
| A1 | XGBoost + 相同 `H` 展平／滚动统计 | 强历史树基线 |
| A2 | 完整官方 RWKV 分类器 | 原生 RWKV 对照 |
| A3 | `A1 +` 无上界 RWKV 残差 | 检查幅度约束是否必要 |
| A4 | `A1 +` 固定门有界残差 | 检查数据依赖门是否必要 |
| A5 | `A1 +` 门控有界残差，即 `SBD-1` | 完整主候选 |
| A6 | A5，但历史状态端点内置乱 | 验证是否真正使用时序 |
| A7 | A5，但 `H=1/4/16/32` | 确定历史收益与饱和点 |
| B0–B3 | `n` 元语法、RWKV 下一码、仅分类、联合目标 | 仅在 `SBD-2` 门禁通过时运行 |

不得以新增公式、复审或更多模块替代上述消融。

## 8. 预注册否决门槛

### 8.1 数据与实现硬否决

出现任一项即停止受影响运行，结果标记为无效而不是科学失败：

1. G0 合同版本或 SHA-256 不匹配；G0-D 核心状态不是放行态。
2. 任一历史、状态或标准化参数跨分区／隔离带／连续段／受保护端点。
3. 直接打开原始标签列页、最终 20% 或攻击叙事。
4. 模型张量包含身份、端口、绝对时间、IDS 分数、样本标识、分区名或路径信息。
5. 模型、种子、字段、样本或分数清单不一致；共同预算不公平。
6. `|ell_t-b_t| > epsilon + 1e-6`、出现非有限分数或状态重置断言失败。

### 8.2 种子 42 淘汰门

在 `architecture-selection` 上定义：

```text
AP_strong = max(AP_相同历史强树, AP_最佳共同预算神经基线)
Delta_AP = AP_SBD-1 - AP_strong
```

- `Delta_AP < 0.005`：否决 `SBD-1` 进入三种子正式开发验证。
- 完整模型相对 `H=1`、状态清零或端点内历史置乱的最好者增量 `<0.002 AP`：否决“RWKV 历史机制”主张。
- 完整模型相对固定门有界残差增量 `<0.002 AP`：否决数据依赖门，只保留较简模型。
- 超过 95% 可评价锚点满足 `g_t<0.05`，或少于 1% 锚点的预测与基座不同：判定残差未被使用；即使最终等于基座，也不能宣称机制有效。
- `SBD-2` 的行为码有效词表占用低于 10%、未知码率高于 1%，或下一码交叉熵未比最好 `n` 元语法降低至少 1%：立即否决该分支。

### 8.3 冻结开发验证门

种子 42 通过后，冻结配置并运行种子 43、44。三种子在 `dev-validation` 各评价一次：

- 三个种子的 `Delta_AP` 必须全部大于 0；
- 三种子 `Delta_AP` 中位数必须至少为 0.005；
- 成簇配对自助法的三种子汇总 95% 置信区间下界必须大于 0；
- 任一种子不得相对强基线下降超过 0.002 AP；
- 历史置乱消融的 AP 至少下降 0.002，否则删除 RWKV 历史贡献表述。

任一条件不满足，主候选标记为“实验否决”或降格为基线。不得通过改切分、补种子、改阈值或查看最终测试后重选配置挽救。

### 8.4 校准与最终边界

只有通过开发验证的冻结模型才可在 60%–80% 拟合预注册单调校准器和阈值。校准区不得更新骨干、树模型、字段编码、`epsilon`、`H` 或损失权重。本实施进程到冻结包即结束；`G0-F` 的最终评价必须由后续获授权的冻结评价流程一次完成。

## 9. 原创边界

### 9.1 不能主张

- 不能主张首次将 RWKV 用于网络入侵检测；PLM-NIDS 已有直接先例。
- 不能主张首次把 RWKV 用于数值时序分类或异常检测；RWKV-TS 已覆盖。
- 不能主张有界门控、零初始化残差或保留强局部路径本身原创；FRWKV+ 与视觉 RWKV 迁移工作已有结构先例。
- 不能把完整官方 RWKV、协议语言建模、强树模型或 G0 数据合同中的任一组件单独写成方法创新。

### 9.2 只有实验通过后可形成的贡献

可候选表述为：在 LSPR24 G0 v5 严格时间前向、去身份、共同预算协议下，提出并验证一种以强字段模型为锚点、以幅度有界 RWKV 状态残差只校正因果历史证据的流式检测器，并通过历史置乱、门控、上界和强历史树消融证明增量来自受限状态机制。

这是一项**组合与任务合同层面的潜在贡献**，而不是 RWKV 基元首创。若主门槛未通过，原创主张自动撤销。

## 10. 数据与算力代价

| 项目 | 代价 | 控制方式 |
| --- | --- | --- |
| 新数据集 | 无；严格只用 LSPR24 | 禁止接入 LSPR23 或其他 NIDS 数据训练／调参 |
| 原始数据工程 | 无新增原始扫描 | 只读消费 G0-D；缺制品时阻塞并请求 G0 生产端扩展 |
| 任务缓存 | 中等 | 只保存样本索引、合法张量块和哈希；不复制原始流与受限标签 |
| 树基线 | 低到中等 CPU／内存 | 每配置一次拟合，最多 12 配置 |
| 神经模型 | 单张 5090 可行性待真实探针确认 | 小型字段编码、`H<=32`、有效批量 256、混合精度；显存超限计入预算，不临时缩模型 |
| 行为码分支 | 中到高 | 只在主候选门禁后运行；码本只在 `train-fit` 拟合 |
| 最终测试 | 当前为零 | 本实施进程不创建、不统计、不访问 G0-F 制品 |

### 10.1 理论深度、第三章工作量与 5090 可实验性

| 维度 | `SBD-1` | `SBD-2` | 裁决 |
| --- | --- | --- | --- |
| 当前实验约束 | 直接保留既有跨年度诊断中唯一明显占优的强字段路径，再单独检验历史残差 | 既有候选未证明离散语言分支有效，需新增码本门禁 | `SBD-1` 优先 |
| 理论对象 | 幅度上界、排序稳定区间、门控退化条件、因果状态重置、共同支持公平性 | 正常语言似然、因果惊异度、码本信息损失 | 两者均可推导，但 `SBD-1` 更贴近当前失败原因 |
| 章级实验对象 | 强树／强神经基线、上界／门／状态置乱／历史长度消融、效率和困难分面 | 再增加量化、`n` 元语法、码本与联合目标消融 | `SBD-1` 先构成最小完整章；`SBD-2` 只作条件扩展 |
| 单张 5090 | 小型字段编码与 `H<=32` 状态，配置逐个运行；无需预训练大语言模型 | 需额外词表、长词元序列与输出层，仍可能运行但工程和显存风险更高 | 先做 `SBD-1` 真实显存探针 |

若实验证据成立，`SBD-1` 能形成“问题定义—有界混合机制—性质—算法—强基线—消融—效率—失败边界”的章级论证链，其功能完整度可参照朱焱雷第三章；不能机械凑页数、公式、定理或图表。朱论文历史效果量级和既有 `16.1%` 错误相对下降只作参照，不替代本册预注册的 LSPR24 AP、多种子和置信区间门槛。若快速实验否决任一机制，相应推导与篇幅必须一并删除。

## 11. 独立实现文件边界

以下是后续“LSPR24 流式行为检测”实现进程的**建议独占所有权**。本册没有创建这些文件；实现者应先确认无人占用，再按此边界工作。

### 11.1 建议独占文件

- `thesis/experiments/llm_probe/src/flow_probe/lspr24_stream_behavior_dataset.py`
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_stream_behavior_models.py`
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_stream_behavior_train.py`
- `thesis/experiments/llm_probe/configs/lspr24-stream-behavior-detection-v1.yaml`
- `thesis/experiments/llm_probe/scripts/run_lspr24_stream_behavior_detection.sh`

不得为增加命令入口修改 `pyproject.toml`；启动器统一使用 `python -m flow_probe.lspr24_stream_behavior_train`。

### 11.2 只读共享输入

- `.Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md`
- `<LSPR24_G0_RUN_ROOT>` 下通过 G0-D 收据登记的开发视图、字段清单、历史样本、锚点、评价簇和收据
- `<LSPR24_G0_RESTRICTED_ROOT>/development-labels.parquet`，只经既有受限接口读取
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_g0_tabular_adapter.py`
- `thesis/experiments/llm_probe/src/flow_probe/tracking.py`
- `thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py`
- `thesis/experiments/llm_probe/src/flow_probe/frozen_protocol.py`
- `thesis/experiments/llm_probe/src/flow_probe/unified_budget.py`
- `thesis/experiments/llm_probe/tools/env/activate.sh`
- `thesis/experiments/llm_probe/tools/lspr24_g0/**`

若共享接口不能支持本任务，优先在本任务独占模块内写薄适配层；涉及 G0 生产合同缺失时必须阻塞并交由数据生产进程处理，不得直接编辑共享 G0 代码。

### 11.3 独立运行根与 SwanLab 名称

- 本地／服务器独立运行根：`runs/candidates/lspr24-stream-behavior-detection-v1/`
- 运行名基串：`lspr24-stream-behavior-detection-v1`
- 阶段运行名格式：`lspr24-stream-behavior-detection-v1-{stage}-{variant}-seed{seed}`
- SwanLab 工作区：`mortiswang`
- SwanLab 项目：`malicious-traffic-llm`
- 跟踪模式：`online`

该运行根不得与跨年度实验、正常行为预测或攻击早期预警任务共享可变子目录。已存在但状态不明的同名运行根不得覆盖；先只读核验，不能确认可恢复时改用带时间戳的新尝试目录。

### 11.4 严禁修改的共享文件

- `.Codex/docs/RWKV/RWKV路线总控.md`
- `.Codex/docs/RWKV/RWKV当前恢复卡.md`
- `.Codex/docs/RWKV/2026-08-08-第三章候选方案登记册.md`
- `.Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md`
- `thesis/experiments/llm_probe/tools/lspr24_g0/**`
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_g0_tabular_adapter.py`
- 既有 `lspr24_screen_*`、跨年度 `crossyear_*`、早期预警与正常预测模块、配置和启动器
- `tracking.py`、`tabular_baselines.py`、`frozen_protocol.py`、`unified_budget.py`、`pyproject.toml`
- G0-F 最终封存、解封与一次性评价制品
- 其他代理的方案册、计划、笔记、日志与未提交改动

## 12. 阶段入口与制品合同

启动器应实现以下幂等阶段；每阶段只在前一阶段收据通过后继续。

| 阶段入口 | 允许动作 | 必需输出 | 明确禁止 |
| --- | --- | --- | --- |
| `g0-preflight` | 只读核验合同、G0-D 决策、输入哈希、路径边界和 SwanLab 目的地 | `receipts/g0-preflight.json` | 读任何最终区制品或原始 Parquet |
| `prepare-task-cache` | 从登记的 G0-D 视图派生流式样本索引与合法张量缓存 | `manifests/task-data.json`、`receipts/task-cache.json` | 重新切分、重拟合 G0 变换、复制受限标签 |
| `cpu-baselines` | 运行常数、逻辑、树与手工历史基线 | `baselines/summary.json`、共同分数清单 | 选择神经架构或读校准区阈值 |
| `architecture-gate` | 种子 42、最多 12 配置、30,000 更新，评价 40%–50% | 配置收据、预测、机制诊断、门槛裁决 | 读 `dev-validation`、校准或最终区来回调参 |
| `frozen-dev-validation` | 冻结配置后训练种子 43/44，并让 42/43/44 各评价 50%–60% 一次 | 三种子汇总、成簇置信区间、冻结收据 | 补种子、重选配置、改指标 |
| `calibrate-only` | 只对冻结分数拟合预注册单调校准器和阈值 | 校准器、阈值、Brier／ECE 收据 | 更新模型权重、字段、`H`、损失或搜索空间 |
| `freeze-package` | 固化代码、配置、输入、预测、统计程序和报告模板哈希 | `final-freeze-candidate.json` | 自行启动 G0-F 或查看最终结果 |

任何 GPU 阶段开始前，实施进程必须向控制进程报告服务器、GPU、运行根、SwanLab 运行名、配置数和预计预算；未经确认不得抢占正在运行的跨年度实验。

## 13. 后续实现的验收命令

以下命令是后续实施合同，**本方案编制过程未执行**。占位路径必须替换为实际已放行路径，命令不得指向最终区。

```bash
cd thesis/experiments/llm_probe
source tools/env/activate.sh

uv run --no-sync python -m py_compile \
  src/flow_probe/lspr24_stream_behavior_dataset.py \
  src/flow_probe/lspr24_stream_behavior_models.py \
  src/flow_probe/lspr24_stream_behavior_train.py

bash -n scripts/run_lspr24_stream_behavior_detection.sh
uv run --no-sync python -m flow_probe.lspr24_stream_behavior_train --help

bash scripts/run_lspr24_stream_behavior_detection.sh g0-preflight \
  --g0-run-root <已放行的LSPR24_G0_RUN_ROOT> \
  --g0-restricted-root <已放行的LSPR24_G0_RESTRICTED_ROOT> \
  --run-root runs/candidates/lspr24-stream-behavior-detection-v1

bash scripts/run_lspr24_stream_behavior_detection.sh prepare-task-cache \
  --run-root runs/candidates/lspr24-stream-behavior-detection-v1

bash scripts/run_lspr24_stream_behavior_detection.sh cpu-baselines \
  --run-root runs/candidates/lspr24-stream-behavior-detection-v1
```

在用户确认 5090 可用且无共享实验冲突后，才允许运行：

```bash
bash scripts/run_lspr24_stream_behavior_detection.sh architecture-gate \
  --run-root runs/candidates/lspr24-stream-behavior-detection-v1 \
  --seed 42

bash scripts/run_lspr24_stream_behavior_detection.sh frozen-dev-validation \
  --run-root runs/candidates/lspr24-stream-behavior-detection-v1 \
  --seeds 42,43,44

bash scripts/run_lspr24_stream_behavior_detection.sh calibrate-only \
  --run-root runs/candidates/lspr24-stream-behavior-detection-v1
```

验收不仅看退出码，还必须逐项核对：合同版本与 SHA、输入与样本清单哈希、五段行数仅含前 80%、历史重置计数、禁入字段计数为 0、共同预算收据、三种子门槛、机制诊断、校准只改校准器，以及 SwanLab 工作区／项目／运行名一致。

## 14. 阻塞条件与解锁动作

| 阻塞条件 | 必须动作 |
| --- | --- |
| G0-D 为 `NOT_READY` 或 `NO_GO` | 停止；等待 G0 生产／审查进程给出新收据，不得自行宣告通过 |
| 合同 SHA、输入哈希或字段清单不匹配 | 停止；由数据合同所有者裁决版本，不做兼容猜测 |
| 所需合法字段、历史样本、锚点或评价簇缺失 | 请求 G0 生产端扩展；任务代码不得扫原始数据补齐 |
| `architecture-selection` 或 `dev-validation` 正负评价簇不足 G0 门槛 | 标记任务不可充分评价；不得移动时间切点或重采样制造簇 |
| 强历史树、GRU／TCN、Transformer、Mamba、完整 RWKV 无法在共同预算运行 | 暂停候选裁决；不能用弱基线替代 |
| 任务运行根与其他实验共享可变文件 | 更换独立运行根并重新出输入哈希收据 |
| SwanLab 目的地不是冻结工作区／项目或 `online` 不可用 | GPU 正式运行不得启动；先修复跟踪环境 |
| 5090 显存探针失败 | 记录为配置预算内失败；不得临时降低仅候选模型的批量或维度 |
| 任一过程需要读取最终 20% | 立即停止并报告合同冲突；本实施进程无权扩展范围 |

## 15. 参考证据

1. Peng 等，*RWKV: Reinventing RNNs for the Transformer Era*，2023。[arXiv](https://arxiv.org/abs/2305.13048)；[官方源码](https://github.com/BlinkDL/RWKV-LM)。
2. Peng 等，*RWKV-7 “Goose” with Expressive Dynamic State Evolution*，2025。[arXiv](https://arxiv.org/abs/2503.14456)。
3. Sharma，*PLM-NIDS: A Protocol-Language Model for Network Intrusion Detection from Raw Packet Sequences Using RWKV State-Space Models*，2026。[arXiv](https://arxiv.org/abs/2606.00155)；[作者源码](https://github.com/shiva2vk/PLM-NIDS)。
4. Hou 与 Yu，*RWKV-TS: Beyond Traditional Recurrent Neural Network for Time Series Tasks*，2024。[arXiv](https://arxiv.org/abs/2401.09093)；[作者源码](https://github.com/howard-hou/RWKV-TS)。
5. 本地全文核验：`wiki/papers/rwkv/2026-Sharma-PLM-NIDS-RWKV协议语言入侵检测.md`、`wiki/papers/rwkv/2024-Hou-RWKV-TS-时间序列.md`、`wiki/papers/rwkv/2026-Yang-FRWKV-Plus-信任门控周期校正.md`、`wiki/papers/rwkv/2026-Rizki-RWKV-CVM门控跨变量混合.md`、`wiki/papers/rwkv/2025-Zhang-STWGRL时空加权图推理异常检测.md`。
6. 数据与评价事实源：`.Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md` 与 `.Codex/docs/RWKV/2026-08-06-LSPR24-G0合同v5修订记录.md`。

## 16. 交接状态

- **已完成**：任务定义、文献迁移矩阵、候选排序、公式、强基线、可观测量、最小消融、否决门槛、原创边界、数据代价、文件所有权、阶段入口、验收命令与阻塞条件。
- **未完成且不得冒充完成**：任何生产代码、G0-D 实例放行、真实基线、GPU 训练、SwanLab 运行、开发验证、校准或最终评价。
- **当前科学状态**：设计可行；全部性能和机制主张均为实验待证。
