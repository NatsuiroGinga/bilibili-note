# 任务 1：ns-3 v4 契约独立最终审查

## 裁决

- **计划符合性：不通过。** 生成器主体符合 v4 契约，预审的 3 个严重问题和 8 个重要问题均已有实质修复；但验证器仍会接受字段顺序错误及两类物理不可能记录，固定契约尚未完整落实。
- **代码质量：不批准。** 当前发现 0 项严重问题、3 项重要问题、1 项次要问题。
- 审查对象：当前工作区三个任务文件、需求简报、实现报告、工作区差异包和先前预审。
- 审查限制：未修改代码、测试、服务器文件、Git 索引或分支；未在本机运行 pytest；未独立重跑服务端编译和冒烟。

## 重要问题

### 重要-1：验证器不检查固定 46 字段的顺序

- 文件与行号：`thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py:179`。
- 现状：`_validate_header` 只比较字段数量、缺失、多余和重复，未要求 `tuple(fieldnames) == CSV_FIELDS`。
- 实证：将合法夹具的前两个表头字段 `schema_version` 与 `scenario_id` 交换，同时按交换后的表头写值，`validate_ns3_truth_paths` 返回 `passed`。
- 影响：`flow_probe_ns3_queue_v4` 声明的固定字段顺序没有成为验证条件；依赖固定列位置的下游读取器可能接收非规范文件。
- 测试缺口：`thesis/experiments/llm_probe/tests/test_ns3_truth.py:470` 只覆盖字段缺失，未覆盖字段置换。

### 重要-2：丢弃字节与包数只做整组非零检查，可被跨窗口拼接绕过

- 文件与行号：`thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py:622`。
- 现状：队列丢弃和下游误码均只比较整组总量是否同时为零或同时非零，没有逐窗检查同一事件域的字节数与包数是否同步出现。
- 实证一：在 `dos-udp-high` 中把窗口 50 设为“丢弃 100 字节、0 包”，窗口 51 设为“丢弃 0 字节、1 包”，并分别保持字节守恒与包守恒，验证结果为 `passed`。
- 实证二：在 `benign-random-loss` 中把窗口 10 设为“误码丢失 100 字节、0 包”，窗口 11 设为“误码丢失 0 字节、1 包”，验证结果为 `passed`。
- 影响：实现报告所述“对应字节数与包数同时非零”只在整组聚合层面成立，无法拒绝单窗物理不可能记录，也无法证明必需丢弃发生在同一计量窗口。
- 测试缺口：`thesis/experiments/llm_probe/tests/test_ns3_truth.py:357` 和 `thesis/experiments/llm_probe/tests/test_ns3_truth.py:372` 只把全组包计数清零，未覆盖跨窗口抵消反例。

### 重要-3：固定 `50p` 队列仍可接受非零初始状态和超过 50 包的队列状态

- 文件与行号：`thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py:353`、`thesis/experiments/llm_probe/src/flow_probe/ns3_truth.py:446`。
- 现状：验证器固定元数据 `queue_limit_packets=50` 并检查跨窗连续，但不要求首窗 `queue_start_packets=0`、`queue_start_l3_bytes=0`，也不要求每窗起止包数不超过 50。
- 实证：把合法 `benign-low` 的全部 120 个窗口都改为起止 51 包、起止 51000 L3 字节，同时保持每窗双残差为零，验证结果为 `passed`。
- 影响：验证器可接受不可能由本任务空队列启动、`FifoQueueDisc MaxSize=50p` 配置产生的状态序列。这里只能从 `50p` 严格约束包数，不能据此推导 L3 字节上限；字节状态仅需检查首窗为零和跨窗连续。
- 测试缺口：`thesis/experiments/llm_probe/tests/test_ns3_truth.py:447` 只检查跨窗连续，不检查初始零状态和包数上限。

## 次要问题

### 次要-1：自动化测试只验证手写夹具，未锁定生成器与验证器的共同契约

- 文件与行号：`thesis/experiments/llm_probe/tests/test_ns3_truth.py:68`、`thesis/experiments/llm_probe/tests/test_ns3_truth.py:153`。
- 现状：所有正向 CSV 都由 Python 手写 `FIELDS` 和 `_rows` 生成，没有测试执行 C++ 生成器或从生成器产物核对 46 列顺序与逐列含义。
- 影响：本轮源码人工核对和报告中的真实冒烟可以支持当前生成器实现，但后续生成器字段漂移时，Python 的 38 项测试仍可能全部通过。
- 边界：这属于回归保护不足，不否定已人工确认的当前 C++ 表头与行值顺序。

## 预审问题复核

| 预审问题                                     | 复核结论             | 当前证据                                                                                                                                              |
| -------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 严重-1：生成器仍为 v3/42 字段                | 已实质解决           | `queue_truth_scenario.cc:75` 的表头和 `queue_truth_scenario.cc:197` 的行值均为 v4，共 46 列，逐列顺序一致                                             |
| 严重-2：缺少包级队列状态与残差               | 已实质解决           | `queue_truth_scenario.cc:104`、`queue_truth_scenario.cc:112`、`queue_truth_scenario.cc:184`、`queue_truth_scenario.cc:222` 同步维护包状态并输出包残差 |
| 严重-3：放行错误拓扑、队列模型、上限和组标识 | 已实质解决           | `ns3_truth.py:353` 固定拓扑、模型、50p 和精确 `group_id`；对应负向测试存在                                                                            |
| 重要-1：跨层字段语义未隔离                   | 已实质解决           | qdisc 字段为 L3，设备和误码字段为 PPP 帧，接收端为应用负载；`queue_truth_scenario.cc:179` 的残差未混入 PPP 或应用负载                                 |
| 重要-2：夹具混算 PPP 与应用负载              | 已实质解决           | `test_ns3_truth.py:134` 和 `test_ns3_truth.py:135` 分别独立给值，不再互减                                                                             |
| 重要-3：七个追踪返回值未检查                 | 已实质解决           | `queue_truth_scenario.cc:442` 至 `queue_truth_scenario.cc:481` 对七次连接逐一终止式检查                                                               |
| 重要-4：配置没有实际对象回读                 | 已实质解决           | `queue_truth_scenario.cc:409` 至 `queue_truth_scenario.cc:421` 回读根队列规则、50p、设备队列 1p 和实际 DataRate 属性                                  |
| 重要-5：FIFO 入队前丢弃原因忽略              | 已实质解决           | `queue_truth_scenario.cc:122` 核对 `FifoQueueDisc::LIMIT_EXCEEDED_DROP`；`DropAfterDequeue` 只计量，不再次扣队列状态                                  |
| 重要-6：攻击尾部检查过弱                     | 已实质解决           | `ns3_truth.py:541` 要求所有攻击暴露窗 qdisc 接收字节和包均非零；`queue_truth_scenario.cc:484` 让流量持续至 12 秒                                      |
| 重要-7：未固定绝对时间轴                     | 已实质解决           | `ns3_truth.py:446` 固定第 i 窗为 `[0.1i, 0.1(i+1)]`，并继续检查字节与包队列连续                                                                       |
| 重要-8：关键负向测试不足                     | 已按预审列举类型补齐 | 字段缺失、119 窗、索引乱序、时间断裂、双队列连续、错误来源、缺少丢弃、非随机误码和包残差均有测试；本报告另指出 3 个未覆盖反例                         |

## 重点语义核对

- **46 字段与行值：**生成器表头 `queue_truth_scenario.cc:75` 至 `queue_truth_scenario.cc:89` 与行输出 `queue_truth_scenario.cc:197` 至 `queue_truth_scenario.cc:219` 一一对应，人工计数均为 46；验证器对字段顺序的漏检见重要-1。
- **量纲隔离：**L3 队列、PPP 帧丢弃、应用负载三个字节域名称明确；队列残差仅使用 L3 字节，未发现跨层相减。
- **守恒符号：**实现等价于 `Q_end - Q_start - received + dequeued + dropped_before = 0`；因为 `received = enqueued + dropped_before`，可化为 `Q_end - Q_start - enqueued + dequeued = 0`，符号正确。包级公式同理。
- **丢弃对状态的影响：**`DropBeforeEnqueue` 从未进入队列，只用于接收分解；`DropAfterDequeue` 对应已经出队的包，不再次扣减状态。当前处理正确。
- **回调与丢弃原因：**七个 `TraceConnectWithoutContext` 返回值均被检查；回调形态与本轮报告的 ns-3.48 编译成功证据一致。FIFO 原因常量比较使用 `FifoQueueDisc::LIMIT_EXCEEDED_DROP`。
- **配置回读：**检查针对安装后的 `queueDisc`、`routerDevice->GetQueue()` 和 `routerDevice` 的 `DataRate` 属性，不是只检查帮助器输入。
- **攻击末窗：**源应用停止时刻为 12 秒；验证器要求最后攻击窗存在 qdisc 入口。实现报告记录最后窗 581756 L3 字节、553 包，但本次审查未独立读取服务端 CSV。

## 验证情况与残余风险

- 已执行 `.venv/bin/black --check src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`，通过。
- 已执行 `.venv/bin/ruff check --no-cache src/flow_probe/ns3_truth.py tests/test_ns3_truth.py`，通过。
- 本机没有 `clang-format`，未独立执行 C++ 格式检查；只核对实现报告中的通过记录。
- 按仓库规则未在本机运行 pytest；服务端 38 项目标测试、179 项完整测试、ns-3 编译和两个真实冒烟未在本次独立审查中重跑。
- 实现报告所列服务端测试和冒烟目录没有同步到本地 `runs/ns3-data/`，本次无法独立回读日志与真实 CSV，只能把这些结果视为未复验的报告证据。
- 聚合 qdisc 入口无法区分良性源和攻击源；当前真实末窗总量明显高于良性负载，但验证规则本身只要求非零。这是既定简报验收条件的识别边界，不作为本轮新增问题。

## 批准条件

- 固定验证器表头顺序为 `CSV_FIELDS`，增加字段置换负向测试。
- 对队列丢弃和误码丢失逐窗检查字节/包零值一致性，增加跨窗口拼接反例。
- 检查首窗字节与包队列状态均为零，并检查所有起止包数不超过 50；增加对应负向测试。
- 修复后重新执行 Black、Ruff、服务端目标测试、完整测试、ns-3 编译和两个真实冒烟，再由独立审查确认。
