# 任务 1A 实现报告：有界物理条件数学模块

## 状态

`DONE`

## 变更文件

- 新增 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`。
- 新增 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-1a-report.md`。
- 未修改其他文件，未创建测试文件。

## 公开接口与形状

- `ConditioningSpec`：冻结数据类；固定并校验 28 层、2048 隐藏维、源层 13、目标层 24 至 27、五状态、九条件令牌、256 瓶颈维、四头注意力、0.1 残差比例上限、`1e-6` 范数稳定项和零门初始化。任何字段变化均抛出 `ValueError`。
- `resolve_conditioning_layers(num_hidden_layers)`：仅接受 `28`，返回 `(13, (24, 25, 26, 27))`。
- `ConditioningDiagnostics`：冻结数据类；`gate_values`、`attention_entropies` 和 `target_hook_counts` 均固定为长度 4，并校验有限数值、非负计数和非负有限最大残差比例。
- `PhysicalConditionEncoder`：接收非负有限状态 `[B,5]`，以五个状态和四个相邻有符号差分构成九个标量令牌；每个标量拼接类型嵌入和位置嵌入，经共享 `Linear-SiLU-Linear` 输出 `[B,9,256]`。
- `BoundedPhysicsCrossAttention`：接收隐藏状态 `[B,T,2048]`、条件令牌 `[B,9,256]` 和布尔注入掩码 `[B,T]`；使用独立 `q_proj`、`k_proj`、`v_proj`、`out_proj` 与四头缩放点积注意力，返回修正隐藏状态 `[B,T,2048]`、标量注意力熵张量和标量实测最大残差比例张量。
- `build_training_injection_mask(labels)`：接收 `[B,T]` 标签，输出 `[B,T]` 布尔掩码；位置 `[:-1]` 对应 `labels[:,1:] != -100`，末位恒为假。
- `build_candidate_injection_mask(completion_start, attention_mask)`：接收逐批次候选起点及 `[B,T]` 布尔或 0/1 整数注意力掩码，输出 `[B,T]` 布尔掩码；每条样本的真值区间为 `completion_start-1` 至最后有效令牌前一位置，并校验起点、有效令牌和区间连续性。
- `build_condition_state(hidden, anchor_positions, state_head)`：从 `[B,T,2048]` 逐样本提取锚点隐藏状态，调用传入的既有状态头，校验并返回非负有限 `[B,5]` 状态。

## 数学边界

- 每个目标层拥有独立零初始化标量参数 `alpha`。
- 修正严格按 `0.1 * tanh(alpha) * stopgrad(||h||) * z / (||z|| + 1e-6)` 逐令牌计算。
- 修正仅作用于布尔掩码为真的位置；零初始化门下输出保持隐藏状态恒等。
- 在门计算前检查隐藏状态、条件、注意力权重、注意力输出、相关范数和 `alpha` 的有限性。

## 检查结果

- 初次直接执行 `black src/flow_probe/bounded_physics_conditioning.py` 失败：当前 shell 中不存在 `black` 可执行文件，未改动源码。
- 初次执行 `uv run --no-sync black ...` 失败：沙箱不允许初始化 `/Users/bilibili/.cache/uv`，未改动源码。
- 经授权执行 `uv run --no-sync black src/flow_probe/bounded_physics_conditioning.py`：通过，格式化 1 个文件。
- 执行 `uv run --no-sync ruff check src/flow_probe/bounded_physics_conditioning.py`：通过，输出 `All checks passed!`。
- 执行 `git diff --check -- thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`：通过，无输出。
- 按任务纪律未运行本地 `pytest`，未执行 Git 提交。

## 遗留边界

- 未实现 Qwen 层挂钩、源层状态采集、四目标层注入和挂钩生命周期管理。
- 未实现训练器、评估器、生成会话、预填充与缓存解码路由、诊断计数聚合。
- 未实现配置入口、命令行或 Shell、制品保存及服务端运行。
- 本任务未创建行为测试；运行时接入和服务器测试由后续任务负责。
