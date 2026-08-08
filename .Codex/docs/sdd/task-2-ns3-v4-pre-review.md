# 任务 1：ns-3 v4 严格预审

## 裁决

**不通过，禁止进入服务端绿测和正式矩阵生成。**

- 严重问题：3 项。
- 重要问题：8 项。
- 审查快照：`test_ns3_truth.py` 为 `d11a3dd1`，`ns3_truth.py` 为 `7be43155`，`queue_truth_scenario.cc` 为 `4f3315a9`。
- 本报告只核对源码与测试契约，未修改代码、测试、服务器文件或 Git 状态。

## 严重问题

### 严重-1：生成器仍输出 v3/42 字段，无法被 v4 验证器读取

- 证据：`queue_truth_scenario.cc:75-94` 仍写出 `service_budget_bytes`、`queue_start_bytes`、`offered_bytes` 等旧表头；`queue_truth_scenario.cc:188` 仍写出 `flow_probe_ns3_queue_v3`。
- 影响：`ns3_truth.py:15,28-75` 和 `test_ns3_truth.py:9-56` 已固定为 v4/46 字段，真实生成文件会在表头或模式版本检查处直接失败。
- 验收条件：生成器表头和每行数据必须与 `CSV_FIELDS` 一一对应，固定为 46 列并写出 `flow_probe_ns3_queue_v4`；不得仅修改版本字符串。

### 严重-2：生成器没有包级队列边界状态和包残差

- 证据：`queue_truth_scenario.cc:109-133` 只维护当前队列字节；`queue_truth_scenario.cc:251-266` 没有 `m_currentQueuePackets` 和 `m_windowStartQueuePackets`；旧输出也缺少 `queue_start_packets`、`queue_end_packets`、`qdisc_received_packets` 和 `queue_balance_residual_packets`。
- 影响：无法生成 v4 所需包级状态，也无法独立证明包守恒；按包配置的 `50p` 上限缺少同量纲真值。
- 验收条件：入队同时增加字节和包状态，出队同时减少并检查两种下溢；每窗写出包级起止状态、接收、接纳、出队、两类丢弃及复算为零的包残差。

### 严重-3：验证器会放行错误拓扑、错误队列模型、错误上限和伪造组标识

- 证据：`ns3_truth.py:251-257` 只固定七个场景；`ns3_truth.py:350-385` 只检查拓扑和队列模型在组内不漂移，未固定为 `star-bottleneck-v1` 和 `fifo-queue-disc`；`queue_limit_packets` 未进入固定值检查；`group_id` 仅用作分组键，未核对其组成。
- 影响：任意拓扑、任意队列模型、任意或漂移的队列上限，以及与 `scenario_id/seed/run` 不一致的 `group_id` 都可能被判定通过，运行来源不可追溯。
- 验收条件：逐行固定 `topology_id=star-bottleneck-v1`、`queue_model=fifo-queue-disc`、`queue_limit_packets=50`，并要求 `group_id` 精确等于 `star-bottleneck-v1|{scenario_id}|seed{seed}|run{run}`。

## 重要问题

### 重要-1：跨层字段尚未在生成器中完成语义隔离

- 证据：`queue_truth_scenario.cc:83-94` 仍使用无层级的通用 `*_bytes` 名称；三个回调实际分别采集队列规则项目、点到点帧和应用负载。
- 影响：L3 字节、PPP 帧字节和应用负载字节仍可能被误用于同窗相减。
- 验收条件：根队列规则字段统一为 `*_l3_bytes`，设备与误码丢失统一为 `*_ppp_frame_bytes`，接收端统一为 `sink_received_app_payload_bytes`；任何残差只在同一层内计算。

### 重要-2：测试夹具仍直接混算 PPP 帧字节和应用负载字节

- 证据：`test_ns3_truth.py:134-145` 用 `enqueued_bytes - downstream_error_loss_ppp_frame_bytes` 构造 `sink_received_app_payload_bytes`。
- 影响：即使验证器没有执行跨层残差，该夹具仍把禁止的量纲换算固化为“有效样本”。
- 验收条件：三个字节域分别给定自洽但互不相减的测试值；跨层关联只使用包数，或显式包含协议头与传播中状态。

### 重要-3：七个追踪连接的返回值均未检查

- 证据：`queue_truth_scenario.cc:414-439` 的 `Enqueue`、`Dequeue`、`DropBeforeEnqueue`、`DropAfterDequeue`、`MacTxDrop`、`PhyRxDrop` 和 `Rx` 共七次连接均忽略布尔返回值。
- 影响：追踪名或签名漂移时可能静默输出全零或不完整真值。
- 验收条件：逐次保存并断言返回值，任一连接失败立即终止，错误信息必须指出追踪源名称。

### 重要-4：`FifoQueueDisc=50p`、设备队列 `1p` 和初始 5 Mbps 只有配置，没有回读自证

- 证据：`queue_truth_scenario.cc:372-393` 只设置属性；安装后没有从实际对象回读根队列规则类型、`MaxSize`、设备队列 `MaxSize` 和 `DataRate`。
- 影响：帮助器默认值、安装对象或未来配置发生变化时，CSV 仍会写出硬编码元数据。
- 验收条件：仿真开始前从已安装对象回读并断言根队列规则类型为 `ns3::FifoQueueDisc`、上限为 `50p`、瓶颈发送设备队列为 `1p`、初始速率为 `5000000 bit/s`。

### 重要-5：FIFO 入队前丢弃原因仍被忽略

- 证据：`queue_truth_scenario.cc:124-127` 丢弃回调丢弃了 `reason` 参数。
- 影响：其他原因造成的入队前丢弃会被错误计为 FIFO 上限丢弃。
- 验收条件：每次 `DropBeforeEnqueue` 都必须核对原因为 `FifoQueueDisc::LIMIT_EXCEEDED_DROP`；空原因或其他原因立即终止。`DropAfterDequeue` 仍应独立计数且不得重复扣减队列状态。

### 重要-6：攻击尾部检查不足以证明攻击源持续到测量结束

- 证据：`queue_truth_scenario.cc:442` 已把应用停止时刻改为 `durationSeconds`，但 `ns3_truth.py:490-511` 把队列存量、出队或接收端延迟到达也算作“攻击活动”；`test_ns3_truth.py:247-269` 只覆盖所有相关量同时归零的弱反例。
- 影响：攻击源提前停止但仍有良性流量、积压排空或传播中包时，错误的满攻击尾部仍可能通过。
- 验收条件：所有 `attack_exposure_fraction>0` 的窗口至少要求根队列规则接收字节和接收包均大于零；增加“接收为零但队列或接收端仍有活动”的负向测试；真实 `dos-udp-high` 最后完整攻击窗口必须有接收活动。

### 重要-7：窗口连续性没有固定 0 至 12 秒绝对边界

- 证据：`ns3_truth.py:388-442` 检查数量、索引、窗口长度和相邻边界，但不要求首窗从 0 秒开始，也不要求第 `i` 窗精确对应 `[0.1i, 0.1(i+1)]`。
- 影响：整体平移后的 120 个窗口仍可通过，标签和容量干预时刻将失去物理含义。
- 验收条件：固定每个窗口的绝对起止时刻，同时继续检查 L3 字节和包队列状态跨窗连续。

### 重要-8：关键负向测试覆盖未达到任务简报要求

- 现有直接覆盖：组内固定值漂移、复算包守恒错误。
- 已新增但当前仍为红测：错误拓扑、错误队列模型。
- 仍缺 8 类：字段缺失、窗口少于 120、索引乱序、时间不连续、字节与包队列状态不连续、错误 `group_id` 组成、缺少必需丢弃、非随机场景出现误码。
- 额外缺口：未单独覆盖保存的 `queue_balance_residual_packets` 非零；未覆盖“必需丢弃或随机损失只有字节非零、包数为零”的不一致记录。
- 验收条件：上述每类至少有一个明确失败测试；七场景正向参数化继续保留，并要求良性降容、三种攻击的队列丢弃以及随机损失场景的下游丢失同时具备非零字节和非零包数。

## 最小批准门槛

- [ ] 严重-1 至严重-3 全部修复。
- [ ] 重要-1 至重要-8 全部补齐。
- [ ] Python 执行 Black、Ruff；C++ 执行 `clang-format`；Markdown 执行 Prettier。
- [ ] 服务端完整测试、ns-3 构建及 `dos-udp-high`、`benign-random-loss` 真实冒烟均通过。
- [ ] 真实 CSV 为 46 字段、120 窗口、双残差为零，攻击尾部有接收活动，且三个字节域未参与跨层残差。
