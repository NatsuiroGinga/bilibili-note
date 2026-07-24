# 任务 1：ns-3 队列真值验证器

## 目标

为 `flow_probe_ns3_queue_v2` CSV 实现可复现验证器，阻止字段、时序、标签或队列守恒错误进入 PINN 训练。

## 修改范围

- 新增 `thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py`。
- 新增 `thesis/experiments/llm_probe/tests/test_ns3_truth.py`。
- 在 `thesis/experiments/llm_probe/pyproject.toml` 增加命令入口 `flow-probe-validate-ns3-truth`。
- 不修改 `ns3/queue_truth_scenario.cc`、运行脚本、实验结果或论文文档。

## 固定数据契约

- 模式版本必须为 `flow_probe_ns3_queue_v3`，每行恰有 42 个命名字段；验证器按字段名解析，不依赖固定列号。
- 场景集合固定为：`benign-low`、`benign-high`、`benign-capacity-shift`、`benign-random-loss`、`dos-udp-medium`、`dos-udp-high`、`dos-udp-capacity-shift`。
- 每个 `group_id` 对应一个完整仿真，默认必须有 120 个窗口，`window_index` 连续为 0 至 119，窗口长度为 0.1 秒，前后窗口连续。
- 同一组的 `scenario_id`、`topology_id`、`queue_model`、`seed` 和 `run` 必须恒定；不同组不得共享 `group_id`。
- 所有计数、字节、队列、容量和服务预算字段必须非负，所有数值必须有限。
- 必须逐行复算并同时满足：`offered_bytes = enqueued_bytes + dropped_before_enqueue_bytes`；`queue_end_bytes - queue_start_bytes - offered_bytes + departed_bytes + dropped_before_enqueue_bytes = 0`；保存的 `queue_balance_residual_bytes = 0`。
- 相邻窗口必须满足前一行 `queue_end_bytes` 等于后一行 `queue_start_bytes`。
- `device_tx_drop_bytes` 和 `device_tx_drop_packets` 必须全为零，否则说明显式队列规则之外仍有隐藏缓冲丢弃。
- 所有良性场景的 `is_attack` 和 `attack_exposure_fraction` 必须全为 0，`traffic_phase` 为 `benign`，三级标签均为良性。
- 三个拒绝服务场景的窗口 0 至 49 为良性；窗口 50 的 `attack_exposure_fraction` 必须严格位于 0 与 1 之间，`traffic_phase` 为 `transition`，且标签为 `malicious/dos/udp`；窗口 51 至 119 的暴露比例为 1，阶段为 `attack`，标签保持 `malicious/dos/udp`。过渡窗口不得作为纯攻击状态训练样本。
- `jitter_stream_base` 和 `jitter_max_ms` 在同一组内必须恒定；当前固定值分别为 100 和 40，表示每个发送端使用独立且可追溯的启动相位随机流。
- `error_stream` 固定为 500；只有 `benign-random-loss` 的 `downstream_error_rate` 为 0.01，其他场景为 0。
- 容量突变场景的窗口 59 必须为起始容量 5,000,000、结束容量 2,500,000、服务预算 62,500 字节；窗口 60 起起止容量均为 2,500,000、服务预算 31,250 字节。非突变场景容量始终为 5,000,000、服务预算 62,500 字节。
- `benign-low`、`benign-high` 和 `benign-random-loss` 不得出现队列规则丢弃；`benign-capacity-shift` 必须在容量下降后出现队列规则丢弃；三个拒绝服务场景必须在攻击开始后出现队列规则丢弃。
- `benign-random-loss` 每组必须出现下游误码丢弃；其他场景不得出现下游误码丢弃。

## 接口与输出

- 提供可导入的单文件验证函数和命令行入口。
- 命令接受一个或多个 CSV 路径，并支持 `--output` 写出 UTF-8 JSON 摘要。
- 摘要至少包含文件数、组数、总窗口数、过渡窗口数、逐场景窗口数、队列丢弃字节、下游误码字节、非零残差数和验证状态。
- 任何违反契约的情况必须返回非零退出码，错误信息需指出文件、组和具体规则。

## 验证纪律

- 使用标准库 `csv` 和 `json`，不新增大型依赖。
- 测试至少覆盖一份最小合法数据、守恒式破坏、标签时序错误、容量预算错误和隐藏设备丢弃。
- 本机只运行 Black 和 Ruff，不运行 pytest；控制器会同步到服务器后使用 `uv run --no-sync pytest`。
- 所有说明与注释使用简体中文；变量和技术标识符可保留英文。
