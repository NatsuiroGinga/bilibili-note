# 任务十四 G5 工程实现简报

## 目标

把已经通过门禁的 G5 独立协调器与一次可微跟随响应接入现有 G2–G4 训练框架，并提供停止反应梯度消融。不得改变 G2、G3、G4 的现有行为。

## 必读

- `.Codex/docs/2026-07-22-任务十四G5主从响应数学门禁.md`
- `.Codex/docs/2026-07-22-任务十四G0-G5同预算训练设计.md`
- `thesis/experiments/llm_probe/src/flow_probe/game_coordination.py`
- `thesis/experiments/llm_probe/src/flow_probe/game_train.py`

## 文件范围

- 修改 `thesis/experiments/llm_probe/src/flow_probe/game_coordination.py`
- 修改 `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
- 修改 `thesis/experiments/llm_probe/tests/test_game_coordination.py`
- 修改 `thesis/experiments/llm_probe/tests/test_game_train.py`
- 报告 `.Codex/docs/sdd/task-14-g5-report.md`

如职责边界确实需要，可新建一个仅承载 G5 可微响应的源码文件，但不得重构无关代码。

## 强制契约

- 独立协调器参数严格采用门禁报告定义的 `A[2,7]` 与 `b[2]`。
- G4 安全权重是协调器零点；协调器只产生安全可行域内的连续修正。
- 跟随参数为 LoRA 与五锚点状态头，执行一次与真实优化器语义一致的可微 AdamW 响应。
- 外层批次必须独立于内层训练批次，效用由验证生成损失、未观测状态误差和物理残差构成。
- 反应梯度必须可观测、非零并逐步记录；停止反应梯度必须严格退化为 G4。
- 有效模型更新仍为 2 步冒烟或 202 步正式预算，协调器更新不计入模型更新次数。
- 对 G5 新增 SwanLab、JSONL、汇总和制品字段；不得破坏现有运行目录和指标键。

## 实现门禁

- 禁止使用测试驱动开发技能；完成实现后再编写或更新最小测试。
- 本机禁止运行 pytest；只执行一次 Black、一次 Ruff、语法检查和差异检查。
- 必须用固定小张量验证安全投影雅可比非零、函数式 AdamW 与真实一步更新逐张量一致、停止响应退化到 G4。
- 不连接服务器、不启动训练、不执行 Git 提交。

## 输出

完整报告写入 `.Codex/docs/sdd/task-14-g5-report.md`，记录修改文件、数学接口、验证命令、未在本机运行 pytest 的事实、服务器最小测试节点和两步冒烟命令。最终状态只能是完成、带关注项完成、需要上下文或阻塞。

