# FT-Transformer 逐字段 Token 协议 A 实施报告（任务 4、5、7）

实现代理 `ftt_task4567_pipeline_opus_high`，模型 `claude-opus-5`，effort `high`。
日期 2026-08-21。状态：**任务 4、5、7 已交付；四个生产阶段全部接通，生产路径无 `NotImplementedError`。**

本报告只记录本轮（任务 4、5、7）的实现事实。任务 1 至 3 的实现事实见前一轮报告，
本报告第六节逐条给出对其八条遗留顾虑的处置结论。

---

## 一、五文件清单与 SHA-256

| 角色 | 路径 | 行数 | SHA-256 | 本轮是否修改 |
| --- | --- | --- | --- | --- |
| 实施计划 | `.Codex/docs/RWKV/2026-08-21-FT-Transformer逐字段Token协议A实施计划.md` | 260 | `bac3ce6e1ec5e8f8c31a1e31ea31823dba58e124defbcc113fcb45721131dfd6` | 否 |
| 工具 | `thesis/experiments/llm_probe/tools/ch3_ft_transformer_field_token_protocol_a.py` | 5180 | `1c8c0cd1ac162149363d13bbda6ca8ec9588424ec494a4c7861d7ce6c347e91b` | **是** |
| 配置 | `thesis/experiments/llm_probe/configs/ch3-ft-transformer-field-token-protocol-a-seed42-v1.json` | 546 | `a9e11e90792a3106c2e8a3bc9cd3843b3cd4fe405a15656501bf715f05c3929a` | **是** |
| 启动器 | `thesis/experiments/llm_probe/scripts/remote_launchers/run_ch3_ft_transformer_field_token_protocol_a_seed42_v1.sh` | 749 | `15ad1877f8bbfb60fef552456552dd33ed38b2fb1d07df07b0a6362516f14965` | 否（已交付验收，本轮未触碰） |
| 实施报告 | `.Codex/docs/RWKV/2026-08-21-FT-Transformer逐字段Token协议A实施报告.md` | 本文件 | 提交后由 `git show` 取 | **新建** |

工具从 2453 行增至 5180 行，顶层定义从 44 个增至 87 个。
未修改任何共享框架（`neural_precision_runtime.py`、同族四格工具、精度合同 JSON），
未派发子代理，未访问服务器，未同步，未启动实验，未运行 `black`。

---

## 二、Codex 六条裁决的逐条落地位置

裁决出处：提交 `82642fb`，看板 `2026-08-20-第三章神经骨干跨进程协作看板.md` 消息表
「2026-08-21 16:20 CST Codex → Claude Code 裁决 N-13」。

| 裁决 | 落地位置 | 机械核验方式 |
| --- | --- | --- |
| 一：`d % n_heads == 0`、每块 `4d²+5d`、十进制字面量截断口径 | `D_FFN_FACTOR = 1.333333333333333`；`_EXPECTED_ARCHITECTURE.d_ffn_hidden = 255`；`transformer_block_parameter_count` 保持 `4d²+5d+h(3d+2)`；`MultiheadAttention.__init__` 断言整除 | `validate_config` 对 `d_ffn_factor`、`d_ffn_hidden` 与 `d_token % n_heads` 三项各抛中文原因；`ffn_factor_rounding_diagnostic` 每次核验打印两种口径 |
| 二：对照固定 `d=192,L=3,n_heads=8`，措辞「同结构近参数对照」 | `CONTROL_D_TOKEN = 192`、`CONTROL_PARAMETER_MATCH_SEMANTICS = "同结构近参数对照"`、`CONTROL_WIDTH_RULING`；`build_control_model` 以裁定宽度优先于搜索结果 | `_validate_control_branch` 逐项断言 `d_token/n_layers/n_heads/parameter_match_semantics/width_ruling`；展示名改为「整向量投影同结构近参数对照（非FT-Transformer）」 |
| 三：阶段一保留两个输入候选，只由 LSPR23 选择 | `INPUT_CANDIDATES` 两项不变；`run_select_input_stage` 按 `order` 逐个训练 C00 后封印 | `selection_metric` 固定为 `lspr23_entity_disjoint_validation_flow_ap`；`forbidden_tie_breakers` 含 `lspr24`；封印写 `target_year_arrays_read=0` |
| 四：两个 AdamW 候选，学习率同为 `1e-4`，只差权重衰减 | `OPTIMIZER_CANDIDATES` 两项不变；`run_select_optimizer_stage` 只重训挑战者，复用阶段一的官方默认结果 | `validate_config` 逐字段比对两个候选并要求非空 `source`；阶段二校验 `stage_two_optimizer` 顺序 |
| 五：不启用梯度裁剪，非有限梯度直接失败 | `no_clip_accumulator_class()` 返回 `EffectiveBatchAccumulator` 的子类，`finish` 不裁剪、用 `torch.nn.utils.get_total_norm(..., error_if_nonfinite=True)` 断言有限后直接 `optimizer.step()` | 传入任何裁剪阈值即抛 `ContractValidationError`；`training.gradient_clip_norm` 为 `null`，`non_finite_gradient_policy = "fail_immediately_no_silent_skip"` |
| 六：预处理用 FT-T 自身常量，状态/词表/OOV/哈希写收据 | 任务 2 的 `QUANTILE_*`、`NUMERIC_NAN_POLICY` 不变；本轮给 `FieldTokenTransform` 增加 `frozen_state`、按源年/目标年分区的 `applied_row_counts`、`out_of_vocabulary_counts`、`zero_one_absorption_counts` 与 `receipt()` | 两级封印与每格目标评价收据均写入 `input_transform_receipt`；`score_target` 用 `switch_region("target")` 分区计数，`finally` 复位 |

### 关于裁决内部的一处数字冲突（必须由 Codex 复核）

**裁决一与裁决二在数字上互相矛盾，本轮按裁决一处置并如实登记。**

- 裁决一要求「严格采用十进制 `ffn_factor = 1.333333333333333` 经截断的口径」，
  实测 `int(192 × 1.333333333333333) = 255`。
- 裁决二引用的三个数字 `907,777`（对照）、`926,017`（主口径）、`-1.9697%`
  只有在 `h = 256`（精确 `4/3`）下才成立。

采用裁决一的理由：前一轮实现代理在同一封消息里**显式提问**「是否改判字面量口径，
若改判则主口径 `926017 → 924283`，请裁决」，裁决一是对该提问的直接回答；
裁决二的三个数字是从裁决前的汇报原样引用，未按新口径重算。
另一佐证是论文自报值：字面量口径得 `928,507`，四舍五入正好是论文表 12 的 `929K`；
精确 `4/3` 得 `930,241`，四舍五入为 `930K`，与论文自报不符。

**裁决二的结构规定全部照办且不受口径影响**：对照固定 `d=192`、`L=3`、`n_heads=8`，
与主口径同宽、同深、同头数；`d=168, L=4` 已否决；措辞统一为「同结构近参数对照」。
**参数差 `-18,240` 与口径无关，恒定不变**——它等于标记器 `34,368` 减去整向量投影
`16,128`，两项都不含前馈宽度 `h`。只有总量与相对百分比随口径改变。

改判成本为一行：把 `D_FFN_FACTOR` 换成同文件已备好的 `EXACT_FOUR_THIRDS_D_FFN_FACTOR`，
并同步配置的 `d_ffn_factor`、`d_ffn_hidden` 与 `paper_self_reported_reference.closed_form_total`。

---

## 三、参数量与对照的最终口径

冻结口径 `d=192`、`L=3`、`n_heads=8`、`d_ffn_factor=1.333333333333333`、`h=255`、`d_out=1`。

### 3.1 骨干闭式（无机制）

| 对象 | `F` | `C` | `Σv` | 标记器 | 块 | 归一化 | 头 | 合计 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 论文自检基准 | 100 | 0 | 0 | 38,592 | 887,418 | 2,304 | 193 | **928,507** |
| 输入候选一（全字段数值 Token） | 83 | 0 | 0 | 32,064 | 887,418 | 2,304 | 193 | **921,979** |
| 输入候选二（协议字段词表 Token） | 81 | 2 | 14 | 34,368 | 887,418 | 2,304 | 193 | **924,283** |
| 整向量投影对照（`d=192`） | — | — | — | 投影 16,128 | 887,418 | 2,304 | 193 | **906,043** |

对照相对主口径（候选二）差 `-18,240`，即 `-1.9734%`，定位为**同结构近参数对照**。

独立交叉核验：按逐个 `nn` 子模块声明的形状算术枚举得
标记器 `34,368` + 注意力 `444,672` + 前馈 `442,746` + 归一化 `2,304` + 头 `193` = `924,283`，
与闭式分项逐项一致，`LayerNorm` 恰为 `2L = 6` 个。

### 3.2 机制外接后的各格参数量（前一轮顾虑 7 的定案）

前一轮遗留的「机制外接后参数量口径未定」由本轮定案：

```
机制闭式 = 2d² + d + 1 = 73,921
        └ 2d² + d  因果前缀聚合的融合层 nn.Linear(2d, d)
        └ +1       ELP 的共享标量 p_log
```

| 分支 | 骨干 | 机制 | **整格实际参数量** |
| --- | --- | --- | --- |
| `C00` / `C01` / `C10` / `C11`（四格） | 924,283 | 73,921 | **998,204（四格恒等）** |
| 整向量投影对照（`C00` 结构） | 906,043 | 73,921 | **979,964** |

四格恒等的机制依据：`aggregate` 为假时上下文张量置零后**仍然拼接**成 `2d` 再过融合层；
`p_log` 四格都持有，只有 `learned_lp` 为真的格在训练目标里使用它。因此机制差异只来自
「上下文是否携带信息」与「是否有 ELP 辅助损失」，不来自参数量。

**对照与主口径的整格差仍是 `-18,240`**，因为两者外接的是同一份机制，机制不参与对位。

机械断言位置：`build_cell_model` 校验「整格减骨干 == 机制闭式」；
`run_cells_stage` 校验四格 `parameter_count` 完全相等，不等即抛错并写明四格取值。

### 3.3 若 Codex 改判回精确 `4/3`

骨干：候选一 `923,713`、候选二 `926,017`、对照 `907,777`；
整格：四格 `1,000,131`（机制 `73,921` 不变，因为机制只依赖 `d`），对照 `981,891`；
差仍为 `-18,240`，相对变为 `-1.9697%`。

---

## 四、任务 4：训练循环与协议 A 选择

### 4.1 等效微批的独立冻结

**有效批、微批与累积步数由本任务独立冻结，未继承 TabM32 的 `4×16`。**

有效批 `64` 序列是协议 A 的跨骨干共同预算，由协议决定，不参与搜索。
微批只能取 `64` 的机械因子。选择规则写在 `freeze_microbatch_plan`：
取使「单微批前向为反向保留的激活解析上界」不超过天花板的**最大**机械因子。
天花板取 GPU 准入阈值 `20480 MiB` 的十分之一，即 `2048 MiB`。

十分之一这个工程余量的依据是本结构的三项同量级放大：注意力 `softmax` 走 FP32 岛，
因而 FP32 与计算类型两份注意力矩阵同时存在；反向为每层保留与前向同量级的梯度缓冲；
缓存分配器碎片。三者叠加使真实峰值可达解析前向上界的数倍。
这是工程资源余量而非科研阈值，**服务器第一次真实 `optimizer.step()` 的显存收据到手后必须复核**。

解析上界的逐项构成（每层，`flows = 微批 × 128`）：
注意力矩阵两份 `flows × 8 × 84 × 84`（FP32 + 计算类型）、查询/键/值三份 `flows × 84 × 192`、
ReGLU 首层展开 `flows × 84 × 510`；再加进入首块前的一份 Token 张量。

本机实算的完整搜索轨迹：

```
  微批  1 -> 保留激活    194.8 MiB 可行=True
  微批  2 -> 保留激活    389.6 MiB 可行=True
  微批  4 -> 保留激活    779.1 MiB 可行=True
  微批  8 -> 保留激活   1558.3 MiB 可行=True
  微批 16 -> 保留激活   3116.5 MiB 可行=False
  微批 32 -> 保留激活   6233.1 MiB 可行=False
  微批 64 -> 保留激活  12466.1 MiB 可行=False
冻结微批=8 累积步数=8 天花板=2048 MiB（准入 20480 / 10）
```

**冻结为微批 `8` 序列 × 累积 `8` 步 = 有效批 `64` 序列。**
该推导在每次 `--validate-config` 与每次 `train_cell` 里都重跑一遍并与冻结值比对，
手改配置里的微批会在核验阶段被拦下。

已知的口径保守性：解析上界把特征标记器输出按计算类型字节计，而实际标记器输出保持 FP32
（`autocast` 只降精度 `matmul`/`linear`），该项被低估约 `32 MiB`。它不改变选择结果——
微批 `16` 即使加上该项仍为 `3179 MiB`，仍超天花板。

### 4.2 精度与 FP32 岛

BF16 autocast 经 `precision.autocast_context` 接入。以下敏感计算进 `fp32_island`：

| 计算 | 位置 | 精度合同类别 |
| --- | --- | --- |
| 注意力 `softmax` | `MultiheadAttention.forward`（任务 3 已实现） | `softmax` |
| 因果前缀聚合的 `cumsum` | `ProtocolACellModel.flow_representation` | `reduction` |
| 逐流概率 `sigmoid` | `ProtocolACellModel.flow_probability` | `probability_normalization` |
| ELP 的 `log`/幂/`logsumexp` | `learned_lp_pool` | `log`、`reduction` |
| 主损失与辅助损失求和 | `train_cell` 微批内 | `loss` |

参数与优化器状态全程 FP32，由 `precision.validate_model_optimizer_fp32` 在建模后与
第一次 `optimizer.step()` 后各核一次；BF16 不创建 `GradScaler`，创建了即抛错。

### 4.3 机制接入位置

采用统一合同第 111 行记载的拟议接口（采用而非强制，已在计划第 3.3 节记明）：

- **CPA 接在 `[CLS]` 之后**：骨干逐流给出 `(N,T,d)` 的 `[CLS]` 表示（末块输出、
  过最后一处归一化之前），沿序列时间轴做掩码因果前缀均值，与表示拼接成 `2d`，
  经融合层投影回 `d`，再交给官方预测头 `Linear(ReLU(LayerNorm(·)))`。
- **ELP 接在分类概率之后**：由共享标量 `p_log`（初值 `log 2`）参数化，
  在序列级辅助损失里训练，在实体聚合时用于主指标。

字段内注意力只在同一条流的 `83+1` 个 Token 之间进行，跨流关系全部由沿时间轴的
因果前缀聚合承担，只读取当前及严格过去时刻。`flow_representation` 里有一条形状断言，
上下文张量与表示不同形即立即失败。

`auxiliary_loss_weight = 1.0` 沿用协议 A 的跨骨干机制常量（ResMLP2 配置第 49 行、
TabM32 配置第 90 行均为 `1.0`），不是为本骨干新设的值——跨骨干比较要求机制定义一致。

### 4.4 选择规则与切分断言

跑满 `20 × 1000` 步，不早停、无学习率调度；每轮在 LSPR23 实体不相交验证集上算逐流 AP，
**严格大于**才更新最优，因此并列保留最早轮次。

切分与形状断言：`source_split` 要求统计逐项等于
`{实体 150680, 训练序列 208598, 验证序列 22444, 交集 0}`；
`load_source_arrays` 要求 `X23 = (16353511, 83)`、`I23 = (271815, 128)`、`M23` 同形、
`y23 = (16353511,)`、`E23/T23 = (271815,)`；`load_target_arrays` 要求
`X24 = (20227356, 83)`。训练有效流掩码由本工具独立重算并与收据的
`effective_flow_mask_sha256` 交叉核验，不单方面信任收据。

### 4.5 资源采集

`collect_resource_receipt` 采集四量（`allocated`/`reserved`/`max_allocated`/`max_reserved`）
外加外部进程占用（`torch.cuda.mem_get_info` 总量减空闲减本进程 `memory_reserved`）。
张量上界按展开维度乘积写明，不按参数量；对照分支的 Token 数为 `1`，其上界按 `1` 个 Token 计。
第一次 `optimizer.step()` 之后落 `first-step-memory-*.json`，含张量上界、累积计划、
冻结微批计划、首步梯度范数与显存快照。

---

## 五、任务 5：三层恢复、封印与 LSPR24 单次评价

### 5.1 三层同身份恢复

| 层 | 判据 | 不符时的行为 |
| --- | --- | --- |
| 完成层 | `checkpoints/selected-{cell}.pt` 与 `receipts/selection-{cell}.json` 同时存在，且传了 `--resume`、收据 `identity` 等于本次身份、收据登记的 `sha256` 等于实测哈希 | 抛错拒绝复用，不覆盖也不部分拼接 |
| 在途层 | 每轮全部 `optimizer.step()` 完成后原子写 `inflight/{cell}.pt`；恢复时校验精度配置 id、微批量、累积步数与身份 | 抛错拒绝恢复 |
| 封印层 | `input_selection_sealed.json`、`optimizer_selection_sealed.json`、`selection_frozen.json` 三级存在性与完整性门 | 抛错并写明应先执行哪个 `--stage` |

在途检查点的运行时状态由 `build_checkpoint_runtime_state` 构造、
`validate_checkpoint_runtime_state` 校验，含精度配置、有效批与单位、微批量、累积步数、
归一化单位、尾批标识、优化步数与四路随机状态（Python `random`、torch CPU、
torch CUDA 全卡、numpy）；采样器状态另存 `generator_state`。
写入点固定在完整 `optimizer.step()` 边界；半个有效批中断时该轮从未落盘，
恢复整轮重放，不会出现「恢复部分累计梯度后跳过样本」。

未传 `--resume` 时，任一历史制品存在即拒绝，不静默覆盖。

### 5.2 两阶段选择封印

`input_selection_sealed.json` 与 `optimizer_selection_sealed.json` 各含：
候选列表与固定顺序、数据清单哈希（`source_data_inventory`）、字段清单与字段策略哈希
（`field_order_sha256`、`field_policy_sha256`、`architecture_sha256`）、
字段基数收据哈希、每候选的结构与优化器与参数量、选择指标的**全精度值**
（`selection_metric_full_precision`，用 `repr` 而非格式化数字比较）、并列规则、
禁用打平依据清单、`target_year_arrays_read = 0`、`target_evaluation_calls = 0`、
`sealed_at_unix`。

`selection_frozen.json` 另含：`sealed_input_candidate`、`sealed_optimizer_candidate`、
`input_dimension`（`x_num` 列数，另附 `vocabulary_token_field_count` /
`vocabulary_total_columns` / `token_count` 说明口径）、`parameter_count` 与
`per_cell_parameter_count`、`backbone_parameter_count`、`mechanism_parameter_count`、
`cardinality_receipt_sha256`、样本顺序哈希、每格的 `cell_hashes`、
`d_ffn_factor_rounding` 取整口径事实、以及裁决六要求的
`input_transform_receipt` 与 `control_input_transform_receipt`
（冻结状态、分位数网格与词表哈希、越界桶位置、按源年/目标年分区的 OOV 计数与比率、
二值直通吸收计数）。

### 5.3 LSPR24 单次评价

封印完成前不加载目标年：`run_evaluate_stage` 先做纯标准库的封印存在性与完整性核验，
`numpy`/`torch`/`sklearn` 延后到确认要做真实评价之后才导入，因此上游阶段未完成时
给出的是明确中文原因而不是导入失败。另核验封印自身声明的
`target_year_arrays_read == 0` 与 `target_evaluation_calls == 0`。

四格每格恰好一次、合计恰好 `4` 次，由计数器机械断言：
`evaluation_calls_this_process + evaluation_receipts_reused == 4` 且 `target_disk_loads == 1`，
不符即抛错。评价阶段全程 `torch.no_grad()`，不训练、不替换检查点、不搜索阈值、
不更新聚合指数或任何超参数。输入变换只 `apply` 不 `fit`，
目标年词表外取值落训练区已冻结的越界桶，词表不扩充。

### 5.4 指标键名

与既有四格工具逐字同名，可直接并入第三章全模型指标总表：
`flow_average_precision`、`flow_roc_auc`、`entity_average_precision`、
`maximum_entity_average_precision`、`dr_at_fpr.fpr_0.001` 至 `fpr_0.08`、
`maximum_dr_at_fpr.*`、`flows_scored`、`entities_scored`、`evaluation_seconds`、
`target_evaluation_call`。

交互项 `interaction.<指标>.causal_prefix_effect`（`C10−C00`）、`.elp_effect`（`C01−C00`）、
`.combined_effect`（`C11−C00`）、`.interaction`（`C11−C10−C01+C00`），
覆盖四个指标：逐流 AP、逐流 ROC AUC、实体 AP、最大池化实体 AP。
资源项在 `resource.*`。

**对照分支的指标单列**在 `control_branch.target` 下，SwanLab 用 `control/` 前缀，
不进入 `target/` 前缀，也不参与任何交互项。

### 5.5 SwanLab

创建运行前机械断言工作区为 `mortiswang`、项目为 `ns3-rwkv-lspr24`，
不一致即抛错退出且不上传。只读取已核验存在的 `Run` 公开属性 `name`/`id`/`url`，
**不访问 `run.public`**（本仓库 2026-08-13 因此崩过一次）。
上报后写 `swanlab-receipt.json` 留痕，不上传任何逐样本值。

---

## 六、前一轮八条顾虑的处置结论

前一轮报告第八节「超出简报的设计决定」三项与第九节「遗留风险」六项，逐条处置如下。

| # | 顾虑 | 本轮处置 |
| --- | --- | --- |
| 1 | 裁决后阶段一是否仍需两个输入候选 | **保留**。裁决三明令保留，定位为数据适配消融，只由 LSPR23 选择。配置与阶段一实现均未改动候选表 |
| 2 | 第二优化器候选只在权重衰减上不同 | **保留**。裁决四确认这是官方范围内的单变量源年选择，学习率同为 `1e-4` 是论文调参区间对数中位与默认值重合的必然结果，不是笔误 |
| 3 | 是否做梯度裁剪 | **不裁剪**。裁决五明令遵循 FT-T 官方配方。实现为 `EffectiveBatchAccumulator` 的无裁剪子类，非有限梯度经 `get_total_norm(error_if_nonfinite=True)` 直接失败 |
| 4 | 全部 PyTorch 侧行为待服务器验证 | **仍待验证**，见第八节。本轮新增的前向路径（机制外接、CPA `cumsum`、ELP、逐流展平与还原）同样只经解析核验与 `pyflakes`，未真实前向 |
| 5 | 机制外接后参数量口径未定 | **已定案**，见第 3.2 节。四格整格 `998,204` 恒等，对照 `979,964`，机制闭式 `2d²+d+1 = 73,921`，并已写入封印与运行时断言 |
| 6 | 微批与累积步数暂取 `4 × 16` | **已按本任务独立冻结为 `8 × 8`**，见第 4.1 节。推导规则、天花板依据与完整搜索轨迹均写入配置的 `microbatch_selection_evidence`，并在每次核验与每次训练时复算比对 |
| 7 | GPU 准入阈值 `20480 MiB` 沿用 N-12 裁定值 | **仍沿用且未取得针对 FT-T 的独立裁定**。本轮把它用作微批天花板的分母来源，因此该值的复核价值上升；服务器首步显存收据到手后应一并复核 |
| 8 | 官方源码归档、易失临时目录 | 前一轮报告发出后由 `d9f37de` 完成归档到 `vendor/ft_transformer/`。本轮未触碰 `vendor/`，也未读取上游源码；工具内的 `OFFICIAL_*` 凭据常量与配置 `official_source` 保持不变，`validate_config` 仍逐项比对 |

---

## 七、跑过的每条命令与真实完整输出

工作目录 `/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe`。
本机 `cd` 被 shell 快照函数覆盖，故统一用 `uv run --directory <path> --no-sync python` 规避。

### 7.1 编译检查

```
$ uv run --directory .../llm_probe --no-sync python -m py_compile tools/ch3_ft_transformer_field_token_protocol_a.py
py_compile 退出码 0
```

### 7.2 配置核验

```
$ uv run --directory .../llm_probe --no-sync python tools/ch3_ft_transformer_field_token_protocol_a.py \
    --config configs/ch3-ft-transformer-field-token-protocol-a-seed42-v1.json --validate-config
2026-08-21 17:38:03,242 INFO 前馈宽度取整口径事实：官方 TOML 字面量 1.333333333333333 得 h=255、论文自检基准总参数 928507（论文自报 929K）；精确 4/3 得 h=256、总参数 930241。Codex 裁决一：本运行按官方十进制字面量冻结。
2026-08-21 17:38:03,243 WARNING 裁决内部数字冲突已按裁决一处置：裁决二引用的主口径 926017 与对照 907777 是裁决前按 4/3 计算的汇报值，在本运行冻结的字面量口径下分别为 924283 与 906043；两者之差 -18240 与口径无关、恒定不变，裁决二的结构规定（d=192、L=3、n_heads=8、同结构近参数对照、否决 d=168/L=4）已全部照办。
配置核验通过
validate 退出码 0
```

该次核验里同时跑过了 `freeze_microbatch_plan` 的重新推导并与冻结值比对，
推导不一致会在此处抛出中文原因。

### 7.3 四个生产阶段的真实入口输出

四次调用均**未**抛 `NotImplementedError`，而是按依赖顺序给出带中文原因的可操作错误，
退出码均为 `1`。本机不存在服务器路径 `/root/autodl-tmp/...`，故第一道拦截各不相同，
正好逐级展示了依赖门。

```
--stage select-input  退出码=1
FileNotFoundError: 缺少字段基数收据：/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-lspr23-field-cardinality-receipt-v1/field-cardinality-receipt.json

--stage select-optimizer  退出码=1
RuntimeError: 尚未完成阶段一输入接口封印，禁止进入阶段二：/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-ft-transformer-field-token-protocol-a-seed42-v1/input_selection_sealed.json；请先执行 --stage select-input

--stage cells  退出码=1
RuntimeError: 尚未完成阶段一或阶段二封印，禁止进入 cells 阶段：输入封印存在=False，优化器封印存在=False；请先依次执行 --stage select-input 与 --stage select-optimizer

--stage evaluate  退出码=1
RuntimeError: 四格选择尚未封印，禁止加载 LSPR24：/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-ft-transformer-field-token-protocol-a-seed42-v1/selection_frozen.json；请先依次执行 --stage select-input、--stage select-optimizer 与 --stage cells
```

`select-input` 的第一道拦截是字段基数收据而不是运行目录，说明纯标准库的收据核验确实
排在建立输出目录与载入数组之前——收据缺失时不会先制造一个误导性的目录创建失败。

残留检查：

```
$ rg -n "NotImplementedError" tools/ch3_ft_transformer_field_token_protocol_a.py
无残留
```

### 7.4 延迟导入性质

```
$ rg -n "^(import |from )" tools/ch3_ft_transformer_field_token_protocol_a.py
40:from __future__ import annotations
42:import argparse
43:import json
44:import logging
45:import sys
46:from pathlib import Path
47:from typing import Any

$ uv run --directory .../llm_probe --no-sync python -c "..."
numpy 不可导入: ModuleNotFoundError
sklearn 不可导入: ModuleNotFoundError
torch 不可导入: ModuleNotFoundError
swanlab 不可导入: ModuleNotFoundError
```

顶层只有六项标准库导入，而在四个依赖全部缺失的本机 `.venv` 上 `--validate-config`
仍 `exit=0`，该性质成立。

### 7.5 静态检查

```
$ uvx --from pyflakes pyflakes tools/ch3_ft_transformer_field_token_protocol_a.py
pyflakes 退出码 0
```

零告警，无未定义名、无未使用导入。`pyflakes` 经 `uvx` 在临时环境运行，未写入本仓库。

### 7.6 解析核验（有解析解的公式实现核验）

按实验工程规则，用有解析解的构造输入核验闭式实现，产物放任务临时目录并已删除。
真实输出：

```
冻结口径: d=192 L=3 heads=8 d_ffn_factor=1.333333333333333 h=255
论文自检基准 F=100,C=0 -> 928507 （论文自报 929K，四舍五入 929 K）
逐模块枚举: 标记器=34368 注意力=444672 前馈=442746 归一化=2304 头=193 合计=924283
闭式分项  : 标记器=34368 块=887418 归一化=2304 头=193 合计=924283
结构声明与闭式一致: True；LayerNorm 个数 2L = 6
候选一骨干=921979 候选二骨干=924283 对照骨干=906043 机制=73921
对照-主口径 骨干差=-18240 相对=-1.9734%
主口径整格=998204 对照整格=979964 整格差=-18240
搜索最优可构造 d=192（参数 906043，差 -18240）；裁定宽度 d=192（参数 906043，差 -18240）

实现正确：全部解析断言通过。
```

**结论只表述为「实现正确」**：这只证明闭式与结构声明一致，不证明任何科学效果。
另注意在字面量口径下，官方区间内的机械搜索最优可构造宽度**恰好也是 `d=192`**，
与裁决二的裁定宽度一致，因此不触发「裁定宽度与搜索不同」的警告。

### 7.7 第三方接口核验

| 库 | 目标机版本 | 来源 | 已核验签名 |
| --- | --- | --- | --- |
| PyTorch | `2.13.0+cu130`（实施计划登记，本机无 torch 无法复核） | Context7 `/websites/pytorch_2_12` 的 `torch.nn.utils.get_total_norm` 文档页 | `get_total_norm(tensors, norm_type=2.0, error_if_nonfinite=False, foreach=None) -> Tensor`；`error_if_nonfinite=True` 时对 `nan`/`inf`/`-inf` 抛错。该函数 PyTorch 2.6 起提供，工具内以 `hasattr` 前置断言并给出中文升级提示，**不静默回退** |
| SwanLab | 目标机版本待服务器核验 | 本仓库已交付并跑通的 `ch3_tabm32_paper_recipe_protocol_a.py` 第 2798 至 2814 行（同一目的地、同一 `swanlab.init` 参数组合） | `swanlab.init(workspace=, project=, name=, mode=, group=, tags=, log_dir=, config=)`；`Run` 只读 `name`/`id`/`url` |

---

## 八、遗留待服务器验证项

以下全部标为**待服务器验证**，本机无 GPU、无 torch、无 numpy、无 sklearn，一律不与实测混写。

1. **真实 `sum(p.numel())`**。四格 `998,204`、对照 `979,964` 目前只有闭式与逐模块枚举两路一致，
   第三路（实际 `sum(p.numel())`）在服务器首次 `build_cell_model` 时由运行时断言核对。
2. **前向张量形状与 `[CLS]` 位置**。含逐流展平 `(N,T,F) → (N*T,F)` 与还原、
   末块只取第 0 个 Token 的切片、`category_offsets` 缓冲的设备放置、
   `fp32_island` 包裹 `softmax` 后 `attention.to(logits.dtype)` 的类型往返。
3. **显存**。冻结微批 `8×8` 只有解析上界 `1558.3 MiB`，**没有任何实测峰值**。
   首次 `optimizer.step()` 的四量与外部进程占用到手后，必须复核微批与天花板分母。
4. **梯度稳定性**。不裁剪是裁决五的明令；若真实运行出现非有限梯度，工具会直接失败
   而不是静默跳过。按裁决五，届时须以**独立新身份**修订，不得在本运行身份里改判。
5. **`torch.nn.utils.get_total_norm` 在目标机版本上确实存在**。已按文档核验签名，
   但目标机 `2.13.0+cu130` 未实测导入。
6. **SwanLab 目标机版本与 `Run` 属性**。沿用同族已跑通工具的调用形状，未在本机复核。
7. **对照分支的目标年评价次数合同**。本轮新增 `evaluation.control_target_evaluation_calls = 1`，
   四格计数仍严格为 `4`、独立计数。**该字段是本代理新增的合同项，需 Codex 确认**；
   若 Codex 认为对照不应触碰 LSPR24，删掉 `run_evaluate_stage` 的对照评价段落即可，
   对照与主口径的比较会退化为只用 LSPR23 验证逐流 AP。
8. **推理批复用训练微批**。验证与目标年打分都用微批 `8` 序列，理由是同批对象数下
   `no_grad` 峰值严格低于训练步。这是保守设定，可能使 LSPR24 全量打分偏慢；
   首步显存收据到手后可上调，属工程参数不影响科学结论。

---

## 九、需要 Codex 裁决的两项

1. **裁决一与裁决二的数字冲突**（第二节末）。本轮按裁决一取字面量口径，
   主口径 `924,283`、对照 `906,043`、相对差 `-1.9734%`。
   若 Codex 实际意图是保留 `926,017` / `907,777` / `-1.9697%`，
   请改判回精确 `4/3`，改动为工具一个常量加配置三个字段。
2. **对照分支的 LSPR24 评价资格**（第八节第 7 条）。当前实现给对照一次独立计数的评价，
   四格计数不受影响。

---

## 十、提交

本轮两次提交，每次只 `git add` 明确路径，未使用 `git add -A` 或 `git add .`；
`scripts/remote_launchers/`、`vendor/`、共享框架与其他代理的未提交改动全程未触碰、
未回滚、未格式化、未暂存。提交哈希见看板回写。
