# LSPR24 正常行为预测任务方案册

- **文档状态**：自包含实施交接包；设计可行，实验待证
- **适用日期**：2026-08-12
- **唯一数据集**：LSPR24
- **冻结数据合同**：`lspr24-g0-v5-staged`
- **合同 SHA-256**：`877488f3529c6c862b060a74782d1904aae81512ea1169c713ba20d8c3f31a0e`
- **方案编制代理**：`/root/rwkv_application_transfer_patterns_sol_max`
- **模型与推理强度**：`gpt-5.6-sol`，`effort=max`
- **本册边界**：只研究合法字段的下一窗口生成预测，不实现代码、不启动实验、不读取最终 20%

## 1. 执行结论

本任务最值得验证的不是普通均方误差预测，而是“**RWKV 因果状态 + 字段类型化概率似然**”：让不同语义字段使用与数据类型相符的概率头，以严格正常训练掩码学习下一窗口分布，并用 proper score 判断模型是否真的学到了行为规律。

| 排名 | 候选 | 本册裁决 | 主要理由 |
| --- | --- | --- | --- |
| 1 | `NBP-1` 字段类型化似然 RWKV | **主候选** | 与 G0 v5 已冻结的 `generation_target` 和似然族选择接口完全相容；可区分计数、零膨胀、正连续和类别字段，生成质量可直接证伪 |
| 2 | `NBP-2` 离散行为码 RWKV 语言模型 | **条件候选** | PLM-NIDS 提供安全相邻先例，能产生因果惊异度；但码本造成信息损失和额外数据工程，必须先击败 `n` 元语法和马尔可夫链 |
| 3 | `NBP-3` RWKV-TS 式分块数值预测 | **必要架构基线** | 提供完整任务化 RWKV 数值预测对照；普通回归头已属既有范式，不能作为主要原创点 |
| 4 | 图、多尺度频域、跨批长历史或在线目标适应 | **当前否决** | LSPR24 `H<=32` 尚无稳定图、周期或跨批收益证据；在线适应违反 60%–80% 只校准和最终冻结边界 |

“正常”必须解释为：按当前 LSPR24 冻结标签，输入历史和目标窗口均未与红队活动关联。它不是已由攻击叙事或人工审计证明的纯净正常，也不保证不存在漏标、背景异常或合法但罕见行为。

## 2. 唯一任务与合法监督

### 2.1 任务定义

设 `x_t` 为受保护端点在窗口 `t` 结束时可用的合法字段，`x_(t+1)^gen` 是同一端点、同一连续段、同一分区的下一窗口冻结生成字段。模型在 `window_end_t` 输出下一窗口分布参数：

```text
eta_(t+1) = G(x_[t-H+1:t], m_[t-H+1:t])
x_hat_(t+1)^gen ~ p(x_(t+1)^gen | eta_(t+1))
```

其中 `H∈{1,4,16,32}`，主节拍固定为 5 秒。每个生成目标必须在 `field-manifest.json` 中满足 `generation_target=true`，且可用时间不晚于目标窗口结束时。

G0 v5 冻结的生成字段覆盖：

- 流数量；
- 双向包数与字节数；
- 持续时间、包长、到达间隔；
- 活动／空闲统计；
- 不依赖端口的协议分布与连接状态分布。

身份、端口、绝对时间、标签、IDS 输出和缺失掩码本身不能作为生成内容目标。缺失掩码只决定相应似然项是否计分。

### 2.2 正常训练掩码

生成器只能在 `train-fit` 中满足以下条件的样本上反向传播：

```text
normal_train_mask_t =
  1[history_labels_[t-H+1:t] 全部为0]
  * 1[label_(t+1) = 0]
  * 1[target_exists]
  * 1[same_endpoint_and_segment]
  * 1[no_split_or_guard_crossing]
```

标签只进入受限训练掩码，绝不作为模型输入、嵌入、门控、采样权重特征或生成目标。推断时对所有有完整上一预测的窗口计分，不根据标签屏蔽。

### 2.3 因果惊异度时间轴

模型在窗口 `t-1` 完成时产生 `eta_t`。窗口 `t` 完成后，才能计算：

```text
s_gen,t = -log p(x_t^gen | eta_t)
```

不得用 `x_t` 产生的 `eta_(t+1)`、`x_(t+1)` 或未来标签反过来给窗口 `t` 计分。重置后没有完整上一预测时，必须写 `generation_score_available=0`；不得填 0、均值或测试统计。

本任务的主目标是预测分布质量。`s_gen,t` 对红队关联窗口的区分能力只是生成器冻结后的**次级异常诊断**，不是未来风险、提前预警或当前监督分类的替代品。

## 3. 精确 60/20/20 与前 60 内部 40/10/10

切分按活动秒时间秩完成，不按流量行、窗口、标签比例或端点数完成。

| 数据区间 | G0 v5 名称 | 正常预测任务中的唯一用途 | 禁止事项 |
| --- | --- | --- | --- |
| 0%–40% | `train-fit` | 拟合归一化、量化码本、生成似然族；正常掩码训练；训练内诊断 | 不得用后续分区拟合任何变换或似然族 |
| 40%–50% | `architecture-selection` | 种子 42 的架构、`H`、字段头和超参数选择 | 不得用攻击区分 AP 选择生成器 |
| 50%–60% | `dev-validation` | 冻结候选的种子 42/43/44 一次性生成质量验证；冻结后才做一次异常区分诊断 | 不得根据诊断重选架构、似然或字段 |
| 60%–80% | `calibration` | 仅冻结预测分布的温度、尺度或覆盖率校准；若输出惊异度阈值，也只能在此冻结 | **只允许校准**；不得重训、选似然、选码本、选字段或选 `H` |
| 80%–100% | `final-test` | 所有方法与统计程序冻结后的唯一最终评价 | 当前实施进程零访问、零统计、零哈希、零成员信息 |

因此，高层协议严格是：前 60% 开发，其中 0%–40% 训练、40%–50% 选择、50%–60% 一次验证；60%–80% 只校准；最后 20% 封存。跨年度结果不进入本任务协议。

### 3.1 前 80% 能否合法构造标签与目标

| 所需信号 | 前 80% 是否可合法构造 | 合法来源与用途 |
| --- | --- | --- |
| 下一窗口生成目标 | **可以，但需门禁确认** | `field-manifest.json` 中 `generation_target=true` 的合法字段；同端点同段索引由 `history-samples.parquet` 派生 |
| 正常训练掩码 | **可以** | 受限开发标签侧车；只在 `train-fit` 控制损失是否反向传播 |
| 生成质量评价 | **可以** | 40%–60% 合法生成目标；不依赖攻击标签选择架构 |
| 惊异度异常诊断 | **可以** | 候选冻结后，在 `dev-validation` 一次连接开发标签；不得回流模型选择 |
| 概率／方差校准 | **可以** | 60%–80% 的合法目标，只调整冻结分布的校准参数 |
| 最终性能 | **当前不可以** | 80%–100% 只能由 G0-F 冻结流程一次性解封评价 |

若实际 G0-D 制品尚未物化生成目标索引或 `generation_target` 字段为空，本任务处于阻塞态；方案册中的合同定义不能替代真实制品。

## 4. 已核验文献事实与移植矩阵

| 工作 | 保留的 RWKV 机制 | 替换的输入／输出 | 新增任务模块与训练目标 | 是否完整使用原生 RWKV | 对本任务的事实边界 |
| --- | --- | --- | --- | --- | --- |
| RWKV 原论文与官方实现 | 时间混合、通道混合；并行训练与固定大小递归状态 | 文本词元输入，下一词元输出 | 因果语言建模交叉熵 | **是** | 支持下一步因果预测接口，不支持数值字段似然或安全效果 |
| RWKV-7 Goose | 向量衰减、移除键和动态状态演化 | 仍以语言序列为主 | 下一词元目标 | **完整层使用时是**；只抽取状态核时不是 | 提供现代状态更新参照；不自动带来更好异常分数 |
| PLM-NIDS | RWKV-4 因果语言模型 | 包元数据离散成协议词元；输出下一词元分布 | 良性序列交叉熵与困惑度异常；可加监督头 | **完整 RWKV-4 骨干，但任务已改造** | 直接支持“正常协议预测惊异度用于 NIDS”；只有 CIC-IDS-2017，缺强树和现代时序对照，不能证明 LSPR24 有效 |
| RWKV-TS | 时间混合与通道混合 | 实例归一化、分块数值序列；输出预测、分类、填补或异常头 | 回归、分类、重建等任务目标 | **完整任务化 RWKV 块** | 支持数值预测迁移；异常检测平均结果低于 TimesNet，不能称普遍最优 |
| RWKV-CVM | RWKV-TS 时序骨干 | 多变量负荷序列 | 轻量门控跨变量混合，仍用预测损失 | **否，增加前置任务模块** | 表明跨字段混合可小幅增益，但平均 MSE 相对改善约 1.8%，且在全量数据上并非最优 |
| MSRWKV-2DTCN | RWKV 式时间混合 | 光伏多变量序列 | 快速傅里叶变换多尺度支路，以二维时序卷积替换通道混合 | **否** | 说明时序骨干可大幅任务化；收益依赖光伏周期，不能迁移成 LSPR24 周期主张 |
| STWGRL | D-RWKV 时序编码 | 多变量传感器序列 | 去噪、自学习有向图和重建／异常目标 | **否** | 图稀疏正则在一个数据集上有负效应，故图模块必须先有数据证据 |
| FRWKV+ | RWKV 式频域状态 | 频域数值输入与预测输出 | 零初始化、有界信任校正 | **否** | 支持对基础预测做保守校正的结构先例，不证明流量惊异度有效 |

### 4.1 文献事实与本课题推论的分界

**文献事实：**正常序列上的下一词元交叉熵可以产生异常惊异度；RWKV 可以由文本词元迁移到数值分块、预测头和多变量混合；不同任务常替换输入编码、输出头与训练目标，而只保留 RWKV 因果状态。

**本课题推论：**LSPR24 的计数、零膨胀正值、正连续值和类别分布不适合用一个统一高斯均方误差头；字段类型化似然可能产生更可校准的下一窗口分布和惊异度。这必须在强概率基线和字段头消融下验证，不能由 PLM-NIDS 或 RWKV-TS 的结果直接推出。

## 5. 主候选 `NBP-1`：字段类型化似然 RWKV

### 5.1 共享因果状态

```text
e_t = FieldEncoder(x_t, m_t)
h_t = RWKV(h_(t-1), e_t)
theta_(t+1,j) = Head_j(h_t, q_t)
```

`q_t` 只含字段清单允许的历史覆盖、缺失、截断与重置质量信息。状态在端点、连续段、分区和隔离带边界清空。实现必须明确记录所用官方 RWKV 版本；若只抽取 RWKV-7 状态核，不能称完整原生 RWKV-7。

### 5.2 字段类型化概率头

候选似然族必须先在 `train-fit` 的无标签分布拟合诊断中预注册，每个语义组最多 6 种；选定后供全部含生成头模型共同使用，不能根据攻击检测结果为某个候选单独挑选。

| 字段类型 | 首选候选族 | 输出参数与约束 | 强基线 |
| --- | --- | --- | --- |
| 非负计数 | 负二项、泊松 | 均值经 `softplus`，离散度为正 | 持久性计数、边际泊松／负二项、XGBoost 计数回归 |
| 零膨胀计数 | 零膨胀负二项 | 零概率经 `sigmoid`，均值／离散度为正 | 零膨胀边际模型、两阶段树模型 |
| 正连续值 | 对数正态、Student-t | 尺度为正；Student-t 自由度受下界约束 | 对数域持久性、滚动中位数、异方差树／线性模型 |
| 类别分布 | 多项分布或 Dirichlet-多项 | 概率经 `softmax`；掩码字段不计分 | 边际频率、马尔可夫链、分类树 |

### 5.3 损失与惊异度

设 `o_(t+1,j)` 为目标字段是否可观测：

```text
L_gen =
  sum_j normal_train_mask_t * o_(t+1,j) * w_j
        * [-log p_j(x_(t+1,j) | theta_(t+1,j))]
  / sum_j normal_train_mask_t * o_(t+1,j) * w_j
```

权重 `w_j` 必须只由 `train-fit` 的字段组规模或预注册等权规则确定。禁止按攻击区分能力调整字段权重。

冻结生成器后，窗口惊异度为：

```text
z_(t,j) = Calibrate_j(-log p_j(x_(t,j) | theta_(t,j)))
r_t = sum_j o_(t,j) * rho_j * z_(t,j) / sum_j o_(t,j) * rho_j
```

`Calibrate_j` 只能在 60%–80% 对冻结预测分布做温度、尺度或覆盖率校准；`rho_j` 在读取 `architecture-selection` 前预注册，不能依据攻击标签调大某些字段。缺失字段不计分，不能以 0 惊异度替代。

### 5.4 质量门控的可选扩展

只有基本类型化似然先通过后，才验证：

```text
u_t = sigmoid(w_u^T q_t + c_u)
r_t^quality = u_t * r_t + (1-u_t) * r_marginal,t
```

该门只在历史覆盖不足、刚重置或字段缺失较多时，在状态惊异度与训练区边际惊异度之间保守回退。门不能读取标签、端点身份或后续统计。若固定回退已足够，删除可学习门。

## 6. 条件候选与不采用方向

### 6.1 `NBP-2`：离散行为码 RWKV 语言模型

量化器和词表只在 `train-fit` 拟合。令 `c_t=Quantize(x_t^gen)`：

```text
L_code = normal_train_mask_t * CE(c_(t+1), P(c_(t+1) | c_[t-H+1:t]))
s_code,t = -log P(c_t | c_[t-H:t-1])
```

该范式更接近 PLM-NIDS，但必须增加码本占用、未知码率、身份可反推、跨分区拟合和信息损失门禁。只有在同一行为码上同时击败固定阶 `n` 元语法、马尔可夫链和频率边际模型后，才允许进入三种子验证。

### 6.2 `NBP-3`：RWKV-TS 式分块数值预测

对合法连续字段做训练区实例归一化或冻结归一化、时间分块与 RWKV 编码，再以线性头输出下一窗口点预测，优化 MAE、Huber 或 MSE。它是完整任务化 RWKV 的必要基线，但点预测不能直接与概率 NLL 混为一个指标；需要用 `train-fit` 残差拟合共同冻结的误差分布，才能参加概率评分比较。

### 6.3 当前不采用

- **统一高斯 MSE 主模型**：无法正确表达零膨胀计数、重尾正值与类别分布，只保留为消融。
- **频域／多尺度分支**：LSPR24 禁止绝对时间特征，且训练区尚未证明稳定周期；光伏预测证据不能外推。
- **图关系模块**：G0 受保护端点视图未冻结无身份、无捷径的图；不得用 IP 或端口构图。
- **跨批状态与超长历史**：`H<=32`，RWKV-TS+ 表明更长历史收益并不单调；先验证 `H>1` 是否优于 `H=1`。
- **在线目标适应或伪正常更新**：会让校准与测试数据改变生成器，违反冻结合同。
- **攻击标签联合分类损失**：本册主任务是正常行为预测；若需要监督检测，应另用流式行为检测方案册，不能用联合标签目标掩盖生成质量失败。

## 7. 共同预算强基线

所有基线共享合法生成字段、正常训练掩码、历史支持、非重叠锚点、评价簇和计分掩码。

| 基线组 | 必须具备的能力 | 它回答的问题 |
| --- | --- | --- |
| 上一窗口持久性 | `x_hat_(t+1)=x_t` | 是否存在无需学习即可利用的局部连续性 |
| 训练区边际分布 | 每字段固定概率分布 | 状态模型是否超过无条件正常性 |
| 因果滚动均值／中位数／指数滑动 | 不用绝对时间的简单历史 | RWKV 是否超过低成本平滑器 |
| AR／VAR／岭回归 | 线性多步字段依赖 | 非线性状态是否必要 |
| 每字段 XGBoost／多输出树 | 强非线性当前和展平历史 | RWKV 是否超过强表格预测 |
| `n` 元语法／马尔可夫链 | 离散行为码的计数记忆 | `NBP-2` 是否需要神经语言模型 |
| GRU、TCN | 因果递归与局部卷积 | RWKV 是否优于常见轻量时序模型 |
| 因果 Transformer、TimesNet | 精确窗口注意力与强时序模式 | RWKV 是否只受益于一般序列容量 |
| 完整官方 RWKV、RWKV-TS | 原生状态核与数值分块 | 类型化概率头是否带来独立增益 |
| 统一高斯头、类型化头、质量回退 | 同骨干控制变量 | 似然族与可靠性机制各自是否有效 |

确定性基线参加 NLL 比较时，必须仅用 `train-fit` 残差拟合统一误差分布；不能在验证区为每个基线单独调方差。神经与树模型仍遵守 G0-A13 的 1–12 配置、有效批量 256、30,000 更新、单检查点与三种子规则。

## 8. 评价指标、可观测量与最小消融

### 8.1 主评价

架构选择只能使用与攻击标签无关的生成质量：

- **主指标**：字段组等权的标准化负对数似然 `NLL_group`；各字段以 `train-fit` 边际 NLL 的绝对尺度加固定下界 `tau=1e-6` 标准化，权重在首次验证前冻结。
- **连续字段**：MAE、RMSE、CRPS、50%／90% 预测区间覆盖率与宽度。
- **计数字段**：Poisson／负二项偏差、零值 Brier 分数。
- **类别字段**：交叉熵、宏平均 Brier 分数、期望校准误差。
- **效率**：每窗口延迟、吞吐率、峰值显存和单端点状态字节。

候选冻结后，才在 `dev-validation` 一次报告惊异度对 `window_label` 的 AP、ROC-AUC 和固定误报率召回。该诊断不能回流架构、似然、字段权重或 `H` 选择。

### 8.2 机制可观测量

- 每个语义组和每个字段的 NLL、偏差、MAE、覆盖率与有效观测数。
- 训练损失中各字段头的梯度份额，防止大尺度字段吞噬其他目标。
- 预测均值、尺度、离散度、自由度、零膨胀概率的分位数与边界命中率。
- RWKV 状态范数、非有限值、状态重置次数与每端点状态字节。
- `H=1/4/16/32` 的生成质量变化与历史覆盖率。
- 状态时间置乱、端点内历史置乱和状态清零后的 NLL 变化。
- 惊异度字段贡献、极端值来源、缺失字段占比和质量回退门分布。
- `NBP-2` 的词表占用、未知码率、码本困惑度、身份／绝对时间反预测探针。

### 8.3 最小消融矩阵

| 编号 | 模型 | 唯一目的 |
| --- | --- | --- |
| P0 | 上一窗口持久性 + 训练区误差分布 | 最小可用预测基线 |
| P1 | 每字段训练区边际概率模型 | 无状态概率基线 |
| P2 | 强 XGBoost 展平历史预测 | 强非神经历史基线 |
| P3 | GRU／Transformer 中最好者 | 强神经时序基线 |
| P4 | 完整官方 RWKV + 统一高斯头 | 原生状态与普通头对照 |
| P5 | RWKV + 字段类型化似然 | `NBP-1` 核心 |
| P6 | P5 + 质量回退 | 完整可选主候选 |
| P7 | P5，但端点内历史置乱 | 验证历史状态是否真实使用 |
| P8 | P5，`H=1/4/16/32` | 确定历史收益与饱和点 |
| C0–C2 | `n` 元语法、马尔可夫链、RWKV 行为码 | 仅用于 `NBP-2` 门禁 |

若 P5 不优于 P4，删除“字段类型化似然贡献”；若 P6 不优于 P5，删除质量门；若 P7 与 P5 等价，删除“RWKV 历史状态贡献”。

## 9. 预注册否决门槛

### 9.1 数据与实现硬否决

出现任一项即停止受影响运行，结果标记为无效：

1. G0 v5 合同版本／SHA 不匹配，或 G0-D 未放行。
2. `generation_target=true` 字段为空、目标索引缺失或目标跨端点、连续段、隔离带、分区。
3. 正常掩码没有同时覆盖完整历史和目标窗口，或标签进入输入张量。
4. 量化器、似然族、归一化器、字段权重或残差分布使用 40% 之后数据拟合。
5. 读取原始标签列页、最终 20%、攻击叙事或禁入字段。
6. 概率参数非法、NLL 非有限、掩码分母为 0、状态重置断言失败。
7. 基线的字段、掩码、样本、分数清单或预算与候选不一致。

### 9.2 种子 42 淘汰门

在 `architecture-selection` 上，令 `Q` 为字段组等权标准化 NLL，越低越好：

```text
Q_strong = min(Q_最强非神经基线, Q_最强共同预算神经基线)
relative_gain = (Q_strong - Q_candidate) / max(abs(Q_strong), 1e-6)
```

- `relative_gain < 1%`：否决候选进入三种子正式开发验证。
- 至少三个可用语义组中，改善组少于两个：否决“普遍字段预测改善”主张。
- 任一语义组相对其最强基线恶化超过 2%：不得以总分掩盖；主候选否决或删除该字段组的机制主张，但不能事后删除合法目标字段。
- `H>1` 相对 `H=1` 的 `Q` 改善小于 1%，或历史置乱相对完整模型恶化小于 1%：否决“RWKV 历史机制”，降格为无状态／短状态头比较。
- P5 相对统一高斯头 P4 改善小于 1%：否决字段类型化似然贡献。
- P6 相对 P5 改善小于 0.5%，或回退门在超过 95% 样本上固定落在同一端点区间：删除质量门。
- `NBP-2` 的有效词表占用低于 10%、未知码率高于 1%，或交叉熵未比最好 `n` 元语法／马尔可夫链降低至少 1%：否决离散语言模型。

仅惊异度 AP 增加而生成 `Q` 未通过，不得挽救生成候选；这通常意味着偶然利用异常幅值，而不是更好的正常行为预测。

### 9.3 冻结开发验证门

种子 42 通过后，配置冻结，种子 43、44 按同一配置训练。三种子在 `dev-validation` 各评价一次：

- 三个种子的 `relative_gain` 均大于 0；
- 三种子相对最强基线的中位相对改善至少 1%；
- 成簇配对自助法的汇总差值 95% 置信区间不跨 0；
- 至少两个语义组在三个种子上方向一致，任何组不得恶化超过 2%；
- 历史置乱在三个种子中的中位 `Q` 至少恶化 1%，否则撤销历史状态主张。

候选冻结后进行一次异常诊断。只有惊异度 AP 比“最好简单预测残差”高至少 0.005，才允许在论文中把异常区分作为次级结果；未达到时仍可保留预测任务结论，但不得称其为安全检测方法。

### 9.4 校准与最终边界

60%–80% 只允许：温度缩放、方差尺度、分位覆盖率校准，以及在预先声明需要异常阈值时冻结该阈值。不得更新 RWKV、字段编码、概率头、量化器、似然族、`H`、字段权重或正常掩码。当前实施进程不得启动 G0-F；最终 20% 由后续冻结评价进程一次性处理。

## 10. 原创边界

### 10.1 不能主张

- 不能主张首次用 RWKV 学习正常协议语言或以困惑度做网络入侵检测；PLM-NIDS 已覆盖。
- 不能主张首次把 RWKV 用于时间序列预测、异常检测或多变量建模；RWKV-TS、STWGRL、RWKV-CVM 等已覆盖。
- 不能主张下一窗口预测、字段类型化概率头、零膨胀似然、惊异度或质量门中的单一组件原创。
- 不能把“只用 LSPR24”“时间前向切分”或 G0 正常掩码合同本身写成模型算法创新。

### 10.2 只有实验通过后可形成的贡献

可候选表述为：在 LSPR24 G0 v5 严格时间前向和受限正常掩码下，构建按网络行为字段语义选择概率族的 RWKV 因果生成器，并通过 proper score、字段组消融、历史置乱和强概率基线证明类型化似然与 RWKV 状态各自提供独立的下一窗口预测增益；冻结后再评价其惊异度的安全诊断价值。

该贡献是**任务化概率建模、因果合同和实证机制验证的组合**。若预测主门槛未通过，不能仅凭异常 AP 或可视化保留原创主张。

## 11. 数据与算力代价

| 项目 | 代价 | 控制方式 |
| --- | --- | --- |
| 新数据集 | 无；严格只用 LSPR24 | 不接入 LSPR23 或其他异常数据训练、调参或拟合码本 |
| 原始数据扫描 | 无新增扫描 | 只读消费 G0-D；缺目标索引时由 G0 生产端扩展 |
| 任务缓存 | 中等偏高 | 保存目标列索引、合法张量块、观察掩码和哈希；不复制原始流或受限标签 |
| 概率头 | 中等 | 按语义组共享小头，避免逐列超大头；参数计数纳入统一预算 |
| 候选似然诊断 | CPU 中等 | 每语义组最多 6 个，只在 `train-fit` 无标签分布上选择一次，供所有生成模型共用 |
| 神经训练 | 单张 5090 可行性待真实探针 | `H<=32`、有效批量 256、混合精度；30,000 更新，显存失败计入预算 |
| 行为码路线 | 中到高 | 仅在连续主候选门禁后运行；增加码本与词元缓存但不新增数据集 |
| 最终测试 | 当前为零 | 本实施进程不创建、统计或访问 G0-F 制品 |

### 11.1 理论深度、第三章工作量与 5090 可实验性

| 维度 | `NBP-1` | `NBP-2` | 裁决 |
| --- | --- | --- | --- |
| 当前实验约束 | 不再依赖跨年度弱分类骨干；先用独立 proper score 判断历史状态是否真实可预测 | 跨年度候选没有证明行为码或后缀记忆增益，离散化风险更高 | `NBP-1` 优先 |
| 理论对象 | 类型化似然、掩码经验风险、严格适当评分、因果惊异度、质量回退退化条件 | 码本信息损失、离散交叉熵与惊异度 | `NBP-1` 的统计对象更清楚且更可证伪 |
| 章级实验对象 | 概率基线、似然族、字段组、历史置乱、`H`、校准、效率和次级异常诊断 | 再增加码本、身份探针、`n` 元语法和未知码分析 | `NBP-1` 可独立成章；`NBP-2` 只在门禁后扩展 |
| 单张 5090 | `H<=32`、共享小状态和字段组小头；微批与梯度累积保持有效批量 256 | 大词表输出层可能增加显存与缓存 | 先对 `NBP-1` 做输出头规模和显存探针 |

若主门槛通过，`NBP-1` 可形成“合法正常监督—类型化概率模型—因果评分性质—训练算法—强概率基线—字段／历史消融—校准—安全诊断边界”的章级论证链，其功能完整度可参照朱焱雷第三章。不得以公式、图表或页数替代真实预测增益。朱论文历史效果量级和 `16.1%` 错误相对下降不是本任务硬门槛；本册以生成 proper score、多种子一致性、置信区间、字段困难分面和效率共同裁决。被实验否决的概率头或质量门不得为工作量保留。

## 12. 独立实现文件边界

以下是后续“LSPR24 正常行为预测”实施进程的**建议独占所有权**。本册没有创建这些代码；实现者应先确认无人占用。

### 12.1 建议独占文件

- `thesis/experiments/llm_probe/src/flow_probe/lspr24_normal_behavior_dataset.py`
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_normal_behavior_models.py`
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_normal_behavior_train.py`
- `thesis/experiments/llm_probe/configs/lspr24-normal-behavior-prediction-v1.yaml`
- `thesis/experiments/llm_probe/scripts/run_lspr24_normal_behavior_prediction.sh`

不得修改 `pyproject.toml` 添加入口；启动器使用 `python -m flow_probe.lspr24_normal_behavior_train`。

### 12.2 只读共享输入

- `.Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md`
- `<LSPR24_G0_RUN_ROOT>/views/development-windows.parquet`
- `<LSPR24_G0_RUN_ROOT>/views/history-samples.parquet`
- `<LSPR24_G0_RUN_ROOT>/manifests/field-manifest.json`
- `<LSPR24_G0_RUN_ROOT>/receipts/field-lineage-and-tensor-probe.json`
- `<LSPR24_G0_RUN_ROOT>/manifests/inference-anchor-manifest.parquet`
- `<LSPR24_G0_RUN_ROOT>/manifests/evaluation-clusters.parquet`
- `<LSPR24_G0_RESTRICTED_ROOT>/development-labels.parquet`，仅经受限接口构造正常掩码与冻结后诊断
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_g0_tabular_adapter.py`
- `thesis/experiments/llm_probe/src/flow_probe/tracking.py`
- `thesis/experiments/llm_probe/src/flow_probe/tabular_baselines.py`
- `thesis/experiments/llm_probe/src/flow_probe/frozen_protocol.py`
- `thesis/experiments/llm_probe/src/flow_probe/unified_budget.py`
- `thesis/experiments/llm_probe/tools/env/activate.sh`
- `thesis/experiments/llm_probe/tools/lspr24_g0/**`

如果 G0-D 没有登记合法生成目标，不能在本任务数据集模块中打开原始 Parquet 补做；必须请求 G0 生产端扩展并重新出具字段谱系、样本与哈希收据。

### 12.3 独立运行根与 SwanLab 名称

- 本地／服务器独立运行根：`runs/candidates/lspr24-normal-behavior-prediction-v1/`
- 运行名基串：`lspr24-normal-behavior-prediction-v1`
- 阶段运行名格式：`lspr24-normal-behavior-prediction-v1-{stage}-{variant}-seed{seed}`
- SwanLab 工作区：`mortiswang`
- SwanLab 项目：`malicious-traffic-llm`
- 跟踪模式：`online`

该运行根不得与跨年度实验、流式检测或攻击早期预警共享可变子目录。不得覆盖状态不明的同名运行；应先只读核验，无法确认可恢复时新建带时间戳的尝试目录。

### 12.4 严禁修改的共享文件

- `.Codex/docs/RWKV/RWKV路线总控.md`
- `.Codex/docs/RWKV/RWKV当前恢复卡.md`
- `.Codex/docs/RWKV/2026-08-08-第三章候选方案登记册.md`
- `.Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md`
- `thesis/experiments/llm_probe/tools/lspr24_g0/**`
- `thesis/experiments/llm_probe/src/flow_probe/lspr24_g0_tabular_adapter.py`
- 既有 `lspr24_screen_*`、跨年度 `crossyear_*`、早期预警与流式检测模块、配置和启动器
- `tracking.py`、`tabular_baselines.py`、`frozen_protocol.py`、`unified_budget.py`、`pyproject.toml`
- G0-F 最终封存、解封与一次性评价制品
- 其他代理的方案册、计划、笔记、日志与未提交改动

## 13. 阶段入口与制品合同

| 阶段入口 | 允许动作 | 必需输出 | 明确禁止 |
| --- | --- | --- | --- |
| `g0-preflight` | 只读核验合同、G0-D、目标字段、正常掩码来源、输入哈希和跟踪目的地 | `receipts/g0-preflight.json` | 读最终区、原始 Parquet 或攻击叙事 |
| `prepare-task-cache` | 从登记 G0-D 视图派生下一窗口目标索引、掩码和合法张量缓存 | `manifests/task-data.json`、`receipts/task-cache.json` | 重新切分、复制受限标签、跨边界配对 |
| `likelihood-family-gate` | 只用 `train-fit` 无标签分布，在每语义组最多 6 个候选中选共同似然 | 共同似然清单、拟合诊断和哈希 | 用攻击标签、40% 之后数据或候选模型结果选似然 |
| `cpu-baselines` | 持久性、边际、滚动、AR／VAR、树、`n` 元语法 | 基线预测、分数与共同清单 | 用异常 AP 选择生成结构 |
| `architecture-gate` | 种子 42、最多 12 配置、30,000 更新，评价 40%–50% 生成质量 | 配置、预测、字段诊断和门槛裁决 | 读 50% 以后结果回调参 |
| `frozen-dev-validation` | 冻结配置后运行 43/44，三种子各评价 50%–60% 一次；之后一次连接标签做异常诊断 | 严格适当评分、成簇置信区间、诊断与冻结收据 | 用异常诊断重选架构或补种子 |
| `calibrate-only` | 对冻结分布做温度／尺度／覆盖率校准，必要时冻结惊异度阈值 | 校准器、覆盖率、阈值与收据 | 更新生成器、量化器、似然、字段权重或 `H` |
| `freeze-package` | 固化代码、配置、输入、预测、统计程序和报告模板哈希 | `final-freeze-candidate.json` | 启动 G0-F 或查看最终结果 |

任何 GPU 阶段开始前，实施进程必须报告服务器、GPU、运行根、SwanLab 运行名、配置数、输出头规模和预计显存；不得干扰根进程正在执行的跨年度实验。

## 14. 后续实现的验收命令

以下是后续实施合同，**本方案编制过程未执行**。占位路径只允许替换为已经通过 G0-D 的开发路径。

```bash
cd thesis/experiments/llm_probe
source tools/env/activate.sh

uv run --no-sync python -m py_compile \
  src/flow_probe/lspr24_normal_behavior_dataset.py \
  src/flow_probe/lspr24_normal_behavior_models.py \
  src/flow_probe/lspr24_normal_behavior_train.py

bash -n scripts/run_lspr24_normal_behavior_prediction.sh
uv run --no-sync python -m flow_probe.lspr24_normal_behavior_train --help

bash scripts/run_lspr24_normal_behavior_prediction.sh g0-preflight \
  --g0-run-root <已放行的LSPR24_G0_RUN_ROOT> \
  --g0-restricted-root <已放行的LSPR24_G0_RESTRICTED_ROOT> \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1

bash scripts/run_lspr24_normal_behavior_prediction.sh prepare-task-cache \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1

bash scripts/run_lspr24_normal_behavior_prediction.sh likelihood-family-gate \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1

bash scripts/run_lspr24_normal_behavior_prediction.sh cpu-baselines \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1
```

只有用户确认 5090 可用、SwanLab `online` 可用且没有共享实验冲突后，才允许运行：

```bash
bash scripts/run_lspr24_normal_behavior_prediction.sh architecture-gate \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1 \
  --seed 42

bash scripts/run_lspr24_normal_behavior_prediction.sh frozen-dev-validation \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1 \
  --seeds 42,43,44

bash scripts/run_lspr24_normal_behavior_prediction.sh calibrate-only \
  --run-root runs/candidates/lspr24-normal-behavior-prediction-v1
```

验收必须核对：合同版本与 SHA、目标字段清单、下一窗口配对哈希、正常掩码覆盖、边界重置、禁入字段计数、似然族只用 `train-fit`、共同样本与分数清单、概率参数合法、三种子门槛、异常诊断未回流选择、校准只改校准参数，以及 SwanLab 目的地一致。

## 15. 阻塞条件与解锁动作

| 阻塞条件 | 必须动作 |
| --- | --- |
| G0-D 为 `NOT_READY` 或 `NO_GO` | 停止；等待 G0 生产／审查进程给出新收据，不得自行放行 |
| 合同 SHA、字段清单、历史样本或输入哈希不匹配 | 停止；由数据合同所有者裁决，不做兼容猜测 |
| `generation_target=true` 字段为空或下一窗口索引未物化 | 请求 G0 生产端扩展；任务代码不得重扫原始数据 |
| `train-fit` 正常历史—目标配对不足 1,000，或任一待评价 `H` 在选择／验证／校准区非重叠锚点不足 200 | 标记该 `H` 不可评价；不得移动切点、缩短历史后仍沿用原主张 |
| 可用生成语义组少于 4 | 阻塞主候选；先核验字段可用性和 G0-A07，不得用单一大字段组冒充多行为预测 |
| 正常掩码需要标签进入模型张量或复制受限标签 | 停止；改为受限加载器内的布尔损失掩码 |
| 强概率、强树、GRU／TCN、Transformer／TimesNet、完整 RWKV 基线无法共同运行 | 暂停候选裁决；不能以弱基线替代 |
| 概率头输出非法、NLL 非有限或大部分字段头无梯度 | 记录实现失败并定位根因；不能用剪除困难字段伪造通过 |
| 任务运行根与其他实验共享可变路径 | 更换独立运行根，重新出具输入与制品哈希 |
| SwanLab 目的地错误或 `online` 不可用 | GPU 正式运行不得启动；先修复跟踪环境 |
| 5090 显存探针失败 | 计入配置预算；不得只降低候选模型预算而保持基线不变 |
| 任一阶段需要读取最终 20% | 立即停止并报告合同冲突；本实施进程无权扩展范围 |

## 16. 参考证据

1. Peng 等，*RWKV: Reinventing RNNs for the Transformer Era*，2023。[arXiv](https://arxiv.org/abs/2305.13048)；[官方源码](https://github.com/BlinkDL/RWKV-LM)。
2. Peng 等，*RWKV-7 “Goose” with Expressive Dynamic State Evolution*，2025。[arXiv](https://arxiv.org/abs/2503.14456)。
3. Sharma，*PLM-NIDS: A Protocol-Language Model for Network Intrusion Detection from Raw Packet Sequences Using RWKV State-Space Models*，2026。[arXiv](https://arxiv.org/abs/2606.00155)；[作者源码](https://github.com/shiva2vk/PLM-NIDS)。
4. Hou 与 Yu，*RWKV-TS: Beyond Traditional Recurrent Neural Network for Time Series Tasks*，2024。[arXiv](https://arxiv.org/abs/2401.09093)；[作者源码](https://github.com/howard-hou/RWKV-TS)。
5. 本地全文核验：`wiki/papers/rwkv/2026-Sharma-PLM-NIDS-RWKV协议语言入侵检测.md`、`wiki/papers/rwkv/2024-Hou-RWKV-TS-时间序列.md`、`wiki/papers/rwkv/2026-Rizki-RWKV-CVM门控跨变量混合.md`、`wiki/papers/rwkv/2024-Hao-多尺度RWKV与2D-TCN光伏预测.md`、`wiki/papers/rwkv/2025-Zhang-STWGRL时空加权图推理异常检测.md`。
6. 数据与评价事实源：`.Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md` 与 `.Codex/docs/RWKV/2026-08-06-LSPR24-G0合同v5修订记录.md`。

## 17. 交接状态

- **已完成**：任务定义、合法标签／目标说明、文献迁移矩阵、候选排序、概率公式、强基线、可观测量、最小消融、否决门槛、原创边界、数据代价、文件所有权、阶段入口、验收命令与阻塞条件。
- **未完成且不得冒充完成**：生产代码、G0-D 真实目标可用性核验、真实基线、GPU 训练、SwanLab 运行、三种子开发验证、校准或最终评价。
- **当前科学状态**：设计可行；预测增益、状态贡献与惊异度安全价值均为实验待证。
