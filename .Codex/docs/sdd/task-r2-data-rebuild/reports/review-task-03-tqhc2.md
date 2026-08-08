# 任务03独立审查：TQH 包序列、QUIC 线图像与聚合重算

## 结论

**请求修改，当前不允许进入服务器目标测试门禁。** 生产代码的公开接口和大部分静态字段合同与计划一致，但 QUIC 上下文在冻结样本过滤前被更新，并跨样本共用；这会让未选样本或另一条样本的长首部改变当前样本的短首部证据。另有五项重要问题涉及截断与结构冲突回退、连接标识变化的缺失语义、可信协议真值来源、旧哈希兼容测试和固定字段顺序测试。

服务器 Black、Ruff 和精确 pytest 应在严重与重要问题完成最小修复、新增回归测试并重新独立审查后执行。若仅为收集诊断证据而提前运行，其结果不能视为任务03放行证据。

## 审查范围与限制

- 已完整读取任务03实施计划、`configs/r2_protocol_data_v1.yaml`、任务03实现报告及适用规则。
- 已逐行审查 `src/flow_probe/r2_protocol_tqhc2.py` 和 `tests/test_r2_protocol_tqhc2.py`，并只读对照旧 `tqh_c2_candidate.py`、`tqh_c2_candidate_abc.py` 的序列哈希实现。
- 按任务约束，未在本机运行 pytest、Black、Ruff、格式化、物化或服务器命令。
- 本审查只新增本报告，未修改生产代码、测试、配置、旧制品或实现报告。

## 发现计数

| 级别 | 数量 | 放行影响 |
| --- | ---: | --- |
| 严重 | 1 | 必须修复并重新审查 |
| 重要 | 5 | 必须修复并补回归测试 |
| 建议 | 2 | 不单独阻塞，但应在正式大表物化前处理或登记边界 |

## 严重问题

### 严重 1：QUIC 上下文在样本筛选前更新，并在整个 PCAP 内跨样本共用

**证据：** `src/flow_probe/r2_protocol_tqhc2.py:1197` 为每个 PCAP 只创建一个 `QuicConnectionContext`；`src/flow_probe/r2_protocol_tqhc2.py:1204` 在调用匹配器和检查 `selected_ids` 之前解析并更新上下文，过滤直到 `src/flow_probe/r2_protocol_tqhc2.py:1205` 至 `src/flow_probe/r2_protocol_tqhc2.py:1207` 才发生。上下文只以方向化四元组为键，不含 `sample_id`。

**影响：** 未冻结样本的可信长首部可以为冻结样本建立短首部上下文；两个复用相同四元组的冻结样本也会互相污染。结果会错误改变 `CONTEXT_BOUND_SHORT_HEADER/AMBIGUOUS/NONE`、连接标识变化、旋转位和九项 QUIC 聚合量，违反“只处理冻结 `sample_id`”、样本隔离和可信上下文门禁。当前测试的两个样本使用不同地址和端口，无法证伪该问题。上下文还会持有整个 PCAP 中所有 UDP 流的原始连接标识，内存上界不再由冻结样本集合约束。

**最小修复条件：**

1. 先调用匹配器并拒绝未命中或不在冻结集合中的包，再允许该包读取或更新 QUIC 上下文。
2. 上下文至少按冻结 `sample_id` 隔离；若要跨样本共享，必须有独立、不可逆且已证明一对一的连接身份合同，不能只用四元组。
3. 增加两个回归测试：未选样本长首部后出现冻结样本同四元组短首部；两个冻结样本复用同四元组。两者都不得继承其他样本上下文。
4. 增加上下文容量断言，证明容量受冻结样本或明确的固定上限约束。

## 重要问题

### 重要 1：截断和 v1 类型特定结构不完整时未统一回退 `AMBIGUOUS`

**证据：** `src/flow_probe/r2_protocol_tqhc2.py:457` 至 `src/flow_probe/r2_protocol_tqhc2.py:461` 对空的已截断 UDP 载荷返回 `NONE`；`src/flow_probe/r2_protocol_tqhc2.py:474` 至 `src/flow_probe/r2_protocol_tqhc2.py:477` 对无上下文短首部忽略截断状态；`src/flow_probe/r2_protocol_tqhc2.py:541` 至 `src/flow_probe/r2_protocol_tqhc2.py:560` 只要读取到源连接标识末尾，就把版本 1 长首部标为 `V1_LONG_HEADER`，没有验证该类型必需的后续结构。测试辅助函数 `tests/test_r2_protocol_tqhc2.py:71` 至 `tests/test_r2_protocol_tqhc2.py:87` 恰好只生成到源连接标识末尾，现有测试因此把结构不完整报文固定成成功样例。RFC 9000 第 17.2.2 至 17.2.5 节定义了各 v1 长首部类型的必需后续字段：[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html#section-17.2)。

**影响：** 抓包截断或仅具有类似 QUIC 前缀的普通 UDP 载荷会被降为 `NONE` 或升级为可信 v1 长首部，进而建立错误上下文并污染协议观测。

**最小修复条件：** 明确定义四种 v1 类型的最小可见结构检查；任何抓包截断、变长整数不完整、长度越界、Retry 完整性标签不足或其他结构冲突都回退 `AMBIGUOUS` 且不得绑定上下文。为每种类型增加恰好截断在各边界前后的测试，并增加空载荷截断、无上下文短首部截断测试。

### 重要 2：未知版本或截断长首部无依据地写入“连接标识未变化”

**证据：** `src/flow_probe/r2_protocol_tqhc2.py:546` 至 `src/flow_probe/r2_protocol_tqhc2.py:552` 在版本不是 1 或抓包截断时固定写入 `quic_cid_changed=False`、`quic_cid_changed_observed=True`，但该分支既没有查询既有上下文，也没有完成可信绑定。`src/flow_probe/r2_protocol_tqhc2.py:679` 至 `src/flow_probe/r2_protocol_tqhc2.py:686` 随后会把这个伪造零值纳入样本总包数分母。版本协商与未知版本测试只检查证据类别和版本，不检查该字段的值、观测与适用掩码。

**影响：** 不可判定被编码成观测到的零，系统性压低 `quic_cid_changed_packet_fraction`，破坏九项 QUIC 聚合的 missing/applicable 语义。

**最小修复条件：** 只有在两个可比较连接标识均完整可见且存在合同允许的同样本上下文时，才写 `observed=1`；否则写 `None/observed=0`，并按合同决定 `applicable`。新增版本协商、未知版本、首个长首部、已有上下文、各截断边界的值与掩码测试，并验证样本级聚合不把不可判定值当成零。

### 重要 3：可信协议真值门禁只验证自声明字符串和任意 SHA-256，无法证明来源不是 profile 或标签

**证据：** `src/flow_probe/r2_protocol_tqhc2.py:1246` 至 `src/flow_probe/r2_protocol_tqhc2.py:1265` 只检查 `evidence_kind` 是否为两个允许字符串、摘要是否为 64 位小写十六进制，以及目标与传输族是否表面一致；它不核对摘要是否属于任务01源锁中的受控配置或可信日志。正向测试 `tests/test_r2_protocol_tqhc2.py:501` 至 `tests/test_r2_protocol_tqhc2.py:509` 直接对 `truth:<sample_id>` 求哈希即可签发 `QUIC`，没有任何证据制品。

**影响：** 调用方可以依据 `profile=B`、标签或任意规则构造目标，再附上任意格式正确摘要，仍通过训练真值门禁。这样产生的 `protocol_target` 不能作为可信训练真值。

**最小修复条件：** `TrustedProtocolTarget` 必须引用任务01已锁定且可复核的证据清单条目；物化时验证证据制品摘要、允许的证据类型、样本覆盖和目标映射，且该映射的输入字段清单明确排除 profile、标签、cell 和端口。新增任意摘要、缺失锁条目、profile 派生、标签派生和篡改证据均拒绝的测试；正向测试必须加载真实或最小锁定证据清单，而不是自声明摘要。

### 重要 4：旧基础序列哈希测试使用被测实现生成期望值，不能证伪兼容性漂移

**证据：** 生产实现 `src/flow_probe/r2_protocol_tqhc2.py:659` 至 `src/flow_probe/r2_protocol_tqhc2.py:672` 静态看来与旧候选构建器的 12 字段逐行 JSON 哈希一致，但测试 `tests/test_r2_protocol_tqhc2.py:338` 只断言结果等于同一个私有函数；微型物化夹具 `tests/test_r2_protocol_tqhc2.py:485` 至 `tests/test_r2_protocol_tqhc2.py:500` 也用同一个函数生成 `expected_base_sequence_sha256`。因此字段顺序、空值规范化或换行规则在生产函数中同步漂移时，所有测试仍会通过。

**影响：** “旧基础哈希与新增解析哈希分离”虽然列上已经实现，但旧哈希逐字节兼容门禁没有独立测试证据。

**最小修复条件：** 增加至少一个由旧 `tqh_c2_candidate.py` 或已冻结真实制品独立产生并硬编码的黄金向量，覆盖空载荷、非 TCP 空标志、布尔值和多包顺序；固定断言精确 SHA-256，并逐一改变 12 个基础字段确认哈希变化。新哈希另用独立黄金向量验证 39 个发布字段和解析器版本。

### 重要 5：QUIC 精确字段顺序和跨任务合同测试存在同源断言

**证据：** `tests/test_r2_protocol_tqhc2.py:141` 至 `tests/test_r2_protocol_tqhc2.py:177` 对基础字段写了精确元组，却只检查 `len(QUIC_PACKET_FIELDS) == 25`；物化测试 `tests/test_r2_protocol_tqhc2.py:529` 至 `tests/test_r2_protocol_tqhc2.py:531` 只把生成模式与同一生产常量比较。`_validate_bindings` 在 `src/flow_probe/r2_protocol_tqhc2.py:1455` 至 `src/flow_probe/r2_protocol_tqhc2.py:1473` 校验聚合字段和枚举，但不校验 25 个 QUIC 包字段的固定顺序。生产代码当前手工对照计划是正确的，但常量与模式一起漂移时测试无法失败。

**影响：** 任务03要求的固定列顺序、任务01合同一致性和下游哈希稳定性没有独立可证伪的门禁。

**最小修复条件：** 在测试中写出完整 25 列黄金元组及完整 39 列发布顺序，独立断言 Parquet 物理类型；若任务01配置继续作为正式合同源，还应提供并校验对应字段顺序，而不是仅校验数量。增加删除、换位和枚举顺序漂移会失败的参数化测试。

## 建议

### 建议 1：把分桶内排序改为真正的流式外部排序，或证明固定上限覆盖冻结数据

`src/flow_probe/r2_protocol_tqhc2.py:1221` 至 `src/flow_probe/r2_protocol_tqhc2.py:1228` 会把一个桶完整转为 Python 字典列表，`src/flow_probe/r2_protocol_tqhc2.py:1281` 至 `src/flow_probe/r2_protocol_tqhc2.py:1285` 同时持有基础侧和 QUIC 侧两个完整列表。当前 200,000 行硬上限虽给出常数界，但没有来自配置或冻结清单的容量证明，合法偏斜桶会直接失败。建议采用有界排序分片和流式双路连接，或在正式源预检中冻结最大桶计数并证明峰值内存可接受；增加接近上限和超过上限的确定性测试。

### 建议 2：失败清理应允许同一阶段目录安全重试

`src/flow_probe/r2_protocol_tqhc2.py:1491` 至 `src/flow_probe/r2_protocol_tqhc2.py:1493` 拒绝任何已存在目录，但异常路径 `src/flow_probe/r2_protocol_tqhc2.py:1605` 至 `src/flow_probe/r2_protocol_tqhc2.py:1613` 只删除顶层 `*.partial` 和桶目录，可能留下已完成命名的包表或协议表。建议失败时写明确失败回执并由编排器安全清理整个未发布阶段，或让函数识别自己的不完整标记后可恢复；不得把残留阶段误当成完成制品。

## 已确认符合计划的部分

- 文件范围符合任务03白名单；未发现旧 `tqh_c2.py`、配置或旧制品被任务03实现改写。
- 三个公开接口名称和参数形状符合计划。
- 基础 14 列和 QUIC 25 列当前手工对照计划一致；传输族、协议目标、QUIC 证据枚举和聚合字段复用任务01常量。
- `packet_index` 连续、首包、时间不回退、方向、网络层长度、TCP 标志适用性和样本内单一传输族均有生产门禁。
- 共同字段、12 项比例和 9 项 QUIC 聚合按固定顺序生成；非 TCP 的 TCP 标志比例使用空值，QUIC 聚合具备同名 missing/applicable 列。
- 旧基础序列哈希、新 39 字段解析哈希和解析器版本分别落入源映射列，没有静默覆盖旧哈希。
- 发布表和临时 Parquet 模式中未发现原始连接标识列；上下文表示也不输出原始连接标识。
- 上游包表先按冻结 ID 做列裁剪和过滤，最终输出按 `(sample_id, packet_index)` 全局严格递增；交错样本和跨非相邻行组已有正向物化测试。

## 放行条件

1. 严重 1 与重要 1 至 5 全部完成最小修复和对应回归测试。
2. 新的独立审查确认上下文隔离、可信真值来源和黄金哈希/字段顺序测试可实际证伪。
3. 再在服务器依次运行计划固定的 Black、Ruff 和 `pytest -q tests/test_r2_protocol_tqhc2.py`；三者全部成功后，才允许任务06消费任务03输出或启动正式 TQH 源物化。
