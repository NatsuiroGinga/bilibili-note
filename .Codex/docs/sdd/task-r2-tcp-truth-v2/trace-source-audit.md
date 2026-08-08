# R2 ns-3 TCP 物理真值 v2 跟踪源审计

- 审计日期：2026-08-04
- 固定源码：服务器 `/root/autodl-tmp/thesis/ns3/ns-3.48/`
- 既有场景：`thesis/experiments/llm_probe/ns3/r2_protocol_queue_scenario.cc`
- 裁决：**条件 GO**。无需修改 ns-3 核心；必须新增独立 v2 场景，并冻结可辨识的 TCP 选项与事件语义。

## 1. 唯一根因

当前 TCP 数据缺少 ACK、RTT、在途字节、慢启动阈值和拥塞状态，不是因为 ns-3.48 没有这些真值，而是既有场景只连接了 `CongestionWindow`，随后又把多个发送者按时间加权平均到窗口级。既有场景没有连接其余公开跟踪源，也没有保留发送者级事件顺序，因此 attempt5 不能逆推出发送者级 NewReno 状态转移。

可证伪假设为：在每个发送 socket 调用 `Connect` 前同时连接状态、包头和重传跟踪源，并按发送者保留事件顺序，即可在不改 ns-3 核心的条件下闭合累计 ACK、RTT、拥塞窗口、慢启动阈值、在途字节、快速恢复和重传超时。下列源码映射支持该假设；最小字段闭合矩阵负责最终行为验证。

## 2. 状态跟踪源映射

| 字段 | 公共跟踪源 | 回调签名 | 单位 | 服务器源码证据 | 场景连接时机 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| 拥塞窗口 | `CongestionWindow` | `uint32_t oldValue, uint32_t newValue` | 字节 | `tcp-socket-state.cc:50-53`，`tcp-socket-base.cc:267-270`，`tcp-socket-base.h:335` | socket 创建和 `Bind` 后、`Connect` 前 | 可用 |
| 慢启动阈值 | `SlowStartThreshold` | `uint32_t oldValue, uint32_t newValue` | 字节 | `tcp-socket-state.cc:58-61`，`tcp-socket-base.cc:275-278`，`tcp-socket-base.h:345` | 同上 | 可用 |
| 在途字节 | `BytesInFlight` | `uint32_t oldValue, uint32_t newValue` | 字节 | `tcp-socket-state.cc:78-81`，`tcp-socket-base.cc:247-250`，`tcp-socket-base.h:370` | 同上 | 条件可用 |
| 平滑 RTT | `RTT` | `Time oldValue, Time newValue` | ns-3 `Time`，输出换算毫秒 | `tcp-socket-state.cc:87-90`，`tcp-socket-base.cc:211-214`，`tcp-socket-base.h:380` | 同上 | 状态值可用 |
| 最近 RTT | `LastRTT` | `Time oldValue, Time newValue` | ns-3 `Time`，输出换算毫秒 | `tcp-socket-state.cc:91-94`，`tcp-socket-base.cc:215-218`，`tcp-socket-base.h:385` | 同上 | 不能单独承担样本均值 |
| 拥塞状态 | `CongState` | `TcpCongState_t oldValue, TcpCongState_t newValue` | 枚举 | `tcp-socket-state.cc:62-65`，`tcp-socket-base.cc:231-234`，`tcp-socket-base.h:350` | 同上 | 可用 |
| 最高累计 ACK | `HighestRxAck` | `SequenceNumber32 oldValue, SequenceNumber32 newValue` | TCP 序号字节 | `tcp-socket-base.cc:259-262`，`tcp-socket-base.h:1454` | 同上；首个 SYN-ACK 只建立基线 | 可用 |

`TcpSocketBase` 在构造函数中创建 `TcpSocketState`，并于 `tcp-socket-base.cc:333-375` 将上述状态源链到 socket 级公开跟踪源；复制构造路径在 `tcp-socket-base.cc:492-532` 做同样连接。因此场景直接对发送 socket 调用 `TraceConnectWithoutContext` 是正确入口。既有场景已经在 `StartApplication` 中证明了 `CongestionWindow` 可在 `Connect` 前成功连接；v2 必须沿用该时机。

### 2.1 在途字节限制

`TcpSocketBase::BytesInFlight()` 在 `tcp-socket-base.cc:3615-3623` 重新计算并写入跟踪状态，但该方法位于头文件 `protected` 区域，场景不能在任意窗口边界主动调用。v2 只能携带最近一次公开跟踪值，并在首次真实变化前保持缺失掩码；不得把未触发回调的默认零写成已观测真值。

### 2.2 RTT 限制与补救

`TracedValue::Set` 仅在新旧值不同时触发回调，证据为 `src/core/model/traced-value.h:220-231`。因此连续相同的 `LastRTT` 样本只产生一次回调，不能把回调次数直接当 RTT 样本数，也不能据此计算无偏的窗口均值。

v2 使用公开 `Tx`、`Rx`、`Retransmission` 包头回调在场景内复现 ns-3 的 RTT 历史：

- `Tx/Rx` 签名为 `Ptr<const Packet>, const TcpHeader&, Ptr<const TcpSocketBase>`，证据为 `tcp-socket-base.h:668-670`。
- `Retransmission` 另带本地和对端地址，证据为 `tcp-socket-base.h:681-685`。
- 发送历史更新规则位于 `tcp-socket-base.cc:3423-3443`；首次发送记录序号、长度和时间，重传将相应历史项标记为歧义。
- ACK 到达后的 RTT 选择与 Karn 规则位于 `tcp-socket-base.cc:3805-3883`；一个累计 ACK 覆盖多个段时，`LastRTT` 使用最新发送的已确认历史项。

为保证场景重建与固定算法一致，v2 合同显式冻结 `Timestamp=false`；重传段不生成 RTT 样本。每个有效 RTT 样本都进入窗口内的 `rtt_mean_ms`、`rtt_min_ms`、`rtt_max_ms` 和样本计数，`LastRTT` 变化回调只作交叉核对，不单独计数。

## 3. ACK、恢复、丢包与超时映射

| 事件 | 能否可靠取得 | 唯一映射 | 边界 |
| --- | --- | --- | --- |
| 累计 ACK 字节 | 是 | `HighestRxAck` 的正向序号增量；首个 SYN-ACK 仅初始化基线 | 12 秒运行不会跨越 32 位序号空间；仍使用 `SequenceNumber32` 差值 |
| ACK 驱动段数 | 条件是 | 累计 ACK 字节加跨窗口余数，除以实际 `SegmentSize` | 必须冻结 `Sack=false`，否则核心的 `currentDelivered` 包含新 SACK 字节，无法仅由累计 ACK 重建 |
| 重复 ACK 数 | attempt5 默认配置下否 | `Rx` 中相同 ACK 号不一定是重复 ACK，也可能是窗口更新或新的 SACK 记分板信息 | v2 不输出猜测值；`Sack=false` 后才允许按核心条件重建，且不是本轮必要字段 |
| 快速恢复事件 | 是 | `CongState` 首次进入 `CA_RECOVERY` | 计数语义为发送者拥塞控制响应，不等同于链路物理丢包数 |
| 非超时丢包事件 | 是 | `loss_event_count` 定义为进入 `CA_RECOVERY` 的次数 | 不用 `Retransmission` 次数冒充独立丢包次数 |
| 重传超时事件 | 是 | `timeout_event_count` 定义为进入 `CA_LOSS` 的次数 | `RTO` 跟踪源只是当前定时器时长，不是超时发生事件 |
| 重传次数 | 是 | `Retransmission` 回调 | 该回调本身不区分快速重传和超时重传，不能单独给出原因 |

源码闭合证据：

- `CA_RECOVERY` 在 ns-3.48 TCP 模型中的唯一赋值位于 `tcp-socket-base.cc:1738-1752`，对应快速重传和进入丢包恢复。
- `CA_LOSS` 在该模型中的唯一赋值位于 `tcp-socket-base.cc:4054-4067`，处于 `TcpSocketBase::ReTxTimeout()` 路径；同一路径先取得 RTO 前在途字节、更新 `ssthresh`，再把 `cwnd` 置为一个 MSS。
- `TcpCongState_t` 枚举语义位于 `tcp-socket-state.h:70-80`：`CA_RECOVERY` 为快速重传恢复，`CA_LOSS` 为 RTO 或 SACK 撤回。当前固定版本全源码搜索仅发现上述一个 `CA_LOSS` 赋值点；v2 又冻结 `Sack=false`，故进入 `CA_LOSS` 可唯一解释为 RTO。
- `RTO` 跟踪源定义位于 `tcp-socket-base.cc:207-210`，回调类型为 `Time` 旧值和新值。RTT 更新和指数退避都会改变该值，因此禁止把其变化次数当超时次数。

## 4. 固定 NewReno 事件方程

v2 冻结 `TcpNewReno`、`Sack=false`、`Timestamp=false`、`UseEcn=Off`，记录实际 MSS，不引入任何可训练参数。

ACK 增长按 ns-3.48 原式逐事件计算：

1. 若 `cwnd < ssthresh` 且本次至少确认一个完整段，慢启动只增加一个 MSS。
2. 若更新后 `cwnd >= ssthresh` 且仍有未消费的确认段，拥塞避免增加 `max(1, floor(MSS^2 / cwnd))` 字节。
3. 源码证据为 `tcp-congestion-ops.cc:162-224`。

丢包收缩的阈值方程为：

```text
ssthresh_after = max(2 * MSS, floor(0.5 * bytes_in_flight_before_loss))
```

`BetaLoss=0.5` 的默认固定值见 `tcp-congestion-ops.cc:90-94`，阈值方程见 `tcp-congestion-ops.cc:243-254`。v2 在每个窗口分别累计 ACK 增长残差和收缩残差的分子平方和、归一化尺度平方和、有效项数与均方误差；不能只保存平均数，也不能用真实 `cwnd` 增量本身充当期望驱动项。

## 5. v2 最小扩展与停止条件

场景内最小扩展如下，不修改 ns-3 核心：

1. 每个发送 socket 在 `Connect` 前连接 `CongestionWindow`、`SlowStartThreshold`、`BytesInFlight`、`RTT`、`LastRTT`、`CongState`、`HighestRxAck`、`Tx`、`Rx` 和 `Retransmission`。
2. 按 `physics_group_sha256 × window_index × sender_index` 保留独立状态；窗口起点严格继承上一窗口终点。
3. 首个 SYN-ACK 只初始化 ACK 序号基线；UDP 不创建任何 TCP 状态行。
4. 每个值附真实观测掩码；首次回调前、无有效 RTT 样本时保持缺失，不填零。
5. 字段闭合矩阵必须至少出现 `acked_bytes > 0`，以及至少一次进入 `CA_RECOVERY` 或 `CA_LOSS` 并伴随 `cwnd` 或 `ssthresh` 收缩。

若实际矩阵不能产生非零 ACK 驱动或拥塞收缩，结论立即退回 `NO-GO`；不得降低事件门槛、从标签推断事件、把下游总丢包均分给发送者，或把 `RTO` 时长变化填作超时计数。

## 6. UDP 后续合同占位

本轮只执行 TCP v2，不扩大字段闭合矩阵。为避免 TCP 完成后重新修改公共窗口接口，后续 UDP 动力学至少必须补齐下列发送者级、窗口级可识别状态：

- `active_duration_s`：窗口内发送应用实际处于活动突发阶段的时长，不能只用窗口是否出现计划事件替代。
- 计划发送事件与计划应用载荷字节。
- `Socket::Send` 实际接受事件与字节。
- 应用未被 socket 接受的事件与字节，或等价的应用积压状态；必须区分主动停发、socket 背压和网络内丢弃。
- 若应用层存在内部队列，输出窗口起点、终点、入队、出队和应用丢弃，并附守恒残差与观测掩码。

这些字段仍只作训练期物理监督，不进入公开数据推理输入。字段不可观测时保持缺失，禁止把 `planned-actual` 无条件解释为网络丢包。
