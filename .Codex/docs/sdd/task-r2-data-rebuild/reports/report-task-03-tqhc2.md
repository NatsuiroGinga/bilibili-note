# 任务03：TQH 包序列、QUIC 线图像与聚合重算实现报告

## 状态

任务03本地实现已完成，等待新的独立审查代理做计划符合性和代码质量审查。正式服务器的 Black、Ruff 和 pytest 尚未执行，因此不能标记为服务器验收通过，也不能启动正式源物化或训练。

## 任务边界

本代理只新增任务03白名单中的以下文件：

- `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_tqhc2.py`
- `thesis/experiments/llm_probe/tests/test_r2_protocol_tqhc2.py`
- `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-03-tqhc2.md`

明确未修改：

- `thesis/experiments/llm_probe/configs/r2_protocol_data_v1.yaml`
- `thesis/experiments/llm_probe/src/flow_probe/r2_protocol_contract.py`
- `thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py`
- 旧候选构建器、A/B/C 制品、同步制品、运行脚本和服务器文件

任务01的配置与合同模块在工作树中仍为其他代理产生的未跟踪文件。本任务只读取和导入其已验收接口，没有改写。

## 实现内容

### 固定合同

- 基础包字段严格按计划第 3.4 节的 14 列顺序冻结。
- QUIC 附加字段严格按计划第 3.4 节的 25 列顺序冻结。
- 12 个基础聚合比例、9 个 QUIC 聚合量、传输族、协议真值和 QUIC 证据枚举直接绑定任务01合同常量。
- QUIC 解析器版本固定为 `flow_probe_quic_wire_image_v1`。
- Parquet 写入参数直接读取任务01的 `ParquetWriteSpec`，不在任务03另设可漂移参数。

### QUIC 线图像

- 复用旧 `tqh_c2.py` 的 `PcapFrame`、`iter_pcap` 和 `parse_ip_packet` 稳定接口。
- 长首部按首字节 `0x80` 位识别，读取四字节网络序版本、目的连接标识长度和源连接标识长度。
- 只有版本 `1` 且两个连接标识长度均不超过 20、可见载荷完整时，才按首字节 `0x30` 位解释 `INITIAL/0RTT/HANDSHAKE/RETRY`。
- 版本协商、未知非零版本、截断和无法完成的结构解析统一标为 `AMBIGUOUS`，未知版本的 v1 包类型适用掩码保持 0。
- 短首部只有在同一流式解析进程中已由可信 v1 长首部建立方向化上下文时，才标为 `CONTEXT_BOUND_SHORT_HEADER`。
- 固定位可以记录为 0 或 1，不作为拒绝条件；旋转位只在已绑定的 v1 短首部上下文中读取，绝不生成 RTT。
- 连接标识变化只输出布尔量；原始连接标识只保存在 `QuicConnectionContext` 的私有内存字典中，自定义 `repr` 只显示方向数量。
- 解析函数没有 `profile`、地址标签、端口规则或攻击标签输入。`profile=B` 及其他 profile 不能改变 QUIC 判定。

### 序列与聚合

- `PacketObservation` 在构造时检查主键、首包、非负时间、方向、网络层长度、载荷观测、TCP 标志适用性、布尔掩码、QUIC 枚举和解析器版本。
- `aggregate_packet_sequence` 要求单样本、`packet_index` 从 0 连续、相对时间不回退，并精确检查 `delta_time_us=floor(delta_ns/1000)`。
- 共同字段重算为包数、网络层字节总量/均值/最小/最大、包含首包零间隔的平均 IAT、包速率和字节速率；持续时间不正时两个速率为 `null` 且缺失掩码为 1。
- 12 个基础比例全部从包序列重算。无 TCP 包时五个 TCP 标志比例为 `null`，不以 0 伪装观测。
- QUIC 证据、固定位和旋转位比率以样本总包数为分母；连接标识变化比例只对存在同样本比较基准的包计算，连接标识长度只对实际可见包求均值。没有适用包时数值为 `null`，并写入同名缺失和适用掩码。
- 样本级 QUIC 证据按 `AMBIGUOUS > V1_LONG_HEADER > CONTEXT_BOUND_SHORT_HEADER > NONE` 归并。
- 旧基础序列哈希逐字节复现现有 TQH 候选算法；新序列哈希覆盖全部 39 个发布包字段并使用任务01规范 JSON 哈希。

### 大包表重组与落盘

- `materialize_tqhc2_sequences` 在扫描包表前冻结 `selected_ids`，每个 Parquet 行组只读取 14 个基础列并立即过滤目标样本。
- 过滤行按 `sha256(sample_id)` 进入固定 64 个稳定桶，单桶超过 200,000 行立即失败；桶写入使用固定 4,096 行缓冲，避免逐包 Parquet 小写入和过多文件描述符。
- PCAP 流式匹配回调只返回无敏感字段的包主键、时间、方向和 burst 信息；模块逐字段比较 PCAP 重算基础行与上游基础行。
- QUIC 安全观测与基础包分别分桶，再按 `(sample_id, packet_index)` 稳定排序连接；最终包表通过 64 路有界批量归并保证全局主键严格递增。
- PCAP 缺包、重复主键、基础字段不一致、旧哈希不一致、样本未唯一绑定 profile 或任务01枚举漂移均硬失败。
- 无受控配置或可信日志时，UDP 样本的 `protocol_target` 固定回退 `UNKNOWN`，即使来自 profile B 或出现 v1 线图像也不得自动写 `QUIC`。
- 只有显式 `TrustedProtocolTarget` 同时提供 `controlled_configuration|trusted_log` 与合法 SHA-256 时，才允许写入 `QUIC` 真值。
- 阶段输出固定为 `packet-observations.parquet`、`protocol.parquet`、`source-row-map.parquet` 和 `sequence-audit.json`。源映射只保留不可逆绑定哈希、旧/新序列哈希、解析器版本和可选真值证据哈希。

## 测试文件

`tests/test_r2_protocol_tqhc2.py` 当前包含 16 个测试函数，并通过参数化覆盖更多具体案例：

- 四种 v1 长首部类型
- 版本协商和未知版本
- 有/无上下文短首部
- 固定位随机化和旋转位
- 截断与连接标识变化
- 原始连接标识不进入记录或上下文表示
- 包主键、时间、方向、长度、TCP 标志、掩码和解析版本失败
- 共同字段、12 个基础比例、9 个 QUIC 聚合量和双哈希
- 持续时间不正时速率缺失
- `sample_id` 交错、跨非相邻行组和同一行组多样本的确定性重组
- profile B 无可信真值时不得生成 QUIC 目标
- 可信日志真值允许 QUIC 目标
- 上游旧基础序列哈希漂移硬失败

按照主代理明确约束，本机未运行 pytest。

## 静态验证

### 通过

1. 两个 Python 文件不写缓存的 AST 解析：退出码 `0`，输出 `ast-ok`。
2. 生产模块默认解释器导入：退出码 `0`，39 个包字段、60 个协议阶段字段和解析器版本均符合预期。
3. 项目 `.venv/bin/python -B` 加载生产模块和测试模块：退出码 `0`，输出 `imports-and-schema-ok`。
4. 使用真实 `configs/r2_protocol_data_v1.yaml` 构造任务01配置并执行 `_validate_bindings`：退出码 `0`。
5. 使用项目 PyArrow 构造包表、协议表和源映射模式，三份列顺序断言通过。
6. 纯函数 QUIC 检查：v1 长首部建立上下文、短首部读取旋转位、上下文表示不泄漏，退出码 `0`，输出 `quic-ok`。
7. 纯函数聚合检查：共同字段、UDP 比例、非 TCP 标志空值、QUIC 比例和双哈希断言通过，退出码 `0`，输出 `aggregate-ok`。
8. 版本回退检查：v1 类型适用，未知版本标为 `AMBIGUOUS` 且 v1 类型不适用，退出码 `0`，输出 `quic-version-mask-ok`。
9. `rg` 检查生产与测试文件中的调试输出、`TODO/FIXME` 和连接标识落盘模式：无匹配。

所有 Python 验证均设置 `PYTHONDONTWRITEBYTECODE=1` 并使用 `-B`，没有写入字节码缓存。

### 失败但未改代码

1. 默认系统解释器加载测试模块失败：`ModuleNotFoundError: No module named 'pyarrow'`。根因是系统解释器不是项目环境；生产模块本身可导入，项目 `.venv` 中相同加载随后通过。
2. `uv run --no-sync` 加载检查失败：现有 `pyproject.toml` 第 116 行附近存在重复 `tool.pyright` 节警告，同时沙箱拒绝初始化 `~/.cache/uv`。本任务白名单不允许修改 `pyproject.toml`，且要求不写缓存，因此没有请求安装、改配置或绕过缓存；改用现有 `.venv/bin/python -B` 完成等价只读导入检查。

## 未执行事项

- 未运行 Black 或 Ruff，遵守主代理“禁止格式化、只做 AST/导入/纯函数行为核验”的约束。
- 未在本机运行 pytest。
- 未执行真实 A/B/C 包表或 PCAP 物化。
- 未访问或修改同步中的 A/B/C 制品。
- 未运行服务器命令、实验或训练。
- 未提交 Git，未推送远程仓库。

## 风险与下一门禁

1. 实际 A/B/C PCAP 匹配器由调用方通过 `TQHPcapSource.match_packet` 提供。正式集成必须证明它逐包复现旧基础序列，并让模块的全字段比较和旧哈希门禁通过。
2. 本机没有执行写文件的微型物化测试；当前只验证了 AST、导入、模式和纯函数。计划中的 `tests/test_r2_protocol_tqhc2.py` 必须在服务器项目 `uv` 环境完整运行。
3. 服务器首次验收仍需按计划依次运行 Black、Ruff 和精确 pytest 文件；这些结果必须由后续审查或服务器执行报告补录。
4. 当前代码尚未经过独立审查代理。严重或重要问题必须由新的修复代理在任务03源码白名单内做最小修复，并重新审查。

## 修复轮次 1：独立审查严重与重要问题

日期：2026-07-31

本轮只修改任务03白名单中的生产文件、测试文件和本报告。两项建议未进入实现范围。

### 逐项状态

| 审查项 | 状态 | 修复与回归证据 |
| --- | --- | --- |
| 严重 1：筛选前解析与跨样本上下文污染 | **已修复** | `_read_quic_buckets` 先执行匹配器并拒绝未冻结样本，再解析 QUIC；`_QuicContextRegistry` 按冻结 `sample_id` 隔离上下文，样本上下文数以冻结集合为容量，单样本方向数固定上限为 64。新增“未选长首部不能为冻结短首部建上下文”“两个冻结样本复用同四元组仍隔离”“样本容量与方向容量硬失败”回归。 |
| 重要 1：截断与 v1 类型结构不完整 | **已修复** | 增加 QUIC 变长整数解码与四类 v1 类型结构门禁：Initial 检查 Token Length、Token、Length 和声明保护体；0-RTT/Handshake 检查 Length 和声明保护体；Retry 检查至少 16 字节完整性标签。空载荷截断、无上下文短首部截断、任何抓包截断、变长整数不完整、Token/Length 越界、保护体越界及 Retry 标签不足均回退 `AMBIGUOUS` 且不绑定。结构依据为 [RFC 9000 第 17.2.2 至 17.2.5 节](https://www.rfc-editor.org/rfc/rfc9000.html#section-17.2)。 |
| 重要 2：CID 未变化的伪零值 | **已修复** | `QuicConnectionContext.bind` 改为返回 `bool | None`；首个完整 v1 长首部建立上下文但写入 `None/observed=0`，已有同样本上下文时才比较为真或假。未知版本只在未截断、连接标识完整且已有同样本上下文时比较；任何截断都不比较。CID 变化比例只以实际可比较包为分母，不再把不可判定包当作零；其他 QUIC 比率继续遵守任务计划的样本总包数分母。新增首包、重复、变化、未知版本、截断和样本级聚合回归。 |
| 重要 3：可信协议真值只有自声明摘要 | **已修复** | `TrustedProtocolTarget` 不再接收任意摘要或证据类型，只引用证据逻辑路径；`TQHSourceBindings` 新增任务01 `SourceLock` 与运行时证据文件绑定。物化在创建阶段目录前检查源锁模式、数据版本、阶段、状态、配置摘要、逻辑路径、允许角色、阻塞状态、文件大小和 SHA-256，再检查证据模式、`controlled_configuration|trusted_log` 类型、显式输入字段允许清单、样本覆盖、profile 和目标映射。新增任意摘要、缺失锁项、`profile`/`binary_label` 派生、文件篡改、缺失样本、目标冲突和自声明类型失败回归；正向夹具使用最小锁定 JSON 证据。 |
| 重要 4：旧/新哈希测试同源 | **已修复** | 旧基础哈希新增测试内独立实现和硬编码黄金摘要 `71cec0...de05`，覆盖空载荷、非 TCP 空标志、布尔量和双包顺序，并逐一改变 12 个旧字段确认摘要变化。新 39 字段哈希新增硬编码黄金摘要 `254434...b2b7`，逐一改变全部 39 个发布字段，明确覆盖解析器版本。微型物化的旧期望哈希不再调用生产 `_legacy_sequence_sha256`。 |
| 重要 5：字段顺序与物理类型同源断言 | **已修复** | 测试内写死完整 14 个基础字段、25 个 QUIC 字段和 39 个发布字段黄金元组，并独立写死全部 PyArrow 物理类型；生产 `_validate_packet_field_order` 与 `_packet_schema` 增加精确 39 列门禁。新增删列、换位和任务01枚举顺序漂移失败回归。任务01配置当前没有包级 39 列字段清单，本轮受白名单限制未修改任务01；测试以已批准任务计划的完整字面量作为独立合同源。 |

### 建议项边界

1. **建议 1 延后：** 未把桶内排序改成外部排序，也未新增冻结数据最大桶容量证明；现有 200,000 行固定上限保持不变。
2. **建议 2 延后：** 未改变失败阶段目录清理或重试语义；由后续编排/发布任务单独处理。

### 修复后验证

1. 项目 `.venv/bin/python -B` 在 `PYTHONPATH=src` 下真实导入生产模块和测试模块通过，并与必要纯函数冒烟合并输出 `final-import-and-pure-smoke-ok`。
2. 纯函数冒烟覆盖四类合法长首部、13 组类型结构失败边界、四类抓包截断、未知版本 CID 比较、CID 三态聚合、双黄金哈希、39 字段逐字段变化、字段物理类型、枚举漂移和上下文固定容量。
3. 两个 PCAP 上下文隔离回归通过直接调用，输出 `final-context-isolation-smoke-ok`；未选样本和另一冻结样本均不能向目标样本传播同四元组上下文。
4. 最小任务01源锁、锁定证据 JSON、样本目标映射与摘要正向验真通过，输出 `final-trusted-source-lock-smoke-ok`。
5. 系统解释器真实导入失败于 `ModuleNotFoundError: No module named 'yaml'`；项目 `.venv` 的等价真实导入已通过，因此未修改代码或安装依赖。
6. 本地未发现 `pyright` 或 `basedpyright` 可执行文件，未临时联网安装；Pyright 留待服务器目标门禁。
7. 用户更新实验规则前曾完成一次抽象语法树解析且通过；该结果只作为历史记录保留。规则更新后已停止所有抽象语法树解析、预检和结构断言，且不再把它们作为当前验收门禁。

### 未执行门禁

- 按任务约束，本机未运行 pytest、Black、Ruff、格式化或真实 A/B/C 物化。
- 未运行服务器命令、训练、同步、提交或推送。
- 当前测试文件共有 31 个测试函数；完整参数化节点必须在服务器项目 `uv` 环境执行。

### 复审条件

修复轮次 1 已具备新的独立复审条件。复审应优先检查上下文过滤顺序、四类结构边界、CID 缺失分母、源锁证据不可伪造边界，以及黄金哈希和完整字段字面量是否真正独立；复审无严重或重要问题后，再执行服务器 Pyright、Black、Ruff 和精确 pytest 文件门禁。

## 正式本机物化进度

日期：2026-07-31

### 生产编排补齐

- 在任务03生产模块内增加正式 TQH 候选绑定入口。入口从冻结的 35,235 条候选读取 `profile`、`capture_id`、父会话、窗口边界、PCAP 摘要、提取器摘要和旧序列摘要；随后读取本机 A/B/C 原始 `conn.log` 与 36 个 PCAP，复现旧提取器的五元组、时间容差、方向、包序号和突发编号状态。
- 匹配器先保留原 cell 的全部会话参与歧义判定，再只输出冻结候选，避免过滤未选会话后把原本歧义的包错误分配给已选样本。
- 增加正式命令入口、逐 cell 进度日志和双物化比较入口。比较同时核对四项载荷的文件集合、字节数、SHA-256、Parquet 行数、列名与物理类型模式摘要，以及 Arrow 批语义摘要。
- Rust 重写未启动。现有 Python 解析、39 列模式、旧/新序列哈希和源合同已经存在，当前 48 GiB PCAP 逐包阶段实测不是需要立即重写的阻塞点；本轮继续使用 Python 保持合同一致性。

### build-a 首次失败

- 首次正式运行完成 36/36 个 PCAP 的实际 SHA-256、原始会话回接和逐包连接。A/B/C 上游包表分别保留 `1,027,418`、`1,323,888`、`124,423` 行，总计 `2,475,729` 行；PCAP 侧逐档计数完全相同。
- 首次运行在桶聚合时以 `TQHC2ProtocolError: 相邻包间隔或首包标志不符合时间序列` 退出。失败发生在 PCAP 基础字段已与上游逐字段相同之后，没有生成可用 Parquet；空阶段目录保留为 `runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.failed-attempt-1/`。
- 根因不是匹配错位。旧提取器独立计算两个时间字段：`relative_time_ns` 会把会话起点前、但仍处于 1 毫秒匹配容差内的包截断为 0；`delta_time_us` 使用相邻原始帧时间戳。旧提取器还允许 PCAP 时间戳回退，并把负间隔截断为 0。原聚合器错误地要求相对时间永不回退，并要求相邻相对时间总能精确推导间隔。
- 全量 `2,475,729` 行根因验证发现，起点截断造成的合法量化差在 A/B/C 分别为 `5,615`、`5,780`、`5,431` 处；时间戳回退分别为 `32`、`1,399`、`23` 处。按旧提取器合同验证后，三档违规数均为 `0`。
- 最小修复只改变聚合时间断言：时间回退要求间隔为 0；前一包相对时间为 0 时允许差值处于 1 毫秒匹配容差内；其余相邻包继续要求精确量化一致。没有修改任何发布字段、字段值、序列哈希、排序或样本选择。

### build-a 第二次失败与当前状态

- 第二次正式运行再次完成 36/36 个 PCAP 的源哈希、会话回接和逐包连接。A/B/C 分别保留 `1,027,418`、`1,323,888`、`124,423` 行，总计 `2,475,729` 行，与冻结上游候选包表完全一致。
- 时间字段合同修复已越过首次失败点，但在首个桶的序列聚合阶段以 `TQHC2ProtocolError: 旧基础序列哈希不匹配：004095237b3e9421cc40aa2daa84eaa58ad1e59167b0a60bb2f5aab29ce4bb09` 退出。完整控制台日志为 `runs/launchers/r2-tqhc2-materialization-build-a-20260731/attempt-2.log`。
- 当前没有四项正式 Parquet 制品，build-a 仍为失败状态；build-b 和双构建比较均未启动。不得把完成 PCAP 扫描误报成完成物化。
- 下一步先从冻结上游包表复现该样本的旧序列哈希并逐字段定位差异，不重新扫描 48.87 GiB PCAP；仅在查明单一根因并完成最小修复后重启 build-a。
- 第二次失败的根因已由冻结上游行组精确复现。候选生成器先读取含 UDP 空 `tcp_flags` 的整行组再连接目标样本，使同档所有非空 TCP 标志以浮点数进入历史 JSON 哈希；正式重建按整数语义编码，字段值相同但摘要不同。失败样本只把 `tcp_flags` 转为浮点编码后，计算结果即从 `bc810c...27f2` 精确变为冻结期望 `ea1806...a6b0`。
- A/B/C 候选各自均含 UDP 样本，三档候选的 `payload_observed_fraction` 最小值均为 `1.0`，因此兼容层只复现历史 `tcp_flags` 类型，不改变载荷长度或其他字段。生产修改仅位于旧哈希函数；发布包字段和覆盖 39 列的新序列哈希继续保持整数语义。
- 针对失败样本直接调用生产旧哈希函数已得到冻结期望摘要。第三次 build-a 已成功完成，日志为 `runs/launchers/r2-tqhc2-materialization-build-a-20260731/attempt-3.log`；运行内硬断言核对了全部 `35,235` 条样本和 `2,475,729` 个包。
- build-a 四项制品位于 `runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.partial/`：`packet-observations.parquet` 为 `17,446,431` 字节，SHA-256 为 `21168c943d7b9be043174a19cbde751c5cdb9c34b37e6902370998be88013991`；`protocol.parquet` 为 `2,691,245` 字节，SHA-256 为 `1c48b3437d5c17b0eb1524bc22856b1803b9dbb5d29b13b4f0593a7542b3560c`；`source-row-map.parquet` 为 `6,298,002` 字节，SHA-256 为 `7dd9a86875ab39f5e789fa54dd3fa8facd3684acbd8e9b63e1ae471b3038ab6e`；`sequence-audit.json` 为 `750` 字节，SHA-256 为 `28a83737757fd326a6218124bec48c363d0827cccf98f545dc94ec6089b97ed8`。
- 独立 build-b 已成功完成，使用全新空目录 `runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-b.partial/`，完整日志为 `runs/launchers/r2-tqhc2-materialization-build-b-20260731/launcher.log`。build-b 没有复用 build-a 的阶段文件；其 `35,235` 个样本、`2,475,729` 个包和四项制品 SHA-256 均与 build-a 相同。
- 双构建正式比较已通过，回执为 `runs/launchers/r2-tqhc2-double-materialization-compare-20260731/comparison.json`，状态为 `pass`，总载荷 Merkle SHA-256 为 `51deee4da715e234763c63e0aa061d20afb29ec37e7ffcdd487e936ef8b329cf`。
- 比较同时核对了精确文件集合、字节数、文件 SHA-256、Parquet 行数、模式摘要和 Arrow 批语义摘要。`packet-observations.parquet` 为 `2,475,729` 行，模式摘要 `22d9478e1e20c495d2e3bb97903bfeb483312d761a52f09a36f2ab90f30ec37f`、语义摘要 `793b53c9ef18e78e8275336e85fd7b07dcda9a60293a6167a161559a91e848bc`；`protocol.parquet` 与 `source-row-map.parquet` 均为 `35,235` 行。
- 任务03的数据派生和确定性双构建证据已经完成。由于任务01正式 `source-lock.json` 与执行代码锁仍未生成，两份构建继续保留 `.partial`，当前裁决为“派生通过、发布 NO-GO”；不得伪造正式移交清单或把任一目录改名为消费者正式根。

## 正式移交合同补齐

日期：2026-08-01

### 实现边界

- 未修改 PCAP 读取、会话匹配、QUIC 判定、序列重组、旧哈希兼容或聚合生产逻辑。
- 仅在既有双物化比较之后增加 `TQHHandoffLocks`、`TQHHandoffManifest`、`TQHHandoffReceipt`、`write_tqhc2_handoff`、`verify_tqhc2_handoff` 与正式 `handoff` 命令入口。
- 新增包装器 `scripts/run_r2_protocol_tqhc2_handoff.sh`，正式运行会重算 build-a/build-b 四项载荷的字节、模式、行数、Arrow 批语义与 Merkle，并逐项绑定 `source-lock.json`、`tqhc2-source-lock.jsonl`、`execution-code-lock.json`、配置和既有比较回执。
- 正式运行硬拒绝额外文件、符号链接、清单非规范字节、单字节变化、模式变化、A/C 状态提升、代码锁或源锁变化。全部门禁通过后才把 build-a 原子改名为规范移交根，保留 build-b，再生成清单并从规范根做本机消费验收。
- 本机正式参数为 `runs/launchers/r2-protocol-data-rebuild-v0/local-producer/tqhc2-handoff-params.json`，SHA-256 为 `55e73792789302314eb30c0766f8ffef9f8d1e927cead4cb36b7349bfd1bc255`；既有比较回执 SHA-256 为 `e7a54299b853ef81525f60c26c280b83d5360c28de1f5d1467ea995757aad296`。
- 两份包装器的集中 `bash -n` 门禁已通过；没有运行独立 Python 验收。
- 当前生产文件 SHA-256：`r2_protocol_tqhc2.py` 为 `51f1be08586437f74e6de26c0594b588dbb31726f2df4c12bc0bf474cf7794d4`，移交包装器为 `fa059973638a132c16e963cc8ea32ba1702f82578045c8032f9ff032fcd8b8a4`。这些值仍待正式提交后的执行代码锁绑定。

### 当前状态

- build-a/build-b 与比较回执仍保持原状态；规范移交根和正式移交清单尚未生成。
- 当前阻塞只来自正式源锁与执行代码锁尚未生成，不是双物化不一致。
- 按用户约束，本轮未重复物化、未格式化、未运行 Prettier、抽象语法树、独立真实导入、独立冒烟、pytest 或重复 Pyright。
