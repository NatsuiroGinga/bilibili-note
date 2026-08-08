# TQH-C2 包级观测提取与审计实施计划

> **代理执行要求**：按仓库的子代理驱动开发规则实现并由新审查代理复核。项目规则禁止使用测试驱动开发；先实现确定性解析与审计，再补充固定夹具测试并在服务器运行精确测试。

**目标**：从官方 TQH-C2 `PCAP + conn.log + labeled.jsonl + manifest.json` 生成可追溯的临时主记录、无敏感字段包观测 Parquet、标签连接审计和来源哈希。

**架构**：使用 Python 标准库流式解析经典 PCAP、以官方 Zeek `uid` 对应的有向五元组和时间区间连接包记录、由候选协议公式生成稳定 `sample_id`。主记录保存标签和分组审计字段；模型包观测表只保存方向、网络层长度、载荷长度、相邻到达间隔、TCP 标志、突发编号与掩码。

**技术栈**：Python 3.10、`pandas`、`pyarrow`、`hashlib`、`struct`、`ipaddress`、JSON、Parquet。

## 全局约束

- 只读取原始 PCAP 和官方标签目录，不修改、覆盖或删除原始文件。
- 当前输出目录必须包含 `provisional`，文献协议最终验收前不得生成 `dataset-v1/freeze_manifest.json`。
- `sample_id` 不包含标签、划分、模型名或训练种子。
- 模型输入表禁止地址、端口、文件名、路径、cell、profile、capture、框架、加密配置和标签字段。
- 无法唯一连接的包或流必须计数并隔离，不得猜测标签。
- 不增加第四数据集，不启动训练，不上传原始 PCAP。

## 任务 1：标签与 cell 审计

**文件**：

- 新建：`thesis/experiments/llm_probe/src/flow_probe/tqh_c2.py`
- 修改：`thesis/experiments/llm_probe/pyproject.toml`
- 新建：`thesis/experiments/llm_probe/tests/test_tqh_c2.py`

**接口**：

- `audit_label_cell(cell_dir: Path) -> dict[str, object]`
- `audit_profile(labels_root: Path, pcap_root: Path, profile: str) -> dict[str, object]`

**步骤**：

- [ ] 校验 `manifest.json`、`conn.log`、`labeled.jsonl`、counts 和 gate 必须存在。
- [ ] 按逐流 JSONL 重计标签，校验 `uid` 唯一且与 `conn.log` 集合完全一致。
- [ ] 校验目录名、profile、interval、jitter、capture 元数据和 PCAP cell 一一对应。
- [ ] 将官方 counts 与逐流重计差异写入审计，但不得改写标签或官方文件。
- [ ] 用固定夹具覆盖 UID 缺失、重复、元数据冲突和 1.0.1 计数差异。

## 任务 2：经典 PCAP 流式解析与包连接

**文件**：同任务 1。

**接口**：

- `iter_pcap(path: Path) -> Iterator[CapturedPacket]`
- `parse_ip_packet(frame: bytes) -> ParsedPacket | None`
- `extract_cell(cell_dir: Path, pcap_path: Path, source_sha256: str, extractor_sha256: str) -> ExtractionResult`

**步骤**：

- [ ] 支持大小端、微秒和纳秒经典 PCAP，拒绝未知链路类型、截断记录和 PCAPNG。
- [ ] 解析以太网、VLAN、IPv4、IPv6、TCP、UDP 与 ICMP；非 IP 和无法读取端口的分片只计审计数量。
- [ ] 以有向五元组和时间区间唯一连接 Zeek 流；重用五元组时只接受唯一候选。
- [ ] 计算方向、相对纳秒、相邻到达微秒、网络层长度、载荷长度、TCP 标志、突发编号和掩码。
- [ ] 固定夹具验证正反方向、包长、载荷长、间隔、突发、无法连接和截断错误。

## 任务 3：稳定主键与临时 Parquet

**文件**：同任务 1。

**接口**：

- `build_sample_id(...) -> str`
- `write_provisional_dataset(result: ProfileExtraction, output_dir: Path) -> dict[str, object]`
- 命令入口：`flow-probe-process-tqh-c2`

**步骤**：

- [ ] 按候选协议规范 JSON 公式生成稳定 `sample_id` 和包含标签的 `record_sha256`。
- [ ] 写入 `master_records.parquet` 和 `views/packet_observations.parquet`。
- [ ] 写入 `schema.provisional.json`、`label_coverage.json`、`leakage_audit.json`、`source_checksums.json` 和 `run_manifest.provisional.json`。
- [ ] 对模型包观测表执行敏感字段拒绝清单，非零命中直接失败。
- [ ] 重跑同一夹具两次并比较 `sample_id`、行数和清单哈希。

## 任务 4：验证、审查与 C 临时物化

- [ ] 本机只运行 `py_compile` 和 C 的只读提取，不运行 `pytest`。
- [ ] 白名单同步源码、测试和 `pyproject.toml` 到服务器，不使用 `scp` 或 `rsync --delete`。
- [ ] 在服务器既有 `uv` 环境运行 `tests/test_tqh_c2.py` 精确测试。
- [ ] 由新审查代理检查正确性、标签泄漏、五元组重用、PCAP 边界和内存使用。
- [ ] 严重或重要问题修复后重跑精确测试；审查通过后物化 C 临时制品。
- [ ] 对 C 临时制品核对 Parquet 可读性、主键唯一性、包数守恒、连接覆盖率和敏感字段零命中。
