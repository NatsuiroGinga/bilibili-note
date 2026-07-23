# 任务 2A 实现报告：E1/E2 训练核心

## 状态

`DONE_WITH_CONCERNS`

训练核心、直接测试和静态检查已完成；按照任务纪律未在本机运行 `pytest`，真实 Qwen、S3、CUDA 与两步梯度路径仍须在 GPU 服务器验收。

## 变更文件

- 新增 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_train.py`。
- 新增 `thesis/experiments/llm_probe/tests/test_bounded_physics_train.py`。
- 新增 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-2a-report.md`。
- 未修改配置、Shell、`pyproject.toml`、任务 1 运行时或其他生产源码。

## 训练核心

- `ConditioningVariantContract` 和 `resolve_conditioning_variant` 只接受 `structure_only` 与 `combined`。
- E1 只启用生成损失，状态损失和物理损失以标量 `0.0` 记录；五维状态只标记为条件潜变量。
- E2 固定采用 `L_gen + 1.0 L_state + 0.01 L_physics`，并复用 `masked_state_target_loss` 与 `queue_balance_residual`。
- `bounded_physics_learning_rate` 固定 202 步线性预热加余弦衰减：第 1 步 `2e-5`、第 20 步 `2e-4`、第 202 步 `2e-5`；两步冒烟直接取前两步。
- `configure_structure_trainability` 冻结 Qwen、S3 和既有 LoRA，只允许状态头、共享条件编码器、四层交叉注意力和四个门训练；发现其他参数立即失败。
- `physics_gradient_isolation` 使用独立梯度读取证明物理损失只到状态头，并强制注入器与冻结基座梯度范数为零。
- `generation_gradient_snapshot` 与 `validate_generation_gradient_step` 强制第一步生成梯度只到四个门，第二步贯通状态头、条件编码器、交叉注意力和门。
- `prepare_base_for_bounded_training` 显式传入 `use_gradient_checkpointing=False`，调用关闭接口后由 `gradient_checkpointing_audit` 复核模型及子模块均未启用梯度检查点。
- 训练循环复用 `PhysicsTrainingSettings`、生成批次、物理批次、状态监督掩码、样本调度、输入与环境清单、控制台捕获、SwanLab 和逐步指标记录。
- 每步记录三项损失、学习率、四层门值、四层注意力熵、最大残差比例、四类结构梯度、三项物理梯度隔离值和训练、生成、候选评分路径计数。

## 制品接口

训练核心保存以下专用制品：

- `structure_config.json`
- `structure_state.pt`
- `base_binding.json`
- `gradient_path.json`
- `runtime_path_audit.json`
- `bypass_equivalence.json`

同时保存配置快照、环境清单、输入哈希、控制台日志、逐步指标、训练摘要、生成与物理样本顺序、SwanLab 原始日志和制品清单。`load_bounded_structure_artifacts` 在核对架构版本、固定结构、基座绑定、S3 绑定和梯度检查点关闭记录后，调用任务 1B 的严格结构加载接口。

## 直接测试

`tests/test_bounded_physics_train.py` 覆盖：

- 两个模式的固定契约、未知模式拒绝和开关或权重篡改拒绝。
- E1 关闭项不执行且写为数值零，E2 使用固定损失权重。
- 第 1、20、21、202 步学习率，以及越界步拒绝。
- Qwen/S3 冻结、四类结构参数分组、四个门和意外参数拒绝。
- 物理梯度只到状态头，以及注入器或基座泄漏拒绝。
- 首步仅门梯度、次步四类新增结构梯度贯通及错误路径拒绝。
- `use_gradient_checkpointing=False` 参数传递、显式关闭和残留启用拒绝。
- 四层门、注意力熵、残差比例和挂钩计数的逐步诊断聚合。
- 强制制品文件名、完成状态、跟踪清单、基座与 S3 内容绑定和严格结构加载。

## 独立复审修复

针对 `task-2a-review.md` 的一项重要问题，严格加载门禁已做最小修复：

- 加载前要求 `BoundedRunLayout.required_paths` 中的全部制品均为普通文件。
- 强制读取 `training_summary.json`，要求架构版本正确且 `status=finished`，并核对变体、基座路径、S3 路径和冻结参数计数。
- 强制读取 `artifact_manifest.json`，要求跟踪架构版本、训练阶段和 `status=finished` 正确，存在 SwanLab 运行编号及完整制品路径键。
- 要求当前运行目录存在非空的 SwanLab 原始日志目录。
- 重新计算当前 S3 适配器目录清单，与 `base_binding.json` 保存清单逐项比较。
- 要求训练前后 S3 参数摘要一致，并重新计算当前内存 S3 参数摘要；任何缺失或变化均在加载结构状态前失败。
- 回归测试新增未完成运行、缺失跟踪键、缺失 S3 清单、同路径 S3 文件变化和内存 S3 参数变化的拒绝场景。

## 验证结果

- 失败测试命令：无。任务明确禁止本机运行 `pytest`，因此未构造或执行红绿测试历史。
- 通过测试命令：未执行。本测试文件须在 GPU 服务器的项目 `uv` 环境运行。
- 格式化：复审修复后执行 `UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync black src/flow_probe/bounded_physics_train.py tests/test_bounded_physics_train.py`，退出状态 `0`，重新格式化 2 个文件。
- 静态检查：`UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync ruff check src/flow_probe/bounded_physics_train.py tests/test_bounded_physics_train.py`，退出状态 `0`，输出 `All checks passed!`。
- 差异检查：复审修复报告写入后重新执行 `git diff --check`，退出状态 `0`，无输出。
- Git：未提交，未推送。

## 运行制品

- 本任务未启动本机或 GPU 训练，因此没有运行目录、SwanLab 运行编号或训练制品。
- 任务 2B 接入配置和 Shell 后，任务 4 才能生成 E1/E2 两步冒烟及正式 202 步制品。

## 遗留风险与边界

- 未执行服务器 `pytest`，真实 PEFT 参数命名、量化模型设备放置和两步梯度范数尚未获得运行证据。
- 本任务没有新增配置、Shell 或控制台入口；这些属于任务 2B，不应在任务 2A 扩展。
- 首步与次步梯度路径在训练循环中为硬门禁；若实际混合精度下某类梯度严格为零，运行会立即失败并保留控制台与 SwanLab 失败制品。
