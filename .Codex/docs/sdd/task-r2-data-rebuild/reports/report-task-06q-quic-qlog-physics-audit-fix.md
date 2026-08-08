# 任务 06Q：QUIC qlog 物理辅助池审计器复审修复报告

> 更新日期：2026-08-03  
> 数据门禁：**GO**  
> 工程状态：**`review_pending`，修复后的独立代码复审尚未完成**

## 结论

独立复审指出的两项重要问题已经完成最小修复。审计器现在按 `initial`、`handshake` 和 `application_data` 分别维护本观察端点与对端的包号和时间历史。ACK 关系继承承载包的方向、包号空间和事件时间，只有范围内所有包均属于相反方向的同空间先前包集合时才有效；`packet_lost` 只有能关联本端同空间先前发送包且时间不早于发送事件时才有效。

解析器登记的核心字段、单位、观察点、ACK 和时序异常已经进入硬门禁。候选与排除制品同时输出分空间关系计数、首次有效关系时间、允许缺失掩码、允许缺失计数及核心异常清单。

修复后两次全量审计均得到 59 条候选、30 条排除 qlog 和 16 条确定性先导。候选包含 1,421,638 条有效 ACK 关系和 3,777 条有效丢包关系；无法关联 ACK、无法关联丢包和候选核心异常均为 0。两次审计的七类制品在文件集合、字节数和 SHA-256 上完全一致。

旧版 59 条候选未删除，但已添加失效标记。修复版数据门禁为 GO；新的独立代码复审通过前，工程状态保持 `review_pending`，不得写入论文最终结论。

## 根因与修复

旧版 `observe_packet` 在调用 ACK 解析前没有保留承载方向、包号空间、事件时间和包历史，`observe_ack_frame` 因而只能检查范围格式。`observe_packet_lost` 同样只能检查字段存在。旧版 `TraceAudit.issues` 只收集异常，不参与 `core_gate_failures`，候选制品也没有异常清单。

修复版增加：

- 按方向和包号空间维护包号、事件时间及事件顺序；
- 使用连续包号区间索引验证 ACK 整个闭区间，避免按大范围逐个枚举；
- 对发送 ACK 使用对端已观察包集合，对接收 ACK 使用本端已发送包集合；
- 同时验证包已在关系事件前出现，且包时间不晚于关系事件；
- 对丢包验证本端同空间先前发送包；
- 分空间输出有效、无法关联及首次有效关系时间；
- 候选至少具有应用数据空间有效 ACK、至少一条有效丢包，且所有无法关联计数为 0；
- 把核心字段、单位和时序异常全部接入硬门禁并输出异常清单。

允许缺失只保留为显式状态。ACK 延迟不是核心 RTT 真值，输出可用性、完整性和缺失帧数；源数据没有显式 PTO，输出轨迹级缺失掩码，不推测或零填充。

## 输入与代码锁

- 原始根：`raw/datasets/QUIC-MedNetCom/`
- 固定提交：`f237a20360b83868a197488c5b557f53e4b7e53c`
- 普通上游文件：200 个，`695847525` 字节
- qlog：89 个，`630227334` 字节
- 上游零字节 qlog：8 个
- 清单 SHA-256：`ad4924be38968925ea0532d32e643709b40f7f852c863108cbd165addf4ecd61`
- 原始目录未修改；H23Q 未下载、未读取、未用于补字段或标签。

| 文件 | SHA-256 |
| --- | --- |
| `Cargo.toml` | `d685999b2badb8866c166c169268133d71b7ae52c659a8ac1f337d74675de74a` |
| `Cargo.lock` | `f49c0f8905c7216302182fd60cdd7592ae90687d91f3454f58667f5f56d3296b` |
| `src/main.rs` | `aba88b492c0fce0604d9a7e0cbc595fcdcc7c6f7db8850786a378fd43633abb8` |

唯一一次发布构建使用 `cargo build --release --offline`，耗时 26.49 秒，退出码 0。macOS 构建报告 Linux 条件分支使用的 `bail` 为未使用导入；该警告不影响二进制生成或运行。

## 修复后审计结果

| 项目 | 数量 |
| --- | ---: |
| qlog 总数 | 89 |
| 非空且成功解析 | 81 |
| 严格候选 | 59 |
| 排除 qlog | 30 |
| 候选事件 | 2,815,899 |
| 候选发送包 | 2,230,100 |
| 候选接收包 | 313,027 |
| 原始 ACK 范围 | 1,421,638 |
| 有效 ACK 关系 | 1,421,638 |
| 无法关联 ACK 关系 | 0 |
| 完整 RTT 状态 | 268,936 |
| 原始端点丢包事件 | 3,777 |
| 有效丢包关系 | 3,777 |
| 无法关联丢包关系 | 0 |
| 在途字节状态 | 268,936 |
| 拥塞窗口状态 | 268,936 |
| 候选核心异常 | 0 |
| 显式 PTO 事件 | 0 |

| 包号空间 | 有效 ACK | 无法关联 ACK | 有效丢包 | 无法关联丢包 |
| --- | ---: | ---: | ---: | ---: |
| `initial` | 118 | 0 | 0 | 0 |
| `handshake` | 110 | 0 | 0 | 0 |
| `application_data` | 1,421,410 | 0 | 3,777 | 0 |

59 条候选共有 237 个 ACK 帧没有可独立解释的 ACK 延迟，59 条轨迹均没有显式 PTO。二者均通过掩码和计数保留，没有进入部署输入，也没有被推测。

排除原因与旧版数据分布一致：8 条是上游零字节占位；20 条缺少端点丢包；另外 2 条过短连接同时缺少 ACK、RTT、在途字节、拥塞窗口、Handshake 和应用数据包号空间。排除原因允许重叠。

## 先导与双审计

修复版先导仍为 16 条。修复前后先导的内容 SHA-256 序列和规范路径序列完全一致。选择规则仍为：先通过全部字段、单位、时序和关系门禁，完成内容去重，再按规范内容 SHA-256 升序取前 16 条；不读取攻击标签、模型结果、场景名或路径类别。

- A：`thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v1-ack-semantics-gate-review-pending.build-a/`
- B：`thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v1-ack-semantics-gate-review-pending.build-b/`

| 构建 | 耗时 | 峰值常驻内存 | 结果 |
| --- | ---: | ---: | --- |
| A | 16.691 秒 | 10,223,616 字节 | GO，59 条候选 |
| B | 16.697 秒 | 10,256,384 字节 | GO，59 条候选 |

七类数据制品的相对路径集合相同；`diff -rq` 没有输出。两目录对应制品的字节数和 SHA-256 逐项相同：

| 制品 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `source-lock.json` | 639 | `618b1ae2e99e8e1dbf8144ffa519998e656c77564fa7b062593219f8e30103ef` |
| `trace-manifest.jsonl` | 145,402 | `f9996195a163d378c625a024168138caa9bc990a26fb7da50ac31fc5f3d9560f` |
| `excluded-traces.jsonl` | 30,990 | `560deb6293b8ebe7ef1a6beeba6f70bbf5d64a1c2df3a99ba226b4ae071de136` |
| `field-coverage.json` | 936 | `2e0e0e99f614c12ba2f6fa367d5869801790387f8de0281873fd5cace0c12e42` |
| `unit-contract.json` | 2,431 | `01bac7cbf467432ad0b1ca2e48422b606b3b44d9430364ee0ff4384a729e8ad8` |
| `pilot-traces.jsonl` | 26,637 | `7bc03995014b89cbc5f985437affc64dd56b2a379386bc81c781337d564ab8c3` |
| `audit-summary.json` | 768 | `21c23d823e852f7ea453cf4b3ccfd2fd952de675f13f49b7db8fe9f2355e2c40` |

两目录在七类制品比较完成后各添加 `REVIEW_PENDING.md`，明确数据 GO 与工程待复审的边界；该文件不属于七类数据制品。

## 旧候选与验证边界

旧候选未删除，并分别添加：

- `thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v0/INVALIDATED_BY_REVIEW.md`
- `thesis/experiments/llm_probe/runs/data-audit/r2-quic-mednetcom-v0.build-b-verified/INVALIDATED_BY_REVIEW.md`

旧目录不得继续作为物理旁路输入或论文结论依据。

- 未运行格式化、Clippy、Pyright、Ruff、pytest、Prettier、冒烟或 `git diff`。
- 没有修改原始 qlog、检测标签、数据选择规则、训练代码或最终测试。
- 本任务没有使用 GPU，也不需要 SwanLab。
- 修复版结果仍需新的独立代码复审；复审不阻塞后续数据物化，但通过前所有衍生结果必须继续标记 `review_pending`。
