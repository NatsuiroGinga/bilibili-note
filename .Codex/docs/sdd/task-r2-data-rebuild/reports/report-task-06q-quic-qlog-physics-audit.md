# 任务 06Q：QUIC qlog 物理辅助池审计报告

> **历史报告：** 本文记录旧版审计器与旧 59 条候选。独立复审后两项重要问题已经修复，旧候选已标记失效。修复版数据、代码锁和双审计证据见 `report-task-06q-quic-qlog-physics-audit-fix.md`；修复版工程状态仍为 `review_pending`。

> 完成日期：2026-08-03  
> 数据裁决：**GO，仅表示 QUIC 物理辅助池候选已冻结**  
> 工程验收：**review_pending，独立代码复审与先导物化并行，不阻塞后续运行**

## 结论

QUIC-MedNetCom 固定提交中的 89 个 qlog 已完成严格只读审计。59 条轨迹同时具备发送包号、ACK 范围、最新/最小/平滑 RTT、端点丢包、在途字节、拥塞窗口及可解释单位时序，进入 QUIC 物理辅助池候选；22 条非空轨迹未通过核心字段门禁，8 条为上游固定提交内的零字节占位。两次独立全量构建的 7 个输出文件在文件集合、字节数和 SHA-256 上完全一致，候选根已经原子发布。

数据中没有显式 PTO 事件。PTO 字段保持缺失掩码，不从丢包、时间间隔或其他恢复指标反推。该数据没有攻击标签，只能用于训练期 QUIC 物理监督，不能替代检测监督数据。

## 输入锁

- 原始根：`raw/datasets/QUIC-MedNetCom/`
- 固定提交：`f237a20360b83868a197488c5b557f53e4b7e53c`
- 普通上游文件：200 个，`695847525` 字节
- qlog：89 个，`630227334` 字节
- 上游零字节 qlog：8 个
- 清单 SHA-256：`ad4924be38968925ea0532d32e643709b40f7f852c863108cbd165addf4ecd61`
- `shasum -a 256 -c SHA256SUMS.codex.txt`：200 项全部通过
- `git fsck --full`：退出码 0
- Git 树额外包含 1 个 27 字节符号链接，不在 200 个普通文件清单内；固定提交锁使其不能静默变化。

原始目录未修改。H23Q 未下载、未读取，也未用于补字段或标签。

## 实现

新增 Rust 工具：

- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/Cargo.toml`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/Cargo.lock`
- `thesis/experiments/llm_probe/tools/r2_quic_qlog_audit/src/main.rs`

代码锁：

| 文件 | SHA-256 |
| --- | --- |
| `Cargo.toml` | `d685999b2badb8866c166c169268133d71b7ae52c659a8ac1f337d74675de74a` |
| `Cargo.lock` | `f49c0f8905c7216302182fd60cdd7592ae90687d91f3454f58667f5f56d3296b` |
| `src/main.rs` | `57137964833637462e36cd8fc5aa860bd5b95da784dda1d4436cd86ece9df309` |

实现边界：

- 使用 Serde 自定义访问器逐事件流式解析，每次只保留当前事件和单轨迹统计，不把完整 qlog 载入内存。
- 只显式接受 `transport:packet_sent`、`transport:packet_received`、`transport:connection_started`、`recovery:metrics_updated` 和 `recovery:packet_lost`。
- 包号空间只映射 `initial`、`handshake` 和 `1RTT`，其中 `1RTT` 规范化为应用数据包号空间。
- 事件时间和 RTT 使用十进制定点解析后乘 `1,000,000` 转为整数纳秒，不经过二进制浮点。
- 部署字段只保留相对时间、包间隔、方向、包长、窗口包数/字节数、速率及传输族适用性。
- 包号、ACK、RTT、端点丢包、在途字节、拥塞窗口和显式 PTO 仅为训练期特权真值。
- `group_id` 与原始连接标识只保存 SHA-256，不进入部署输入。
- 恶意标签始终为 `null`。

## 审计结果

| 项目 | 数量 |
| --- | ---: |
| qlog 总数 | 89 |
| 非空且成功解析 | 81 |
| 严格候选 | 59 |
| 排除 qlog | 30 |
| 候选事件 | 2,815,899 |
| 候选发送包 | 2,230,100 |
| 候选接收包 | 313,027 |
| ACK 帧 | 309,421 |
| ACK 范围 | 1,421,638 |
| 完整 RTT 状态 | 268,936 |
| 端点丢包事件 | 3,777 |
| 在途字节状态 | 268,936 |
| 拥塞窗口状态 | 268,936 |
| 显式 PTO 事件 | 0 |
| 候选原始字节 | 621,900,185 |

排除原因可以重叠：

- 8 条：上游零字节占位；
- 20 条：其他核心字段完整，但没有任何端点 `packet_lost` 真值；
- 2 条：过短连接，除没有端点丢包外，还缺 ACK、RTT、在途字节、拥塞窗口、Handshake 和应用数据包号空间。

清单中共有 6 组 qlog 与 `.json` 内容重复。5 组对应候选轨迹，已把 `.qlog` 固定为规范路径并记录 `.json` 别名；另 1 组是被排除的 `QUIC_1K_IT`，两种扩展名具有相同摘要且不会进入候选计权。没有同一轨迹重复进入物理池。

## 确定性先导子集

先导清单：`thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v0/pilot-traces.jsonl`

- 数量：16 条
- 原始字节：217,705,721
- 规则：先通过全部核心字段、单位和时序门禁并完成内容去重，再按规范内容 SHA-256 升序取前 16 条。
- 规则不读取攻击标签、模型结果、场景名或路径类别。
- 用途仅限开发集物理旁路先导，不得冒充最终 QUIC 物理辅助池。

## 双构建与发布

发布构建：

- 首次在线依赖解析在编译前失败：本机网络沙箱无法解析 `index.crates.io`。
- 单一根因修复：使用已缓存依赖执行 `cargo build --release --offline`。
- 发布构建成功：43.69 秒，退出码 0。
- 未运行格式化、Pyright、pytest、Prettier、冒烟、Clippy 或无关 Git 检查。

运行记录：

| 构建 | 耗时 | 峰值常驻内存 | 结果 |
| --- | ---: | ---: | --- |
| A | 9.150 秒 | 3,538,944 字节 | GO，59 条候选 |
| B | 9.063 秒 | 3,440,640 字节 | GO，59 条候选 |

第一次启动 A 时误用了项目根 `target/release/`，在进入数据处理前以 127 退出且未创建制品。改用 `tools/r2_quic_qlog_audit/target/release/` 后正式 A 运行成功；防复发规则已写入 `thesis/experiments/llm_probe/AGENTS.md`。

双构建比较：7 个文件的相对路径、字节数和 SHA-256 全部一致。

| 制品 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `source-lock.json` | 639 | `618b1ae2e99e8e1dbf8144ffa519998e656c77564fa7b062593219f8e30103ef` |
| `trace-manifest.jsonl` | 85,731 | `e0ce87e543167f1438d57e58990ea19d043a2a95ed7d3b7cf2cc06c8d83d95d2` |
| `excluded-traces.jsonl` | 10,127 | `1ce52fb3a653f7727df1ba2d70f307ae841b5a006f8cfd05de37370ee067de5c` |
| `field-coverage.json` | 694 | `a1c1f8dd279fcdfa1a51608ecd170e373187c69188d672b8571857e178272a14` |
| `unit-contract.json` | 2,431 | `01bac7cbf467432ad0b1ca2e48422b606b3b44d9430364ee0ff4384a729e8ad8` |
| `pilot-traces.jsonl` | 11,762 | `fcb36eee45a22dcbdc333618f9d4c0ae83f5c8651878b3c255982904c6c8b88a` |
| `audit-summary.json` | 707 | `d97cefe95ae3bc9d792d3bcdb662b9214a31bab61e5d3d56ad70f9cc52657f70` |

正式候选根：

- `thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v0/`

第二次确定性证据：

- `thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v0.build-b-verified/`

## 放行边界与下一步

本任务已经满足 QUIC 物理辅助池候选 `GO`。它不表示检测监督数据、共同观测模式、最终数据混合或 R2 大模型训练已经冻结。

下一步必须依次完成：

1. 将先导 16 条轨迹物化为与物理旁路实现兼容的窗口级观察和特权真值视图；
2. 与 GeNIS、TQH-C2、ns-3 的共同被动观测模式完成字段交集和专家适用掩码；
3. 只在冻结开发集运行 `A`、`A+P`、`A+P_shuffle`、`A+P_random`；
4. 物理旁路显示真实增量后，才进入 QUIC 专家与 R2 大模型联合训练。

H23Q 继续保持条件备选，不是上述步骤的依赖。

独立代码复审由主进程另建只读代理执行。复审完成前，候选的数据门禁保持 `GO`，工程结论标记为 `review_pending`；若复审发现影响结果有效性的严重或重要问题，当前候选必须转为无效并在最小修复后重新构建。
