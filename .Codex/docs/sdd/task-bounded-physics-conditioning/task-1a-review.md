# 任务 1A 独立复核：有界物理条件数学模块

## 结论

- **规格符合性：规格通过。** 实现覆盖任务 1A 的全部固定接口与数学边界，未发现严重、重要或次要偏差。
- **代码质量：质量通过。** 输入校验、数值保护、接口复用和职责边界清晰，未发现会阻塞后续运行时接入的问题。

## 问题分级

- 严重问题：无。
- 重要问题：无。
- 次要问题：无。

## 规格符合性复核

1. **固定常数严格锁定。** `ConditioningSpec` 使用冻结数据类，并在 `bounded_physics_conditioning.py:23` 至 `bounded_physics_conditioning.py:84` 对全部整数、浮点数、目标层元组、可除性和层索引关系进行校验；任一字段变化均抛出 `ValueError`。`resolve_conditioning_layers` 在 `bounded_physics_conditioning.py:87` 至 `bounded_physics_conditioning.py:92` 仅接受 28 层并返回固定层位。
2. **九词元编码符合要求。** `PhysicalConditionEncoder` 在 `bounded_physics_conditioning.py:141` 至 `bounded_physics_conditioning.py:198` 将五个状态和四个相邻有符号差分拼成九个标量令牌，分别加入类型嵌入和位置嵌入，经共享的 `Linear-SiLU-Linear` 输出 `[B,9,256]`；形状、非负性和有限性均有显式校验。
3. **训练与候选掩码均完成因果移位。** `build_training_injection_mask` 在 `bounded_physics_conditioning.py:421` 至 `bounded_physics_conditioning.py:428` 将 `labels[:,1:] != -100` 映射到 `[:-1]`，末位保持为假。`build_candidate_injection_mask` 在 `bounded_physics_conditioning.py:462` 至 `bounded_physics_conditioning.py:514` 将真值区间设为 `completion_start-1` 到最后有效令牌的前一位置，并校验起点、前驱、空样本和区间空洞。
4. **零门严格恒等。** `alpha` 在 `bounded_physics_conditioning.py:214` 按固定值零初始化；`bounded_physics_conditioning.py:308` 至 `bounded_physics_conditioning.py:313` 中 `tanh(0)=0`，因此掩码内外残差均为零，返回隐藏状态与输入恒等。
5. **残差比例界成立。** `bounded_physics_conditioning.py:302` 至 `bounded_physics_conditioning.py:313` 严格实现 `0.1*tanh(alpha)*stopgrad(||h||)*z/(||z||+1e-6)`。逐令牌残差比例同时受 `|tanh(alpha)|<=1`、`||z||/(||z||+1e-6)<=1` 和诊断分母稳定项约束，因此不超过固定上限 0.1；`bounded_physics_conditioning.py:330` 至 `bounded_physics_conditioning.py:336` 返回实测最大比例并拒绝非有限结果。
6. **门前非有限值被拒绝。** `bounded_physics_conditioning.py:250` 至 `bounded_physics_conditioning.py:307` 在计算门值前依次检查隐藏状态、条件、注意力权重、注意力输出、`alpha` 及相关范数的有限性，零门不会掩盖非法注意力输出。
7. **注意力熵与诊断四元组完整。** `bounded_physics_conditioning.py:317` 至 `bounded_physics_conditioning.py:328` 只对注入位置聚合四头注意力熵，无注入位置时返回零。`ConditioningDiagnostics` 在 `bounded_physics_conditioning.py:95` 至 `bounded_physics_conditioning.py:138` 将门值、注意力熵和四层目标挂钩次数锁定为长度 4 的元组，并记录最大残差比例、源挂钩次数、预填充次数和缓存解码次数。
8. **状态头复用而未复制。** `build_condition_state` 在 `bounded_physics_conditioning.py:380` 至 `bounded_physics_conditioning.py:418` 只接收并调用外部 `state_head`，保持对锚点隐藏状态的梯度路径，并校验输出 `[B,5]`、非负和有限。既有 `ContinuousQueueStateHead` 仍唯一实现在 `physics_train.py:346` 至 `physics_train.py:356`；本模块未复制该类或其物理公式。
9. **未越权实现运行时。** 本模块仅包含规格、编码器、交叉注意力、掩码和状态构造函数。针对运行时挂钩、训练器、评估器、生成入口、子进程和命令行标识的定向搜索无匹配；任务范围内也未创建有界条件测试文件。

## 代码质量复核

- 公开接口通过 `__all__` 明确限定，辅助函数分别负责锚点和候选起点规范化，职责单一。
- 半精度输入下，注意力 Softmax 与范数计算提升到 `float32`，并在投影、范数、门值和最终输出处设置有限性门禁。
- 掩码、设备、数据类型、批次和序列边界均在进入核心计算前校验，错误均以具体 `ValueError` 暴露。
- 状态头通过依赖注入复用，模块没有引入 `physics_train.py` 的运行时依赖或复制实现。
- 未发现训练器、评估器、Qwen 挂钩、生成会话或 Shell 相关实现，职责边界符合任务 1A 简报。

## 验证情况

- 已读取任务简报、实现报告、完整新增模块及既有 `ContinuousQueueStateHead` 接口。
- 已执行 `uv run --no-sync ruff check src/flow_probe/bounded_physics_conditioning.py`；通过，输出 `All checks passed!`。首次因默认 `uv` 缓存目录受沙箱限制失败，改用 `/tmp/codex-uv-cache` 后通过。
- 已执行 `git diff --no-index --check /dev/null thesis/experiments/llm_probe/src/flow_probe/bounded_physics_conditioning.py`；无空白错误输出。退出码 1 仅表示新增文件与空文件存在内容差异。
- 按任务纪律未运行 `pytest`，未修改任何源码、测试、配置或运行时文件。

## 遗留边界

- 本次结论仅验收任务 1A 的纯数学模块；Qwen 挂钩生命周期、训练与候选运行时路由、诊断累计和服务器行为测试属于后续任务，不作为本次缺陷。
- 工作区存在大量既有未提交改动，Git 无法独立归因其他历史文件；本次未发现与任务 1A 同名的额外测试或运行时制品。
