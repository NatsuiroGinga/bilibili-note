# 共享 B0 状态监督与标准 PINN 基线实施计划

> 执行阶段固定使用 `subagent-driven-development`，每项实现由独立代理完成，并由新的审查代理复核。当前用户已取消格式化，不运行 Black、Prettier 或仅格式类检查。

**目标：** 在不改变普通共享 B0 Qwen 分类输入、样本顺序和训练协议的前提下，补齐仅状态监督与标准 PINN 两条种子 42 基线，并形成可恢复、可审计、可公平比较的运行制品。

**架构：** 冻结分类 JSONL 保持不可变，ns-3 物理真值进入独立旁路。公共 Qwen 构建路径由原训练入口提取，新训练器以 `sample_id` 连接两路输入，共用状态头、初始化、调度和检查点，仅以 `lambda_physics=0` 或 `0.01` 区分两条基线。

**技术栈：** Python、PyTorch、Transformers、TRL、PEFT、QLoRA、YAML、JSONL、SwanLab、受管同步脚本。

## 全局约束

- 科学参数固定为：`seed=42`、`max_steps=200`、生成微批量 `2`、梯度累积 `2`、有效生成批量 `4`、保存间隔 `20`。
- 无卡或显存不足时只允许生成微批量 `1`、梯度累积 `4`，有效批量仍为 `4`。
- `lambda_state=1.0`；仅状态监督的 `lambda_physics=0.0`；标准 PINN 的 `lambda_physics=0.01`。
- 状态掩码固定为 `anchor0_plus_one`；物理记录固定 `2421` 条；物理微步固定 `400`；用途固定 `train_fit_diagnostic`。
- 分类输入只读绑定 `runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl`，禁止修改、复制后加入物理字段、过采样或按物理标签重排。
- 物理字段不得进入提示词、分类数值视图或标签；训练时只允许按 `sample_id` 连接独立旁路。
- 两条基线必须共用生成清单及顺序、物理旁路及调度、状态头结构及初始化、优化器、调度器、梯度裁剪、保存间隔和公开检测评估清单。
- 不修改 `shared_b0_view.py`、`shared_b0_view_v1.yaml`、`physics_train.py`、`evaluate_model.py`、`run_qwen_physics_m012.sh`、任何冻结数据和历史运行制品。
- Python `pytest` 只在服务器项目 `uv` 环境中运行；本机实现代理不得运行测试。
- 不自动提交或推送；达到可提交状态时只提醒用户。
- 详细科学合同以 `.Codex/docs/sdd/task-shared-b0-physics-baselines/implementation-input.md` 为准；若本文与其冲突，停止并由主代理裁决。

## 任务 01：物理旁路合同与确定性物化

**依赖：** 无。

**文件白名单：**

- 新建 `thesis/experiments/llm_probe/configs/shared_b0_physics_sidecar_v1.yaml`
- 新建 `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_sidecar.py`
- 新建 `thesis/experiments/llm_probe/tests/test_shared_b0_physics_sidecar.py`
- 新建 `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-01-sidecar.md`

**接口：**

```python
load_shared_b0_physics_sidecar_config(path: Path) -> SharedB0PhysicsSidecarConfig
materialize_shared_b0_physics_sidecar(config: SharedB0PhysicsSidecarConfig, output_root: Path) -> PhysicsSidecarManifest
validate_shared_b0_physics_sidecar(output_root: Path, classification_manifest: Path) -> PhysicsSidecarAudit
```

**行为：**

- 固定输出 `dataset-v1-shared-b0-physics-v1` 下的旁路 JSONL、数据清单、来源清单、连接审计和物化审计。
- 每条旁路记录必须包含实施输入第 3.2 节列出的全部字段；五锚点数组等长、时间严格递增、数值有限、归一化尺度为正。
- 记录数必须为 `2421`，`sample_id` 唯一，且与冻结分类清单中的 ns-3 标识集合完全相等。
- `usage` 必须严格为 `train_fit_diagnostic`；禁止把当前 2,421 条训练记录标为外部物理测试。
- 两次从空目录独立物化必须逐字节一致；物化前后冻结分类文件 SHA-256 必须不变。
- 缺失、重复、额外或错配标识、非法锚点、非有限数、非正尺度以及来源哈希变化均立即失败。

**服务器目标测试：**

```bash
uv run --no-sync pytest -q tests/test_shared_b0_physics_sidecar.py
```

## 任务 02：普通 Qwen 构建路径行为等价提取

**依赖：** 无；任务 03 集成前必须通过。

**文件白名单：**

- 修改 `thesis/experiments/llm_probe/src/flow_probe/train_sft.py`
- 修改 `thesis/experiments/llm_probe/tests/test_train_sft.py`
- 新建 `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-02-sft-parity.md`

**行为：**

- 从原训练入口提取模型与量化配置、LoRA 挂载、聊天样本与截断、训练参数、检查点发现与绑定、优化器和调度器的稳定构建函数。
- 原命令行、配置含义、默认值、运行目录和普通 Qwen 训练行为不变。
- 数据加载后保留 `sample_id`，但不得把它渲染进提示词或标签。
- 固定小样本在重构前后的聊天文本、令牌、标签掩码、截断和训练参数逐项相等。
- 公共文件不得引用物理旁路配置、状态头或 PINN 损失。

**服务器目标测试：**

```bash
uv run --no-sync pytest -q tests/test_train_sft.py
```

## 任务 03：共同状态头、物理调度与可恢复训练器

**依赖：** 任务 01、02。

**文件白名单：**

- 新建 `thesis/experiments/llm_probe/configs/shared_b0_physics_baselines_seed42_200_v1.yaml`
- 新建 `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_train.py`
- 新建 `thesis/experiments/llm_probe/tests/test_shared_b0_physics_train.py`
- 新建 `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-03-trainer.md`

**接口：**

```text
flow-probe-train-shared-b0-physics --config <配置> --baseline state_supervision|standard_pinn [--preflight-only] [--resume auto|never|<检查点>]
```

**行为：**

- 直接复用 `ContinuousQueueStateHead`、`build_state_supervision_masks`、`select_last_token_hidden` 和 `queue_balance_residual`，不得复制物理公式。
- 两条基线的状态头结构和初始化随机状态完全相同；初始化后记录参数树 SHA-256。
- 状态头只读取普通 Qwen 前向的最后有效令牌隐藏状态并预测五锚点连续队列状态。
- 状态损失按有效掩码逐元素归约；仅状态监督分支在字段访问层拒绝读取物理系数，标准 PINN 分支增加 `0.01` 倍队列平衡残差。
- 冻结 400 个物理微步：21 批大小为 7，379 批大小为 6，2,421 条记录各出现一次；保存完整顺序、批边界和哈希。
- 每步记录生成、状态、物理损失、有效元素数、梯度范数和非有限数；出现非有限损失或梯度立即失败。
- 每 20 个优化步保存 LoRA、状态头、优化器、调度器、梯度缩放器、生成与物理游标、随机数状态、步数、全部绑定哈希、基线身份和损失权重。
- 配置、数据、顺序、初始化或基线身份不匹配时拒绝恢复；已完成运行拒绝覆盖。
- 4 步连续运行必须与运行 2 步、保存并恢复至 4 步在参数、游标和指标容差内等价。

**服务器目标测试：**

```bash
uv run --no-sync pytest -q tests/test_shared_b0_physics_train.py
```

## 任务 04：公开检测与训练拟合物理诊断薄封装

**依赖：** 任务 03 的检查点与绑定格式冻结。

**文件白名单：**

- 新建 `thesis/experiments/llm_probe/configs/shared_b0_state_supervision_seed42_genis_batch16_v1.yaml`
- 新建 `thesis/experiments/llm_probe/configs/shared_b0_state_supervision_seed42_tqhc2_batch16_v1.yaml`
- 新建 `thesis/experiments/llm_probe/configs/shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml`
- 新建 `thesis/experiments/llm_probe/configs/shared_b0_standard_pinn_seed42_tqhc2_batch16_v1.yaml`
- 新建 `thesis/experiments/llm_probe/src/flow_probe/shared_b0_physics_evaluation.py`
- 新建 `thesis/experiments/llm_probe/tests/test_shared_b0_physics_evaluation.py`
- 新建 `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-04-evaluation.md`

**行为：**

- 公共检测评估复用既有评估器、GeNIS/TQH-C2 固定清单、批量 16、无长度分桶、SDPA、确定性贪心生成和批级恢复。
- 验证适配器、状态头、训练绑定、数据清单与评估清单哈希；不得改变提示词、标签合同或解码参数。
- 物理诊断只在训练拟合集上报告状态均方误差、平均绝对误差、各锚点误差、掩码覆盖率、有效元素数、队列平衡残差和非有限数。
- 所有物理诊断显式写入 `evaluation_scope=train_fit_diagnostic`，不得输出“未见物理测试”或“跨拓扑泛化”结论。
- 已完成评估幂等返回，未完成评估支持断点恢复。

**服务器目标测试：**

```bash
uv run --no-sync pytest -q tests/test_shared_b0_physics_evaluation.py
```

## 任务 05：命令入口与受管启动包装

**依赖：** 任务 01、03、04。

**文件白名单：**

- 修改 `thesis/experiments/llm_probe/pyproject.toml`
- 新建 `thesis/experiments/llm_probe/scripts/run_shared_b0_physics_baselines.sh`
- 新建 `thesis/experiments/llm_probe/scripts/run_shared_b0_physics_evaluation.sh`
- 新建 `thesis/experiments/llm_probe/tests/test_run_shared_b0_physics_baselines_wrapper.py`
- 新建 `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/report-task-05-wrappers.md`

**行为：**

- 注册物化、训练、评估三个命令入口。
- 训练包装器只接受 `smoke|formal|recovery-check` 与 `state_supervision|standard_pinn`；评估包装器只接受两条基线与 `genis|tqhc2|physics_fit`。
- 冒烟、恢复检查和正式运行目录完全隔离；已有完成目录拒绝覆盖。
- 启动前执行数据、批量、调度、绑定、设备能力和 SwanLab 标签长度预检；命令失败保留原始退出码和唯一日志目录。
- 正式 GPU 训练使用 SwanLab 在线项目 `mortiswang/malicious-traffic-llm`，保存逐步指标、本地 SwanLab 日志、配置、环境、预测、结果和制品清单。

**服务器目标测试：**

```bash
uv run --no-sync pytest -q tests/test_run_shared_b0_physics_baselines_wrapper.py
bash -n scripts/run_shared_b0_physics_baselines.sh
bash -n scripts/run_shared_b0_physics_evaluation.sh
```

## 任务 06：独立审查、服务器门禁与正式运行

**依赖：** 任务 01 至 05 均完成实现并通过独立审查。

**文件白名单：**

- 新建 `.Codex/docs/sdd/task-shared-b0-physics-baselines/reports/review-final.md`
- 更新 `.Codex/docs/sdd/task-shared-b0-physics-baselines/notes.md`
- 实验完成后更新 `output/第一创新点实验总控.md`

**执行顺序：**

1. 逐文件使用 `guarded_rsync.py` 计划、应用并核对收据；禁止目录覆盖、`--delete` 和直接 SSH/rsync。
2. 服务器运行五个目标测试文件、两份 Shell 语法检查和普通 Qwen 行为等价回归。
3. 两次独立物化旁路并逐文件比较字节与 SHA-256；核对分类冻结文件哈希未变。
4. 分别运行两条 2 步冒烟，确认损失分支、字段隔离、检查点与日志。
5. 运行 4 步连续与 2 步恢复等价检查。
6. 全部门禁通过后再运行两条种子 42、200 步正式训练；探索性短运行可并行，正式效率计时必须分开记录。
7. 对两条检查点分别运行 GeNIS、TQH-C2 和训练拟合物理诊断。
8. 验收本地制品、服务器制品和 SwanLab 云端标量及图表；将结果、运行编号、路径和哈希写入总控。

## 当前状态

- [x] 审计完成。
- [x] 科学参数与文件范围冻结。
- [x] 正式实施计划建立。
- [ ] 任务 01 至 05 实现与逐项审查。
- [ ] 服务器门禁与冒烟。
- [ ] 两条正式训练与评估。
