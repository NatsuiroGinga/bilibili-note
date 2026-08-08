# ns-3 v4 队列真值契约实现报告

## 结论

任务 1 已完成。生成器固定输出 `flow_probe_ns3_queue_v4` 的 46 个字段，验证器执行 L3 字节与包级守恒复算、来源配置核验和场景规则检查。服务器目标测试、完整测试、ns-3 编译以及 `dos-udp-high`、`benign-random-loss` 两组真实冒烟均通过。

## 修改文件

- `thesis/experiments/llm_probe/ns3/queue_truth_scenario.cc`
- `thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py`
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py`
- `.Codex/docs/sdd/task-2-ns3-v4-contract-report.md`

未修改任务范围外的生产代码、配置、Git 索引或提交历史。未执行 `git add`、`commit`、`reset`、`checkout`、`stash` 或 `push`。

## 实现内容

### 生成器

- 模式版本更新为 `flow_probe_ns3_queue_v4`，表头和每行固定为 46 列。
- 队列规则字节统一标记为 L3 字节，设备与误码丢失标记为 PPP 帧字节，接收端标记为应用负载字节。
- 同时维护当前队列 L3 字节数和包数；入队同时增加，出队同时检查并减少。
- 每窗输出队列字节与包的起止状态、qdisc 接收量、接纳量、出队量、两类丢弃量和两种保存残差。
- L3 残差只使用 L3 字节，包残差只使用包数；设备丢弃、下游误码和应用负载不进入队列残差。
- 七个 `TraceConnectWithoutContext` 返回值均检查，任一连接失败立即终止。
- 仿真开始前回读并断言根队列规则为 `ns3::FifoQueueDisc`、上限为 `50p`、设备队列为 `1p`、初始链路速率为 `5000000 bit/s`。
- `DropBeforeEnqueue` 仅接受 `FifoQueueDisc::LIMIT_EXCEEDED_DROP`，其他原因立即终止。
- 攻击与良性流量均持续到 12 秒测量结束，保留攻击尾部修复。

### 验证器

- 验证入口保持 `validate_ns3_truth_paths(input_paths, expected_windows=120)`。
- 摘要输出 `qdisc_drop_l3_bytes`、`downstream_error_loss_ppp_frame_bytes`、`nonzero_l3_residual_count`、`nonzero_packet_residual_count`。
- 逐行复算 qdisc 接收分解、L3 队列守恒和包级队列守恒；复算残差和两个保存残差都必须为零。
- 固定拓扑、队列模型、`50p` 上限和 `group_id` 精确组成。
- 固定 120 个窗口、索引 `0..119` 和第 `i` 窗绝对边界 `[0.1i, 0.1(i+1)]`。
- 同时检查 L3 字节与包队列状态跨窗连续。
- 所有攻击暴露窗口都要求 `qdisc_received_l3_bytes` 与 `qdisc_received_packets` 同时非零。
- 必需队列丢弃和随机误码均要求对应字节数与包数同时非零；非随机场景禁止出现误码。

## 测试驱动记录

服务器项目根目录：`/root/autodl-tmp/thesis/experiments/llm_probe`

日志根目录：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/validator-tests-20260720`

| 轮次         | 红测命令与结果                                                                                                                                                              | 红测日志                               | 绿测命令与结果                               | 绿测日志                                 |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | -------------------------------------------- | ---------------------------------------- |
| v4 字段契约  | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_accepts_minimal_complete_group`，7 个场景因旧验证器要求 v3/42 字段而失败                    | `red-v4-contract.log`                  | 同一命令，7 项通过                           | `green-v4-contract.log`                  |
| 固定拓扑     | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_wrong_topology`，因未抛异常而失败                                                   | `red-wrong-topology.log`               | 错误拓扑测试与正向契约组合运行，8 项通过     | `green-wrong-topology.log`               |
| 固定队列模型 | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_wrong_queue_model`，因未抛异常而失败                                                | `red-wrong-queue-model.log`            | 错误队列模型与错误拓扑组合运行，2 项通过     | `green-wrong-queue-model.log`            |
| 精确组标识   | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_forged_group_id`，因未抛异常而失败                                                  | `red-forged-group-id.log`              | 伪造组标识与正向契约组合运行，8 项通过       | `green-forged-group-id.log`              |
| 固定队列上限 | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_wrong_queue_limit`，全组 49p 和单窗漂移两项均失败                                   | `red-wrong-queue-limit.log`            | 两个负向用例与正向契约组合运行，9 项通过     | `green-wrong-queue-limit.log`            |
| 绝对时间轴   | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_shifted_absolute_timeline`，整体平移 0.1 秒被错误接受                               | `red-shifted-timeline.log`             | 平移反例与正向契约组合运行，8 项通过         | `green-shifted-timeline.log`             |
| 攻击尾部入口 | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_attack_tail_without_qdisc_ingress`，接收端仍有活动但 qdisc 入口为零的反例被错误接受 | `red-attack-tail-qdisc-ingress.log`    | 两个攻击尾部反例与正向契约组合运行，9 项通过 | `green-attack-tail-qdisc-ingress.log`    |
| 丢弃双计量   | 运行队列丢弃和误码丢弃两个负向测试，只有字节非零、包数为零的两项均被错误接受                                                                                                | `red-loss-byte-packet-consistency.log` | 两个负向用例与正向契约组合运行，9 项通过     | `green-loss-byte-packet-consistency.log` |
| 包队列连续性 | `uv run --no-sync pytest tests/test_ns3_truth.py::test_validate_ns3_truth_paths_rejects_discontinuous_queue_state`，L3 字节反例通过拒绝测试，包状态反例因未抛异常而失败     | `red-packet-queue-continuity.log`      | 两个连续性用例与正向契约组合运行，9 项通过   | `green-packet-queue-continuity.log`      |

其余已存在规则的明确覆盖作为有界批次加入，包括字段缺失、119 窗、索引乱序、局部时间断裂、缺少必需丢弃、非随机场景误码和保存包残差非零。

最终目标模块命令：

```bash
uv run --no-sync pytest tests/test_ns3_truth.py
```

结果：38 项通过。最终日志：`runs/ns3-data/validator-tests-20260720/green-validator-module-final.log`。

最终完整测试命令：

```bash
uv run --no-sync pytest
```

结果：179 项通过。最终日志：`runs/ns3-data/validator-tests-20260720/full-pytest-final.log`。

## 生成器红测与编译

现有 scratch v3 生成器真实生成 `dos-udp-high` 后交给 v4 验证器，因 42 字段和旧字段名被拒绝。红测目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/generator-red-20260720`

关键日志：`red-generator-v4-contract.log`。首次准备远端项目副本时发现其 `ns3/` 目录尚不存在，因此预复制命令报告一次 `cannot stat`；红测随后使用服务器既有 ns-3 scratch v3 源码成功构建、运行并产生 42 字段失败证据。正式实现已补齐远端项目副本并覆盖 scratch。

v4 编译命令：

```bash
export PATH=/root/autodl-tmp/thesis/ns3/.tools/ns3-cmake-3.25.2/bin:$PATH
env USER=ns3builder ./ns3 build scratch/flow-probe-queue-truth
```

结果：编译与链接成功。日志：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/v4-build-20260720/build.log`

## 真实冒烟

服务端冒烟目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/v4-smoke-20260720-task1`

| 指标                        | `dos-udp-high` | `benign-random-loss` |
| --------------------------- | -------------: | -------------------: |
| 字段数                      |             46 |                   46 |
| 数据窗口                    |            120 |                  120 |
| 非零 L3 残差窗口            |              0 |                    0 |
| 非零包残差窗口              |              0 |                    0 |
| qdisc 丢弃 L3 字节          |     36,138,304 |                    0 |
| 下游误码 PPP 帧字节         |              0 |               46,376 |
| 下游误码包数                |              0 |                   44 |
| 设备发送丢弃字节/包         |            0/0 |                  0/0 |
| 最后窗口索引                |            119 |                  119 |
| 最后窗口 qdisc 接收 L3 字节 |        581,756 |               38,924 |
| 最后窗口 qdisc 接收包数     |            553 |                   37 |

关键文件：

- `dos-udp-high-seed42.csv`
- `dos-udp-high.log`
- `dos-udp-high-validation.log`
- `dos-udp-high-validation.json`
- `benign-random-loss-seed42.csv`
- `benign-random-loss.log`
- `benign-random-loss-validation.log`
- `benign-random-loss-validation.json`
- `smoke-audit.log`

验证结果同时证明：攻击最后完整窗口仍有 qdisc 接收活动；随机误码只出现在 `benign-random-loss`；两个场景的设备队列丢弃均为零。

## 格式与静态检查

- Python：本机执行 `uv run --no-sync black src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`，两个文件已格式化。
- Python：本机执行 `uv run --no-sync ruff check src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`，全部通过。
- C++：本机执行 `clang-format -i ns3/queue_truth_scenario.cc`，随后执行 `clang-format --dry-run --Werror`，通过。
- Markdown：报告完成后使用仓库内 Prettier 格式化。
- Git：报告完成并格式化后执行 `git diff --check`。

## 边界与遗留风险

- `configured_capacity_integral_link_bytes` 是配置容量的时间积分，只作为外生控制量或归一化尺度，不代表实际服务字节，也不进入队列守恒残差。
- `queue_balance_residual_l3_bytes` 只由 L3 队列状态和 qdisc L3 事件计算；PPP 帧字节和应用负载字节禁止与 L3 字节互减。
- 保存残差是数据生成审计量，当前不得作为训练目标或物理创新证据；后续训练只能对模型预测的可微状态施加约束。
- 当前任务只完成两个指定场景的真实冒烟，不代表七场景、多随机种子正式数据矩阵已经生成。
- 服务器数据盘使用率为 54%，可用空间约 24 GiB，未达到告警阈值。

## 独立审查修复轮

### 修复范围

本轮只修改以下文件，未修改 C++、任务 2 文件或 Git 状态：

- `thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py`
- `thesis/experiments/llm_probe/tests/test_ns3_truth.py`
- 本报告追加本节

最终审查提出的 3 个重要问题均已按批准条件最小修复：

1. `_validate_header` 在字段集合检查通过后，继续要求 `tuple(fieldnames) == CSV_FIELDS`，拒绝字段相同但顺序不同的 CSV。
2. `_validate_drop_rules` 对每个窗口分别检查队列规则丢弃和下游误码丢失的字节/包零值一致性，不再允许两个相邻窗口拼接出整组非零假象。
3. `_validate_timeline` 要求首窗 `queue_start_l3_bytes` 与 `queue_start_packets` 均为零，并拒绝任一窗口的 `queue_start_packets` 或 `queue_end_packets` 超过该窗 `queue_limit_packets`。未从 `50p` 推导任何字节上限。

### 测试驱动证据

服务端日志根目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/validator-fix-tests-20260720`

| 行为             | 红测结果                                                             | 红测日志                                | 绿测结果 | 绿测日志                                  |
| ---------------- | -------------------------------------------------------------------- | --------------------------------------- | -------- | ----------------------------------------- |
| 固定字段顺序     | 1 项失败，交换前两列表头及对应值后旧验证器未抛异常                   | `red-reordered-fields.log`              | 1 项通过 | `green-reordered-fields.log`              |
| 逐窗丢弃计量     | 2 项失败，队列丢弃与误码丢失的跨窗拼接反例均被旧验证器接受           | `red-cross-window-loss-measurement.log` | 2 项通过 | `green-cross-window-loss-measurement.log` |
| 初始队列与包上限 | 4 项失败，首窗字节/包非零和晚期起止包状态超过 `50p` 均被旧验证器接受 | `red-queue-state-bounds.log`            | 4 项通过 | `green-queue-state-bounds.log`            |

目标模块命令：

```bash
uv run --no-sync pytest tests/test_ns3_truth.py
```

结果：45 项通过。日志：`green-validator-module-final.log`。

完整回归命令：

```bash
uv run --no-sync pytest
```

结果：200 项通过，其中包括并行完成的 14 项字段角色测试。日志：`full-pytest-final.log`。

### 构建与修复后冒烟

ns-3 重新构建命令：

```bash
env USER=ns3builder ./ns3 build scratch/flow-probe-queue-truth
```

结果：构建成功。日志：`validator-fix-tests-20260720/ns3-build.log`。

最终成功冒烟目录：

`/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/v4-fix-smoke-20260720-task1-review2`

| 指标                | `dos-udp-high` | `benign-random-loss` |
| ------------------- | -------------: | -------------------: |
| 字段数              |             46 |                   46 |
| 数据窗口            |            120 |                  120 |
| 非零 L3 残差窗口    |              0 |                    0 |
| 非零包残差窗口      |              0 |                    0 |
| qdisc 丢弃 L3 字节  |     36,138,304 |                    0 |
| 下游误码 PPP 帧字节 |              0 |               46,376 |

验证入口使用：

```bash
uv run --no-sync python -m flow_probe.ns3_truth <CSV> --output <JSON>
```

两个验证摘要均为 `validation_status=passed`；`smoke-audit.log` 同时记录两份 CSV 均为 121 行含表头、46 列。首个唯一目录 `v4-fix-smoke-20260720-task1-review1` 的两组生成均成功，但环境未安装 `flow-probe-validate-ns3-truth` 控制台脚本，验证启动失败；该失败日志已保留，未覆盖，随后在新的 `review2` 目录改用同一验证器的 Python 模块入口重新生成并成功验证。

### 最终格式与静态检查

- `.venv/bin/black src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`：通过，两个文件无需再次修改。
- `.venv/bin/ruff check --no-cache src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`：通过。
- `.Codex/tools/prettier/node_modules/.bin/prettier --write .Codex/docs/sdd/task-2-ns3-v4-contract-report.md`：通过。
- `git diff --check`：通过。

### 残余风险

- 自动化测试仍未直接执行 C++ 生成器以锁定生成器与验证器的共同契约；按审查边界，本轮不新增集成框架，由任务 3 的正式运行器覆盖。
- `review1` 暴露服务端在 `--no-sync` 模式下没有已安装的控制台脚本；Python 模块入口可用且已完成真实冒烟，不影响验证器逻辑，但任务 3 应通过正式入口安装或固定模块调用方式。
