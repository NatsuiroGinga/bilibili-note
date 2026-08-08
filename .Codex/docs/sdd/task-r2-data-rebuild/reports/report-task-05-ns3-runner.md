# 任务05：R2 ns-3 场景、TCP trace 与运行身份修复报告

日期：2026-08-03  
状态：`review_pending`（任务04R/05R本地修复完成，正式矩阵第三次启动尚未执行）

## 结论

任务05首次正式入口在运行矩阵前安全失败。根因是 ns-3.48 的 `PhyRxDrop` 在 `ProcessHeader` 移除 PPP 头之前触发，而原场景把含头整包长度误记为网络层字节。任务05R已按唯一允许方案完成本地最小修复：C++ 回调使用 `PeekHeader(PppHeader&)` 取得实际解析长度，严格核对声明长度和 IPv4 协议后再扣除；Python 审计器改为绑定真实错误分支顺序、PPP 头长、`PeekHeader` 实现和场景扣除表达式。

第二次正式入口完成首个 TCP/UDP 配对模拟后，在 `truth_tcp_congestion_control` 身份校验处安全失败：任务04清单错误声明 `ns3::TcpCubic`，而计划、场景与审计器均固定 `ns3::TcpNewReno`。任务04R现已修正配置并重生成512条清单；除两个来源绑定哈希和拥塞控制身份外，逐记录语义、运行种子、配对组标识与协议顺序全部不变。当前仍没有任何有效 ns-3 窗口、协议配对或512条矩阵结果，前两次失败证据都必须保留。

## 修改文件

- `thesis/experiments/llm_probe/ns3/r2_protocol_queue_scenario.cc`
- `thesis/experiments/llm_probe/src/flow_probe/r2_ns3_protocol_runner.py`
- `thesis/experiments/llm_probe/configs/r2_ns3_protocol_matrix_runtime_v0.json`
- `thesis/experiments/llm_probe/scripts/run_r2_ns3_protocol_matrix.sh`
- `thesis/experiments/llm_probe/tests/test_r2_ns3_protocol_runner.py`
- `thesis/experiments/llm_probe/tests/test_run_r2_ns3_protocol_matrix_wrapper.py`
- `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-05-ns3-runner.md`

任务04R在任务05范围内只修改了 Python 运行器的冻结哈希、受控参数、直接绑定测试和本报告；C++ 场景、Shell 包装器、字段定义、丢失率及旧 ns-3 运行制品均未改动。任务04生成器、配置、清单和校验文件的变更见任务04报告。

## 场景实现

1. TCP 发送端由应用显式创建 `ns3::TcpSocketFactory` socket，在每个发送 socket 上直接连接 `CongestionWindow`，并在节点创建前固定 `ns3::TcpL4Protocol::SocketType=ns3::TcpNewReno`。
2. CSV 显式写出 ns-3 版本 `3.48`、拥塞控制类型 `ns3::TcpNewReno`、trace 名、时间加权聚合规则及 TCP/UDP 适用掩码。
3. 场景使用一个路由器出口共享队列。`Enqueue`、`Dequeue`、`DropBeforeEnqueue` 和 `DropAfterDequeue` 直接形成队列计数；每窗独立写出窗起/窗末队列、容量积分及包/网络层字节整数残差。
4. 下游独立错误丢失取自接收设备 `PhyRxDrop`，接收量取自接收端 `Ipv4L3Protocol/LocalDeliver`。`PhyRxDrop` 包仍含 PPP 头；回调先检查包长，再以 `PeekHeader` 只读解析头部，要求解析长度等于 `PppHeader::GetSerializedSize()`、协议号等于 IPv4 的 `0x0021`，最终只累计 `packet->GetSize() - parsedPppHeaderBytes`。
5. UDP 只写计划应用载荷包/字节、实际发送事件/字节、目标速率和突发状态。TCP 对应字段强制为零；UDP 的 TCP trace 文本和数值状态强制为不适用。
6. TCP 与普通 UDP 读取同一个任务04基础配置，除协议外使用同一拓扑、运行种子、总提供负载、容量、时延、队列、丢失率、到达过程与发送者组成。

## 运行器门禁

1. 启动前锁定任务04清单 SHA-256 `d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111`、矩阵配置 SHA-256 `0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb` 和任务01共享配置 SHA-256 `aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566`。
2. 只接受256个基础组和512条运行；每组必须恰含一个 TCP 和一个 UDP，移除协议字段后配置逐字段相同。
3. 每条运行先写 `.<协议>.partial/`。退出状态、120窗、字段顺序、配置真值、容量轨迹、公共观测、独立重算守恒、设备发送丢弃、UDP直接状态和 TCP `cwnd` 覆盖全部通过后，才把 CSV 与整个运行目录原子发布。
4. TCP `cwnd` 覆盖率低于0.95、任何独立重算残差非零、窗口不是120、UDP携带 TCP 状态、成功回执或制品哈希不符均为硬失败。
5. 一侧失败后仍执行同一基础组的另一协议，然后在配对边界停止。两侧目录、日志和回执均保留，失败配对不写为有效配对。
6. 恢复只跳过清单、场景源码、trace 合同、单运行配置、CSV 与通过状态全部匹配的已发布运行。旧 `.partial` 目录改名为带序号的失败尝试，不覆盖、不删除。
7. 最终 `source-lock.json` 同时绑定源文件、trace 源码、每条计划配置、成功目录、当前失败目录、历史失败尝试、配置 JSON、CSV、日志、单运行回执和配对回执的逻辑相对路径、字节数与 SHA-256。
8. trace 审计现同时绑定 `PointToPointNetDevice::Receive` 中“错误分支先触发 `PhyRxDrop`、成功分支后调用 `ProcessHeader`”的顺序、`ProcessHeader` 的 `RemoveHeader`、PPP 固定 2 字节声明及 `Packet::PeekHeader` 的只读反序列化实现。合同模式版本提升为 `flow_probe_r2_ns3_trace_contract_v2`。

## 包装器

包装器先加载 `~/.bashrc`，再启用未定义变量检查；只接受一个受控 JSON 参数文件，固定正式项目根和 ns-3.48 根，设置 `CUDA_VISIBLE_DEVICES=""` 与 `SWANLAB_MODE=disabled`，并通过 `uv run --no-sync` 调用运行器。参数 JSON 必须精确给出以下键：

```json
{
  "expected_manifest_sha256": "d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111",
  "expected_scenario_source_sha256": "8a6fbfdb88784c7f951ef880bbd223a1f5df041a56f4615d62b7589a60af76c5",
  "manifest_path": "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl",
  "ns3_root": "/root/autodl-tmp/thesis/ns3/ns-3.48",
  "output_dir": "runs/ns3-data/r2-protocol-paired-v0",
  "project_root": "/root/autodl-tmp/thesis/experiments/llm_probe",
  "resume": false,
  "scenario_source": "ns3/r2_protocol_queue_scenario.cc",
  "schema_version": "flow_probe_r2_ns3_wrapper_params_v1"
}
```

## 文件哈希

- C++ 场景：`8a6fbfdb88784c7f951ef880bbd223a1f5df041a56f4615d62b7589a60af76c5`
- Python 运行器：`40a97ee063d2e846b7c5971d0498a886ac67a2b190676c750b16eeca1d3a7c8b`
- 受控运行参数：`a32978154c4a5203e621bf2e8b8f2789b3777a104eff430b7dcf5b59810a6f05`
- Shell 包装器：`61e54d85602263b8a53d0692b24ebc9e7504e368a9d9fa7e78f4b2d7045ba228`
- Python 后置回归合同：`bd7cbdeb26abb56f05b13cc46ab4e53651e886848c79de316e520344a534d64f`
- Shell 后置回归合同：`fc54d493b71f24312b94f6f7a878185ede18849a0c2c535adbddae23d2fe3ae8`

## 已执行验证

- `bash -n thesis/experiments/llm_probe/scripts/run_r2_ns3_protocol_matrix.sh`：退出码0，仅执行一次。
- 任务04R正式入口退出码为0，重新生成256个基础组和512条协议运行；逐记录等价、分布、字节和哈希核对均通过，详见任务04报告。
- 任务05R上传前的历史只读核对曾确认正式输出 `runs/ns3-data/r2-protocol-paired-v0/` 不存在、ns-3.48 的 `ipv4-queue-disc-item.cc` 存在、数据盘使用率76%且剩余 `12,898,284 KiB`；该状态不代表第二次失败后的当前服务器实况。
- 同一历史核对曾确认任务04模块、冻结清单和校验文件尚未同步，因此当时没有误启动不完整正式运行。
- 依据 ns-3 官方源码与文档核对，`TcpNewReno` 由 `tcp-congestion-ops.h` 导出，`CongestionWindow` 位于 TCP socket trace，`LocalDeliver` 使用显式 IPv4 头与包参数；据此修正了头文件和 TCP `Connect()` 返回值处理。正式服务器源码审计仍是最终事实门禁。
- 任务05R重新核对本机 `ns-3.48.tar.bz2` 原始源码：`PhyRxDrop` 位于接收错误分支第333行，`ProcessHeader(packet, protocol)`位于成功分支第358行；`PppHeader::GetSerializedSize()`返回2；`Packet::PeekHeader(Header&) const`返回实际反序列化长度且不移除头部。
- `UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync python -m py_compile src/flow_probe/r2_ns3_protocol_runner.py tests/test_r2_ns3_protocol_runner.py`：退出码0。首次使用默认 `uv` 缓存因沙箱不可写而退出码2，改用临时缓存后同一命令通过；该失败与源码无关。
- `python3 -m json.tool configs/r2_ns3_protocol_matrix_runtime_v0.json`：退出码0。
- 静态令牌核对确认 C++ 只按 `PeekHeader` 返回长度扣除，旧的直接整包累计式不再存在于回调；Python 合同记录新语义并纳入 PPP 与 Packet 上游源码制品。

按任务04R/05R边界，没有运行格式化、Prettier、抽象语法树检查、独立冒烟、独立 pytest、全量测试或 Pyright。直接语义测试已经更新但未执行。C++ 场景和 Shell 包装器在任务04R中未改动；服务器编译与运行时断言由第三次正式矩阵的首个配对承担。

## 阻塞与下一步

当前下一步由主代理按既有服务器授权执行，最小动作如下：

1. 第二次失败输出的精确源为 `/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/r2-protocol-paired-v0/`，唯一归档目标为 `/root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/r2-protocol-paired-v0.failed-attempt2-cubic-contract/`。确认源存在且目标不存在后，在同一文件系统执行原子命令：`mv -- /root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/r2-protocol-paired-v0 /root/autodl-tmp/thesis/experiments/llm_probe/runs/ns3-data/r2-protocol-paired-v0.failed-attempt2-cubic-contract`。不得删除、覆盖或合并旧内容。
2. 只同步任务04R/05R白名单生产文件、重生成清单、校验文件、受控参数以及当前任务01共享配置 `configs/r2_protocol_data_v1.yaml`，并逐文件核对本报告 SHA-256；不使用 `--delete`，不复制数据集或历史运行目录。
3. C++ 场景继续使用 SHA-256 `8a6fbfdb88784c7f951ef880bbd223a1f5df041a56f4615d62b7589a60af76c5`，复制到固定 ns-3.48 `scratch/flow-probe-r2-protocol.cc` 后由运行器再次核对项目副本和编译副本哈希。
4. 通过统一远程启动器传入上述受控参数，在新启动目录 `runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/` 从事前不存在的 `runs/ns3-data/r2-protocol-paired-v0/` 启动正式矩阵，`resume=false`。不另起独立冒烟、格式化、Pyright或全量测试。
5. 首个正式配对承担编译、NewReno身份、120窗、双守恒与 TCP `cwnd` 覆盖门禁；通过后继续512条矩阵。任一配对失败即保留双侧回执并停止。磁盘达到80%或剩余不足10 GiB立即停止并汇报。
6. 完成后回收 `matrix-summary.json`、`matrix-state.json`、`source-lock.json`、`ns3-trace-contract.json`、统一启动器状态和日志，再更新实验总控。未取得这些制品前，R2数据重建和模型实验继续保持 `NO-GO`。
