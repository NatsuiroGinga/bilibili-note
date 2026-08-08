# 任务 02T：GeNIS 全记录全局包身份分配与 Dur 逆像门禁报告

## 1. 结论

- 最终有效全量扫描已完成，验证器状态为 `completed`，`error_count=0`，`structural_error_count=0`。
- 本任务裁决为 **NO-GO**。
- `3973` 条冻结候选中，`3810` 条获得全局唯一包身份，`163` 条不存在可行身份，`0` 条存在多个全局解。
- 在 `3810` 条身份唯一候选中，`3716` 条满足 `Dur` 逆像区间，`94` 条不满足；`Dur` 逆像为空的候选为 `0` 条。
- `TotBytes` 与二层线上字节在身份唯一候选中精确匹配，但并非对全部候选精确匹配；与三层网络字节的精确匹配为 `0/3973`。因此不能把 GeNIS `TotBytes` 解释为三层网络字节。
- 该结论只裁决 GeNIS 包身份、`Dur` 和字节语义门禁，不代表 R2 协议自适应 PINN 总路线失败。

## 2. 实施边界

本任务只使用冻结候选清单、GeNIS 公开的 10 秒流记录和对应抓包完成身份辨识。全局分配阶段没有使用 `Dur`、`TotBytes`、标签、攻击类型或测试结果。`Dur` 只在身份唯一后作为独立门禁验证。

修改文件：

- `thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/flow.rs`
- `thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/model.rs`
- `thesis/experiments/llm_probe/tools/r2_genis_totbytes_verifier/src/output.rs`

新增执行锁：

- `thesis/experiments/llm_probe/runs/data-audit/r2-genis-totbytes-rust-v1-inputs/execution-code-lock-task02t.json`

正式输出：

- `thesis/experiments/llm_probe/runs/data-audit/r2-genis-global-assignment-v0/`

## 3. 实现要点

1. 加载 10 秒 CSV 的全部 `1,472,133` 条记录，以原始记录顺序约束同一规范化五元组内的候选分段。
2. 候选身份仅由端点、协议、原始记录顺序、粗粒度 `StartTime/LastTime`、`TotPkts/SrcPkts/DstPkts` 和抓包方向前缀决定。
3. 使用前向与后向动态规划统计全局路径，计数上限截断为 `2`：零解记为缺失，多解记为歧义，唯一解才回填候选包身份。
4. 保留抓包原始顺序；建立“四舍五入秒中心到抓包位置”的索引，末包直接与 `LastTime` 对照，方向前缀始终按抓包顺序计算。
5. 身份冻结后，再按 Argus 单精度六位小数表示构造 `Dur` 的微秒逆像集合及纳秒区间。
6. 比较结果新增身份状态、`Dur` 逆像数量、区间上下界、实际时长和区间匹配标记，并写入 Parquet 与两份 JSON 清单。

## 4. 根因修复记录

### 4.1 第一次有效运行前修复

首次正式命令在约 1 秒内因 `Proto=arp` 停止，尚未扫描抓包或创建正式输出。全量 CSV 盘点确认协议仅包含 `arp`、`icmp`、`ipv6-icmp`、`tcp` 和 `udp`。修复后，非候选 ARP 记录计入全量记录统计但不进入 IP 包身份分配；若冻结候选本身为 ARP，则仍直接失败。

### 4.2 第二次且最终最小修复

下一次运行暴露“连接包序列时间戳逆序”。根因是实现错误地假设抓包时间戳全局单调，并按该假设执行提前终止。最终修复不再排序或依赖单调性，改用抓包位置索引，并直接验证末包时间。

这是合同允许的第二次且最终最小修复。修复后的正式扫描没有再出现结构性错误。

## 5. 代码与执行锁

变更前 SHA256：

| 文件 | SHA256 |
|---|---|
| `flow.rs` | `28e411c5e40a8cc226fbf4d1dde2e4fde0c4d45864aad56c7d3a497462fa0013` |
| `model.rs` | `ce638ecff11c536ce43c04950c1b715ad4106c92c137e19eecdd0a2599b6fbdb` |
| `output.rs` | `87a01552ef727de14e3b4b911e054e605e2d01368a83e30928129efff21a59c4` |

最终 SHA256：

| 对象 | SHA256 |
|---|---|
| `flow.rs` | `06549d60b5e3e2ce3ee0b4e1ab7d60fbe124c88754d08c77d36137460c363ea5` |
| `model.rs` | `9fb6514fea7ea4d1934547824a01e6fe74d318791dc7e2a2d22b40c57fa42314` |
| `output.rs` | `6be43ff324a6f8568c9c7c658f518235790bda901adf4e9939b298ca7dcb2d31` |
| 工具修订树 | `652d266bf2d35b474fc64106f6ba4d5706694fb4d6fa949604878f8c56fb505c` |
| release 二进制 | `2c9d26616f8197a772632621ca16252603c5edd2a61249641fd0fc25b8244913` |
| 执行锁 | `f06133884521bad8f0441cb9e675bd261a9b566e467fd5bec95bb64f35ba5d5b` |

最终二进制大小为 `4,410,400` 字节。

## 6. 构建与执行

最终构建：

```bash
cargo build --release --manifest-path tools/r2_genis_totbytes_verifier/Cargo.toml
```

结果：退出码 `0`，耗时约 `62` 秒。仅有旧字段 `duration_ns` 未读取的警告，不影响本任务输出，未为消除警告再次构建。

正式执行使用冻结的输入哈希、工具修订哈希和执行锁哈希。验证器自身记录：

- 运行时间：`54,426` 毫秒。
- 峰值常驻内存：`739,311,616` 字节。
- 扫描包数：`37,681,001`。
- IP 包数：`37,664,960`。
- 非 IP 包数：`16,041`。
- 候选选择包数：`25,323`。
- IPv4/IPv6 分片数：均为 `0`。
- 未解析分片数：`0`。

外层 `/usr/bin/time -l` 因当前沙箱不能读取 `kern.clockrate` 而返回退出码 `1`，但验证器已完成事务提交，四个正式制品均存在，`run_manifest.json` 明确记录 `status=completed` 和 `error_count=0`。因此该包装器退出码不属于实验失败。

## 7. 输入证据

| 输入 | SHA256 |
|---|---|
| `1-packets.zip` | `1977cd7620e9f12adcb8b031d23974e229a690bbbaeda3d18828b27b79a007d3` |
| `2-flows.zip` | `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30` |
| 冻结候选清单 | `b39b60af6baec91e4586947e7e5a9fdba947419285a37f2ca9fd54cf241b56f3` |
| 成员映射 | `1574de180e67e3f38b47f38c9115a9e26ee090943f56dc4688f6ef19c46407c4` |

## 8. 八项身份与 Dur 指标

| 指标 | 数值 |
|---|---:|
| `all_rows_loaded` | 1,472,133 |
| `candidate_identity_unique` | 3,810 |
| `candidate_identity_missing` | 163 |
| `candidate_identity_ambiguous` | 0 |
| `dur_inverse_empty` | 0 |
| `dur_interval_match` | 3,716 |
| `dur_interval_mismatch` | 94 |
| `repeated_flow_id_candidate_count` | 3,056 |

补充说明：`dur_interval_match + dur_interval_mismatch = 3810`，只对身份唯一候选执行 `Dur` 门禁。

## 9. 字节与包数门禁

| 门禁 | 流级精确匹配 | 派生组精确匹配 | 全部精确 |
|---|---:|---:|---|
| 二层线上字节 | 3810/3973 | 3810/3973 | 否 |
| 三层网络字节 | 0/3973 | 0/3973 | 否 |

- 包数精确匹配：`3810/3973`。
- `mapped_semantics=neither_exactly`。
- 二层的 `163` 条不匹配与身份缺失候选一致，不能据此把全部候选判为二层语义精确。
- 三层为全量不匹配，足以否决把 `TotBytes` 直接当作三层网络层字节。

## 10. 输出制品

| 制品 | SHA256 |
|---|---|
| `summary.json` | `798550f9710ca296ccbd4b50809403b0560fc38c53f04cd9552d4427659e19ed` |
| `run_manifest.json` | `0ba347eb94275d3c2809c2ad63f8178f5c6b4b426a58617684cede44105fed37` |
| `artifact_manifest.json` | `b1dc385faadc9548065fdd12b26b8fe53e6ea263a09645999878ca082ea6fe73` |
| `flow_byte_comparison.parquet` | `b5eae7a39be8e95dd5e705ec1eb0725bb9f255fdf0ca14fbbc7c3d05ae8aab71` |

`artifact_manifest.json` 的自哈希按设计排除，其记录的其他三个制品哈希与独立计算一致。

## 11. 裁决边界与下一步

本任务证明：增加全记录顺序约束后，没有候选保留多解，但仍不能为全部冻结候选建立包级唯一身份，也不能使全部身份唯一候选满足公开 `Dur` 表示；因此 GeNIS 当前包级物理真值构造方案不得进入 R2 正式训练数据冻结。

后续只能依据上层 R2 数据合同选择以下动作，不得对本任务继续做第三次补丁：

1. 对 `163` 条身份缺失和 `94` 条 `Dur` 不匹配做只读分层诊断，判断它们是否来自公开数据生成口径，而不是实现错误。
2. 若任务目标只需要可靠子集，应预先定义、不读取模型结果的剔除规则，并重新冻结候选清单后再构建物理旁路。
3. 若要求全部候选可追溯，则需要调整 GeNIS 作为 R2 包级物理真值来源的角色，而不是继续放宽身份或时长容差。

## 12. 未执行项

按任务合同，本轮没有执行格式化、Pyright、pytest、冒烟实验、Prettier 或与本任务无关的 Git 检查。它们没有阻塞正式扫描。
