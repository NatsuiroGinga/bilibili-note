# 任务十七公共观测可辨识性接口审计

## 审计范围与结论

本次只读审计覆盖以下现有实现和制品：

- `src/flow_probe/representation_coupling.py`
- `src/flow_probe/representation_train.py`
- `src/flow_probe/physics_train.py`
- `src/flow_probe/ns3_sequences.py`
- `src/flow_probe/ns3_field_roles.py`
- `src/flow_probe/adapters/genis.py`
- `src/flow_probe/genis_forward_split.py`
- `src/flow_probe/schemas.py`
- 对应的 GeNIS、ns-3、物理训练和任务十六测试
- GeNIS 分层多任务种子 42 数据包与 ns-3 正式四窗口序列制品

**结论：任务十七不能直接沿用任务十六的五字段 ns-3 提示。** 现有五字段中的 `capacity_start_bps`、`capacity_end_bps` 和 `configured_capacity_integral_link_bytes` 是仿真环境真值，GeNIS 推理时没有这些字段。若继续把它们输入状态估计器，再报告“环境容量可辨识”，结论将由真值直通造成。

任务十七应保留任务十六的四窗口分组、五锚点状态定义和验证公式，但新增一个**与公开数据同构的数值观测视图**。当前 GeNIS 与 ns-3 可形成的最小共同字段为五个：

1. `total_packets`
2. `total_bytes`
3. `packet_length_mean`
4. `packet_rate`
5. `byte_rate`

`packet_length_min`、`packet_length_max` 和 `iat_mean_ms` 在当前 ns-3 真值 CSV 中没有对应测量，不能用常数填充后假装已覆盖。它们可以出现在“字段支持率”审计中，但首轮状态估计器只能使用上述五字段交集。

任务十六源码与既有 ns-3 四窗口制品应保持冻结。任务十七通过新的派生适配器读取既有制品，不修改 `ns3_queue_truth_field_roles.json`、`ns3_sequences.py`、`physics_train.py`、`representation_coupling.py` 或 `representation_train.py`，从而避免改变 B0/B1 已验收协议。

## 1. 当前 GeNIS 与 ns-3 输入字段和张量形状

### 1.1 GeNIS 当前接口

`adapters/genis.py:55-100` 把一条 GeNIS Argus 流记录适配为 `canonical_core_v1` 的八个数值字段：

| 统一字段             | GeNIS 原始字段或计算        |
| -------------------- | --------------------------- |
| `total_packets`      | `TotPkts`                   |
| `total_bytes`        | `TotBytes`                  |
| `packet_length_mean` | `TotBytes / TotPkts`        |
| `packet_length_min`  | `min(sMinPktSz, dMinPktSz)` |
| `packet_length_max`  | `max(sMaxPktSz, dMaxPktSz)` |
| `iat_mean_ms`        | 按源、目的包间隔和包数加权  |
| `packet_rate`        | `Rate`                      |
| `byte_rate`          | `Load / 8`                  |

`schemas.py:12-21` 冻结了这八个字段及其顺序。当前分层多任务数据包中的每条记录仍是**单条流记录**，`features` 是八个标量组成的映射，不是历史张量。种子 42 数据包含 15,000 条训练记录和 2,700 条验证记录。

任务十六实际输入 Qwen 的是 `prompt` 文本，而不是八维数值张量。`physics_train.py:837-880` 的 `_generation_batch` 生成：

| 张量              | 当前形状       | 说明                       |
| ----------------- | -------------- | -------------------------- |
| `input_ids`       | `[B, L]`       | `L <= 512`，批内动态补齐   |
| `attention_mask`  | `[B, L]`       | 有效令牌掩码               |
| `labels`          | `[B, L]`       | 提示位置为 `-100`          |
| Qwen 最终隐藏状态 | `[B, L, 2048]` | Qwen3-1.7B 隐藏维度为 2048 |
| 提示末令牌表示    | `[B, 2048]`    | 首个监督令牌之前的位置     |
| 预测队列状态      | `[B, 5]`       | 五个非负归一化锚点         |

当前 GeNIS 数据包没有四窗口张量。`genis_forward_split.py:117-156` 读取原始 `FlowID`、`StartTime` 和 `LastTime` 以建立会话级前向切分，但 `genis_forward_split.py:312-325` 的物化记录删除了时间字段。随后分层采样和多任务打包还会排序或打乱记录。因此不能把多任务 JSONL 中相邻四行解释成连续历史。

若任务十七需要 GeNIS 四观测历史，必须从原始 CSV 和既有 `session_assignments.jsonl` 重新构造：以不可逆会话标识分组，以 `StartTime`、`LastTime` 和原始行序稳定排序，只把五个共同数值字段送入模型。`FlowID`、时间戳、会话标识和原始行号只能用于分组、排序与切分，不能进入数值输入张量。

### 1.2 ns-3 当前接口

`ns3_sequences.py:25-39` 将窗口数固定为 `H=4`。正式序列共 2,421 条，训练、验证、测试各 807 条；每个切分含七个完整运行组，分别使用种子 42、43、44。

`ns3_queue_truth_field_roles.json:2-8` 和 `physics_train.py:25-31` 当前允许进入状态提示的字段均为长度 4 的数组：

1. `capacity_start_bps`
2. `capacity_end_bps`
3. `configured_capacity_integral_link_bytes`
4. `qdisc_received_l3_bytes`
5. `qdisc_received_packets`

`ns3_sequences.py:156-191` 还输出以下监督和审计对象：

| 对象                              | JSON 形状 | 训练批次形状                    | 用途                            |
| --------------------------------- | --------- | ------------------------------- | ------------------------------- |
| `model_inputs.<field>`            | `[4]`     | 先序列化成文本，再变为 `[B, L]` | 当前任务十六状态输入            |
| `queue_boundary_anchors_l3_bytes` | `[5]`     | `state_targets: [B, 5]`         | 五锚点状态真值                  |
| `state_supervision.<field>`       | `[4]`     | 各通量 `[B, 4]`                 | 状态监督与物理残差              |
| `normalization_scale_*`           | `[4]`     | 当前重新计算为 `scale: [B]`     | 每条序列公共尺度                |
| `state_mask`                      | 无        | `[B, 5]`                        | 双锚点稀疏监督掩码              |
| 预测状态                          | 无        | `[B, 5]`                        | `ContinuousQueueStateHead` 输出 |
| 守恒残差                          | 无        | `[B, 4]`                        | 四个单窗口残差                  |

`physics_train.py:883-941` 的 `_state_batch` 仍然把四窗口数据渲染为文本并分词，得到动态长度的 `[B, L]`，没有显式的 `[B, 4, F]` 数值历史张量。状态路径为：

```text
四窗口文本 -> Qwen 隐藏状态 [B,L,2048]
            -> 最后有效令牌 [B,2048]
            -> 状态头 [B,5]
```

`physics_train.py:512-542` 的残差契约已经冻结：预测状态为 `[B,5]`，容量和四类通量为 `[B,4]`，输出残差为 `[B,4]`。该公式可以继续作为验证指标，但其中的容量、离开量和丢弃量只能在 ns-3 训练监督或验证侧使用。

### 1.3 任务十七建议冻结的公共数值张量

ns-3 的五个共同观测字段应按每个 0.1 秒窗口派生：

| 公共字段             | ns-3 派生式                         | 边界处理                         |
| -------------------- | ----------------------------------- | -------------------------------- |
| `total_packets`      | `qdisc_received_packets`            | 零是合法观测                     |
| `total_bytes`        | `qdisc_received_l3_bytes`           | 零是合法观测                     |
| `packet_length_mean` | `received_bytes / received_packets` | 分母为零时数值置零且观测掩码为假 |
| `packet_rate`        | `received_packets / window_seconds` | `window_seconds` 只用于单位换算  |
| `byte_rate`          | `received_bytes / window_seconds`   | `window_seconds` 只用于单位换算  |

建议将任务十七的纯数值接口固定为：

| 张量                 | 四窗口形状   | 单窗口对照形状                   |
| -------------------- | ------------ | -------------------------------- |
| `observation_values` | `[B, 4, 5]`  | `[B, 1, 5]`，只取最后有效窗口    |
| `observation_mask`   | `[B, 4, 5]`  | `[B, 1, 5]`                      |
| `history_mask`       | `[B, 4]`     | `[B, 1]`                         |
| 编码器实际输入       | `[B, 4, 10]` | `[B, 1, 10]`，数值与缺失掩码拼接 |
| `state_targets`      | `[B, 5]`     | `[B, 5]`                         |
| `state_mean`         | `[B, 5]`     | `[B, 5]`                         |
| `state_log_variance` | `[B, 5]`     | `[B, 5]`                         |
| `uncertainty_score`  | `[B, 1]`     | `[B, 1]`                         |

为了保证单窗口与四窗口只比较历史信息，二者必须使用同一五字段变换、同一训练组、同一目标、同一损失和同一容量级别的估计器，不能让四窗口模型额外读取容量或标签。

当前序列制品可提供的最小环境真值只有容量相关字段。建议首轮把最后一个窗口的 `capacity_start_bps` 和 `capacity_end_bps` 作为 `environment_targets: [B,2]`，并输出对应的 `environment_mean`、`environment_log_variance: [B,2]`。`configured_capacity_integral_link_bytes` 与前两者及窗口长度存在确定关系，只保留为状态归一化与残差评分尺度，避免把同一容量重复算作三个独立环境变量。

当前制品没有逐样本保留链路时延；`queue_model` 和 `queue_limit_packets` 在现有矩阵中固定，且没有写入序列样本；下游错误率也未写入序列样本。因此本轮不能宣称已经辨识时延、队列策略或丢包环境。若这些量是后续 `c_hat` 的必要组成，必须进入一次且仅一次的 ns-3 域随机化扩展，而不能从 `scenario_id` 反推。

## 2. 可直接复用的接口

### 2.1 可直接复用

| 接口                                                           | 复用方式                                      | 边界                                   |
| -------------------------------------------------------------- | --------------------------------------------- | -------------------------------------- |
| `ns3_sequences.py` 的四连续窗口、五边界锚点和完整组切分制品    | 直接读取既有 JSONL                            | 不复用旧 `model_inputs` 作为新观测张量 |
| `ContinuousQueueStateHead`                                     | 时间编码器输出 `[B,D]` 后接该头，得到 `[B,5]` | 只产生状态均值；不包含环境或方差头     |
| `state_target_loss`                                            | 五锚点总体均方误差                            | 仅适用于 `[B,5]`                       |
| `masked_state_target_loss`                                     | 双锚点训练损失                                | 掩码必须为 `[B,5]`                     |
| `build_state_supervision_masks`                                | 保持 `anchor0_plus_one` 的组级确定性分配      | 只按完整组生成，不按滑动窗口随机生成   |
| `queue_balance_residual`                                       | 任务十七 ns-3 验证的物理残差                  | 真值容量和通量不得进入估计器输入       |
| `physics_sample_schedule`                                      | 单窗口、四窗口和常数基线共享样本顺序          | 不能把重叠窗口当作独立切分单位         |
| `decoder_last_hidden`、`select_last_token_hidden`              | 任务十八若重新接入 Qwen 可复用                | 任务十七纯数值诊断不必加载 Qwen        |
| `coupled_next_token_forward` 的 `predicted_state` 外部传入参数 | 任务十八可注入历史估计结果                    | 当前 B0/B1 耦合模块本身不进入任务十七  |

### 2.2 只能复用计算逻辑，不能直接调用

`representation_train.py:452-536` 的 `_evaluate_physics` 已经包含总体、已观测、未观测状态误差和物理残差的正确累计逻辑，但它硬编码 `_state_batch`、Qwen 文本提示和当前五字段模型输入。因此任务十七应抽取等价的纯张量指标函数，不应直接调用这个私有验证入口。

`physics_train.py:453-509` 的 `prepare_state_record` 和 `prepare_physics_record` 可以作为目标与残差字段语义参考，但不能用于任务十七观测构造，因为它们会调用当前五字段提示，并从容量真值构造提示。新适配器应分别返回“公共观测”和“仅监督真值”，在类型和键空间上隔离两者。

### 2.3 当前切分不能支撑的表述

现有 ns-3 训练、验证、测试包含相同的七种 `scenario_id`，只改变随机种子。因此它是**留出运行种子**，不是留出场景。任务十七若要报告“留出场景可辨识”，必须在既有 21 个完整组上另建按 `scenario_id` 留出的诊断折，并保证缩放器、常数均值、模型拟合和不确定性校准都不读取测试场景。`scenario_id` 只允许用于构造折和分层报告，不能作为模型输入。

此外，2,421 条序列来自 21 个运行组的高度重叠滑动窗口，独立实验单位仍是运行组，不是窗口数。域分类器、置信区间和显著性报告都必须按组计算或自助抽样，不能把 807 个重叠窗口当作 807 个独立重复。

## 3. 任务十七所需最小新增文件和函数

### 3.1 新增生产文件

#### `src/flow_probe/observability.py`

建议集中实现无文件副作用的接口：

1. `PUBLIC_OBSERVATION_FIELDS`：冻结五字段交集及顺序。
2. `PublicHistoryBatch`：保存 `observation_values`、`observation_mask`、`history_mask`、`state_targets`、`environment_targets`、`sample_ids` 和 `group_ids`；模型输入属性只能暴露前三项。
3. `ns3_public_history(sample)`：只从 `qdisc_received_*` 和窗口起止时间派生 `[4,5]` 公共观测；容量、队列、通量、标签和场景字段进入单独监督对象。
4. `build_genis_public_histories(csv_paths, assignments_path, split, horizon=4)`：按哈希会话分组并按 `StartTime`、`LastTime`、原始行序排序；使用 `adapt_row` 生成公共字段；不持久化原始 `FlowID`、地址或端口。
5. `single_window_view(batch)`：从同一批四窗口张量取得最后有效窗口，输出 `[B,1,5]`，禁止重新采样。
6. `validate_public_history_batch(batch)`：检查形状、有限性、掩码、组标识和禁止字段，防止监督真值混入输入。
7. `HistoricalEnvironmentStateEstimator`：同一时间编码器输出状态均值、环境均值及对数方差；状态均值保持非负。
8. `heteroscedastic_regression_loss`：对状态与环境目标计算异方差负对数似然，方差上下界必须显式限制。
9. `fit_constant_baseline(train_targets)`：只用训练组计算五状态和环境均值；验证、测试和公开数据不能参与拟合。
10. `observability_metrics`：返回状态总体、已观测、未观测误差，环境误差和相对常数基线改善率。
11. `calibrate_uncertainty(validation_errors, validation_scores)`：只在验证组拟合单调校准或保序校准；测试集只应用不拟合。
12. `public_support_metrics(ns3_train, public_values)`：在同一五字段变换上报告支持区间越界率、最近邻距离或马氏距离；不得读取攻击标签。

#### `src/flow_probe/observability_diagnostic.py`

只负责配置、数据读取、模型训练、验证、域覆盖诊断和制品写出：

- 固定比较 `constant`、`single_window` 和 `history_h4` 三个变体。
- 按完整运行组和场景折训练，验证集用于早停与不确定性校准，测试组只做一次最终评分。
- GeNIS 与 HIKARI 只提供公开观测和覆盖诊断，不提供伪造的队列标签。
- 域可分性分类器只能使用五字段数值与缺失掩码，并按组切分；输出接收者工作特征曲线下面积和组级置信区间。
- 至少写出 `config_snapshot.yaml`、`input_manifest.json`、`split_manifest.json`、`metrics.json`、`predictions.jsonl`、`support_report.json`、`calibration.json`、`console.log` 和 `artifact_manifest.json`。

### 3.2 新增配置与测试文件

1. `configs/observability_diagnostic_seed42.yaml`
2. `tests/test_observability.py`
3. `tests/test_observability_diagnostic.py`

只需在 `pyproject.toml` 增加一个控制台入口，例如 `flow-probe-diagnose-observability = "flow_probe.observability_diagnostic:main"`。首轮不需要新增 shell 包装器，也不需要修改任务十六配置。

### 3.3 不建议新增或修改

- 不新增另一套状态头文件；五维非负状态均值继续复用 `ContinuousQueueStateHead`。
- 不改 `ns3_queue_truth_field_roles.json`，否则会改变已验收的任务十六制品语义。
- 不改 `representation_coupling.py` 或 `representation_train.py`；任务十七不训练生成器。
- 不把任务十七诊断塞入 `physics_train.py`；该文件已经同时承担多组历史实验协议，继续扩张会使旧结果不可审计。
- 不在首轮引入 Qwen、LoRA、软令牌或 C1/C2；任务十七只回答公共观测是否足以辨识和校准不确定性。

## 4. 服务器最小测试节点

以下是建议在实现计划中冻结的**精确节点**。本次审计没有运行这些测试；前九个节点需要随任务十七实现新增，后三个是受影响边界的现有回归节点。

```bash
uv run pytest -q \
  tests/test_observability.py::test_ns3_public_history_uses_only_five_common_fields \
  tests/test_observability.py::test_zero_packet_mean_is_masked_instead_of_fabricated \
  tests/test_observability.py::test_genis_history_is_time_ordered_and_label_free \
  tests/test_observability.py::test_single_and_four_window_views_have_frozen_shapes \
  tests/test_observability.py::test_truth_and_metadata_fields_cannot_enter_observation_tensor \
  tests/test_observability.py::test_estimator_outputs_nonnegative_state_and_finite_variance \
  tests/test_observability.py::test_constant_baseline_uses_training_targets_only \
  tests/test_observability.py::test_uncertainty_calibration_uses_validation_only \
  tests/test_observability_diagnostic.py::test_group_disjoint_run_writes_complete_artifacts \
  tests/test_adapters.py::test_genis_adapter_maps_official_fields \
  tests/test_ns3_sequences.py::test_sequence_preserves_five_anchors_roles_and_raw_supervision \
  tests/test_physics_train.py::test_truth_anchors_have_zero_residual_and_perturbation_is_nonzero
```

若实现只新增上述两个生产模块，完整测试文件或全仓 pytest 不属于首轮最小行为门禁。生产源码完成后仍需按仓库规则在服务器集中执行一次 Black 和 Ruff；Ruff 首次无语法或结构问题即停止。

## 5. 不能复用或会泄漏真值的字段

### 5.1 ns-3 严禁进入任务十七观测张量

| 字段或对象                                                          | 原因                                   | 允许用途                                   |
| ------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------ |
| `capacity_start_bps`                                                | 待辨识环境真值                         | 环境目标、分层评分                         |
| `capacity_end_bps`                                                  | 待辨识环境真值                         | 环境目标、分层评分                         |
| `configured_capacity_integral_link_bytes`                           | 容量真值，且当前用于状态归一化         | 目标归一化、残差评分                       |
| `queue_boundary_anchors_l3_bytes`                                   | 五锚点状态真值                         | 状态监督与验证                             |
| `queue_start_*`、`queue_end_*`                                      | 队列状态真值                           | 状态监督与连续性审计                       |
| `qdisc_enqueued_*`                                                  | 入队通量真值                           | 物理审计                                   |
| `qdisc_dequeued_*`                                                  | 离开通量真值                           | 守恒残差                                   |
| `qdisc_dropped_before_enqueue_*`                                    | 丢弃通量真值                           | 守恒残差                                   |
| `qdisc_dropped_after_dequeue_*`                                     | 丢弃通量真值                           | 守恒残差                                   |
| `normalized_physics`                                                | 同时含队列和通量真值，并使用容量归一化 | 只读审计与评分                             |
| `queue_balance_residual_*`                                          | 保存的真值残差                         | 只读数据审计，训练接口继续主动拒绝         |
| `is_attack`、`attack_exposure_fraction`、`traffic_phase`、`label_*` | 检测标签                               | 分层报告，不进入状态估计                   |
| `scenario_id`                                                       | 可直接揭示容量切换、攻击或随机丢包场景 | 构造场景留出折、分层报告                   |
| `seed`、`run`、`group_id`、`source_csv_path`                        | 可形成运行记忆或来源捷径               | 切分、追踪和去重                           |
| `queue_model`、`queue_limit_packets`                                | 当前为环境真值且支持范围固定           | 域随机化目标或分层报告                     |
| `window_index`、绝对窗口时间                                        | 可能编码攻击开始和场景阶段             | 仅排序与连续性验证；窗口长度可用于单位换算 |

`qdisc_received_l3_bytes` 和 `qdisc_received_packets` 可以进入公共观测，但必须明确其局限：它们是瓶颈队列规则层的窗口聚合，而 GeNIS 的 `TotBytes`、`TotPkts` 是单流聚合。字段单位可以对齐，统计对象并不完全相同。任务十七的域可分性与支持范围诊断正是用来量化这项语义差异，不能预先写成“真实等价”。

### 5.2 GeNIS 严禁进入任务十七状态估计器

| 字段或对象                                        | 原因                                         | 允许用途                                     |
| ------------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| `completion`、`task_label`                        | 直接标签真值                                 | 生成任务监督，不用于任务十七                 |
| `binary_label`、`attack_family`、`attack_subtype` | 攻击标签                                     | 分层覆盖报告                                 |
| `prompt` 中的任务说明与候选标签                   | 与同一流量特征无关，且多任务数据会重复样本   | 任务十六生成训练，不用于数值辨识             |
| `sample_id`                                       | 文件名常含攻击子类，存在显式来源标签捷径     | 去重和提取稳定原始行序；字符串不得编码入模型 |
| `group_id`                                        | 会话标识可被记忆                             | 分组、历史构造和无交叉切分                   |
| `source_dataset`、`source_file`                   | 直接域标识或攻击文件名                       | 审计和域标签，不进入估计器                   |
| `FlowID`、地址、端口                              | 会话与网络身份捷径，且既有隐私协议禁止持久化 | 原始读取期临时分组，随后哈希并丢弃           |
| `StartTime`、`LastTime`                           | 可能编码攻击阶段和数据采集顺序               | 仅构造因果历史；绝对时间不得输入             |

GeNIS 的五个公共字段必须直接来自 `features` 数值映射，不从 `prompt` 反向解析。多任务数据包对同一流可能存在重复任务记录；历史构造前必须按 `sample_id` 去重，不能把同一观测重复当成相邻窗口。

## 6. 实施前必须冻结的边界

1. **任务十七是可辨识性诊断，不是生成训练。** 不加载 Qwen，不启动 C1/C2，不复跑 B0/B1。
2. **公共观测固定为五字段交集。** 首轮不通过补零或标签推断扩展到八字段。
3. **环境目标首轮只评价当前制品真实支持的容量。** 时延、队列策略和丢包环境没有变异或没有保留，不作正面结论。
4. **切分单位是完整运行组或会话。** 不随机拆分重叠窗口，不用测试场景拟合缩放器、均值基线或校准器。
5. **GeNIS 四历史从原始时间序列构造。** 当前分层多任务 JSONL 只用于核对字段与覆盖，不足以证明时间连续性。
6. **不确定性必须经过验证组校准。** 仅输出网络方差、熵或距离而未检查误差覆盖关系，不算通过门禁。
7. **若五字段域可分性接近完全可分，或绝大多数公开样本超出 ns-3 支持范围，应触发唯一一次 ns-3 域随机化扩展。** 此时只扩容量、时延、测量噪声、队列策略、丢包和流量混合，不改 Qwen 或任务十八结构。

## 审计状态

- 本次只读检查未修改实验源码、配置、测试或既有制品。
- 未运行本机或服务器测试。
- 未启动训练、GPU 任务或 SwanLab 运行。
- 唯一新增文件为本审计报告。
