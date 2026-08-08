# 任务 05T：突发整数时间步修复与 attempt5 正式运行报告

日期：2026-08-03  
状态：`finished/review_pending`

## 结论

attempt3 的零延迟事件循环已通过单一最小代码变更修复。突发活动判断和下一开启延迟现在统一使用 ns-3 整数时间步；非活动分支对下一事件延迟执行严格正时间步运行时断言。冻结的 512 条清单、运行顺序、种子、标签、负载、协议和输出字段均未改变。

修复后的 attempt5 已完成 512/512 条协议运行和 256/256 个严格 TCP/UDP 配对，失败运行、失败配对和跳过运行均为 0。attempt3 失败的首个 `bursty` 配对已通过：TCP 与 UDP 各产生 120 个窗口，双侧守恒残差违反数为 0，TCP 拥塞窗口覆盖率为 1.0，CSV 拥塞控制身份为 `ns3::TcpNewReno`。代码独立复审完成前仍保持 `review_pending`，不能晋级最终数据发布。

## 根因与修复假设

attempt3 在仿真时刻 0.3 秒同时卡住 TCP 与 UDP。旧实现用双精度浮点数计算突发周期相位和剩余延迟；极小正浮点差转换到 ns-3 离散时间后成为 0，导致 `ScheduleNext(0)` 在同一仿真时刻无限调度。

唯一修复假设是：若活动判断、相位偏移、开关周期和下一延迟都在同一 ns-3 整数时间步域内计算，并在非活动分支断言等待时间严格大于 0，则周期边界不会再产生零延迟事件，同时 0.2 秒开启、0.1 秒关闭的物理周期不发生容差性改写。

## 修改与绑定

- 生产代码：`thesis/experiments/llm_probe/ns3/r2_protocol_queue_scenario.cc`
  - 新增统一的整数时间步相位计算；
  - `BurstActive()` 和 `DelayUntilBurstActive()` 改用 `Time`；
  - 非活动分支断言下一延迟严格为正时间步；
  - SHA-256：`b82efbbc5a90b535463282263f76b1c04f4b49da654af17d2d3c1301efb5c771`。
- 受控参数：`thesis/experiments/llm_probe/configs/r2_ns3_protocol_matrix_runtime_v0.json`
  - 只更新 `expected_scenario_source_sha256`；
  - 其余清单、路径和 `resume=false` 均未改变；
  - SHA-256：`791122e6aad728c3a03feb96716fe7e68d319a477f5a19897911684f368c94e9`。
- 服务器项目源码与固定 ns-3 scratch 编译副本逐哈希一致，均为上述新源码摘要。

## 失败保全与运行身份

- attempt3 输出已在同一文件系统原子归档为：
  - `runs/ns3-data/r2-protocol-paired-v0.failed-attempt3-burst-zero-delay/`
- attempt4 在仿真计算前被双副本哈希门禁安全拒绝：项目源码已更新，但 ns-3 scratch 副本仍为旧摘要。
  - 启动目录：`runs/launchers/r2-ns3-protocol-matrix-v0-attempt4/`
  - 状态：`failed`；
  - 完成运行：0；
  - 未创建正式输出根；
  - 失败证据保留，目录未复用。
- attempt5 在同步并逐哈希核对 scratch 副本后从空输出根启动：
  - `screen`：`r2-ns3-attempt5`；
  - 启动目录：`runs/launchers/r2-ns3-protocol-matrix-v0-attempt5/`；
  - 输出根：`runs/ns3-data/r2-protocol-paired-v0/`；
  - `resume=false`；
  - 状态：`finished/review_pending`；
  - 开始时间：`2026-08-03T08:29:09.201297+00:00`；
  - 完成时间：`2026-08-03T08:47:39.632404+00:00`；
  - 受管进程与日志写入器退出码均为 0。

## 首个突发配对证据

配对标识：`8c4900f37191dadd918827d0123deb1919828b17d14caca232a815dbe7f55867`。

- 配对回执：`status=pass`；
- TCP 窗口数：120；
- UDP 窗口数：120；
- TCP 守恒残差违反数：0；
- UDP 守恒残差违反数：0；
- TCP 拥塞窗口覆盖率：1.0，120/120 窗有观测；
- TCP CSV 身份：`ns3::TcpNewReno`；
- 两个 CSV 均为 121 行，包含 1 行表头和 120 行窗口；
- 非活动严格正延迟断言未触发，配对在正常仿真时间内完成。

## 最终矩阵与制品

attempt5 最终完成 512/512 条运行和 256/256 个有效配对，失败运行、失败配对和跳过运行均为 0。服务器结果目录为 50 MiB，数据盘保持 76% 使用率、约 13 GiB 可用。

关键制品及 SHA-256：

- `matrix-summary.json`：`574118e3a3ddddc21f23fdcb9c770ab7f9b3f86dd73feb018bd067d181234819`；
- `matrix-state.json`：`db80f0ca42840a8b5b9ec53294844ee552f5cee739d6df532716a5701155c50f`；
- `run-binding.json`：`d89ee697ce213c0b20c78d636c0fb89f346e63dc263828ca02784e5e380ebab5`；
- `source-lock.json`：`95708a0fffd702f65ec18acfe9ca1c806ba893b5d4f816643bdc59534ec8d38b`；
- `ns3-trace-contract.json`：`b90e4b657b0b5e8cece9af577e05f24d84da58cc7af33a596f21aadcd5b481d9`；
- 汇总记录中的 trace 合同载荷摘要：`89390f51b077118b6c1246ece6b68496f4e720528eb69a23ebb7a280210907fe`。

完整矩阵已通过 `rsync` 回收到本机 `thesis/experiments/llm_probe/runs/ns3-data/r2-protocol-paired-v0/`，共 2,821 个文件、50 MiB；上述五项本地摘要与服务器逐项一致。attempt5 的启动状态、日志和能力清单已回收到 `thesis/experiments/llm_probe/runs/launchers/r2-ns3-protocol-matrix-v0-attempt5/`。

下一门禁是新的独立审查代理复核整数时间步实现与受控参数绑定。复审没有严重或重要问题后，attempt5 才能从 `review_pending` 晋级为 R2 正式 ns-3 物理池输入；在此之前，R2 大模型正式训练继续保持 `NO-GO`。

## 未执行

- 未运行格式化、Prettier、Ruff、Pyright、pytest、独立冒烟、独立目标测试或 `git diff`；
- 未修改 512 条清单、顺序、种子、标签、负载、协议、拓扑或输出字段；
- 未使用 GPU，未初始化 SwanLab；
- 未删除或覆盖 attempt3、attempt4 及历史失败证据。
