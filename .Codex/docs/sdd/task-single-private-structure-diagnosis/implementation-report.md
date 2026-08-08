# 单私有 LoRA 结构与优化归因实现报告

## 实现结果

- 在 `asymmetric_physics_train.py` 中新增四种预注册模式：`joint_constant`、`generation_only`、`physics_only`、`joint_warmup_cosine`。
- 保留 `--diagnostic-mode` 默认值 `joint_constant`，旧 D0 包装器无需修改。
- D1 仅执行子类生成反向传播；D2 仅执行双锚点状态与有限队列物理反向传播；D3 执行三种损失。
- D3 学习率固定为第 1 步 `2e-5`、第 20 步 `2e-4`、第 21 至 202 步无重启余弦衰减、第 202 步 `2e-5`。两步冒烟直接使用正式轨迹前两步。
- 三种诊断均保存相同规则生成的生成与物理样本顺序，并保留同一个优化器参数组。
- 逐步指标新增损失开关、实际处理样本数、实际吞吐量；训练摘要新增诊断契约、实际样本累计量和状态头实际获得非零梯度的步数。
- 新增种子 42 固定训练配置、D1/D2/D3 三份 `eval300` 配置，以及训练、评估、统计三个包装器。
- 统计入口固定复用 S3 训练与评估制品；历史输出键名 `s4` 仅表示当前候选，包装器在日志中明确记录该语义。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/asymmetric_physics_train.py`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_seed42.yaml`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_d1_seed42_eval300.yaml`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_d2_seed42_eval300.yaml`
- `thesis/experiments/llm_probe/configs/asymmetric_diagnostic_d3_seed42_eval300.yaml`
- `thesis/experiments/llm_probe/scripts/run_asymmetric_diagnostic.sh`
- `thesis/experiments/llm_probe/scripts/run_asymmetric_diagnostic_eval.sh`
- `thesis/experiments/llm_probe/scripts/run_asymmetric_diagnostic_analysis.sh`
- `thesis/experiments/llm_probe/tests/test_asymmetric_physics_train.py`

## 检查结果

- Black：项目现有 `uv` 环境格式化两个 Python 文件，通过。
- Python 语法：两个 Python 文件使用写入 `/tmp` 的 `py_compile` 检查，通过。
- Shell 语法：三个新增包装器执行一次 `bash -n`，通过。
- YAML：四份新增配置使用项目 Python 环境解析，通过。
- 未运行本地 pytest，未连接 GPU 服务器，符合任务边界。

## 遗留验证与风险

- 仍需在 GPU 服务器执行新增单测试文件和 D1/D2/D3 各两步真实模型冒烟。
- D1 的状态头按合同保留在同一优化器参数组中，但不会获得梯度；其状态与物理验证指标只用于确认损失关闭效果，不能作为方法性能结论。
- 正式统计程序沿用历史 `s4` 字段名，报告解释时必须把它表述为候选而非 S4 方法。
