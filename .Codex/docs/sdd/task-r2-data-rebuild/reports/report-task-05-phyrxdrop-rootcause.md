# 任务05 `PhyRxDrop` 网络层字节口径根因调查

## 裁决

**根因已确认。** 任务05错误地假定 `PointToPointNetDevice/PhyRxDrop` 在 PPP 头移除后触发。服务器 ns-3.48 的真实实现恰好相反：接收错误分支先触发 `m_phyRxDropTrace(packet)` 并结束；只有成功接收分支才调用 `ProcessHeader(packet, protocol)` 移除 PPP 头。该错误假设同时进入了 Python 源码审计器和 C++ 下游丢失计数器。

因此，本次正式入口失败是正确的安全停止。当前 C++ 回调若继续运行，会把每个丢失包的 2 字节 PPP 头计入 `truth_downstream_error_loss_l3_bytes`，违反冻结的网络层字节口径。不得通过删除审计、改名为网络层字节或容忍 2 字节误差来继续矩阵。

## 失败证据

- 本地失败日志：`thesis/experiments/llm_probe/runs/launchers/r2-ns3-protocol-matrix-v0/launcher.log`
- 日志 SHA-256：`1a3a443e967f9a42bb3cd3c638d1fe92ec4028f646ba7967f66a5c77fcec1af5`
- 唯一错误：`无法证明 PhyRxDrop 在 PPP 头移除后触发，禁止把其字节记为网络层字节`
- 失败发生在 `audit_ns3_trace_contract`，尚未进入 512 条 TCP/UDP 正式运行，未产生可用矩阵结果。

本轮生产文件绑定如下：

| 文件 | SHA-256 |
| --- | --- |
| `src/flow_probe/r2_ns3_protocol_runner.py` | `c627b066a62bd096b18b93056837b1967f5a5e9e0c9558063f59e35299f58631` |
| `ns3/r2_protocol_queue_scenario.cc` | `17981b036e3dbf5373efbc5786bbfd92f0202527bfd49150161eaad3618de8cf` |

服务器 ns-3.48 证据源绑定如下：

| 文件 | SHA-256 |
| --- | --- |
| `VERSION` | `cff3a5c5ca2302c6d3f9beccd18688434589ab29c4df8f3bae2aaff16efddf1c` |
| `src/point-to-point/model/point-to-point-net-device.cc` | `8be7f207419ca5670f3ed74ba199edf166b31262c312e29db0d22a989eacf2bb` |
| `src/point-to-point/model/point-to-point-net-device.h` | `93e3f22e2c8ba5c4053b7bf3ff1ab19f8f392dc9cd4b44680fb4c3e1af379b03` |
| `src/point-to-point/model/ppp-header.cc` | `914a1e5ce34d96a69829782c525ca50f0df78a709aed2651d9b220f6d2742a14` |
| `src/point-to-point/model/ppp-header.h` | `03ff4a0fc6d66e8991d57f1faa1386a6b7b2513f07bc1281a2f44a345571bbfb` |
| `src/network/model/packet.cc` | `fd47794638b837592b0269178e5e9d20255864fd2bd7c3db4b1d6b23f027a217` |
| `src/network/model/packet.h` | `46e6df98e37de6f8523911b5847f97aed5aab4d191c1a994070a4a5f3c66c156` |

## 调用顺序核对

服务器文件 `src/point-to-point/model/point-to-point-net-device.cc` 的相关顺序为：

1. `PointToPointNetDevice::Receive` 第 327 行判断接收错误模型。
2. 错误分支第 333 行执行 `m_phyRxDropTrace(packet)`。
3. 成功接收的 `else` 分支第 358 行才执行 `ProcessHeader(packet, protocol)`。
4. `ProcessHeader` 第 193 至 195 行构造 `PppHeader`、调用 `RemoveHeader`，再读取协议号。

这两个调用不但顺序相反，而且位于互斥分支。丢失包不会执行 `ProcessHeader`。

服务器文件 `src/point-to-point/model/ppp-header.cc` 第 67 至 69 行证明 `PppHeader::GetSerializedSize()` 固定返回 2。服务器文件 `src/network/model/packet.h` 和 `packet.cc` 同时证明 `Packet::PeekHeader(Header&) const` 可以在不修改 `Ptr<const Packet>` 的情况下反序列化并返回实际读取的头长度。

## 本地实现中的错误传播

### Python 审计器

`src/flow_probe/r2_ns3_protocol_runner.py` 第 384 至 390 行存在两层问题：

1. 它搜索 `ProcessHeader(packet)`，而 ns-3.48 的真实调用是 `ProcessHeader(packet, protocol)`，所以该令牌本身无法命中。
2. 即使把令牌改成真实签名，审计器仍要求 `ProcessHeader` 早于 `m_phyRxDropTrace`；该顺序与真实接收生命周期相反。

这两层问题来自同一个根因，即把 `PhyRxDrop` 的包错误理解为已经剥离 PPP 头的包。单独修正搜索字符串不能修复字节语义。

### C++ 场景

`ns3/r2_protocol_queue_scenario.cc` 第 261 至 264 行的 `OnDownstreamErrorLoss` 直接执行：

```cpp
m_downstreamErrorLossBytes += packet->GetSize();
```

由于该回调连接到接收设备的 `PhyRxDrop`，这里得到的是仍含 2 字节 PPP 头的包长，而字段名和后续合同要求的是网络层字节。包数计数不受影响，字节计数受影响。

## 单一、可证伪的最小修复假设

**假设：** 保留 `PhyRxDrop` 作为下游错误丢失的直接事件源，但在回调内使用 `Packet::PeekHeader(PppHeader&)` 只读解析实际 PPP 头，严格确认返回长度等于 `PppHeader::GetSerializedSize()`、协议为 IPv4、包长不小于头长，然后仅累加 `packet->GetSize() - ppp_header_bytes`。同时让 Python 审计器证明“`PhyRxDrop` 发生在 PPP 头移除前、PPP 头固定为 2 字节、场景显式解析并扣除该头”，而不是继续证明一个不存在的调用顺序。

该假设保持以下边界不变：

- 不改变 `truth_downstream_error_loss_l3_bytes` 的网络层字节定义。
- 不改变 256 个基础配置、512 条协议运行、标签、种子、拓扑或下游丢失率。
- 不使用固定常数盲减；实际扣除长度必须来自 `PeekHeader` 的返回值，并与 PPP 实现声明的序列化长度一致。
- 不允许解析失败、非 IPv4、长度不足或来源源码变化时继续运行；任一情况必须使正式运行失败。
- `downstream_loss_l3_semantics` 应改成明确表示“`PhyRxDrop` 包减去已验证 PPP 头”的新语义，不得继续写 `ProcessHeader_before_PhyRxDrop`。

**证伪条件：** 若正式运行中的任一 `PhyRxDrop` 包无法只读解析出长度与 `PppHeader::GetSerializedSize()` 一致的 IPv4 PPP 头，或扣除后的字节口径不能通过正式运行内的整数断言，则该假设为假，立即停止矩阵；不得改为固定减 2、容差守恒或应用载荷字节。

## 最小文件范围

实施代理只需检查以下文件：

1. `thesis/experiments/llm_probe/ns3/r2_protocol_queue_scenario.cc`
2. `thesis/experiments/llm_probe/src/flow_probe/r2_ns3_protocol_runner.py`
3. `thesis/experiments/llm_probe/tests/test_r2_ns3_protocol_runner.py`，仅增加直接覆盖新源码审计语义的最小回归用例；若当前正式运行合同继续禁止独立目标测试，则不在启动前单独执行。
4. `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-05-ns3-runner.md`，仅在修复验证后更新旧错误描述。
5. 修复验证后，在 `thesis/experiments/llm_probe/AGENTS.md` 写入一条可复用防复发规则：点到点 `PhyRxDrop` 携带 PPP 头，网络层字节必须经显式头解析后计数。

不得修改 ns-3.48 上游源码、冻结矩阵清单、数据合同、标签或网络层字节定义。

## 验证命令与通过标准

本轮调查没有执行格式化、Pyright、全量测试、独立冒烟或代码修改。最小修复完成后，先用以下只读命令重新绑定上游调用顺序：

```bash
cd /root/autodl-tmp/thesis/ns3/ns-3.48
rg "PointToPointNetDevice::Receive|m_phyRxDropTrace|ProcessHeader\\(|PppHeader::GetSerializedSize|Packet::PeekHeader" src/point-to-point/model/point-to-point-net-device.cc src/point-to-point/model/ppp-header.cc src/network/model/packet.cc --line-number --context 12
```

随后将修复后的两个生产文件按白名单同步服务器，在新的唯一输出目录启动原 512 条正式矩阵，不另跑冒烟。正式包装器启动阶段必须同时通过：

1. 上游六个证据文件及场景文件 SHA-256 进入新的 `ns3-trace-contract.json` 和源码锁。
2. trace 合同记录新的 PPP 显式剥离语义，不再记录 `ProcessHeader_before_PhyRxDrop`。
3. 每次 `PhyRxDrop` 回调均通过 PPP 长度、IPv4 协议和包长下界断言。
4. 第一对 TCP/UDP 正式配置仍分别产生 120 窗；既有包与网络层字节整数残差保持逐窗为 0。
5. 首个包含非零下游错误丢失的正式配置产生非零丢失包时，运行不触发 PPP 解析断言，且其字节字段由逐包扣除后的整数和产生。
6. 任一断言失败时保留失败回执并停止，不发布该配对组。

## 当前状态

- 根因调查：`完成`
- 生产代码修改：`未执行`
- 正式矩阵：`阻塞，等待最小修复`
- R2 数据与训练：继续保持 `NO-GO`
