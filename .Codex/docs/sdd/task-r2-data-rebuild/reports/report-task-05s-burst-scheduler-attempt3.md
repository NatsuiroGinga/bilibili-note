# 任务 05S：attempt3 突发调度零延迟循环报告

日期：2026-08-03  
状态：`failed_preserved`  
范围：服务器正式矩阵启动、运行时证据核验与失败保全；未修改生产代码、冻结配置、512 条清单或正式运行顺序

## 结论

R2 ns-3 第三次正式矩阵已通过启动前目录、进程、磁盘、工具和文件哈希门禁，并在唯一 `screen` 中从空输出根启动。前 32 个 TCP/UDP 配对全部通过，随后第 33 个、也是首个 `bursty` 配对在仿真时间 0.3 秒进入零延迟事件循环。TCP 与 UDP 两侧均复现同一现象。

该问题会使后续所有命中同一浮点周期边界的突发配置无法完成，因此 attempt3 不能继续等待，也不能作为最终矩阵。两个陷入循环的 ns-3 模拟子进程分别在确认进程身份、配对哈希和协议身份后收到 `SIGTERM`；上层运行器据此写出双侧失败回执并在配对边界自然停止。成功运行、失败 `.partial`、启动状态、能力清单、日志和先导清单均已保留，没有删除或覆盖制品。

## 启动前现场与原子归档

- attempt2 源 `runs/ns3-data/r2-protocol-paired-v0/` 是普通目录且不是符号链接。
- 唯一归档目标 `runs/ns3-data/r2-protocol-paired-v0.failed-attempt2-cubic-contract/` 事前不存在。
- attempt3 启动目录 `runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/` 事前不存在。
- 现场没有实验 `screen` 或同名运行进程。
- 数据盘使用率为 76%，启动前可用 13,200,187,392 字节。
- `rg`、`uv` 与 `screen` 均可用。
- attempt2 已在同一文件系统原子移动到上述唯一归档目标；没有删除、覆盖或合并旧证据。

## 同步与哈希

任务 04R/05R 的生产文件、配置、512 条清单、校验制品及受管启动器逐文件同步后，服务器摘要与本地摘要一致：

| 制品 | SHA-256 |
| --- | --- |
| `src/flow_probe/r2_ns3_protocol_matrix.py` | `2228a0ac820895fbfbc11c4dda20c2406fcea638c2402e283a160ee96a874395` |
| `configs/r2_ns3_protocol_matrix_v1.yaml` | `0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb` |
| `runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl` | `d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111` |
| `runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.sha256` | `3cfdfc1d2270b38ea3915325abbf8c7f16f1a11492088f15e4706b8adebd53ab` |
| `ns3/r2_protocol_queue_scenario.cc` | `8a6fbfdb88784c7f951ef880bbd223a1f5df041a56f4615d62b7589a60af76c5` |
| `src/flow_probe/r2_ns3_protocol_runner.py` | `40a97ee063d2e846b7c5971d0498a886ac67a2b190676c750b16eeca1d3a7c8b` |
| `configs/r2_ns3_protocol_matrix_runtime_v0.json` | `a32978154c4a5203e621bf2e8b8f2789b3777a104eff430b7dcf5b59810a6f05` |
| `scripts/run_r2_ns3_protocol_matrix.sh` | `61e54d85602263b8a53d0692b24ebc9e7504e368a9d9fa7e78f4b2d7045ba228` |
| `configs/r2_protocol_data_v1.yaml` | `aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566` |
| `scripts/guarded_execution_common.py` | `432a0981a1389836c8e5a09f6bc5ed18bc586058c760a8f4063252ca9322a36b` |
| `scripts/guarded_remote_runner.py` | `ef7396d2e22c4c97552795448fd439784e3b65b9ec1b1821d940652a6d425043` |

同步未使用 `--delete`，未复制数据集、模型或历史运行目录。

## 正式运行身份与首配对门禁

- `screen`：`8953.r2-ns3-attempt3`，结束后套接字已退出。
- 启动目录：`runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/`。
- 正式输出根：`runs/ns3-data/r2-protocol-paired-v0/`。
- 受管参数固定 `resume=false`。
- 首配对哈希：`dd83746a955899c9b5c5db2d074e65e0059a73424803090b0cc83f932b550739`。

首配对运行时证据全部通过：

- TCP 与 UDP 均为 120 个窗口；
- 两侧 `residual_violation_count=0`；
- TCP `cwnd` 覆盖率为 1.0，120 个窗口均有状态；
- CSV 拥塞控制身份为 `ns3::TcpNewReno`；
- 两侧回执、CSV 和配置哈希均绑定当前清单、场景与 trace 合同。

## 首 16 配对先导制品

正式矩阵达到 32 个有效配对后，从不可变清单顺序中选择前 16 个配对，仅在独立启动目录生成先导引用，没有复制或修改正式输出：

- `runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/pilot-first16-pairs.manifest.jsonl`
  - 32 条运行记录，对应 16 个 TCP/UDP 配对；
  - SHA-256：`e842c287995da8c3c634b5fd01a079f60fe25965a42d7772881c7209e10d88fb`。
- `runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/pilot-first16-pairs.artifacts.sha256`
  - 81 项摘要；
  - 绑定先导清单，以及每个配对的配对回执、TCP/UDP 单运行回执和 TCP/UDP CSV。

两个文件模式均为只读。它们只允许用于开发集物理旁路先导实验，不能标为完整矩阵、最终数据或论文主表证据，也不能据此跳过后续正式运行。

## 失败现象与根因

第 33 个配对哈希为 `8c4900f37191dadd918827d0123deb1919828b17d14caca232a815dbe7f55867`，参数包含：

- `arrivalModel=bursty`；
- `burstOnSeconds=0.2`；
- `burstOffSeconds=0.1`；
- 总提供负载 7 Mbps；
- 容量 20 Mbps 在 6 秒变为 10 Mbps；
- TCP 与 UDP 使用相同基础配置和种子。

UDP 与 TCP 两侧均只写出窗口 0、1、2，最后一个窗口终点恰为 `0.300000000` 秒，此后文件不再增长；对应模拟进程持续占用 100% 单核。无异常输出或内存增长证据。

场景中的 `DelayUntilBurstActive()` 使用双精度浮点计算：

1. 周期为 `0.2 + 0.1`；
2. 使用 `fmod(now + phase_offset, cycle)` 求相位；
3. 非活动区间返回 `Seconds(cycle - phase)`；
4. 在 0.3 秒周期边界，浮点差可以成为极小正数；
5. 该值转换为 ns-3 离散时间后量化为 0；
6. `ScheduleNext(0)` 在同一仿真时刻反复调度 `AttemptSend()`，形成无限事件循环。

TCP 与 UDP 在同一窗口、同一配对上独立复现，排除了协议栈、队列、PPP 修复或 NewReno 身份导致单侧变慢的解释。

## 停止与最终状态

- 启动状态：`failed`，主进程退出码 1，日志写入器退出码 0，日志非空。
- 矩阵状态：`failed`。
- 成功运行：64 条。
- 有效配对：32 个。
- 失败运行：2 条。
- 失败配对：1 个。
- 跳过运行：0 条。
- 失败配对的 TCP/UDP `.partial`、回执、标准输出、标准错误和 CSV 均已由运行器纳入配对回执。

两个模拟子进程的 shell 退出状态为 241，对应接收 `SIGTERM` 后由上层命令返回；这不是模型或守恒门禁失败，而是为终止已证实的无限循环而产生的受控停止状态。

## 后续最小修复边界

attempt3 不能恢复。后续应新建最小修复任务并使用新 attempt 身份：

1. 只修改突发周期相位与下一事件延迟计算，冻结的 512 条清单、顺序、种子、标签、协议、负载和输出字段不得变化。
2. `BurstActive()` 与 `DelayUntilBurstActive()` 必须使用同一套 ns-3 整数时间步语义，不能继续分别用浮点相位判断和浮点延迟。
3. 非活动分支的下一事件延迟必须运行时断言为严格正的时间步；不得用任意毫秒容差改变 0.2/0.1 秒物理周期。
4. attempt3 输出应原子归档到新的唯一失败目录，保留先导清单和全部失败证据；新正式运行必须使用空输出根、`resume=false` 和新的唯一启动目录。
5. 新运行的首个 `bursty` TCP/UDP 配对必须直接承担 120 窗、严格正延迟、NewReno、双守恒和 `cwnd` 覆盖门禁；不另跑独立冒烟、格式化、Pyright 或 pytest。

在新矩阵完整通过前，R2 最终 ns-3 数据发布和正式模型训练继续保持 `NO-GO`。首 16 配对先导仅可解锁开发集物理旁路先导实验。

## 未执行与未变更

- 未运行格式化、Prettier、Ruff、Pyright、pytest、独立冒烟或额外目标测试。
- 未修改生产代码、测试、配置、清单、种子、运行顺序或已通过运行。
- 未使用 GPU，未初始化 SwanLab。
- 未删除、覆盖或合并 attempt2、attempt3 或历史制品。
