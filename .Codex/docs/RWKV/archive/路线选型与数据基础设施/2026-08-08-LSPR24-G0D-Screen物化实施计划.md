# LSPR24 开发宽表物化与快速实验计划

> **代理执行要求：**使用 `subagent-driven-development` 派发实现，具体编码执行 `daily-coding`。不使用测试驱动开发，不创建独立审查代理。

**目标：**只扫描一次 LSPR24 原始数据，生成覆盖前 80% 开发区的宽表、标签旁车和历史索引；前 60% 用于训练，随后 20% 用于验证，最后 20% 保持不可见。后续所有基线与 RWKV 机制候选直接复用这些制品并按列取数。

**架构：**Rust 物化器读取真实 Parquet 模式，按被防御端点和 5 秒窗口聚合全部合法字段。模型特征、标签、历史关系和字段谱系分别保存，候选只提交投影清单，不再重新物化原始数据；训练与验证按活动时间顺序切为 `60%/20%`，最终 20% 在方法冻结前不读取、不统计、不输出。

**技术栈：**Rust 2024、Rust 1.85 以上、Arrow/Parquet 55.2.0、Serde、SHA-256。

## 不可变边界

- 唯一原始数据是 LSPR24，源时间为 UTC 微秒，规范纳秒为 `checked_mul(1_000)`。
- `External_src/External_dst` 只接受 UTF-8 `"0"/"1"`；IP、端口、绝对时间、标签、IDS 和身份字段不得进入模型特征。
- 开发宽表只包含 `train` 与 `validation`：全局活动时间前 60% 为训练，随后 20% 为验证；`test` 为最后 20%，不生成任何特征、标签、成员、计数或哈希。
- 不采用随机 `8:1:1`：LSPR24 约 31.6 小时，10% 测试仅约 3.2 小时，时间相关窗口的有效样本量取决于独立事件而不是行数。训练区数据量已经充足，因此用 `6:2:2` 保留更稳定的验证与最终时间前向评价区。
- 所有候选共享同一窗口、字段清单、样本身份、历史索引、拆分和标签旁车。候选特有信息只能从宽表派生并绑定宽表哈希。
- 不创建或运行人工夹具、单元测试和集成测试；仅运行一次 Rust 编译检查，随后在 `GPU_SSH` 服务器用真实 LSPR24 物化和快速实验判断问题。
- 当前工作区有其他改动，只修改本计划列出的 LSPR24 Rust 文件和配置，不回滚或暂存其他文件。

## 唯一基础制品

- `views/development-wide.parquet`：每行一个“伪名端点 × 5 秒窗口”，包含全部合法聚合特征和非模型元数据。
- `views/development-labels.parquet`：以 `window_id` 关联的开发标签旁车。
- `views/history-index.parquet`：`H={1,4,16,32}` 的样本到有序窗口索引映射，特征不重复存储。
- `manifests/field-manifest.json`：字段组、源列、类型、聚合器、缺失规则、变换和生成目标标志。
- `receipts/development-wide-receipt.json`：输入、代码、合同、字段清单和四个基础制品的哈希、行数、时间范围及 `final_accessed=false`。

### Task 1：真实模式、微秒时间和端点语义

**状态：**已完成。生产代码提交为 `45a8a16aa63546d29afb3b0de2e89cecffa37e62`，编译检查通过，尚待真实数据物化验证。

**文件：**

- `tools/lspr24_g0/src/screen/mod.rs`
- `tools/lspr24_g0/src/screen/source.rs`
- `tools/lspr24_g0/src/lib.rs`
- `tools/lspr24_g0/src/formal_parquet.rs`

**验收：**生产入口只接受真实 UTF-8 外部标记、微秒时间和 `Int32/Int64/Float64` 数值列；非法值明确失败。只运行：

```bash
cargo check --manifest-path tools/lspr24_g0/Cargo.toml --locked
```

### Task 2：单次开发宽表物化

**文件：**

- 创建 `tools/lspr24_g0/src/screen/wide.rs`
- 创建 `tools/lspr24_g0/src/screen/history.rs`
- 创建 `tools/lspr24_g0/src/screen/output.rs`
- 创建 `tools/lspr24_g0/src/screen/config.rs`
- 创建 `tools/lspr24_g0/src/bin/lspr24_development_wide.rs`
- 修改 `tools/lspr24_g0/src/screen/mod.rs`
- 修改 `tools/lspr24_g0/Cargo.toml`

**接口：**

- `materialize_development_wide(config: &DevelopmentWideConfig) -> Result<DevelopmentWideReceipt, DevelopmentWideError>`。
- `DevelopmentWideConfig` 使用 `#[serde(deny_unknown_fields)]`，绑定原始 Parquet、合同版本与哈希、运行根和字段清单。
- 窗口固定为纪元对齐的左闭右开 5 秒窗口；数值字段按现有 `FieldManifestEntry/AggOp` 聚合。
- 标签旁车与特征分离；历史索引只保存窗口行索引；模型加载器依靠 Parquet 列裁剪读取候选所需特征。
- 所有输出排他发布；状态明确写 `screen_ready=true`、`formal_evidence=false`、`final_accessed=false`。

**执行：**

1. 实现全部合法字段的稳定窗口聚合和无流窗口。
2. 写出全局前 60% 训练区和随后 20% 验证区的宽表与标签旁车，并在列中记录 `split_name`；最终 20% 直接丢弃。
3. 从宽表一次生成 `H={1,4,16,32}` 历史索引。
4. 写字段清单和机器收据。
5. 运行一次：

```bash
cargo check --manifest-path tools/lspr24_g0/Cargo.toml --locked
```

### Task 3：服务器真实物化与快速实验

1. 白名单同步 Task 1/2 的 Rust 源码和配置到 `GPU_SSH` 指向的服务器。
2. 核验服务器身份、项目根、LSPR24 原始 Parquet、Rust、磁盘和内存。
3. 运行一次真实开发宽表物化，保存完整控制台日志、状态和制品哈希。
4. 直接复用宽表运行 HGB、XGBoost 和小型因果 Transformer 基线。
5. 按候选登记册依次运行 C3、C1、C6、C2 的种子 42 快速消融；每项只改变对应机制。
6. 依据真实指标和日志决定继续、修复或淘汰，不用文档审查替代实验。

## 完成条件

真实服务器生成四个基础制品且 `final_accessed=false`，至少一个传统强基线和一个小型因果 Transformer 能从同一宽表完成训练与评价，即可进入候选快速消融。
