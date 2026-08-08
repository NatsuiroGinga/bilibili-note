# Task 14 G5 最小测试失败调试报告

日期：2026-07-22

## 结论

服务器最小测试共 6 个节点，其中 4 个通过、2 个失败。两个失败均已按最小范围修复：测试只在断言边界读取可微范数的脱离标量；函数式 AdamW 按 PyTorch 的算子顺序计算一阶矩和二阶矩，同时使用非原位算子保持虚拟响应无副作用。严格 `torch.equal` 门槛未放宽，G4R 路径未修改。

## 根因证据

### 可微裁剪范数断言

- 失败节点：`tests/test_game_train.py::test_differentiable_global_clip_preserves_weight_gradient`
- 服务器证据：`total_norm` 是 `requires_grad=True` 的张量，直接传入 `pytest.approx` 后触发 NumPy 转换异常。
- `total_norm` 保留计算图是 G5 反应梯度契约的一部分，不应在生产实现中脱离计算图。
- 根因位于测试观察边界，而非 `differentiable_clip_grad_norm` 的训练实现。

### AdamW 动量状态逐位差异

- 失败节点：`tests/test_game_train.py::test_two_step_functional_commit_matches_real_adamw_stop_baseline`
- 服务器证据：最终参数已满足 `torch.equal`，但显示相同的 `exp_avg` 未满足逐位相等。
- 修复前函数式实现使用代数展开：`beta1 * exp_avg + (1 - beta1) * gradient` 和 `beta2 * exp_avg_sq + (1 - beta2) * gradient.square()`。
- 主代理核验的服务端 PyTorch `2.13.0+cu130` 已安装源码在 `torch/optim/adam.py:456` 使用 `exp_avg.lerp_`，在 `torch/optim/adam.py:471-475` 使用 `exp_avg_sq.mul_().addcmul_()`；[PyTorch 上游 Adam 实现](https://github.com/pytorch/pytorch/blob/main/torch/optim/adam.py)采用相同顺序。代数等价表达式采用不同算子与舍入路径，足以造成第二步动量状态的末位差异。

## 单一修复假设

两个失败都是边界语义未与参考实现一致，而不是 G5 数学契约失效：断言边界错误地请求 NumPy 转换，函数式优化器边界采用了与真实 AdamW 不同的浮点算子序列。仅将这两个边界对齐后，两个精确节点应通过，且可微反应链、无副作用虚拟更新和严格逐位验收均保持不变。

## 修改内容

- `thesis/experiments/llm_probe/tests/test_game_train.py`
  - 将范数断言改为 `total_norm.detach().item()`，只在测试观察处读取标量。
  - 保留对裁剪后梯度关于协调权重导数的检查。
  - 未修改 AdamW 状态的 `torch.equal` 断言。
- `thesis/experiments/llm_probe/src/flow_probe/game_train.py`
  - 一阶矩改为非原位 `exp_avg.lerp(gradient, 1.0 - beta1)`。
  - 二阶矩改为非原位 `exp_avg_sq.mul(beta2).addcmul(...)`，保持 PyTorch 的 `mul` 后 `addcmul` 顺序。
  - 未引入生产路径 `detach`，`gradient -> moment -> next_parameter` 的可微链仍然存在。
  - 未修改 G4R、停止反应分支、参数提交逻辑或优化器状态相等门槛。

## 本地验证

- Black：通过，2 个 Python 文件无需重排。
- Python 语法编译：通过。
- `git diff --check`：通过。
- 按任务约束未运行 Ruff、本机 pytest、服务器命令或 Git 提交。

## 服务端精确重跑命令

```bash
source ~/.bashrc >/dev/null 2>&1
cd /root/autodl-tmp/thesis/experiments/llm_probe
uv run --no-sync pytest \
  tests/test_game_train.py::test_differentiable_global_clip_preserves_weight_gradient \
  tests/test_game_train.py::test_two_step_functional_commit_matches_real_adamw_stop_baseline
```

## 遗留门禁

由于本任务明确禁止连接服务器，两个精确节点的运行结果仍需由主代理在当前 G4R 运行不受影响的前提下复核。
