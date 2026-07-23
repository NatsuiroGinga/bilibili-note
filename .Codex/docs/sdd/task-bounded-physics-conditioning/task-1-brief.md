# 任务 1 简报：核心条件结构与运行时

## 任务位置

这是 E1/E2 实验的第一项实现任务。只实现可复用核心结构和运行时，不实现训练器、正式评估器、配置或 Shell 包装器。

## 必读材料

1. `/Users/bilibili/personal/note/AGENTS.md`。
2. `/Users/bilibili/personal/note/.Codex/docs/sdd/task-second-structural-pillar-selection/cross-attention-architecture-audit.md`。
3. `/Users/bilibili/personal/note/.Codex/docs/sdd/task-second-structural-pillar-selection/implementation-interface-audit.md`。

## 允许修改

- 新建 `thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`。
- 新建 `thesis/experiments/llm_probe/tests/test_bounded_physics_conditioning.py`。
- 写入 `.Codex/docs/sdd/task-bounded-physics-conditioning/task-1-report.md`。

不得修改其他源码、配置、测试、依赖或既有运行制品。

## 固定结构

- Qwen 层数 28、隐藏维度 2048。
- 源层索引 13；目标层索引 `(24,25,26,27)`。
- 五个状态锚点和四个相邻状态增量，共 9 个条件词元。
- 条件与注意力瓶颈维度 256，4 头。
- 每个目标层使用独立查询、键、值、输出投影和独立标量门；状态头和条件编码器共享。
- 门参数初始化 `0.0`，相对残差上限 `0.1`，数值常数 `1e-6`。
- 逐令牌修正为 `0.1*tanh(alpha_l)*stopgrad(||h||)*z/(||z||+1e-6)`。
- 禁用梯度检查点；生成只允许 `num_beams=1`。

## 必须提供

- `ConditioningSpec`：不可变对象，默认值就是固定结构，并拒绝不同值、非法维度和非有限常数。
- `ConditioningDiagnostics`：四层门值、注意力熵、最大残差比例、源/目标挂钩次数、完整提示预填充次数和缓存解码次数。
- `PhysicalConditionEncoder`：输入 `[B,5]`，内部构造 `[B,4]` 差分，输出 `[B,9,256]`。
- `BoundedPhysicsCrossAttention`：输入 `[B,T,2048]` 与 `[B,9,256]`，按注入掩码输出修正后的隐藏表示和诊断。
- `resolve_conditioning_layers(num_hidden_layers)`：仅接受 `28`，返回 `(13,(24,25,26,27))`。
- `build_training_injection_mask(labels)`：只覆盖预测完成文本的位置。
- `build_candidate_injection_mask(completion_start, attention_mask)`：候选状态锚点固定为 `completion_start-1`，掩码覆盖被评分预测位置。
- `PhysicsConditionedRuntime`：注册源层输出挂钩和四层带关键字参数的前向预挂钩，统一提供训练 `forward`、缓存式 `generate`、显式 `bypass`、诊断快照、结构状态保存和严格加载。

## 运行时契约

1. 源层从提示锚点取得表示并调用现有 `ContinuousQueueStateHead` 产生五个非负锚点。
2. 训练 `forward` 从 `labels` 推出提示锚点和监督注入掩码，不更改底层模型输出格式。
3. `generate` 仅在预填充计算一次条件，以后缓存解码复用；使用 `try/finally` 清理，拒绝嵌套调用和多束生成。
4. 候选评分必须显式传入 `completion_start`；相同提示不能因候选完成文本不同而产生不同状态。
5. `bypass=True` 时不捕获状态、不注入，直接返回原模型路径。
6. 计算门乘法前拒绝非有限状态、条件词元或注意力输出。
7. 状态头、条件编码器、交叉注意力和门是运行时注册子模块，可由 `state_dict` 保存并严格加载；底层 Qwen/S3 不进入该状态字典。

## 实现后测试

直接测试至少覆盖：

- 配置、形状、9 个词元及四层解析。
- 状态非负、零门函数恒等、每令牌残差比例严格低于或等于 `0.1+1e-6`。
- 第一步生成梯度只到门；模拟一次门更新后，第二步生成梯度到状态头、条件编码器和交叉注意力。
- 状态置零、跨样本置换和固定扰动会改变结构启用时的 logits 或隐藏表示。
- 训练、生成、候选评分挂钩调用；生成只有一次完整提示预填充。
- 候选完成文本不影响相同提示的条件状态。
- 旁路、嵌套拒绝、多束拒绝、异常后的上下文清理和保存加载往返。

不得使用真实 1.7B 模型写单元测试；使用最小伪模型模拟 `model.layers`、`forward` 和缓存式 `generate`。

## 验证与报告

- 禁止调用或遵循 `test-driven-development`；先实现，再补测试。
- 不运行本地 pytest。
- 运行 `black`、Ruff 一次和 `git diff --check --` 对应两个新增文件。
- 报告必须写明修改文件、验证命令及结果、未运行的服务器 pytest、遗留风险。
- 返回状态只能是 `DONE`、`DONE_WITH_CONCERNS`、`NEEDS_CONTEXT` 或 `BLOCKED`。
