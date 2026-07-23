# 任务 1B 简报：Qwen 挂钩运行时与直接测试

## 前置事实

任务 1A 已通过独立复核。必须复用现有 `ConditioningSpec`、`ConditioningDiagnostics`、`PhysicalConditionEncoder`、`BoundedPhysicsCrossAttention`、掩码函数和 `build_condition_state`，不得重写其数学逻辑。

## 允许修改

- 修改 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`，仅追加运行时相关实现或为其增加必要公开方法。
- 新建 `thesis/experiments/llm_probe/tests/test_bounded_physics_conditioning.py`。
- 写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-1b-report.md`。

不得修改其他文件。

## 必须新增的类型

1. `PhysicsConditionedOutput`：包含底层 `model_output`、`predicted_state`、`condition_tokens` 和 `ConditioningDiagnostics`；提供 `loss`、`logits` 和按名称读取底层输出的兼容访问。
2. 内部 `_ConditioningSession`：保存模式、提示锚点、注入掩码、缓存状态、条件词元、四层诊断与计数；不得跨调用复用。
3. `PhysicsConditionedRuntime(torch.nn.Module)`：注册状态头、共享条件编码器和四个独立注入器，但不得把底层 Qwen/PeftModel 注册进自身 `state_dict`。

## 模型与挂钩

- 运行时构造参数：底层模型、现有 `ContinuousQueueStateHead`、可选 `ConditioningSpec`。
- 解析并验证实际解码层数量 28 和隐藏维度 2048；兼容项目当前 PeftModel/Qwen 的层路径，但不要针对未知模型静默猜测。
- 第 13 层使用输出挂钩：从 Tensor 或 tuple 首元素提取 `[B,T,2048]`；预填充或普通前向时按提示锚点计算状态和 9 个条件词元；缓存解码时不得重复计算。
- 第 24、25、26、27 层使用 `with_kwargs=True` 的前向预挂钩：取得 `hidden_states`，按当前掩码调用对应注入器，并返回修改后的参数；保持其他位置参数和关键字参数原样。
- 运行时使用 `object.__setattr__` 或等价非注册引用保存底层模型，保证运行时 `state_dict` 不包含 Qwen/S3 参数。
- 提供 `close()` 移除全部挂钩；析构不能替代显式关闭。

## 三条调用路径

### 训练或普通前向

`forward(input_ids, attention_mask, labels=None, completion_start=None, bypass=False, **kwargs)`：

- `labels` 存在且 `completion_start` 为空时，用首个非 `-100` 标签位置减一作为提示锚点，并使用训练注入掩码。
- `completion_start` 存在时，用 `completion_start-1` 为提示锚点，使用候选注入掩码；同一提示的不同候选必须得到相同状态。
- 两者都缺失时拒绝结构启用；`bypass=True` 时允许直接执行底层前向。
- 返回 `PhysicsConditionedOutput`；会话必须在 `finally` 中清理。

### 缓存自由生成

`generate(input_ids, attention_mask, bypass=False, **kwargs)`：

- 仅允许 `num_beams` 缺省或等于 1。
- 从 `attention_mask` 取得每条提示最后有效位置，建立一次生成会话后委托底层 `model.generate`。
- 首次源层调用若序列长度大于 1，计算并缓存条件，`prefill_count=1`；以后序列长度为 1 的缓存步只复用条件并增加 `cached_decode_count`。
- 预填充只注入最后有效提示位置；缓存步对当前单令牌位置注入。
- 返回底层生成结果以及最终诊断，具体形式用 `PhysicsConditionedGeneration` 冻结数据类固定。
- 无论成功或异常都在 `finally` 清理会话。

### 旁路与并发纪律

- `bypass=True` 时挂钩保持无动作，底层输出必须与直接调用模型一致。
- 发现嵌套 `forward/generate`、已有活动会话、未关闭运行时、缺失条件或目标层先于源层调用时立即失败。
- 本任务只支持单进程、单 GPU 同步调用；不得假装线程安全。

## 保存加载

- `structure_state_dict()` 只返回状态头、条件编码器、四个注入器和门参数。
- `load_structure_state_dict(state, strict=True)` 必须拒绝缺键、多键、形状不符和非有限门值。
- 提供结构参数名、参数量和意外底层参数检查接口，供训练器建立白名单。

## 直接测试

使用最小伪模型模拟 `model.layers`、标准 `forward` 和缓存式 `generate`，不得加载真实 Qwen。至少覆盖：

1. 运行时只注册新结构参数，状态字典不含底层模型。
2. 第 13 层捕获和四个目标层挂钩均执行。
3. 零门启用与旁路严格相同，固定非零门后结构输出变化且残差界成立。
4. 第一步生成梯度只到门；模拟一次门更新后第二步梯度到状态头、条件编码器和注入器。
5. `forward` 的训练掩码和候选掩码正确；不同候选完成文本不改变相同提示状态。
6. `generate` 只有一次完整提示预填充，后续均为单令牌缓存步；条件状态只计算一次。
7. 多束、嵌套、缺失边界、非有限状态、异常清理和关闭后调用均被拒绝。
8. 保存加载往返后结构输出一致；缺键和多键失败。

## 纪律与验证

- 禁止 `test-driven-development`；先实现运行时，再补测试。
- 不运行本地 pytest。
- 只执行一次 Black、一次 Ruff 和一次 `git diff --check`，覆盖两个目标文件。
- 不执行 git commit，不改无关文件。
- 报告必须列出实现接口、静态检查、未运行服务器测试和已知风险。
