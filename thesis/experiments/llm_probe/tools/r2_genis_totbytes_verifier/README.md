# GeNIS `TotBytes` Rust 逐包复算器

## 用途与裁决边界

本工具只解决 R2 任务 02R 的一个问题：对冻结的 3,973 条 GeNIS 候选，从官方 `1-packets.zip` 逐包复算两种字节总量，并与官方 `2-flows.zip` 的 `TotBytes` 做零容差整数比较。

- `l2_wire_bytes`：每个 PCAPNG 包块的 `original_len` 之和。它对应送入 Argus 的捕获包原始长度，包含该接口链路类型在捕获记录中的链路头；不推断未被捕获的以太网帧校验序列、前导码或帧间隙。
- `l3_network_bytes`：IPv4 使用报头 `total_length`，IPv6 使用 `40 + payload_length`，再按流求和。
- 只有全部冻结流及全部派生 `group_id` 的 `l3_network_bytes == TotBytes`，`summary.json` 才输出 `GO`。
- 抽样一致、相关性、近似相等、二层一致或总量一致都不能得到 `GO`。

工具不会修改现有 Python 物化器、冻结候选或任何训练制品。本轮只编译工具与冻结输入合同；完整官方包归档到达本机前，不产生字段语义裁决。

## 冻结输入

正式运行必须同时提供以下四项非符号链接普通文件，并通过命令行传入相应 SHA-256：

| 输入 | 固定约束 |
| --- | --- |
| `1-packets.zip` | 精确大小 `1028741083` 字节；官方 MD5 `5afbceaadfe3c3476f54723434d59b4a`；SHA-256 由源锁回执提供 |
| `2-flows.zip` | 精确大小 `380755720` 字节；官方 MD5 `063b7a2ec6e6b73cc302151d2b3ba6d7`；SHA-256 `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` |
| 冻结候选 JSONL | 每行必须含字符串 `sample_id`；恰好包含 3,973 个唯一的 `genis:<sha256>` 标识 |
| 成员配对 JSONL | 恰好 11 行；精确覆盖归档内全部 10 秒流 CSV 与全部 PCAPNG 捕获成员 |

成员配对清单每行只能包含以下三个字段：

```json
{"schema_version":"flow_probe_r2_genis_member_map_v1","flow_member":"2-flows/flows-10-sec/<成员>.csv","packet_member":"1-packets/<成员>.pcapng"}
```

配对关系必须由官方归档目录与一手采集说明事先审计后冻结，不能按场景标签或运行结果临时选配。工具拒绝绝对路径、父目录分量、反斜杠、NUL、重复成员、符号链接成员、经典 PCAP 和不完整覆盖。

## 连接与隐私规则

冻结候选只通过既有无标签标识回接：

```text
old_sample_id = "genis:" + member_basename + ":" + csv_data_row_number_1_based
sample_id = "genis:" + sha256("dataset-candidate-genis-v0\0" + old_sample_id)
```

候选回接完成后，工具才在内存中读取该行的方向五元组和起止时间，把对应 PCAPNG 包归入该流。这些字段是逐包复算所必需的连接键，不参与冻结候选身份选择，不写入任何输出，也不作为标签、场景或采集单元捷径。`group_id` 精确复用 `BLAKE2b-128(trim(member_basename) + NUL + trim(FlowID))`。

官方 CSV 把 `StartTime` 与 `LastTime` 发布为舍入后的整数 Unix 秒，而 `Dur` 保留微秒。工具因此把每个整数秒解释为以前闭后开的 `中心值 ± 0.5 秒` 发布精度区间；这不是可调时间容差，正式参数 `time_tolerance_ns` 仍固定为 `0`。`Dur` 的固定十进制或科学计数法都通过整数尾数和十进制指数精确换算，不能精确落在整数纳秒的值直接失败。入选包的首包和末包必须分别回舍入到原始 `StartTime` 与 `LastTime`，且实际首末跨度与 `Dur` 的差值不得超过 `500 ns`。舍入区间重叠时直接失败。

同一成员内，相同规范五元组的候选舍入时间窗不得重叠。每条流复算后必须同时满足 `TotPkts`、`SrcPkts` 和 `DstPkts`，否则整次运行失败，不输出部分裁决。

## 解析失败边界

解析采用单个可复用 PCAPNG 块缓冲区和有上限的流、索引及分片表，不解压整份归档到内存。以下情况直接失败：

- 输入大小、MD5、SHA-256、成员覆盖或成员哈希不一致。
- PCAPNG 块损坏、首尾长度不一致、未知链路类型、多余简单包块或块超过配置上限。
- IP 报头、扩展头或传输层连接字段被截断，声明网络层长度超过 PCAPNG `original_len`。
- IPv6 巨型载荷、分片后扩展头、无首分片上下文、未闭合分片上下文或分片表超限。
- 候选重复、候选缺失、多流时间窗重叠、一个包多义归属、包计数或方向计数不一致。
- 正式输出目录或同名 `.partial` 目录已经存在。

非 IP 包会计数但不会进入候选流。发生写出错误时，工具清理本次新建的 `.partial` 目录；已经存在的正式目录和输入文件永不覆盖。

## 唯一发布构建

在本目录执行：

```bash
cargo build --release
```

任务合同禁止运行 `cargo fmt`。首次发布构建生成并冻结 `Cargo.lock`；后续正式执行应使用该锁文件与同一发布二进制。

## 正式运行参数

以下命令从 `thesis/experiments/llm_probe/` 执行。尖括号值必须来自源锁或代码锁回执，不能手填猜测值。

```bash
tools/r2_genis_totbytes_verifier/target/release/r2_genis_totbytes_verifier \
  --packet-archive /Users/bilibili/personal/note/raw/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/1-packets.zip \
  --packet-archive-sha256 <源锁中的1-packets.zip-SHA-256> \
  --flow-archive /Users/bilibili/personal/note/raw/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/2-flows.zip \
  --candidate-manifest runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl \
  --candidate-manifest-sha256 <冻结候选SHA-256> \
  --member-map <冻结成员配对JSONL路径> \
  --member-map-sha256 <成员配对清单SHA-256> \
  --output runs/data-audit/r2-genis-totbytes-rust-v1 \
  --tool-revision <40或64位不可变代码版本> \
  --execution-code-lock-sha256 <执行代码锁SHA-256> \
  --expected-candidate-count 3973 \
  --expected-member-count 11 \
  --time-tolerance-ns 0 \
  --max-pcapng-block-bytes 16777216 \
  --max-flow-bindings 10000 \
  --max-fragment-contexts 65536
```

禁止改变正式运行的候选数、成员数和时间容差来换取通过。内存上限只有在归档一手证据证明不足时才能事前修订并重新冻结代码锁。

## 正式输出

成功时以同文件系统原子重命名发布以下四项：

- `run_manifest.json`：工具版本、可执行文件大小与 SHA-256、工具链、输入锁、成员锁、包数、峰值内存、耗时、错误数和语义裁决。
- `flow_byte_comparison.parquet`：逐流及逐组的 CSV、二层、三层字节、整数差值、匹配状态和证据哈希。
- `summary.json`：二层与三层逐流、逐组精确匹配计数及最终 `GO` 或 `NO-GO`。
- `artifact_manifest.json`：前三项输出的大小和 SHA-256；自身哈希按声明排除。

逐行 `evidence_sha256` 计算时把该字段置空后序列化整行，因此不存在自引用哈希。

## 数据拉取与损坏清理

服务器规划路径：

- 已知流归档：`/root/autodl-tmp/thesis/datasets/GeNIS-2025/2-flows.zip`。
- 包归档计划路径：`/root/autodl-tmp/thesis/datasets/GeNIS-2025/1-packets.zip`。当前记录仍标为服务器缺失，必须先从官方 Zenodo 记录 `14919237` 获取并核验，不能假定已经存在。

本机目标统一放在：

```text
/Users/bilibili/personal/note/raw/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/
```

拉取必须先写临时文件，核对精确大小、官方 MD5 和源锁 SHA-256 后再原子改名。若本机已有文件未通过任一校验，应先登记路径、实际大小和摘要，再只删除该已确认损坏文件；不得覆盖后继续使用，也不得删除同目录其他原件。按两份归档合计 `1409496803` 字节计算，最终压缩原件约需 `1.31 GiB`，临时拉取期间至少预留双份空间；连同首次 Rust 发布构建，建议本机预留不少于 `6 GiB`。网络与磁盘速度未知时，拉取估计 `10-60` 分钟，首次构建估计 `5-20` 分钟，全量复算估计 `10-45` 分钟，正式回执以实测为准。
