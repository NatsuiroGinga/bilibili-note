# 任务 1：ns-3 队列真值验证器实施报告

## 结论

已按测试先行顺序新增 v3、42 字段 ns-3 队列真值验证器、测试和命令入口。验证器按完整 `group_id` 检查字段、数值、时序、标签、攻击暴露、抖动配置、误码配置、容量、队列守恒和丢弃来源，并可输出 UTF-8 JSON 摘要。按照本机验证纪律，未运行 `pytest`。

## 需求变更

实施期间，控制器根据运行审查补充了正式数据契约：

- CSV 先从 36 字段升级为 40 字段，随后最终升级为 42 字段，模式版本确定为 `flow_probe_ns3_queue_v3`。
- 新增 `attack_exposure_fraction`、`traffic_phase`、`jitter_stream_base` 和 `jitter_max_ms`。
- 最终再新增 `error_stream` 和 `downstream_error_rate`；前者固定为 500，后者仅在 `benign-random-loss` 中为 0.01，其余场景为 0。
- 良性窗口必须为 `attack_exposure_fraction=0`、`traffic_phase=benign`。
- 拒绝服务场景窗口 0 至 49 必须保持良性；窗口 50 必须为部分暴露、`traffic_phase=transition` 且 `is_attack=1`；窗口 51 至 119 必须为全量暴露、`traffic_phase=attack`。
- 摘要新增 `transition_window_count`。
- 验证器必须按完整仿真组检查，错误信息不得暗示逐窗口随机切分。

表头按 42 个字段名的集合校验，不依赖字段位置。

## 修改文件

- `thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py`
  - 新增 `NS3TruthValidationError`。
  - 新增批量函数 `validate_ns3_truth_paths` 和单文件函数 `validate_ns3_truth_file`。
  - 校验精确 42 字段、`flow_probe_ns3_queue_v3` 模式和固定场景集合。
  - 使用 `Decimal` 检查所有数值有限、计数字段为整数且数值非负。
  - 按组内原始出现顺序校验 120 个窗口、索引、0.1 秒窗口、时间连续和队列连续。
  - 校验组内场景、拓扑、队列模型、随机种子、运行编号和抖动配置恒定。
  - 校验 `error_stream=500` 以及各场景对应的 `downstream_error_rate`。
  - 复算流量分解式和队列守恒式，拒绝保存残差或设备发送丢弃非零。
  - 校验良性、拒绝服务、过渡暴露、容量突变、队列规则丢弃和下游误码丢弃规则。
  - 输出文件数、组数、总窗口数、逐场景窗口数、队列丢弃字节、下游误码字节、非零残差数、过渡窗数和验证状态。
  - 命令行接受一个或多个位置参数 CSV，支持 `--output`，契约错误返回退出码 1。
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py`
  - 先于实现创建测试，再依次补充 40 字段和最终 v3/42 字段需求变更测试。
  - 定义 10 个测试函数，其中七场景参数化测试预期展开为 7 项，总计预期 16 项测试。
- `thesis/experiments/llm_probe/pyproject.toml`
  - 新增命令入口 `flow-probe-validate-ns3-truth = "flow_probe.ns3_truth:main"`。
- `.Codex/docs/sdd/task-1-ns3-validator-report.md`
  - 本实施报告。

未修改 `thesis/experiments/llm_probe/ns3/queue_truth_scenario.cc`、运行脚本、实验结果或论文文档。

## 测试用例

1. 七个固定场景各自包含一个完整 120 窗口组时通过，并核对摘要中的场景窗口数、队列丢弃、下游误码和过渡窗数。
2. `offered_bytes` 不等于入队字节与入队前丢弃字节之和时拒绝。
3. 流量分解正确但队列守恒残差非零时拒绝。
4. 拒绝服务标签提前到窗口 49 时拒绝。
5. 窗口 50 的过渡暴露比例取边界值 1 时拒绝。
6. 同组 `jitter_max_ms` 发生变化时拒绝。
7. `benign-random-loss` 中 `downstream_error_rate` 不为 0.01 时拒绝。
8. 容量突变后服务预算仍为 62,500 字节时拒绝。
9. `device_tx_drop_bytes` 或 `device_tx_drop_packets` 非零时拒绝。
10. 命令入口对合法输入写出 UTF-8 JSON，对非法输入返回 1 并向标准错误输出文件名。

## 运行命令

```bash
uvx --from black==25.1.0 black src/flow_probe/ns3_truth.py tests/test_ns3_truth.py
uvx --from ruff==0.12.12 ruff check src/flow_probe/ns3_truth.py tests/test_ns3_truth.py
prettier --check .Codex/docs/sdd/task-1-ns3-validator-report.md
git diff --check
```

未运行以下命令，等待控制器同步到 GPU 服务器后执行：

```bash
uv run --no-sync pytest tests/test_ns3_truth.py
uv run --no-sync pytest
```

## 格式检查结果

- Black：通过；最终一轮显示两个 Python 文件均无需改写。
- Ruff：通过；输出为 `All checks passed!`。
- Prettier：通过；实施报告符合格式规范。
- `git diff --check`：通过；无错误输出。
- `pytest`：本机未运行，不能宣称运行时测试已通过。

## 顾虑

1. 已只读核对共享工作区中的 `ns3/queue_truth_scenario.cc`：实际表头为 v3、42 字段，字段名集合与验证器一致；本任务未重新执行 ns-3 冒烟运行。
2. `pyproject.toml` 在本任务开始前已处于未跟踪状态。本任务只追加了一个命令入口，没有覆盖其他已有内容。
3. 本机未运行 `pytest`。服务器需先运行目标测试，再运行完整测试套件，才能确认实际收集数量、命令入口和仓库级回归状态。
