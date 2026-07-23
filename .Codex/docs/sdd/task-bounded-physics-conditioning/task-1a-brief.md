# 任务 1A 简报：有界物理条件数学模块

## 目标

只实现不依赖 Qwen 挂钩的数学模块，为后续运行时提供稳定接口。不得实现训练器、评估器、生成会话或 Shell。

## 允许修改

- 新建 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`。
- 写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-1a-report.md`。

不得修改其他文件，不得创建测试文件。

## 固定实现

1. `ConditioningSpec`：冻结数据类，字段及唯一允许值为：
   - `num_hidden_layers=28`
   - `hidden_size=2048`
   - `source_layer=13`
   - `target_layers=(24,25,26,27)`
   - `state_size=5`
   - `condition_tokens=9`
   - `bottleneck_size=256`
   - `attention_heads=4`
   - `residual_ratio_cap=0.1`
   - `norm_epsilon=1e-6`
   - `gate_init=0.0`
   构造后校验所有值、可除性、有限性和层索引，任何变化都抛出 `ValueError`。
2. `resolve_conditioning_layers(num_hidden_layers)`：仅接受 `28`，返回 `(13,(24,25,26,27))`。
3. `ConditioningDiagnostics`：冻结数据类，记录门值元组、注意力熵元组、最大残差比例、源挂钩次数、四层目标挂钩次数、预填充次数和缓存解码次数。
4. `PhysicalConditionEncoder`：输入 `[B,5]` 非负有限状态，计算四个相邻有符号差分；状态标量与差分标量分别拼接类型嵌入和位置嵌入，通过共享两层 `Linear-SiLU-Linear` 编码为 `[B,9,256]`。拒绝形状错误和非有限输入。
5. `BoundedPhysicsCrossAttention`：输入隐藏 `[B,T,2048]`、条件 `[B,9,256]`、布尔掩码 `[B,T]`。使用独立 `q/k/v/out` 投影、4 头缩放点积注意力和独立零初始化标量 `alpha`。修正公式严格为 `0.1*tanh(alpha)*stopgrad(||h||)*z/(||z||+1e-6)`，只应用于掩码位置。返回修正隐藏、注意力熵和实测最大残差比例。计算门前拒绝非有限输入和注意力输出。
6. `build_training_injection_mask(labels)`：`labels[:,1:] != -100` 映射到对应预测位置 `[:-1]`，最后位置为假。
7. `build_candidate_injection_mask(completion_start, attention_mask)`：每条样本从 `completion_start-1` 到最后一个有效令牌的前一位置为真；校验边界。
8. `build_condition_state(hidden, anchor_positions, state_head)`：从 `[B,T,2048]` 取每条锚点，调用传入状态头，校验输出 `[B,5]`、非负、有限。

## 纪律与验证

- 读取项目 `AGENTS.md` 和现有 `physics_train.ContinuousQueueStateHead`，不得复制状态头或物理公式。
- 禁止使用 `test-driven-development`，禁止运行 pytest，禁止 git commit。
- 完成后只执行 Black、Ruff 和 `git diff --check` 针对新增模块。
- 报告列出公开接口、形状、格式检查结果和运行时尚未实现的边界。
- 最终只返回 `DONE`、`DONE_WITH_CONCERNS`、`NEEDS_CONTEXT` 或 `BLOCKED`。
