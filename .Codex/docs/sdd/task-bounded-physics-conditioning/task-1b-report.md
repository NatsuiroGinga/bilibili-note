# 任务 1B 实现报告：Qwen 挂钩运行时与直接测试

## 状态

`DONE`

## 变更文件

- 修改 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`。
- 新建 `thesis/experiments/llm_probe/tests/test_bounded_physics_conditioning.py`。
- 新建 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-1b-report.md`。
- 未修改训练器、评估器、配置、依赖、命令行、Shell 或其他文件。

## 实现接口

- `PhysicsConditionedOutput`：冻结数据类，保存底层 `model_output`、`predicted_state`、`condition_tokens` 和 `ConditioningDiagnostics`；支持 `loss`、`logits`、按名称下标和按属性读取底层输出。
- `PhysicsConditionedGeneration`：冻结数据类，保存底层生成结果和最终诊断，并支持按名称读取底层生成输出。
- `_ConditioningSession`：逐调用保存模式、提示锚点、注入掩码、缓存条件、四层熵/残差诊断、挂钩次数、预填充次数和缓存解码次数；所有公开调用均在 `finally` 中清理会话。
- `PhysicsConditionedRuntime`：注册既有状态头、一个共享条件编码器和四个独立注入器；底层 Qwen/PeftModel 使用非注册引用，不进入运行时 `state_dict`。
- 层解析只接受直接 Qwen 的 `model.layers` 路径和项目 PeftModel 的 `base_model.model.model.layers` 路径，并同时校验 28 层和 2048 隐藏维；未知或歧义路径直接失败。
- 第 13 层输出挂钩负责按提示锚点构造一次状态和九个条件词元；第 24、25、26、27 层使用 `with_kwargs=True` 的前向预挂钩，兼容位置参数和 `hidden_states` 关键字参数，并保持其余参数不变。
- `forward` 支持标签训练掩码、候选完成起点掩码和显式旁路；缺少结构边界时拒绝启用结构。
- `generate` 只接受单束生成；一次完整提示预填充后只接受单令牌缓存步骤，预填充仅注入每条提示最后有效位置，缓存步骤注入当前令牌。
- `structure_state_dict`、`load_structure_state_dict`、`structure_parameter_names`、`structure_parameter_count` 和 `unexpected_base_parameter_names` 提供结构保存、严格加载和训练白名单检查；严格加载会在写入前拒绝缺键、多键、形状不符和非有限门值。
- `close()` 显式移除全部挂钩；关闭后 `forward` 和 `generate` 均拒绝调用。

## 直接测试覆盖

- 直接 Qwen 与 PeftModel 两条伪模型层路径，以及底层参数不进入运行时状态字典。
- 第 13 层捕获、四个目标层注入、零门恒等、旁路与底层直接调用恒等、非零门输出变化和 0.1 残差比例界。
- 第一步结构梯度只到四个门参数；模拟门更新后，梯度到达状态头、条件编码器和注入器内部参数。
- 训练掩码、候选掩码，以及同提示不同完成文本得到相同提示锚点状态。
- 生成只做一次完整提示预填充，后续输入长度均为 1，条件状态只计算一次。
- 多束、嵌套调用、缺少边界、目标层早于源层、非有限状态、底层异常、异常后恢复和关闭后调用。
- 结构状态保存加载往返输出一致，以及缺键、多键、形状错误和非有限门值失败。

## 静态检查

- `UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync black src/flow_probe/bounded_physics_conditioning.py tests/test_bounded_physics_conditioning.py`：通过。
- `UV_CACHE_DIR=/tmp/codex-uv-cache uv run --no-sync ruff check src/flow_probe/bounded_physics_conditioning.py tests/test_bounded_physics_conditioning.py`：通过，输出 `All checks passed!`。
- `git diff --check -- thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py thesis/experiments/llm_probe/tests/test_bounded_physics_conditioning.py`：通过，无输出。
- 按任务纪律未运行本地 `pytest`，未执行 Git 提交。

## 服务器尚待验证

- 尚未在项目 `uv` 环境运行 `tests/test_bounded_physics_conditioning.py`，测试收集、直接伪模型行为和梯度断言需要服务器执行确认。
- 尚未使用真实 Qwen3-1.7B 与项目 PeftModel 核验两条层路径、层输出形态、前向预挂钩参数形态和真实缓存生成序列。
- 新结构模块默认由 PyTorch 创建；接入训练器时必须把整个运行时移动到与第 13 层隐藏状态相同的设备和兼容数据类型。
- 本任务只实现单进程、单 GPU、同步、单束调用，不提供线程安全、多束扩展或跨调用会话复用。
- 未修改训练器和梯度检查点策略；真实训练反向传播及梯度检查点重计算行为属于后续集成任务的服务器门禁。
