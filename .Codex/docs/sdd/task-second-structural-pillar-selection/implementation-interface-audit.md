# 第二结构支柱最小实验实现接口审计

## 1. 审计结论

- D1、D2、D3 的完整路径由 `asymmetric_physics_train.py`、三个 Shell 包装器、三份评估配置、`hierarchical_evaluation.py` 和 `s3_s4_detection_analysis.py` 组成。
- 当前代码足以复用数据装载、双锚点状态头、有限队列残差、在线跟踪、固定评估分区、九项门槛与配对统计，但**不能直接承载任意新结构**。
- 新结构不能继续向 `DiagnosticModeContract` 增加 D4/D5，也不能扩展 `PhysicalRepresentationCoupling` 的 B0/B1 变体。应建立独立结构模块、独立训练入口与独立推理运行时，同时保持数据、物理公式、评估样本和九项门槛不变。
- 最严重的实施风险位于正式推理：现有自由生成直接调用 `model.generate`，候选评分直接调用 `model(...).logits`。任何外置状态条件模块若没有同时接入这两条路径，`eval300` 会静默绕过第二结构支柱。
- 本地仓库中存在 D0、B0/B1 制品，但没有 D1、D2、D3 正式训练、评估与统计目录；当前 D1/D2/D3 结论只能由恢复文档和服务端制品定位。新实验开始前应先确认服务端基准制品仍完整，并在结果回收阶段补齐本地归档。

## 2. D1/D2/D3 训练接口地图

### 2.1 命令入口与配置类型

| 层级         | 精确位置                                         | 接口                                                                             | 作用                                                 |
| ------------ | ------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 控制台入口   | `thesis/experiments/llm_probe/pyproject.toml:54` | `flow-probe-train-asymmetric-physics = flow_probe.asymmetric_physics_train:main` | 训练 D0/D1/D2/D3                                     |
| Shell 入口   | `scripts/run_asymmetric_diagnostic.sh`           | `d1/d2/d3 + 输出目录 + 训练步数`                                                 | 把短模式映射为预注册模式，固定基座、配置与 S3 适配器 |
| 配置         | `configs/asymmetric_diagnostic_seed42.yaml`      | `probe`、`training`、`tracking`                                                  | 固定种子 42、LoRA、数据、批量、损失权重与 SwanLab    |
| 探针配置类型 | `src/flow_probe/config.py:14`                    | `ProbeConfig`、`ProbeConfig.from_mapping`                                        | 模型、字段视图、种子、长度和 LoRA 参数校验           |
| 训练配置类型 | `src/flow_probe/physics_train.py:319`            | `PhysicsTrainingSettings`、`_build_settings`                                     | 数据路径、批量、步数、状态监督和损失权重             |
| 跟踪配置类型 | `src/flow_probe/tracking.py:22`                  | `TrackingSettings.from_mapping`                                                  | 强制在线模式和固定云端项目                           |
| 模式契约     | `src/flow_probe/asymmetric_physics_train.py:57`  | `DiagnosticModeContract`                                                         | 固定三种损失开关和学习率类型                         |
| 模式解析     | `src/flow_probe/asymmetric_physics_train.py:105` | `resolve_diagnostic_mode`                                                        | 拒绝预注册集合外的临时模式                           |
| 学习率       | `src/flow_probe/asymmetric_physics_train.py:114` | `diagnostic_learning_rate`                                                       | D1/D2 常数学习率；D3 固定 202 步预热余弦轨迹         |
| 主训练函数   | `src/flow_probe/asymmetric_physics_train.py:367` | `train_asymmetric_physics`                                                       | 数据、模型、损失、优化、验证和制品生命周期           |
| 命令解析     | `src/flow_probe/asymmetric_physics_train.py:902` | `_parse_args`、`main`                                                            | 将 YAML 和命令行参数组装为训练调用                   |

`run_asymmetric_diagnostic.sh` 的固定值如下：

- 服务端根目录：`/root/autodl-tmp/thesis/experiments/llm_probe`。
- 基座：`/root/autodl-tmp/thesis/models/Qwen3-1.7B`。
- S3 检测适配器：`runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter`。
- 训练配置：`configs/asymmetric_diagnostic_seed42.yaml`。
- 默认训练步数：`202`。
- 运行方式：`uv run --no-sync flow-probe-train-asymmetric-physics ...`。

### 2.2 模型、LoRA 与路由

| 精确位置                                         | 接口                                   | 当前语义                                                   |
| ------------------------------------------------ | -------------------------------------- | ---------------------------------------------------------- |
| `src/flow_probe/asymmetric_physics_train.py:46`  | `DETECTION_ADAPTER`、`PRIVATE_ADAPTER` | 固定命名为 `detection` 与 `physics_private`                |
| `src/flow_probe/asymmetric_physics_train.py:223` | `_set_adapter_route`                   | 家族只激活检测适配器；子类和物理批次激活检测加私有适配器   |
| `src/flow_probe/asymmetric_physics_train.py:232` | `_load_model`                          | 载入 4 位 NF4 基座、冻结 S3、增加零初始化全线性私有 LoRA   |
| `src/flow_probe/asymmetric_physics_train.py:206` | `_adapter_parameter_digest`            | 训练前后计算冻结检测适配器参数摘要                         |
| `src/flow_probe/asymmetric_physics_train.py:325` | `_last_token_logits`                   | 测量家族路由训练前后最大输出差                             |
| `src/flow_probe/physics_train.py:346`            | `ContinuousQueueStateHead`             | `hidden_size -> 5 -> Softplus`，输出五个非负归一化队列锚点 |

`_load_model` 使用 `PeftModel.from_pretrained` 装入冻结 S3，再用 `model.add_adapter` 增加秩 16、缩放 32、丢弃率 0.05、`target_modules="all-linear"` 的私有 LoRA。训练器只允许私有 LoRA 和状态头可训练，发现其他可训练参数会立即失败。

### 2.3 损失与梯度路径

| 精确位置                                         | 接口                            | 当前语义                                             |
| ------------------------------------------------ | ------------------------------- | ---------------------------------------------------- |
| `src/flow_probe/asymmetric_physics_train.py:288` | `_subtype_generation_loss`      | 保留完整调度，仅对子类任务完成词元计算交叉熵         |
| `src/flow_probe/physics_train.py:837`            | `_generation_batch`             | 构造因果语言模型提示、完成文本与 `-100` 掩码         |
| `src/flow_probe/physics_train.py:883`            | `_state_batch`                  | 构造状态目标、状态掩码、公共尺度、容量与四类通量张量 |
| `src/flow_probe/physics_train.py:552`            | `build_state_supervision_masks` | 按组确定性分配 `q0 + 一个内部锚点`                   |
| `src/flow_probe/physics_train.py:591`            | `masked_state_target_loss`      | 只在两个观测锚点计算状态均方误差                     |
| `src/flow_probe/physics_train.py:512`            | `queue_balance_residual`        | 用预测五锚点构造四窗口有限队列守恒残差               |
| `src/flow_probe/qwen_physics_gradient.py`        | `select_last_token_hidden`      | 从最终隐藏层抽取每条物理序列的最后有效令牌           |
| `src/flow_probe/asymmetric_physics_train.py:576` | 优化循环                        | 生成微批次四次累积，物理批次一次，随后裁剪并更新     |
| `src/flow_probe/asymmetric_physics_train.py:682` | 梯度诊断                        | 记录私有 LoRA 与状态头梯度范数及非零步数             |

D1/D2/D3 的开关是：

| 模式                     | 生成损失 | 双锚点状态损失 | 队列物理损失 | 学习率                                            |
| ------------------------ | -------- | -------------- | ------------ | ------------------------------------------------- |
| D1 `generation_only`     | 开       | 关             | 关           | 常数 `2e-4`                                       |
| D2 `physics_only`        | 关       | 开             | 开           | 常数 `2e-4`                                       |
| D3 `joint_warmup_cosine` | 开       | 开             | 开           | 第 1 步 `2e-5`，第 20 步 `2e-4`，第 202 步 `2e-5` |

固定损失为 `L = L_gen + 1.0 L_state + 0.01 L_physics`。D1/D2 关闭的分量写为数值零，但仍按同一随机调度执行前向，以保留样本顺序和运行预算可比性。

### 2.4 训练制品契约

`AsymmetricRunLayout` 位于 `src/flow_probe/asymmetric_physics_train.py:145`。一次完成运行至少应有：

1. `config_snapshot.yaml`。
2. `environment.json`。
3. `input_sha256.json`，包括生成数据、物理数据和 S3 适配器摘要。
4. `console.log` 与包装器复制的 `launcher.log`。
5. `step_metrics.jsonl`，每步同时写本地、控制台和 SwanLab。
6. `training_summary.json`。
7. `final_private_adapter/physics_private/`。
8. `state_head.pt`。
9. `generation_sample_order.json`。
10. `physics_sample_order.json`。
11. `family_route_equivalence.json`。
12. `artifact_manifest.json`。
13. `swanlog/asymmetric-physics-train/`。

训练摘要还必须记录运行时间、峰值显存、私有 LoRA 参数量、状态头参数量、验证子类生成损失、已观测与未观测状态误差、物理残差，以及冻结路由是否严格等价。

## 3. 评估与九项门槛接口地图

### 3.1 `eval300`

| 层级       | 精确位置                                                     | 接口                                                                         |
| ---------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| 控制台入口 | `pyproject.toml:45`                                          | `flow-probe-evaluate-hierarchical = flow_probe.hierarchical_evaluation:main` |
| Shell 入口 | `scripts/run_asymmetric_diagnostic_eval.sh`                  | `d1/d2/d3`，固定训练目录、评估配置和输出目录                                 |
| 评估配置   | `configs/asymmetric_diagnostic_d{1,2,3}_seed42_eval300.yaml` | 每标签 300 条、生成批量 16、评分批量 24、已知拒识上限 0.05                   |
| 配置类型   | `src/flow_probe/hierarchical_evaluation.py:41`               | `EvaluationSettings`                                                         |
| 固定分区   | `src/flow_probe/hierarchical_evaluation.py:132`              | `build_evaluation_plan`                                                      |
| 模型加载   | `src/flow_probe/hierarchical_evaluation.py:379`              | `_load_model_runtime`                                                        |
| 任务路由   | `src/flow_probe/hierarchical_evaluation.py:432`              | `_set_task_adapter_route`                                                    |
| 自由生成   | `src/flow_probe/hierarchical_evaluation.py:455`              | `_run_free_generation`                                                       |
| 候选评分   | `src/flow_probe/hierarchical_evaluation.py:591`              | `_run_candidate_scoring`                                                     |
| 总入口     | `src/flow_probe/hierarchical_evaluation.py:729`              | `run_hierarchical_evaluation`                                                |

固定六个分区依次为 `family_test`、`subtype_validation`、`subtype_test`、`ood_dos_icmp`、`ood_dos_pushack`、`ood_dos_udp`。阈值只能由 `subtype_validation` 校准，未知攻击标签不能进入训练或阈值校准。

评估制品为：

- `predictions/` 下六个分区各一份 `_free.jsonl` 和 `_candidate.jsonl`，共 12 个预测文件。
- `evaluation_summary.json`、`swanlab_metrics.json`、`metric_history.jsonl`。
- `threshold_calibration.json`、`selected_samples_manifest.json`。
- `config_snapshot.json`、`environment.json`、`console.log`、`launcher.log`。
- `artifact_manifest.json` 与 `swanlog/hierarchical-generative-evaluation/`。

### 3.2 两千次配对统计与九项门槛

| 层级       | 精确位置                                         | 接口                                            |
| ---------- | ------------------------------------------------ | ----------------------------------------------- |
| Shell 入口 | `scripts/run_asymmetric_diagnostic_analysis.sh`  | 把固定 S3 与 D1/D2/D3 候选交给比较程序          |
| 分析函数   | `src/flow_probe/s3_s4_detection_analysis.py:335` | `analyze`                                       |
| 命令入口   | `src/flow_probe/s3_s4_detection_analysis.py:603` | `python -m flow_probe.s3_s4_detection_analysis` |
| 门槛定义   | `src/flow_probe/s3_s4_detection_analysis.py:510` | `criteria` 字典与 `overall_pass`                |

固定九项门槛为：

1. 家族自由生成宏平均 F1 相对 S3 下降不超过 `0.01`。
2. 子类自由生成宏平均 F1 相对 S3 下降不超过 `0.01`。
3. 全部分区自由生成结构化输出合法率最低值不低于 `0.95`。
4. 三个未知攻击场景平均召回下降不超过 `0.05`。
5. 三个未知攻击场景平均良性误报率增加不超过 `0.02`。
6. 子类测试已知类拒识率增加不超过 `0.02`。
7. 子类测试期望校准误差增加不超过 `0.02`。
8. 未观测状态均方误差相对 S3 至少改善 `10%`。
9. 物理残差均方误差相对 S3 至少改善 `10%`。

九项全部为真才设置 `overall_pass=true`。配对统计要求两个评估目录的 `selected_samples_manifest.json` 完全一致，并对自由生成、候选评分和开放集聚合执行种子 42、按真实标签分层的 2,000 次配对自助法。

统计制品为 `analysis_config.json`、`environment.json`、`input_manifest.json`、`calibration_metrics.json`、`paired_bootstrap.json`、`comparison_summary.json` 和 `artifact_manifest.json`，包装器另保存 `launcher.log`。

## 4. 现有运行命令

以下命令均须在服务端项目根目录执行，先 `source /root/.bashrc`，并使用 `screen` 承载长任务。

### 4.1 D1/D2/D3 两步冒烟与 202 步训练

```bash
bash scripts/run_asymmetric_diagnostic.sh d1 runs/asymmetric-physics-diagnostics/<唯一冒烟目录> 2
bash scripts/run_asymmetric_diagnostic.sh d2 runs/asymmetric-physics-diagnostics/<唯一冒烟目录> 2
bash scripts/run_asymmetric_diagnostic.sh d3 runs/asymmetric-physics-diagnostics/<唯一冒烟目录> 2

bash scripts/run_asymmetric_diagnostic.sh d1 runs/asymmetric-physics-diagnostics/<唯一正式目录> 202
```

包装器拒绝未知模式、非项目根目录和复用已有输出目录。D3 的两步冒烟沿用正式 202 步轨迹前两步，不按两步预算重新缩放。

### 4.2 现有 50 步结构探针

任务十六使用的入口是：

```bash
uv run --no-sync python -m flow_probe.representation_train \
  --config configs/representation_coupling_seed42.yaml \
  --variant B0 \
  --output-dir runs/representation-coupling/<唯一目录> \
  --run-name <唯一运行名> \
  --max-steps 50 \
  --model-path /root/autodl-tmp/thesis/models/Qwen3-1.7B
```

`representation_train.py` 只允许 B0/B1 和 2/50 步，不能把新理论直接追加为 B2。可复用的是其“生成损失对预测状态梯度非零”和“固定状态扰动改变 logits”的诊断模式，不可复用其已失败的普通加法投影、可靠性门或 QR-Stiefel 计算图。

### 4.3 固定 `eval300`

```bash
bash scripts/run_asymmetric_diagnostic_eval.sh d1
bash scripts/run_asymmetric_diagnostic_eval.sh d2
bash scripts/run_asymmetric_diagnostic_eval.sh d3
```

该包装器把训练目录和私有适配器路径写死，仅适用于 D1/D2/D3。新结构必须拥有独立评估入口，不能伪装成 D1/D2/D3 目录。

### 4.4 两千次配对统计

```bash
bash scripts/run_asymmetric_diagnostic_analysis.sh d1
```

通用底层入口为：

```bash
uv run --no-sync python -m flow_probe.s3_s4_detection_analysis \
  --s3-output <固定S3评估目录> \
  --s4-output <候选评估目录> \
  --s3-training <固定S3训练目录> \
  --s4-training <候选训练目录> \
  --output <唯一统计目录> \
  --bootstrap-repetitions 2000 \
  --seed 42
```

输出中的 `s4` 只是历史候选键名，不表示候选必须采用原 S4 方法。

## 5. 第二结构支柱的最小改动边界

### 5.1 应新增或调整的文件

文献方向冻结后，实施计划应把最终理论名称代入以下职责，不能把占位名称直接提交为最终命名：

1. **新增结构模块**：位于 `src/flow_probe/`，只定义第二支柱前向、恒等旁路、结构状态和结构诊断，不复制物理公式。
2. **新增独立训练器**：位于 `src/flow_probe/`，复用 `PhysicsTrainingSettings`、数据批次、状态头、状态掩码和队列残差；显式提供基础模型、PINN 单支柱、结构单支柱、组合方法四种不可变消融契约。
3. **新增独立正式评估器或推理运行时**：必须同时覆盖自由生成和候选完成评分，加载结构权重与状态头，并保持现有六分区、阈值校准、预测格式和效率字段。
4. **新增训练配置和 `eval300` 配置**：固定种子、数据、LoRA、批量、评价样本和九项门槛，只增加结构必要参数。
5. **新增训练、评估与统计包装器**：固定服务端绝对路径、唯一输出目录和 `uv run --no-sync`。
6. **修改 `pyproject.toml`**：只增加新训练与评估控制台入口，不删除现有入口。
7. **新增直接覆盖结构契约的测试文件**：实现完成后在服务器执行，不在本机运行 pytest。

### 5.2 可以直接复用且原则上不修改的接口

- `ProbeConfig` 与 `TrackingSettings`。
- `PhysicsTrainingSettings`、`_build_settings`、`_generation_batch`、`_state_batch`。
- `ContinuousQueueStateHead`、`build_state_supervision_masks`、`masked_state_target_loss`。
- `queue_balance_residual` 与现有五锚点、四窗口物理数据协议。
- `physics_sample_schedule`、`_input_manifest`、`_environment_manifest` 和 `record_step_metrics`。
- `hierarchical_evaluation.py` 中的固定评估计划、分层抽样、标签解析、开放集指标和阈值校准纯函数。
- `s3_s4_detection_analysis.analyze` 的预测配对、校准、统计和九项门槛逻辑，前提是候选训练摘要继续提供 `validation.state_mse_unobserved` 与 `validation.physics_residual_mse`。
- `tracking.swanlab_run`、`capture_console_log` 和制品清单协议。
- `representation_coupling.py` 中 `decoder_last_hidden`、`output_embeddings`、`prompt_anchor_positions`、`supervised_prediction_mask`、`causal_lm_loss` 与状态扰动诊断的**接口思路**；不得复用已失败的 `PhysicalRepresentationCoupling` 作为新理论。

### 5.3 禁止修改或覆盖

- `asymmetric_physics_train.py` 中 D0/D1/D2/D3 的契约、学习率、损失开关和历史结果解释。
- 三份 D1/D2/D3 评估配置与三个既有包装器。
- `representation_coupling.py` 的 B0/B1 历史语义；不得增加 B2 冒充新理论。
- `physics_train.queue_balance_residual`、双锚点监督方式、五锚点维度、公共字段和 ns-3 通量定义。
- S3 检测适配器和所有既有正式运行目录。
- GeNIS 与 ns-3 数据文件、样本顺序、种子、训练和阈值校准的未知类排除规则。
- `hierarchical_evaluation.build_evaluation_plan` 的六个分区、每类 300 条和只用子类验证集校准阈值的协议。
- `s3_s4_detection_analysis.py` 的九项数值门槛与 2,000 次配对统计协议。
- SwanLab 项目、工作区、在线模式和运行制品清单。

## 6. 新结构必须新增的最小接口契约

不预选具体理论时，仍可固定以下候选无关接口：

1. `forward` 必须接收生成隐藏表示与模型预测的五维物理状态，返回改写后的隐藏表示和可记录的结构诊断量。
2. 必须提供显式恒等或旁路模式；关闭第二支柱时，输出应与同初始化基础路径相同，并保存 logits 最大差。
3. 必须暴露结构可训练参数集合，训练器应拒绝非预期参数泄漏进入优化器。
4. 必须保存结构权重，并能由正式评估器无真值加载。公开数据推理时不得读取队列真值、场景编号或未知攻击标签。
5. 必须同时实现训练期因果语言模型前向、自由生成下一词元前向和候选完成整序列评分前向。
6. 必须记录 `dL_gen/dq_hat`、物理损失到结构参数的梯度范数、结构参数梯度范数和状态干预造成的 logits 变化。
7. 必须记录恒等旁路差、结构启用差、训练后旁路保护差和冻结参数摘要。

## 7. 四组消融与实施风险

### 7.1 四组消融尚缺统一契约

当前 D1/D2/D3 只是在同一私有 LoRA 上开关损失，不能直接表示以下四组：

1. 基础模型。
2. PINN 单支柱。
3. 结构单支柱。
4. PINN 与结构组合。

新训练器必须预先回答“结构单支柱在不使用 PINN 时从哪里获得条件状态”。若仍使用状态真值辅助监督，它不是完全无物理结构；若完全不使用状态头，则与组合方法的参数量和前向接口不同。该定义必须在 writing-plans 中冻结，不能运行后解释。

### 7.2 正式评估可能静默绕过结构

- `_run_free_generation` 在 `hierarchical_evaluation.py:492` 直接调用 `model.generate`。
- `_run_candidate_scoring` 在 `hierarchical_evaluation.py:646` 直接调用 `model(...).logits`。
- 现有 `_load_model_runtime` 只知道基础 LoRA 和名为 `physics_private` 的第二 LoRA，不加载状态头或任意结构模块。

因此，只在训练器中手工调用结构模块是不够的。两步冒烟必须对训练前向、贪心生成和候选评分三条路径分别做结构开关干预；三条都改变输出且关闭时恢复基线，才能进入 50 步。

### 7.3 梯度存在不等于物理信息有效

D1/D2/D3 只记录参数梯度范数。任务十六已有 `dL_gen/dq_hat` 与状态扰动诊断，可作为新结构的最低机制门槛，但仍需同时证明：

- 物理损失确实到达第二支柱参数。
- 生成损失确实依赖预测状态。
- 扰动状态会改变受监督位置与推理位置 logits。
- 恒等旁路关闭结构后恢复基础检测路径。

### 7.4 恒等旁路需要双重验证

- 初始化验证：结构启用但保持恒等初始化时，与基础路径的 logits 差应满足预注册容差。
- 训练后验证：显式关闭结构后，基础检测路径不能因意外可训练参数而改变。

现有 `_adapter_parameter_digest`、`_last_token_logits` 和 `family_route_equivalence.json` 可复用其审计模式，但新结构不能沿用“只保护家族、牺牲子类与开放集”的旧硬路由。

### 7.5 显存、吞吐与延迟

训练至少记录运行时间、每步吞吐、峰值显存、总可训练参数、结构参数和状态头参数。评估至少记录：

- 自由生成每秒样本数、输入与生成词元数、延迟第 50 与第 95 百分位、峰值显存。
- 候选评分每秒样本数、候选序列数、候选词元数和峰值显存。
- 相对基础模型的参数、训练时间、显存、吞吐和推理延迟变化。

两路探索进程可以并行，但并行运行的吞吐和显存不得用于正式效率比较。正式效率必须独占 GPU、相同批量、相同输入和相同评估顺序。

## 8. 不可变实验约束

- 本地项目根目录：`/Users/bilibili/personal/note/thesis/experiments/llm_probe`。
- 服务端项目根目录：`/root/autodl-tmp/thesis/experiments/llm_probe`。
- 基座：`/root/autodl-tmp/thesis/models/Qwen3-1.7B`。
- 硬件：单块 RTX 5090 32GB；环境使用 `uv`。
- 依赖命令：仅 `uv run --no-sync` 或 `uv pip install --no-deps -e .`，禁止裸 `uv sync`。
- 生成训练：`runs/data-bundled/genis-hierarchical-v2-multitask-seed42/train.jsonl`。
- 生成验证：同目录 `validation.jsonl`。
- 物理训练、验证、测试：`runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/{train,validation,test}.jsonl`。
- `eval300` 数据：`runs/data-sampled/genis-hierarchical-v2-seed42`。
- 种子：首轮固定 42；通过九项门槛后才允许 43、44。
- 有效生成批量：`4 x 4 = 16`；物理批量 4；验证批量 8。
- 状态监督：`anchor0_plus_one`；状态权重 1.0；物理权重 0.01；梯度裁剪 1.0。
- SwanLab：在线模式，工作区 `mortiswang`，项目 `malicious-traffic-llm`。
- 每次运行使用唯一输出目录，保存配置、环境、输入哈希、控制台、逐步指标、摘要、预测、权重、SwanLab 原始日志和制品清单。
- 新实验不得修改数据、PINN 方程、原始九项门槛、未知攻击协议或已有正式制品。
- 同步使用 `rsync` 白名单，不使用 `--delete`；服务端长期任务使用 `screen`。

## 9. writing-plans 的直接输入

首选结构返回后，实施计划应按以下顺序形成：

1. 冻结结构前向、恒等旁路、状态来源和三条推理路径。
2. 冻结四组消融的准确含义与同预算规则。
3. 新建结构模块、训练器、正式评估运行时、配置、包装器、入口和直接测试。
4. 服务器只运行最小目标测试与两步真实模型冒烟。
5. 两步同时通过训练梯度、状态干预、恒等旁路、自由生成和候选评分门槛后，运行一次 50 步方向探针。
6. 50 步只有在检测、状态与物理三类预注册门槛同时通过时，才运行种子 42 的 202 步、`eval300` 和 2,000 次配对统计。
7. 九项全部通过后才进入种子 43、44；失败则按一次性合同停止，不增加同方法调参变体。

## 10. 最关键的三个接口

1. `physics_train.queue_balance_residual` 与 `ContinuousQueueStateHead`：固定 PINN 支柱的可微状态和守恒接口。
2. 新结构必须覆盖 `hierarchical_evaluation._run_free_generation` 与 `_run_candidate_scoring` 的推理路径：否则正式评估不会测试实际结构。
3. `s3_s4_detection_analysis.analyze` 的九项 `criteria`：保持检测、开放集、校准、状态和物理证据的最终单次裁决入口。
