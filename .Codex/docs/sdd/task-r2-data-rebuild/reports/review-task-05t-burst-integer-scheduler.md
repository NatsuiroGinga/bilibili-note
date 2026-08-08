# 任务 05T：attempt5 突发整数调度独立复审

日期：2026-08-03  
结论：`通过`  
运行状态裁决：attempt5 可由 `finished/review_pending` 晋级为已通过代码独立复审的 ns-3 物理池输入。

## 复审范围与限制

- 复审生产文件：`thesis/experiments/llm_probe/ns3/r2_protocol_queue_scenario.cc`、`thesis/experiments/llm_probe/configs/r2_ns3_protocol_matrix_runtime_v0.json`。
- 复审运行证据：本机回收的 attempt5 启动制品、矩阵摘要、状态、运行绑定、源码锁、256 个配对回执、512 个单运行回执，以及首个突发配对的 TCP/UDP CSV。
- 未修改任何生产代码、配置、清单或运行制品；只新增本复审报告。
- 按任务边界未构建、未运行测试、未运行格式化、未执行静态检查、未执行 `git diff`，也未阻塞或重启其他实验。
- 运行时服务器双副本事实以 attempt5 回收的 `source-lock.json` 和 `run-binding.json` 为证；本次未重新查询服务器当前文件，因为运行后的服务器现状不能替代该次运行时绑定。

## 分级发现

### 严重

无。

### 重要

无。

### 建议

1. 当前冻结清单的 `0.2` 秒开启和 `0.1` 秒关闭均远大于 ns-3 时间分辨率，不影响 attempt5。若未来允许清单外的任意突发周期，建议在 `ValidateConfig()` 中分别断言开启、关闭时长量化后均至少为一个时间步；现实现只检查双精度值为正，并在调度函数中检查两者之和量化后为正。该建议不阻塞本次验收。

## 核对证据

### 1. 整数时间步与严格正等待

- `BurstPhaseTimeSteps()` 在源码第 628 至 636 行把开启时长、关闭时长、当前时刻和相位偏移统一转换到 ns-3 时间步后计算取模。
- `BurstActive()` 在第 639 至 645 行使用同一整数相位与整数开启时长判断活动状态。
- `DelayUntilBurstActive()` 在第 648 至 659 行复用同一相位函数，并在返回 `TimeStep` 前断言非活动分支等待时间严格大于零。
- `AttemptSend()` 在第 680 至 697 行仅在非活动分支调用上述严格正等待；旧的浮点 `fmod` 和浮点剩余延迟路径不再存在。

### 2. 0.2/0.1 秒周期保持不变

- 生产源码默认值仍为 `burstOnSeconds=0.2`、`burstOffSeconds=0.1`。
- 冻结清单全部 256 条 `bursty` 运行记录的周期组合唯一为 `[0.2, 0.1]`。
- 首个突发配对 TCP 与 UDP 的 `config.json` 均记录 `burst_on_seconds=0.2`、`burst_off_seconds=0.1`；没有加入毫秒容差、最小延迟钳制或周期改写。

### 3. 生产源码、运行参数与双副本绑定

- 本机生产源码重算 SHA-256 为 `b82efbbc5a90b535463282263f76b1c04f4b49da654af17d2d3c1301efb5c771`。
- 受控参数重算 SHA-256 为 `791122e6aad728c3a03feb96716fe7e68d319a477f5a19897911684f368c94e9`，其中 `expected_scenario_source_sha256` 精确等于上述源码摘要，`resume=false`。
- attempt5 启动 `state.json` 绑定同一参数摘要，受管进程与日志写入器退出码均为 0。
- `run-binding.json` 的 `scenario_source_sha256` 与 `compiled_source_sha256` 均为 `b82e...c771`。
- `source-lock.json` 同时登记项目副本 `ns3/r2_protocol_queue_scenario.cc` 与编译副本 `scratch/flow-probe-r2-protocol.cc`；两者大小均为 40,301 字节、SHA-256 均为 `b82e...c771`。

### 4. 512 条清单与实验因子未改变

- 冻结清单重算为 512 行、SHA-256 为 `d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111`，与任务04冻结报告、受控参数、矩阵摘要、全部回执完全一致。
- 清单仍为 256 个物理组，每组恰有一个 TCP 与一个 UDP；移除 `transport_family` 后组内两条记录逐字段相同，异常配对数为 0。
- 协议各 256 条，良性/DoS 各 256 条，常量/突发各 256 条；划分仍为 `train-fit=256`，其余四个划分各 64 条协议运行。
- 队列、负载、容量变化、接入时延、瓶颈时延、队列上限和下游丢失率的取值集合与任务04报告一致；拥塞控制身份唯一为 `ns3::TcpNewReno`，每条运行仍为 120 窗。
- 首个突发记录仍位于零基索引 64，即第 33 个配对，组标识仍为 `8c4900f37191dadd918827d0123deb1919828b17d14caca232a815dbe7f55867`。

### 5. 512/512 与 256/256 完成证据

- `matrix-summary.json`：`completed_run_count=512`、`failed_run_count=0`、`skipped_run_count=0`、`valid_pair_count=256`、`status=finished`。
- `matrix-state.json`：`failed_pair_count=0`，开始于 `2026-08-03T08:29:09.201297+00:00`，完成于 `2026-08-03T08:47:39.632404+00:00`。
- 独立聚合 512 个单运行回执：512 个 `status=pass`、512 个 `validation_status=pass`、512 个退出码为 0、512 个均为 120 窗、残差违反运行数为 0；TCP/UDP 各 256 个。
- 独立聚合 256 个配对回执：256 个均为 `pass`，窗口或拥塞窗口门禁失败数均为 0，物理组标识去重后恰为 256 个。
- `source-lock.json` 登记 512 个通过的计划运行、256 个配对回执，并统一绑定同一清单与场景源码摘要。

### 6. 首个突发配对直接证据

- TCP 与 UDP CSV 均为 121 行，即 1 行表头加 120 个窗口；配对回执记录两侧窗口数均为 120。
- 对两份 CSV 按表头独立聚合：网络层字节守恒残差非零窗口数均为 0，包守恒残差非零窗口数均为 0。
- TCP 的 120 个窗口全部满足 `truth_tcp_cwnd_applicable=1`、`truth_tcp_cwnd_observed=1`，拥塞窗口覆盖率为 `1.0`。
- TCP 的 120 个窗口全部记录 `truth_tcp_congestion_control=ns3::TcpNewReno`；UDP 的 TCP 状态保持不适用。
- 首配对 TCP/UDP 的配置、CSV 和回执重算摘要与配对回执及源码锁登记值逐项一致；四个标准输出/错误日志均为空，严格正等待断言没有触发。

### 7. 全矩阵拥塞窗口边界

- 256 个 TCP 回执的最小拥塞窗口覆盖率为 `0.9833333333333333`，高于运行器冻结门槛 `0.95`；224 个运行观测 120 窗，18 个观测 119 窗，14 个观测 118 窗。
- 32 个非首配对 TCP 运行并非 120/120 全覆盖，但均通过预注册的 `>=0.95` 门槛；这不影响报告中只针对首个突发配对作出的 `1.0`、`120/120` 主张。

## 制品摘要复核

- `matrix-summary.json`：`574118e3a3ddddc21f23fdcb9c770ab7f9b3f86dd73feb018bd067d181234819`
- `matrix-state.json`：`db80f0ca42840a8b5b9ec53294844ee552f5cee739d6df532716a5701155c50f`
- `run-binding.json`：`d89ee697ce213c0b20c78d636c0fb89f346e63dc263828ca02784e5e380ebab5`
- `source-lock.json`：`95708a0fffd702f65ec18acfe9ca1c806ba893b5d4f816643bdc59534ec8d38b`
- `ns3-trace-contract.json`：`b90e4b657b0b5e8cece9af577e05f24d84da58cc7af33a596f21aadcd5b481d9`
- trace 合同载荷摘要：`89390f51b077118b6c1246ece6b68496f4e720528eb69a23ebb7a280210907fe`

## 最终裁决

attempt5 的整数时间步修复符合 attempt3 的最小修复边界，运行时源码绑定、项目与 scratch 双副本、冻结清单及实验因子均一致。512/512 条运行、256/256 个严格配对和首个突发配对的窗口、NewReno、守恒与拥塞窗口证据均闭合。

本复审没有发现影响结果正确性或有效性的严重、重要问题。attempt5 可以通过代码独立复审；上述建议仅用于未来开放任意周期参数时的防御性加固，不要求重跑本矩阵。
