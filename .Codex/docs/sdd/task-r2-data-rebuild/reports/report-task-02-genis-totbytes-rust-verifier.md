# R2 任务 02R：GeNIS `TotBytes` Rust 逐包复算器报告

> **当前有效状态以本节为准。** 文末“历史构建快照”保留首次构建时的原始记录，其中“缺少输入”和“尚未正式运行”等状态已经失效，不得用于当前裁决。

## 终态结论

- **当前裁决：不能放行，状态为 `NO-GO / review_pending`。** 最终二进制已处理完 11 个 PCAPNG 成员并进入 3,973 条冻结候选的末端校验，但在一条流的 `Dur` 精度门禁处安全失败，未生成正式逐流、逐组或汇总制品。
- **诊断证据强烈支持 GeNIS `TotBytes` 是二层口径。** 失败样本的官方 `TotBytes=2588`，独立逐包复算得到二层 `2588`、三层 `2086`。这是一条诊断证据，不能替代任务要求的 3,973 条正式全量汇总。
- 已按主线程约束停止第四次修复、第四次构建和第四次全量运行。没有修改阈值、数据、冻结候选、成员映射或 Python 双物化路径。
- 本机正式输出目录和同名 `.partial` 目录均不存在，没有残留可被误认作正式结果的损坏制品。

## 终态冻结输入

| 输入 | 大小 | SHA-256 | 当前状态 |
| --- | ---: | --- | --- |
| `raw/datasets/GeNIS-2025/1-packets.zip` | 1,028,741,083 字节 | `1977cd7620e9f12adcb8b031d23974e229a690bbbaeda3d18828b27b79a007d3` | MD5 `5afbceaadfe3c3476f54723434d59b4a`；11 个 PCAPNG；ZIP 完整性通过 |
| `raw/datasets/GeNIS-2025/2-flows.zip` | 380,755,720 字节 | `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` | MD5 `063b7a2ec6e6b73cc302151d2b3ba6d7`；ZIP 完整性通过 |
| `thesis/experiments/llm_probe/runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl` | 3,728,545 字节 | `b39b60af6baec91e4586947e7e5a9fdba947419285a37f2ca9fd54cf241b56f3` | 10,000 行，GeNIS 候选 3,973 条 |
| `thesis/experiments/llm_probe/runs/data-audit/r2-genis-totbytes-rust-v1-inputs/member-map.jsonl` | 1,891 字节 | `1574de180e67e3f38b47f38c9115a9e26ee090943f56dc4688f6ef19c46407c4` | 11 行，唯一且完整覆盖两个归档 |

两份官方归档已从服务器受控拉取到本机，并完成大小、摘要和 ZIP 完整性校验。本轮没有再次拉取，也没有发现需要删除的损坏权威原始数据。

成员映射采用结果观察前冻结的确定性规则：去扩展名后按完全相同 basename 配对 10 组；两侧各仅剩一个成员时配对唯一残余项，即 `attack-bruteforce-ftp.csv` 与 `attack-bruteforce-ssh-ftp.pcapng`。没有按标签或比较结果调整映射。

## 终态执行身份

| 制品 | 大小 | SHA-256 |
| --- | ---: | --- |
| `thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/target/release/r2_genis_totbytes_verifier` | 4,377,312 字节 | `6bfa9443848d078a54af2ca56f4713f6f4f52a65c65c8856f0b6fc66a1aee049` |
| `thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/Cargo.lock` | 33,524 字节 | `8fb474555425d0e5b7f31cb05112135248050f854bba27eca9c56526a12f7e8f` |
| `thesis/experiments/llm_probe/runs/data-audit/r2-genis-totbytes-rust-v1-inputs/execution-code-lock.json` | 2,754 字节 | `2aeab4aa578fa93cc83c14ac63935a52e12155bd2d71b87b8d33786a313362af` |

最终代码锁记录 Git 提交 `527531f2f188de21489311259dbb5fcf4f1731ee`、`worktree_clean=false`、`review_pending`、Rust/Cargo 版本、`Cargo.toml`、`Cargo.lock`、全部 `src/` 文件和最终二进制摘要。工作树非净状态被显式记录，没有伪装为干净提交。

## 构建与三次运行失败链

### 构建阶段

1. 首次 `cargo build --release` 下载并锁定 142 个兼容软件包，但出现 7 个编译错误：`flow.rs` 5 处摘要更新方法歧义 `E0034`，`output.rs` 2 处 Arrow 布尔数组接口错误 `E0599`。
2. 主线程只授权修复这 7 处。补救构建通过，用时 59.81 秒，二进制 SHA-256 为 `3bfe9530c4c53a4409866f20adb827b34347a019a9fbca358430fd60ab93a0ab`。
3. 第一次运行暴露时间语义后，只进行获批的时间精度修复。构建通过，用时 44.43 秒，二进制 SHA-256 为 `c96f9f9b0295ddfda82f5b47de3ede3e86e087eebe2a24d7c1d9d0f912d1e78e`。
4. 第二次运行暴露 `Dur` 科学计数法兼容问题后，只增加十进制定点/科学计数法到整数纳秒的精确解析。最终构建通过，用时 1 分 10 秒，二进制 SHA-256 为 `6bfa9443848d078a54af2ca56f4713f6f4f52a65c65c8856f0b6fc66a1aee049`。
5. 第三次运行失败后没有再改代码或构建。

### 第一次运行：整数绝对时间被误当作精确边界

- 失败样本：`genis:a60bbca45e775a5218f941dee50d074aefb38a19e30b5ac75ab07323e6e138b4`。
- CSV 行：`Start=1739189477`、`Last=1739189481`、`Dur=4.020207`、`TotPkts=35`、`SrcPkts=18`、`DstPkts=17`、`TotBytes=2583`。
- 原实现按精确整数秒窗口只分到 26 包。独立逐包诊断确认同一连接共有 35 包，首包比 `Start` 早 381.014399 毫秒，末包比 `Last` 早 360.807251 毫秒，实际跨度为 4.020207148 秒。
- 根因是官方 `Start`、`Last` 只保留整数秒，而 `Dur` 保留微秒，绝对时间不能当作纳秒级精确边界。
- 失败版本代码锁：`execution-code-lock-failed-exact-time-v1.json`，SHA-256 `787a5df1aef4a5f902863bab3271f3eddbc4c000e75c9e09aa33024715fb4b56`。

### 第二次运行：`Dur` 存在科学计数法

- 全量 CSV 载入时安全失败，错误为 `Dur 秒字段不是整数`。
- 对 3,973 条冻结候选做只读格式审计：3,972 条是固定小数，1 条是 `6e-06`，位于 `attack-dos-slowloris.csv` 第 75,469 行。
- 根因是解析器只接受固定小数，没有接受等价的十进制科学计数法。
- 失败版本代码锁：`execution-code-lock-failed-duration-format-v2.json`，SHA-256 `598f804a026d94e4a67f984fe2d186e4e103783377dceef624397a0ad7790402`。

### 第三次运行：500 纳秒持续时间门禁过严

- 最终二进制处理完 11 个 PCAPNG 成员并进入 3,973 条候选末端验证。
- 失败样本：`genis:05769bc97f41c70f01b0d0da45be3443c97f8dfab712eb39f9885a9558cab819`。
- 失败信息：该样本首末包跨度与 `Dur` 的差异超过冻结的 500 纳秒容差。
- 主线程要求在第三个运行时语义问题后停止补丁链。此后只做只读诊断，没有修改代码、阈值、数据或代码锁，也没有发起第四次运行。

## 第三次失败样本的只读诊断

失败样本映射到 `2-flows/flows-10-sec/attack-bruteforce-ftp.csv` 第 25 行。整个 FTP CSV 中只有这一行具有相同规范五元组，没有相邻同五元组流记录。

| CSV 字段 | 值 |
| --- | --- |
| `FlowID` 的 SHA-256 | `ccf6f976d5b2f39e0e64d4d0c8762812d9ebd586d93f7cf92154c8a38bba8961` |
| `StartTime / LastTime / Dur` | `1739189481 / 1739189485 / 3.987493` |
| `TotPkts / SrcPkts / DstPkts` | `35 / 18 / 17` |
| `TotBytes` | `2588` |
| `Retrans / SrcRetra / DstRetra` | `0 / 0 / 0` |
| `Trans / Cause` | `1 / Start` |
| `Rank / Seq` | `9930 / 9889` |
| `NStrok` | 空值 |
| `RunTime / IdleTime` | `3.987493 / 1739991936.0` |

对 `1-packets/attack-bruteforce-ssh-ftp.pcapng` 独立只读解析得到：

| 指标 | 值 |
| --- | ---: |
| 时间窗口内包数 | 35 |
| 源向 / 目的向包数 | 18 / 17 |
| 二层字节总和 / 三层字节总和 | 2588 / 2086 |
| 官方 `TotBytes` | 2588 |
| 首包时间 | `1739189480.638225074` |
| 末包时间 | `1739189484.625718744` |
| 首包相对 `StartTime` | `-361,774,926` 纳秒 |
| 末包相对 `LastTime` | `-374,281,256` 纳秒 |
| 实际首末跨度 / CSV `Dur` | `3,987,493,670 / 3,987,493,000` 纳秒 |
| 实际跨度减 CSV `Dur` | `+670` 纳秒 |
| 最大相邻包间隔 | `974,956,964` 纳秒 |
| 超过 1 秒的相邻包间隔 | 0 |

包数和方向数完全一致，说明该样本的包身份与归属没有歧义。官方 `TotBytes` 与 PCAPNG 二层原始长度完全一致，与三层长度相差 502 字节。

670 纳秒差异小于 1 微秒，与源 PCAPNG 纳秒时间戳转换到 Argus/HERA 微秒字段时的截断区间一致。若两个端点分别截断到微秒，持续时间误差可落在严格小于 1 微秒的区间内，因此 500 纳秒门禁不能覆盖全部合法截断结果。该判断是基于观测的最小解释，不构成对生成器内部实现的未经验证断言。

其他解释已被当前证据削弱：三个重传字段均为 0；整个 FTP CSV 只有这一行使用该五元组；`Cause=Start`、`Trans=1`、持续时间不足 4 秒、最大包间隔小于 1 秒且没有超过 1 秒的间隔。`IdleTime=1739991936.0` 明显异常，但与原始包序列和当前流记录不一致，不能据此推断活动超时。

## 后续架构选择

1. **推荐：显式建模微秒截断区间。** 将 `Dur` 合法性从“与原始纳秒跨度相差不超过 500 纳秒”改为可审计的微秒量化区间，例如严格要求绝对差小于 1,000 纳秒，并在运行清单中记录语义。该方案改动最小且符合已观察证据，但属于语义合同变更，必须新建计划、冻结代码锁、独立审查并从头全量运行，不能作为本轮快速补丁。
2. **备选：由包边界生成权威连接清单。** 直接从原始包边界构造连接清单，再用 `TotPkts`、`SrcPkts`、`DstPkts` 和 `Start`、`Last`、`Dur` 的量化区间绑定 CSV。该方案减少对单一时间容差的依赖，但实现范围更大，需要新的架构设计和独立审查。
3. **保持当前严格门禁。** 继续保留 500 纳秒门禁，则任务维持 `NO-GO / review_pending`，不产生任何语义输出。这是当前实际状态。
4. **不得把单条二层证据当作全量结论。** 当前样本的 `CSV TotBytes = L2 != L3` 可作为设计决策证据，但不能替代 3,973 条逐流、逐组和总体 `summary.json`。

## 输出与清理终态

- `thesis/experiments/llm_probe/runs/data-audit/r2-genis-totbytes-rust-v1` 不存在。
- `thesis/experiments/llm_probe/runs/data-audit/r2-genis-totbytes-rust-v1.partial` 不存在。
- 三次失败均未留下可被下游消费的正式结果。
- 本机此前确认损坏的流归档和失败临时输出已清理；当前权威归档摘要与登记值一致，没有删除或覆盖它们。
- 第三次失败后没有执行构建、测试、阈值调整或全量复算命令。

## 终态验证

1. 两份官方 ZIP 的大小、MD5、SHA-256 和 ZIP 完整性已验证。
2. 候选清单行数、GeNIS 数量和 SHA-256 已验证。
3. 成员映射行数、唯一性、双侧完整覆盖和 SHA-256 已验证。
4. 最终二进制、`Cargo.lock`、最终代码锁和两个失败版本代码锁的大小与 SHA-256 已复核。
5. 最终全量运行读取 11 个 PCAPNG 成员并进入 3,973 条候选末端验证。
6. 失败样本的 CSV 唯一性、包数、方向数、首末时间、包间隔、二层字节和三层字节已做独立只读诊断。
7. 正式输出目录与 `.partial` 目录不存在性已复核。

---

## 历史构建快照（状态已失效，仅供追溯）

日期：2026-08-03

### 1. 当时结论

- **工具状态：发布构建已通过。** 已生成 ARM64 macOS 发布二进制和冻结 `Cargo.lock`。
- **语义状态：尚未执行正式全量裁决。** 本机目前只有官方 `2-flows.zip`，缺少正式运行必需的 `1-packets.zip`、冻结候选 JSONL 和冻结成员配对 JSONL。
- **字段状态：继续沿用既有 `NO-GO`，不能据本轮编译改成 `GO`。** 这里的 `NO-GO` 表示证据尚未闭合，不是本工具已经跑出不一致结果。
- 未修改 Python 双物化路径、冻结候选、任务 03 或训练制品，未启动训练。

### 2. 实现范围

新增独立 Rust 工具：

```text
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/
```

主要行为如下：

1. 对官方包、流、候选和成员配对四项输入执行普通文件、大小、MD5 与 SHA-256 门禁。
2. 流式读取两个 ZIP，不把归档整体或 PCAPNG 成员解压到磁盘，也不把完整成员载入内存。
3. 用单个可复用 PCAPNG 块缓冲区解析 Section Header、Interface Description、Enhanced Packet 和旧 Packet Block，显式处理字节序、时间分辨率、时间偏移、多接口、快照长度和块首尾长度。
4. 支持 Ethernet、RAW IP、Linux SLL、Linux SLL2、NULL、IPv4 和 IPv6 链路类型；未知链路类型直接失败。
5. 二层量固定为 PCAPNG `original_len` 之和；三层量固定为 IPv4 `total_length` 或 IPv6 `40 + payload_length` 之和。
6. 有界处理 IPv4/IPv6 分片。缺首分片、未闭合分片、巨型载荷、分片后扩展头、不可无损表示的亚纳秒时间或连接字段截断均直接失败。
7. 先用既有无标签 `sample_id` 公式回接 3,973 条冻结候选，再临时使用候选行的方向五元组和精确时间窗分包。地址、端口、场景名和标签不进入候选身份选择或输出。
8. 每条流同时核对 `TotPkts`、`SrcPkts`、`DstPkts`；重复、缺失、多义时间窗、未消费候选或方向不一致均直接失败。
9. 逐流和逐 `group_id` 输出 CSV `TotBytes`、二层值、三层值、整数差值、精确匹配布尔值、来源绑定哈希和行证据哈希。
10. 只有全部逐流和逐组三层值零容差精确一致时才输出 `GO`。二层全等只能登记为 `pcap_original_length_l2`，不能放行共同三层字节合同。
11. 输出先写同目录 `.partial`，失败时清理本次临时目录，成功后原子改名；既有正式目录拒绝覆盖。

完整输入模式、失败边界和命令见：

```text
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/README.md
```

### 3. 构建记录

#### 3.1 首次构建

执行命令：

```bash
cargo build --release
```

首次构建下载并锁定 142 个与 Rust 1.85 兼容的软件包，但生产模块编译失败，未产出二进制。错误只有两类：

- `flow.rs` 5 处 `SHA-256` 的 `update` 同时命中 `blake2::digest::Update` 与 `sha2::Digest`，产生 `E0034`。
- `output.rs` 2 处使用 Arrow 55 不提供的 `BooleanArray::from_iter_values`，产生 `E0599`。

没有隐藏该失败，也没有借助其他编译命令绕过门禁。主线程随后明确授权一次补救性发布构建，并把修复范围锁死为上述 7 处。

#### 3.2 最小修复与补救构建

仅执行以下修复：

- 5 处改为 `Digest::update(&mut hasher, ...)`。
- 2 处改为 `BooleanArray::from_iter(... Some(bool) ...)`。

补救命令仍为：

```bash
cargo build --release
```

结果：

```text
Finished `release` profile [optimized] target(s) in 59.81s
```

未出现警告或错误。没有执行第三次构建。

#### 3.3 构建制品

| 制品 | 大小 | SHA-256 |
| --- | ---: | --- |
| `target/release/r2_genis_totbytes_verifier` | 4,377,312 字节 | `3bfe9530c4c53a4409866f20adb827b34347a019a9fbca358430fd60ab93a0ab` |
| `Cargo.lock` | 33,524 字节 | `8fb474555425d0e5b7f31cb05112135248050f854bba27eca9c56526a12f7e8f` |

二进制格式：`Mach-O 64-bit executable arm64`。

### 4. 已执行验证

1. 补救性 `cargo build --release`：通过，无警告、无错误。
2. `target/release/r2_genis_totbytes_verifier --help`：通过，全部必填输入和固定默认上限可见。
3. `file target/release/r2_genis_totbytes_verifier`：确认 ARM64 macOS 可执行文件。
4. `shasum -a 256` 与 `wc -c`：登记二进制和锁文件摘要、大小。
5. `rg '[[:blank:]]+$' Cargo.toml Cargo.lock README.md src --line-number`：无输出，未发现行尾空白。
6. `unzip -Z1 raw/datasets/GeNIS-2025/2-flows.zip | rg '/flows-10-sec/.*\.csv$'`：确认 11 个 10 秒流 CSV 成员，名称覆盖 8 个攻击场景和 3 个良性场景。

按任务合同**没有运行 `cargo fmt`**，也没有使用合成包、抽样包或少量 CSV 声称语义通过。

### 5. 正式输入状态

#### 5.1 已到位

| 输入 | 本机路径 | 已知证据 |
| --- | --- | --- |
| 官方流归档 | `raw/datasets/GeNIS-2025/2-flows.zip` | 380,755,720 字节；MD5 `063b7a2ec6e6b73cc302151d2b3ba6d7`；拉取方已报告 `unzip -t` 全通过；固定 SHA-256 应为 `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` |

服务器来源：

```text
/root/autodl-tmp/thesis/datasets/GeNIS-2025/2-flows.zip
```

#### 5.2 尚缺

| 输入 | 要求 | 计划本机路径 |
| --- | --- | --- |
| 官方包归档 | 1,028,741,083 字节；MD5 `5afbceaadfe3c3476f54723434d59b4a`；必须补充实算 SHA-256 | `raw/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/1-packets.zip` 或主线程指定的等价源锁路径 |
| 冻结候选 | `train_candidate_approx10000.jsonl`；10,000 行中恰好 3,973 个唯一 GeNIS 标识；必须补充制品 SHA-256 | `thesis/experiments/llm_probe/runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl` |
| 成员配对 | 11 行；按两个归档内 PCAPNG 与 10 秒 CSV 的规范化同名规则确定性生成并冻结；必须补充 SHA-256 | 待主线程在白名单内指定 |

成员配对不得人工按标签或比较结果选配。当前已确认的 11 个流成员 basename 为：

```text
attack-bruteforce-ftp.csv
attack-bruteforce-smb.csv
attack-bruteforce-ssh.csv
attack-dos-hulk.csv
attack-dos-icmp.csv
attack-dos-pushack.csv
attack-dos-slowloris.csv
attack-dos-udp.csv
benign-admin-activity.csv
benign-background-activity.csv
benign-user-activity.csv
```

由于缺少 `1-packets.zip`，尚不能核对另一侧 11 个成员，也不能安全生成配对清单。

### 6. 正式运行与输出

输入到位后，从 `thesis/experiments/llm_probe/` 按 README 的冻结参数执行，正式输出固定为：

```text
runs/data-audit/r2-genis-totbytes-rust-v1/run_manifest.json
runs/data-audit/r2-genis-totbytes-rust-v1/flow_byte_comparison.parquet
runs/data-audit/r2-genis-totbytes-rust-v1/summary.json
runs/data-audit/r2-genis-totbytes-rust-v1/artifact_manifest.json
```

正式运行前必须先冻结：包归档 SHA-256、候选 SHA-256、成员映射 SHA-256、工具不可变版本和执行代码锁 SHA-256。任何一个值缺失时不得用全零、占位符或当前工作树猜测值启动。

### 7. 磁盘、时间与执行位置

- 两份压缩归档合计 `1,409,496,803` 字节，约 `1.31 GiB`。
- 服务器数据盘当前使用率 76%，仅余约 13 GiB。工具可以直接流式读取 ZIP，不需要解压副本；若把 ARM64 二进制同步到 Linux 服务器将无法运行，服务器侧必须使用 Linux 目标重新构建，这会改变工具链和二进制锁。
- 推荐路径：把缺失包归档和小型冻结清单通过带临时文件及摘要门禁的受控拉取放到本机，然后使用本轮 ARM64 发布二进制执行。这样不在服务器制造大型重复副本。
- 拉取期间若同时保留临时文件和正式文件，两份归档至少预留约 `2.63 GiB`；连同 Rust `target/`，本机建议预留不少于 `6 GiB`。
- 网络、磁盘和 PCAPNG 解压速度未实测。事前估计：包归档拉取 `10-60` 分钟，全量复算 `10-45` 分钟；最终以 `run_manifest.json` 实测为准。

### 8. 损坏数据清理规则

本机已有输入只要大小、官方 MD5、源锁 SHA-256 或 ZIP 完整性任一失败，就必须：

1. 先登记精确路径、实际大小和摘要。
2. 只删除该已确认损坏文件及本次失败拉取产生的临时文件。
3. 重新拉取到新的临时路径，全部校验通过后原子改名。
4. 不覆盖损坏文件后继续使用，不删除同目录其他权威原件，不制造服务器大型重复副本。

此前损坏的本机 `2-flows.zip` 已由上游任务清理；本报告没有再次删除或覆盖任何原始数据。

### 9. 变更文件

新增：

```text
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/Cargo.toml
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/Cargo.lock
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/README.md
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/archive.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/cli.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/flow.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/lib.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/main.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/model.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/output.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/packet.rs
thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/pcapng.rs
.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-02-genis-totbytes-rust-verifier.md
```

未修改现有 Python 源码、测试、配置、冻结制品、恢复文档或其他任务报告。
