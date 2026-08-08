# R2 协议自适应数据重建实施计划

> **执行约束：** 本计划是后续 `superpowers:subagent-driven-development` 的唯一需求源。每个实现任务由独立实现代理完成；行为测试、代码与制品哈希、必要冒烟和输出隔离通过后立即以 `review_pending` 进入下一阶段，新的审查代理并行做计划符合性与代码质量复审，不得把等待复审作为实验启动门。并行复审发现严重或重要问题时，主代理立即停止相关运行、作废受影响制品并交由新的修复代理处理。项目明确禁止读取或使用测试驱动开发技能；测试在实现后作为行为验收执行。

**目标：** 在不修改任何既有冻结数据的前提下，实现并验收 `flow_probe_r2_protocol_dataset_v0` 的确定性双构建和原子发布，为 R2 的 A/B/C/D 候选筛选提供共同候选、协议观测、包序列和训练期物理真值。

**当前裁决：** 2026-08-03 已将任务 01/03 的七个生产文件绑定至提交 `527531f2f188de21489311259dbb5fcf4f1731ee`，并在干净隔离工作树生成代码锁。本机 `2-flows.zip`、`1-packets.zip` 与冻结候选清单均已完成大小、登记摘要和归档完整性核验。Rust 工具已完成三版发布构建并流式处理全部 11 个 PCAPNG 成员，但最终绑定在第三类 Argus 时间语义差异上安全失败；没有原子输出，现已停止继续修补，只允许只读诊断并转入架构裁决。源锁及任务 03 消费路径已统一到 `runs/data-freeze-configs/r2-protocol-v1/source-locks-v1`，独立复审未发现严重或重要问题。任务 05 的九项冻结输入已逐哈希同步服务器，首个正式入口于 `2026-08-03T04:36:52Z` 安全失败；根因已证明为 `PhyRxDrop` 触发时仍含 2 字节 PPP 头，而场景错误地把整包长度计为网络层字节。失败状态、能力清单和日志已回收到 `runs/launchers/r2-ns3-protocol-matrix-v0/`，现在只允许按任务 05R 显式解析并扣除实际 PPP 头长，不得盲减常量或放宽网络层字节语义。正式四锁仍未发布，R2 数据和主实验继续保持 `NO-GO`。

**固定发布根：** `runs/data-frozen/dataset-candidate-r2-protocol-v0/`

**技术边界：** Python 3.10 至 3.12、PyArrow 25、Parquet、YAML、JSON、JSONL、pytest、ns-3.48 C++、Bash、项目统一远程启动器。数据预检、TQH 派生、构建、审计和验证全部支持纯 CPU，且不得初始化 SwanLab。本机与服务器必须使用同一已提交代码版本、配置、`uv.lock` 和 PyArrow 完整版本；主机差异只能写入发布根外的运行回执。

### 困难评测与效果解释预注册

1. 数据构造目标是消除域内捷径并覆盖真实部署偏移，不是让某个基线表现变差。困难分区必须在读取 R2 预测前按时间、攻击子类、采集条件、加密条件、协议适用性、字段缺失、容量、往返时延、突发负载和拓扑身份确定，并保存样本清单与 SHA-256。
2. GeNIS 固定提供时间前向、留一攻击子类、长尾和部分可观测分区；TQH-C2 固定提供留一采集条件、跨加密条件、协议－标签匹配与未知协议回退分区；ns-3 固定提供 TCP/UDP 同参数严格配对、容量和往返时延偏移、突发负载，并只在方法冻结后读取哑铃与停车场外测结果。
3. 所有方法共享样本、划分、可见字段、训练预算、调参次数和评价器。A/C 分类视图逐字节一致；若 B/D 的协议字段进入分类输入，全部受影响基线必须在同一视图重跑。禁止根据预测正确与否、置信度或方法间差值选取最终测试样本。
4. 朱焱雷第三章第 3.6 节仅作为效果量级参照：相对当格最强外部基线的鲁棒准确率约提高 `3.3—4.8` 个绝对百分点，宏平均 F1 约提高 `4.1—5.1` 个绝对百分点；完整方法相对最强单模块提高 `4.7—6.0` 个百分点，常规干净准确率最大折损 `2.1` 个百分点。第四章约 `4.6` 倍加速伴随约 `0.3—0.6` 个百分点鲁棒性能折损，说明论文贡献可以是受约束的性能－成本优势，不要求所有指标同向提高。
5. R2 将困难条件下相对最强外部基线 `3—6` 个绝对百分点的检测收益视为合理量级，将常规宏平均 F1 折损不超过 `2.1` 个百分点视为非劣参考，但不得以命中该区间为目标修改数据。超过 `10` 个绝对百分点的异常增益必须先完成泄漏、重复、协议－标签捷径、划分和弱基线审计；审计通过后仍按实值报告，禁止主动压低。
6. 结构与超参数最多在开发训练和开发验证上进行两轮有明确假设的修订。最终测试只读一次；测试结果不得触发重采样、改比例、删样本、换指标、挑种子或削弱基线。
7. R2 的章级优先门槛是常规检测非劣、至少一个冻结困难分区 `C-A>0` 且正式三种子置信区间支持正方向、未观测状态误差和物理残差均改善至少 `10%`、协议－标签匹配对照仍保留收益。若只取得检测非劣下的物理、泛化、校准或成本正收益，论文必须收窄相应主张，不得写成总体检测精度提升。

---

## 1. 不可变边界

1. 现有 `runs/data-frozen/dataset-v1/`、`runs/data-frozen/dataset-v1-shared-b0/`、所有 GeNIS/TQH-C2 候选和历史 ns-3 制品均只读，禁止覆盖、改名、原位增列或修补。
2. 发布版本固定为 `flow_probe_r2_protocol_dataset_v0`，阶段固定为 `theory_selection`，状态固定为 `review_pending`。
3. 分类共同候选固定为 10,000 条，来源数量固定为 GeNIS 3,973、TQH-C2 3,606、历史 ns-3 2,421；样本增删只能通过独立变更清单和新的用户批准，不得作为实现细节发生。
4. 新 ns-3 TCP/普通 UDP 配对运行作为 `physics_auxiliary` 记录加入物理监督池，不替换、不扩充上述 10,000 条 `classification_candidate`。A/B/C/D 读取完全相同的物理辅助样本、运行分组和真值预算。
5. 模型视图不得包含地址、端口、采集配置、场景编号、文件路径、服务名、网址、密钥、明文、攻击标签、原始连接标识或可逆行引用。
6. QUIC 第一轮仅用于协议识别、置信度校准、开放协议评价和未知回退。禁止建立 QUIC 专属动力学专家，禁止由被动抓包补造丢包、确认范围、在途字节、迁移后连接、可靠 RTT 或拥塞窗口真值。
7. 任一字段单位未由一手证据闭合、一对一连接不可证明、跨划分重复、标签捷径未隔离、TCP/普通 UDP 真值不配对、共享守恒非零、禁止字段泄漏或双构建不一致时，立即停止并保持 `NO-GO`。
8. 冻结文件不得含当前时间、绝对路径、主机名、进程号或随机生成标识。运行时间、服务器路径和主机信息只能写到发布根外的启动回执。
9. 所有 Parquet 行按固定稳定键排序，列顺序和数据类型由 `schema.json` 固定。JSON 和 JSONL 使用 UTF-8、键排序、紧凑分隔符和换行结尾。
10. 发布根已存在即失败。构建只能写同文件系统的 `.partial` 目录，验证通过后仅用原子重命名发布 build-a，build-b 保留供人工复核。
11. TQH 原始目录固定留在本机只读使用，默认禁止向服务器上传、镜像或展开该约 98 GiB 目录；服务器只接收源锁、代码锁、移交清单和清单逐项绑定的 TQH 派生制品。
12. 本机 TQH 派生必须从两个空目录独立构建并逐文件一致后才形成跨主机移交；服务器不得因缺少原始 TQH 而把“传输成功”改写为“服务器重算原始源成功”。
13. 独立复审与 `review_pending` 实验并行，不得作为启动前置条件；行为门禁未通过不得启动，复审后出现严重或重要问题则立即停止运行并把相应源锁、移交或构建制品标为作废，修复和目标门禁重跑后才能恢复。

---

## 2. 冻结输入与源预检

### 2.1 既有冻结制品

| 角色 | 路径 | 固定绑定 |
| --- | --- | --- |
| 主记录 | `runs/data-frozen/dataset-v1/master_records.parquet` | SHA-256 `16458a4a191c51eefc58717e16609790b9914936a2470ef29099bdfbc70af703` |
| 预算校验 | `runs/data-frozen/dataset-v1/manifests/budgets/budget_checksums.json` | SHA-256 `38883c7ef8b1e47ebd218514e71f95474cebaa8637df6b5203326802546a6c2e` |
| 共同候选 | `runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl` | 10,000 条；GeNIS 3,973、TQH-C2 3,606、ns-3 2,421 |
| GeNIS 候选 | `runs/data-frozen/dataset-candidate-genis-v0/protocol/samples.parquet` | SHA-256 `2b0d8b49ef81db3a9f9338dfbabe185bab54c02512786c9f64f52718ee8c55a0` |
| GeNIS 验证 | `runs/data-frozen/dataset-candidate-genis-v0/protocol/splits/genis-family-development-validation.jsonl` | SHA-256 `52cce0c3b36273542e1fb05956e30876a8add1f6defd769ffa69b43bfaf19fca`；10,399 条 |
| GeNIS 字典 | `raw/datasets/GeNIS-2025/0-info.zip` | SHA-256 `7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc` |
| TQH-C2 候选 | `runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/samples.parquet` | SHA-256 `05cb0774f8197f07d842a21d3c22ce07c111289b7cabe6950023b689c6b51dac` |
| TQH-C2 验证 | `runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/splits/tqhc2_cell_indomain-validation.jsonl` | SHA-256 `729860d24f6e6a400ec061077f0111d2fc8504eeb3c3700e21ab6641869d5997`；4,000 条 |
| 历史 ns-3 训练 | `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/train.jsonl` | SHA-256 `d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0` |
| 历史 ns-3 验证 | `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/validation.jsonl` | SHA-256 `0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723` |
| 历史 ns-3 测试 | `runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/test.jsonl` | SHA-256 `6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94` |

历史 ns-3 仅维持共同候选身份和历史对照，不得充当 R2 多协议物理真值。

### 2.2 TQH-C2 上游锁

| 档位 | 上游根 | 主记录 SHA-256 | 包表 SHA-256 | 行数 |
| --- | --- | --- | --- | --- |
| A | `runs/data-frozen/dataset-v1-provisional/tqh-c2-A-20260728-v1/` | `8dcbce77d18f785c1712f525807aab7f4ddf1c53ce1fc559cb59765487280799` | `2366a25dc3a3c847ecb3549c4d79d131e172a17aa53b709dd65949a26647a32f` | 主记录 181,556；包 15,761,376 |
| B | `runs/data-prepared/tqh-c2-b-v101-provisional-20260728/` | `bac856cfbae0aa9a31faeaead635b3852bb68765209c0769eaee42b5cb5eb6ba` | `97e736d28920702c3fab72cf86040a3258d4f0dcd8ea6a2c9db31d4b60a2f108` | 主记录 115,734；包 9,857,089 |
| C | `runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v8/` | `fbbfaaae1a8bc27fb658700f53ad3af371c968f3c9c143c6b6928c40d155ceba` | `44547ce8421015ebfe5efead5fac4638ad5169137db735955e550c800fd4ef86` | 主记录 36,671；包 396,271 |

还必须绑定 `runs/data-freeze-configs/tqhc2-abc-v0/approved-inputs.json`，并把 A/B/C 对应的 36 个 PCAP、标签文件、单元审计和 `source_checksums.json` 逐项规范化为相对逻辑路径、字节数和 SHA-256。上游清单里的绝对路径不得复制到冻结输出。

A/C 的历史提取器条目固定登记大小 `46140` 字节和 SHA-256 `7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617`，但本机工作树、全部 Git 分支与 reflog 均无该快照。源锁必须保留 `evidence_mode=approved_manifest_only_blocked` 和 `evidence_status=blocked`；禁止改写当前 `tqh_c2.py`、复制 B 快照、生成占位文件、碰撞旧哈希或以批准清单冒充实物快照。该阻塞禁止宣称 A/C 提取器可重现，但不阻止对已批准 PCAP、标签、审计和既有上游制品执行预检与新 QUIC 派生。

### 2.3 GeNIS 官方源

- 权威原件当前固定为服务器只读路径 `/root/autodl-tmp/thesis/datasets/GeNIS-2025/2-flows.zip`；本机完整预检使用新建逻辑暂存路径 `raw/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/2-flows.zip` 或对权威原件的只读挂载，绝对运行路径不得进入冻结锁。
- 官方登记固定为 Zenodo `14919237`、DOI `10.5281/zenodo.14919237`、版本 `1.0.0`。
- 官方文件地址固定为 `https://zenodo.org/api/records/14919237/files/2-flows.zip/content`，精确大小 `380755720` 字节，官方 MD5 `063b7a2ec6e6b73cc302151d2b3ba6d7`，已核验归档 SHA-256 固定为 `72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30`。
- 服务器原件已通过大小、MD5、SHA-256、ZIP 中央目录和 11 个物化成员核验。本机取得完整归档时只允许从该已核验服务器原件拉取到上述新路径，或使用只读挂载；传输前后都核对精确大小、MD5 和 SHA-256，随后重新执行 ZIP 路径安全、数量、表头、CRC、逐成员大小与 SHA-256 检查。任何一项失败即隔离新暂存文件、保留失败回执并停止；未经用户确认不得删除，也不得回退到损坏副本。
- 重建直接流式读取 ZIP 内 `flows-10-sec` 的 11 个 CSV，不依赖展开目录。每个 CSV 作为独立源制品写入 `source-artifacts.jsonl`，逻辑路径格式固定为 `zenodo:14919237/2-flows.zip!/成员相对路径`。
- 本机 `raw/datasets/GeNIS-2025/2-flows.zip` 缺少 ZIP 中央目录，禁止读取、续传、拼接、修补或物化。
- 只有服务器权威原件的大小、MD5、SHA-256 或 ZIP 完整性失败时，才启用已获用户授权的官方恢复路径。固定临时文件为 `/root/autodl-tmp/thesis/datasets/GeNIS-2025/official/zenodo-14919237-v1.0.0/2-flows.zip.download.partial`，固定发布文件为同目录 `2-flows.zip`；从上述官方地址断点续传，完成全部哈希、ZIP 安全和成员核验后以 `os.replace` 发布。恢复流程不得覆盖当前原件，也不得以损坏本机副本作为续传前缀。
- 若需用原始包证明 `TotBytes` 层级，官方地址固定为 `https://zenodo.org/api/records/14919237/files/1-packets.zip/content`，精确大小 `1028741083` 字节，官方 MD5 `5afbceaadfe3c3476f54723434d59b4a`。仅在 HERA 一手实现不足以闭合语义时按同样门禁取得，不得因为文件完整就宣称单位已闭合。

### 2.4 源锁输出

预检生成但不发布为模型数据的源锁固定放在：

```text
runs/data-freeze-configs/r2-protocol-v1/
├── source-lock.json
├── execution-code-lock.json
├── genis-member-lock.jsonl
├── tqhc2-source-lock.jsonl
├── tqhc2-handoff-manifest.json
├── ns3-config-manifest.jsonl
├── ns3-config-manifest.sha256
└── ns3-trace-contract.json
```

所有源锁按逻辑路径排序，不含绝对路径、时间或主机名。`source-lock.json` 只绑定 `genis-member-lock.jsonl`、`tqhc2-source-lock.jsonl`、静态配置、`execution-code-lock.json` 和旧冻结制品的 SHA-256；后生成的 `tqhc2-handoff-manifest.json` 单向绑定这些锁，源锁不得反向绑定移交清单，避免自指。任一输入在本机两次 TQH 派生之间、跨主机移交前后或服务器 build-a/build-b 之间变化即失败。

`execution-code-lock.json` 必须记录一个已提交的 40 位 Git 提交、`worktree_clean=true`、`pyproject.toml`、`uv.lock`、`configs/r2_protocol_data_v1.yaml` 以及任务 01/03 实际导入的全部生产 Python 文件的逻辑路径、字节数和 SHA-256，并绑定 Python 与 PyArrow 完整版本。只执行 `git rev-parse HEAD` 不足以签锁；任一必需文件未跟踪、工作树脏、提交不一致或文件哈希变化即失败。测试文件可写入发布根外验收回执，但不得代替生产代码锁。

### 2.5 混合主机 TQH 移交合同

本机从两个空目录独立生成 `runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.partial/` 和 `.build-b.partial/`。两边的四项语义载荷必须逐文件、逐模式、逐行数和逐内容哈希一致：

```text
runs/data-frozen/r2-protocol-tqhc2-handoff-v0/
├── packet-observations.parquet
├── protocol.parquet
├── source-row-map.parquet
└── sequence-audit.json
```

一致后只原子发布 build-a 为上述规范根，build-b 保留至最终 R2 发布验收完成。`tqhc2-handoff-manifest.json` 使用规范 JSON，逐项记录相对逻辑路径、角色、字节数、SHA-256、Parquet 行数、模式 SHA-256 和整体语义载荷 Merkle，并绑定 `source-lock.json`、`tqhc2-source-lock.jsonl`、`execution-code-lock.json`、配置和本机双派生比较对象的 SHA-256。清单不得含绝对路径、主机名、时间、进程号、原始地址、端口、连接标识或可逆行号。

跨主机只允许同步三份源锁、代码锁、TQH 移交清单及清单枚举的四项规范载荷。服务器先接收到同文件系统 `.incoming.partial`，拒绝符号链接、额外文件、缺项、绝对路径、大小或哈希变化，再复核 Parquet 行数、列顺序、数据类型、模式哈希和 Merkle；全部通过后才原子重命名为只读消费者根。包含 PCAP、`conn.log`、原始标签目录或约 98 GiB TQH 根的同步参数必须在传输前硬失败。运行时间、两端绝对路径和主机角色只进入发布根外的移交回执。

---

## 3. 发布文件合同

```text
runs/data-frozen/dataset-candidate-r2-protocol-v0/
├── master_records.parquet
├── views/
│   ├── common_features.parquet
│   ├── protocol_observations.parquet
│   ├── packet_observations.parquet
│   └── physics_targets.parquet
├── mappings/
│   └── source_row_map.parquet
├── splits/
│   ├── train-fit.jsonl
│   ├── calibration.jsonl
│   ├── validation.jsonl
│   ├── test.jsonl
│   ├── unseen-configuration.jsonl
│   └── open-protocol.jsonl
├── audits/
│   ├── join-audit.json
│   ├── unit-audit.json
│   ├── leakage-audit.json
│   ├── protocol-label-contingency.json
│   ├── duplicate-screen.json
│   └── deterministic-build-comparison.json
├── field-roles.yaml
├── schema.json
├── source-artifacts.jsonl
├── artifact-checksums.json
└── freeze-manifest.json
```

不得添加未在 `schema.json` 登记的发布文件。构建恢复用 `_INCOMPLETE.json`、阶段状态和外部排序分片只能存在于 `.partial`，发布前必须删除。

### 3.1 主记录角色

`master_records.parquet` 至少固定以下逻辑列并由 `schema.json` 给出精确物理类型：

```text
sample_id, stable_order, source_dataset, record_role,
candidate_member, binary_label, family_label, subtype_label,
group_id, capture_group_id, parent_session_id, split_id,
packet_view_available, protocol_target,
source_record_sha256, common_observation_sha256,
observation_sequence_sha256, physics_group_sha256
```

- `record_role` 只能为 `classification_candidate`、`evaluation_reference`、`physics_auxiliary` 或 `open_protocol`。
- 10,000 条共同候选必须全部为 `classification_candidate` 且 `candidate_member=1`。
- 新 ns-3 配对样本必须为 `physics_auxiliary` 且 `candidate_member=0`。
- 10,000 条分类候选的 `sample_id` 原样继承现有候选，不再次加盐或重哈希；其 `stable_order` 固定为共同候选清单中的 0 至 9,999。评价引用随后按 `(record_role, source_dataset, split_id, sample_id)` 排序，物理辅助记录最后按 `(physics_group_sha256, transport_family, window_index)` 排序。
- `protocol_target` 是训练期协议真值，不是攻击分类输入。没有可信协议真值时写 `UNKNOWN`，不能按 `profile`、标签或端口推断。
- 原始行号、文件名、地址、端口和配置编号不得进入主记录；只能通过不可逆哈希写入映射表。

### 3.2 共同视图

`views/common_features.parquet` 列顺序必须精确为：

```text
sample_id, stable_order,
total_packets, total_bytes,
packet_length_mean, packet_length_min, packet_length_max,
iat_mean_ms, packet_rate, byte_rate,
total_packets_missing, total_bytes_missing,
packet_length_mean_missing, packet_length_min_missing,
packet_length_max_missing, iat_mean_ms_missing,
packet_rate_missing, byte_rate_missing
```

- 数值列使用可空 `float64`；`sample_id` 为字符串，`stable_order` 为 `int64`，缺失掩码为 `uint8` 且只能取 0 或 1。
- 单位依次为包、网络层字节、网络层字节/包、网络层字节、网络层字节、毫秒、包/秒、字节/秒。
- GeNIS 映射固定为 `TotPkts`、`TotBytes`、`TotBytes/TotPkts`、`min(sMinPktSz,dMinPktSz)`、`max(sMaxPktSz,dMaxPktSz)`、以 `max(SrcPkts-1,0)` 和 `max(DstPkts-1,0)` 为权重的 `SIntPkt/DIntPkt` 加权均值、`Rate`、`Load/8`。
- TQH-C2 映射精确复用现有确定性聚合：`packet_count`、网络层字节总和/均值/最小/最大、包含首包零值在内的全部 `delta_time_us` 算术均值再除以 1,000、包数/有效持续秒、网络层字节/有效持续秒。`flow_duration_us` 固定为 `max(relative_time_ns)/1000`，有效持续秒再除以 `1e6`；持续时间不正时两个速率为空。
- 新 ns-3 四窗序列映射固定为四窗公开包数和网络层字节之和、总字节/总包数、四窗最小/最大、按有效间隔数加权的到达间隔、总包数/0.4 秒和总字节/0.4 秒。
- 分母为零、没有有效间隔或来源确实不提供时，数值写 `null` 且对应掩码写 1。不得以数值 0 表示缺失。
- 对 10,000 条分类候选生成独立的规范 JSON 数值哈希，并与现有 `shared_b0_view_v1` 的候选顺序、数值、缺失掩码和渲染前处理逐项比较。只有全部相同，A/C 的非物理分类基线才可能复用。

### 3.3 协议视图与字段角色

`views/protocol_observations.parquet` 以 `sample_id` 为唯一主键，至少包含：

```text
sample_id,
transport_family, transport_family_observed,
quic_evidence_class, protocol_target, protocol_confidence,
shared_expert_mask, tcp_expert_mask, udp_expert_mask,
loss_packets, loss_packets_missing, loss_packets_applicable,
retrans_packets, retrans_packets_missing, retrans_packets_applicable,
tcp_rtt_ms, tcp_rtt_ms_missing, tcp_rtt_ms_applicable,
src_window_bytes, src_window_bytes_missing, src_window_bytes_applicable,
dst_window_bytes, dst_window_bytes_missing, dst_window_bytes_applicable,
tcp_packet_fraction, udp_packet_fraction,
icmp_packet_fraction, other_transport_packet_fraction,
tcp_syn_packet_fraction, tcp_ack_packet_fraction,
tcp_fin_packet_fraction, tcp_rst_packet_fraction,
tcp_psh_packet_fraction, payload_observed_fraction,
tcp_flags_applicable_fraction, truncation_fraction,
quic_observed_packet_fraction, quic_v1_long_packet_fraction,
quic_context_short_packet_fraction, quic_ambiguous_packet_fraction,
quic_fixed_bit_one_fraction, quic_spin_bit_one_fraction,
quic_cid_changed_packet_fraction,
quic_src_cid_length_mean, quic_dst_cid_length_mean
```

- `transport_family` 枚举固定为 `TCP/UDP/ICMP/SCTP/DCCP/ESP/OTHER/UNKNOWN`。
- `quic_evidence_class` 枚举固定为 `NONE/V1_LONG_HEADER/CONTEXT_BOUND_SHORT_HEADER/AMBIGUOUS`。
- 样本级 QUIC 证据归并优先级固定为 `AMBIGUOUS`、`V1_LONG_HEADER`、`CONTEXT_BOUND_SHORT_HEADER`、`NONE`；出现未知版本、结构冲突或无法归属的 QUIC 候选包时，整条样本优先标为 `AMBIGUOUS`。
- `protocol_target` 在传输族枚举基础上增加 `QUIC`，仅用于协议识别损失和评价。
- `protocol_confidence` 范围为 `[0,1]`。GeNIS 和 ns-3 的直接、可信协议字段可取 1；TQH 必须由独立校准流程产生。
- `shared_expert_mask` 对所有样本为 1。只有可信 TCP 或可信普通 UDP 且通过置信门槛时，对应专属掩码才可为 1。
- QUIC、无法识别的 UDP、未知版本、证据冲突或低置信样本必须令 `tcp_expert_mask=0` 且 `udp_expert_mask=0`。
- `Loss` 和 `Retrans` 只按非负包计数处理；`Retrans` 仅在 TCP 时适用。
- `TcpRtt`、`SrcWin`、`DstWin` 没有一手单位和缩放证据时不得填值、换算或进入 `x_proto`。未闭合时整个发布保持 `NO-GO`，不得通过填空掩码绕过 P0。
- 静态配置先把这三个字段声明为 `blocked_pending_semantics` 并列出所需证据。只有单位证据锁逐项通过后，构建器才能按配置预注册决策转为 `router_or_physics_input` 或 `audit_only`；最终发布的 `field-roles.yaml` 不得残留 `blocked_pending_semantics`。
- `SrcWin`/`DstWin` 只能解释为通告接收窗口，永远不能代替 ns-3 `cwnd` 真值。
- TQH 的 12 个聚合比例全部从 R2 包序列重算；非 TCP 的 TCP 标志比例必须为空且适用掩码为 0，不能用零伪装观测。
- 九个样本级 QUIC 聚合量全部从包表重算，每列都配同名 `_missing` 和 `_applicable` 掩码。比率分母固定为样本包数；连接标识长度均值只对相应长度可见的包计算；没有适用包时写空而非零。
- `field-roles.yaml` 对每列只允许 `router_or_physics_input`、`audit_only` 或 `blocked_pending_semantics`。C/D 物理分支读取的全部 `router_or_physics_input` 字段及掩码构成唯一 `x_proto`；B/D 分类器获得逐列、逐位相同的 `x_proto`。

### 3.4 包序列与 QUIC 字段

基础包列顺序固定为：

```text
sample_id, packet_index, relative_time_ns, delta_time_us,
direction, network_length_bytes, payload_length_bytes,
transport_family, tcp_flags, burst_id, is_first_packet,
payload_length_observed, tcp_flags_applicable, truncation_mask
```

QUIC 附加列顺序固定为：

```text
quic_header_form, quic_header_form_observed, quic_header_form_applicable,
quic_version_u32, quic_version_observed, quic_version_applicable,
quic_v1_packet_type, quic_v1_packet_type_observed, quic_v1_packet_type_applicable,
quic_fixed_bit, quic_fixed_bit_observed, quic_fixed_bit_applicable,
quic_spin_bit, quic_spin_bit_observed, quic_spin_bit_applicable,
quic_src_cid_length_bytes, quic_src_cid_length_observed, quic_src_cid_length_applicable,
quic_dst_cid_length_bytes, quic_dst_cid_length_observed, quic_dst_cid_length_applicable,
quic_cid_changed, quic_cid_changed_observed, quic_cid_changed_applicable,
quic_parser_version
```

- `packet_index` 对每个样本从 0 连续递增；不允许假设同一样本在 Parquet 行组内连续。
- `relative_time_ns` 非负且不回退；首包 `delta_time_us=0`，其余为相邻包时间差向下整除 1,000 后的非负整数。
- `direction` 只能为 -1 或 1；`network_length_bytes` 非负；`tcp_flags` 只能为 0 至 `0x1FF` 且仅 TCP 适用；每个非空序列恰有一条首包。
- R2 先按冻结样本 ID 过滤上游包行，再采用有界内存分桶或外部排序按 `(sample_id, packet_index)` 重组。交错样本、跨非相邻行组和同一行组含多个采集单元都必须有行为测试。
- QUIC 长首部只按可见线图像解析；版本为 1 时才解释 v1 包类型。版本协商、未知版本、截断或结构冲突标为 `AMBIGUOUS`。
- 短首部只有在同一构建进程内已由可信长首部建立连接上下文时才能标为 `CONTEXT_BOUND_SHORT_HEADER`。原始连接标识只允许驻留内存，用于长度和变化布尔量，禁止写入临时文件、日志或发布表。
- 固定位和旋转位都是弱观测，不能单独形成 QUIC 硬标签；旋转位不得生成 RTT。
- `quic_parser_version` 固定由配置绑定，不含运行时间。第一轮值固定为 `flow_probe_quic_wire_image_v1`。
- `observation_sequence_sha256` 对上述全部发布包字段的规范 JSON 序列计算。旧基础字段另算兼容哈希并与上游候选绑定；因新增 QUIC 字段产生的新哈希必须在 `source_row_map.parquet` 明确标记解析版本，不能静默覆盖。
- GeNIS 不伪造包序列，`packet_view_available=0`。A/B/C/D 对序列可用性使用相同掩码和同维度统一空分支。

### 3.5 物理真值

`views/physics_targets.parquet` 只保存训练期真值和适用掩码，不进入攻击分类输入。共享队列至少包含每窗：

```text
sample_id, physics_group_sha256, window_index,
queue_start_l3_bytes, queue_end_l3_bytes,
qdisc_received_l3_bytes, qdisc_enqueued_l3_bytes,
qdisc_dequeued_l3_bytes,
qdisc_dropped_before_enqueue_l3_bytes,
qdisc_dropped_after_dequeue_l3_bytes,
downstream_error_loss_l3_bytes, sink_received_l3_bytes,
queue_start_packets, queue_end_packets,
qdisc_received_packets, qdisc_enqueued_packets,
qdisc_dequeued_packets,
qdisc_dropped_before_enqueue_packets,
qdisc_dropped_after_dequeue_packets,
downstream_error_loss_packets, sink_received_packets,
capacity_integral_link_bytes,
queue_balance_residual_l3_bytes, queue_balance_residual_packets
```

- 包和网络层字节守恒分别使用精确整数核对，两个残差必须逐窗等于 0。任一窗口失败时拒绝完整 TCP/UDP 配对组的全部四窗序列，并保留失败回执。
- TCP 候选真值为 `cwnd_bytes`、`bytes_in_flight`、采样或平滑 RTT、确认字节/包、重传字节/包和发送字节/包。每项必须在 `ns3-trace-contract.json` 写明 ns-3.48 trace source、连接对象、回调类型、窗口聚合和适用掩码。
- 第一轮 TCP 实现固定为 `ns3::TcpNewReno`。`CongestionWindow` 是强制 trace；若服务器 ns-3.48 源码或运行时 TypeId 无法确认并稳定采集，任务立即停止。
- 其他 TCP 候选字段只有在 ns-3.48 源码和最小运行同时确认后才进入最终模式；无法稳定追踪的字段从模式中删除，不得估算。
- UDP 真值固定为应用计划发送字节/包、实际发送字节/包、发送速率和突发开关状态。UDP 的 TCP 状态列必须为空，适用掩码为 0。
- 环境参数、协议身份、攻击模式、队列模型、种子和配置哈希仅用于真值、分组和审计，不进入攻击分类输入。

---

## 4. 划分、校准、泄漏和 A/B/C/D

### 4.1 分组与划分

- GeNIS 以现有 `group_id` 对应的源文件或采集单元整体分组。
- TQH-C2 以 `capture_group_id` 和父会话整体分组；`profile`、`interval_s` 和 `jitter_pct` 仅用于划分与审计。
- ns-3 以基础配置哈希和种子构成配对组；同一基础配置的 TCP 与普通 UDP 以及该运行所有窗口必须进入同一划分。
- 现有验证和测试边界原样继承；任何组与现有验证/测试清单相交时，不得进入 `train-fit` 或 `calibration`。
- 对原训练候选按组计算 `sha256("flow_probe_r2_calibration_v1\\0" + source_dataset + "\\0" + group_id)`。摘要前 16 位解释为无符号整数，小于 `0x1999999999999999` 的组进入 `calibration`，其余进入 `train-fit`，约为 10%。算法不得根据标签结果重抽或改阈值；若共同支持不足则失败。
- `unseen-configuration` 只含预注册的 ns-3 范围外配置和 TQH 留采集配置；`open-protocol` 只含未知协议、未知 QUIC 版本、低置信协议和原有开放集清单。两者均不得参与协议训练或温度拟合。

### 4.2 协议识别与校准

- 协议识别器只读取 `train-fit` 的可见协议字段，禁止读取攻击标签、来源名、`profile`、地址、端口和配置编号。
- 识别器特征固定为 `transport_family` 独热编码、`transport_family_observed`、四个传输族包比例、`quic_evidence_class` 独热编码、九个样本级 QUIC 聚合量及其掩码。`loss_packets`、`retrans_packets`、RTT、窗口、共同流量统计和全部攻击相关字段不得进入协议识别器。
- 第一轮识别器固定为标准化数值与固定词表独热类别上的多项逻辑回归：`solver="lbfgs"`、`multi_class="multinomial"`、`C=1.0`、`fit_intercept=true`、`class_weight=None`、`max_iter=1000`、`tol=1e-8`，固定随机种子 `20260731`。每个数值特征的均值和标准差只用 `train-fit` 中掩码为观测的值计算，零方差时标准差置 1；缺失值标准化后填 0 并保留掩码。类别词表固定由合同给出，不从测试数据扩展。
- 采用单一全局温度缩放；温度只在 `calibration` 的协议真值上拟合。温度搜索固定在闭区间 `[0.05,10.0]`，以 200 次黄金分割迭代最小化负对数似然；测试、未见配置和开放协议不得参与。
- 低置信阈值固定为 `0.80`。未知 QUIC 版本或 `AMBIGUOUS` 证据无条件进入 `UNKNOWN`；不得用最大概率强制激活专家。
- 报告准确率、宏平均 F1、负对数似然、Brier 分数、15 等宽箱期望校准误差、覆盖率风险曲线，以及按来源、协议、同分布、留采集配置、跨源和开放协议分层结果。
- 进入 C/D 物理路由的置信度必须是冻结标量。后续模型接口必须显式停止梯度；攻击分类损失对协议识别器和温度参数的梯度精确为 0。
- 数据适配器只返回离线冻结的协议概率、置信度和掩码，不返回识别器对象或可训练温度参数；后续张量构造固定 `requires_grad=false`，从结构上切断攻击分类损失路径。
- 识别器系数、截距、标准化统计、类别词表、全局温度、阈值、训练与校准输入哈希及分层指标以规范 JSON 嵌入 `freeze-manifest.json`；阶段目录中的中间模型文件发布前删除，但不得只保留无法复现的模型哈希。

### 4.3 泄漏与捷径门禁

自动生成并冻结以下审计结果：

1. `protocol × binary_label × source/profile/split` 完整列联表；主评价单元必须同时有协议内正例和负例，否则该单元标记为不支持检测收益论断。
2. TQH 协议字段确定性置换视图，置换仅在同一划分和协议标签支持层内按固定哈希排序循环移动。
3. TQH 协议字段全掩码视图。
4. TQH 去握手前缀视图，移除每个序列首个应用有效载荷前的 TCP 握手或 QUIC Initial/Handshake 包；无法确定边界的样本排除并计数，不能猜测。
5. TQH 留一 `profile` 视图，A、B、C 三个档位各一次。
6. 协议与攻击标签匹配子集，在每个来源、划分、协议和二元标签单元取固定哈希排序后的共同最小数，不做有放回采样。
7. 地址/端口隔离审计基线只在持有原始敏感字段的独立进程内运行，输出仅含汇总指标和输入哈希，绝不输出特征或样本行。
8. 对每个发布模型字段执行禁止词、唯一值、与标签互信息、与来源可预测性审计。高来源可预测性触发跨源和留配置评价，不允许静默删除后重算。
9. 对包序列哈希、共同特征哈希和源记录哈希执行跨划分重复检查；标签冲突或非独立重复为 P0 硬失败。

### 4.4 A/B/C/D 信息预算

| 组 | 分类头 | 物理分支 | 物理真值 |
| --- | --- | --- | --- |
| A | `x_common` | 无协议统一残差分支 | 与 C 完全相同 |
| B | `x_common + x_proto` | 无协议统一残差分支 | 与 D 完全相同 |
| C | `x_common` | `x_proto`、固定硬掩码、停止梯度的校准置信度 | 与 A 完全相同 |
| D | `x_common + x_proto` | 与 C 完全相同 | 与 B 完全相同 |

- 四组的分类候选、样本顺序、标签、划分、共同特征和物理辅助运行集合完全一致。
- `field-roles.yaml` 冻结 `x_common` 和唯一 `x_proto` 列表；B/D 分类器与 C/D 物理分支的 `x_proto` 列顺序、类别字典、数值和掩码哈希必须相同。
- A/B 的统一残差网络与 C/D 的 TCP、UDP 专家总参数量匹配；该容量约束属于后续模型实施，但数据冻结清单必须提供对应的字段和真值哈希。
- `freeze-manifest.json` 为 A/B/C/D 分别记录 `candidate_order_sha256`、`label_sha256`、`split_sha256`、`x_common_sha256`、`x_proto_sha256`、`physics_auxiliary_sha256` 和字段列表 SHA-256。没有协议输入的组仍记录空向量固定哈希，不能省略。

### 4.5 基线复用与重跑边界

- Qwen、HGB、XGBoost、DistilBERT 在 A/C 的共同输入结果，只有在候选顺序、标签、划分、`x_common` 规范值、渲染或预处理配置五类哈希全部等于既有共享 B0 时才允许复用；任一不等即全部重跑。
- A/C 的状态仅基线和现有统一物理基线必须在新的 TCP/普通 UDP 物理辅助真值上重跑，旧 UDP-only 结果只能作历史参照。
- B/D 暴露新 `x_proto`，因此 Qwen、HGB、XGBoost、DistilBERT、状态仅基线和现有统一物理基线全部重跑。
- A/B/C/D 主实验全部使用同一新冻结数据版本重新运行。数据发布只生成绑定和读取接口，不在本计划内启动任何正式模型训练。

---

## 5. ns-3 固定矩阵与覆盖门槛

### 5.1 配置设计

- 先生成不含协议的基础配置，再为每个基础配置派生同种子、同负载、同拓扑、同队列、同容量、同丢包和同到达过程的 TCP 与普通 UDP 两条运行。
- 运行时长固定 12 秒，窗口固定 0.1 秒，每条完整运行预期 120 个窗口；四窗序列长度固定 4，使用不重叠窗口，因此每条完整运行预期 30 个序列。
- 基础配置数量固定为：`train-fit=128`、`calibration=32`、`validation=32`、`test=32`、`unseen-configuration=32`，合计 256 个基础配对组、512 条协议运行、61,440 个窗口、15,360 个四窗序列。
- 每个同分布划分按 `traffic_mode ∈ {benign,dos}`、`arrival_model ∈ {constant,bursty}`、`queue_model ∈ {fifo,codel}`、四个负载带完全因子化。训练每个因子单元使用 4 个预注册种子，校准、验证和测试每个因子单元使用 1 个不重叠种子。
- 四个负载带固定为初始瓶颈容量的 `{0.35,0.70,1.05,1.40}` 倍。良性和攻击配置保持相同总提供负载，`traffic_mode` 只改变发送者组成，不能由总速率直接恢复标签。
- 同分布参数网格固定为：初始容量 `{10,20}` Mbps、容量变化倍数 `{0.5,1.0}`、接入时延 `{1,5}` ms、瓶颈时延 `{5,20}` ms、队列上限 `{32,128}` 包、下游丢失率 `{0.0,0.01}`。每个因子单元用基础配置规范哈希从各网格独立选值，不能用协议或标签索引选值。
- `unseen-configuration` 使用训练未见的 `red` 队列，参数网格固定为初始容量 `{5,40}` Mbps、容量变化倍数 `{0.25,1.5}`、接入时延 `{0.25,8}` ms、瓶颈时延 `{50,100}` ms、队列上限 `{8,256}` 包、下游丢失率 `{0.03,0.05}`；继续按良性/攻击、恒定/突发和四个负载带配平，每个因子单元使用 2 个不重叠种子。
- 矩阵主种子固定为 `20260731`；各基础配置的运行种子由规范基础配置 JSON 的 SHA-256 前 8 字节映射为非零 31 位整数，不依赖列表索引，因此配置编号不能预测协议或标签。
- 协议只作为基础配置的最后一个笛卡尔维度，`config_id` 不含 `tcp`、`udp`、标签或顺序编号；公开映射只保留不可逆 `physics_group_sha256`。
- 配置 JSONL 必须在任何 ns-3 CSV 生成前写定并生成 `ns3-config-manifest.sha256`。CSV 启动后禁止修改配置清单。

### 5.2 预注册覆盖门槛

- 配对完成率在每个划分至少 95%，且只有 TCP 与 UDP 都成功、守恒都通过的基础配置才计为有效配对。
- `train-fit` 每个 `traffic_mode × arrival_model × queue_model` 单元至少保留 15 个有效基础配对；校准、验证和测试各单元至少保留 3 个；未见配置每个 `traffic_mode × arrival_model` 单元至少保留 3 个。
- 每个 `transport_family × binary_label` 在 `train-fit` 至少有 1,728 个四窗序列，在校准、验证、测试和未见配置各至少有 432 个。
- 每个划分至少 95% 的 TCP 有效窗口必须具有直接采集的 `cwnd` 状态。低于该门槛即停止，不得用插值或均值填充。
- 任一失败配置保留独立失败回执和错误类别；不得删除失败难例后重新编号或悄悄更换种子。

---

## 6. 实现任务与文件白名单

源码、配置、测试、脚本和 ns-3 路径均相对于 `thesis/experiments/llm_probe/`；`.Codex/docs/` 报告路径相对于仓库根。每个任务只能修改其白名单。若白名单文件在执行前出现其他任务的新改动，实现代理必须停止并交由主代理重新分配。

每个实现代理完成后写各任务文件白名单中明确列出的 `report-task-*`；目标行为门禁通过后状态写为 `review_pending` 并允许下一阶段启动，新的审查代理并行只写下表对应文件，不得要求等待报告落盘才启动。严重或重要问题由新的修复代理在原任务源码白名单内做最小修复；主代理同时停止相关运行、作废受影响制品，修复后重跑对应行为门禁并继续并行复审。

| 任务 | 独立审查报告 |
| --- | --- |
| 01 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-01-contract.md` |
| 02 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-02-genis.md` |
| 03 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-03-tqhc2.md` |
| 04 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-04-ns3-matrix.md` |
| 05 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-05-ns3-runner.md` |
| 06 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-06-calibration.md` |
| 07 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-07-views.md` |
| 08 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-08-audits.md` |
| 09 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-09-rebuild.md` |
| 10 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-10-validate.md` |
| 11 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-11-remote.md` |
| 12 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-12-final.md` |

**固定运行制品路径：**

| 任务 | 运行制品 |
| --- | --- |
| 01 | `runs/data-freeze-configs/r2-protocol-v1/source-lock.json`、`execution-code-lock.json`、`genis-member-lock.jsonl`、`tqhc2-source-lock.jsonl` |
| 02 | 构建目录的 `.stages/genis/common.parquet`、`protocol.parquet`、`source-row-map.parquet`、`unit-evidence.json` |
| 03 | 本机 `runs/data-frozen/r2-protocol-tqhc2-handoff-v0/` 的四项规范载荷、保留的 build-b 和 `tqhc2-handoff-manifest.json` |
| 04 | `runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl` 与 `ns3-config-manifest.sha256` |
| 05 | `runs/ns3-data/r2-protocol-paired-v0/`，每个 `physics_group_sha256` 下保存 TCP/UDP CSV 和两份运行回执 |
| 06 | 构建目录的 `.stages/protocol-calibration/{router.json,temperature.json,predictions.parquet,metrics.json}` |
| 07 | 构建目录中的 `master_records.parquet`、四个 `views/*.parquet`、六个 `splits/*.jsonl`、`field-roles.yaml` 和 `schema.json` |
| 08 | 构建目录中的五份构建期 `audits/*.json` 和 `mappings/source_row_map.parquet` |
| 09 | `runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial/` 与 `runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial/` |
| 10 | `runs/data-frozen/dataset-candidate-r2-protocol-v0/` 与保留的 `runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial/` |
| 11 | `runs/launchers/r2-protocol-data-rebuild-v0/` 与发布根外的本机生产、跨主机传输和服务器消费回执 |
| 12 | `.Codex/docs/sdd/task-r2-data-rebuild/reports/` 中的全链路报告与最终审查 |

除已冻结的 TQH 跨主机消费者根外，所有 `.stages` 只属于 `.partial`，验证发布前必须删除；源锁、TQH 移交根、ns-3 原始运行和启动回执位于最终发布根外并由冻结清单只读绑定。

### 任务 01：合同常量、模式和源预检

**依赖：** 无。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_contract.py`
- 新建 `configs/r2_protocol_data_v1.yaml`
- 新建 `tests/test_r2_protocol_contract.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-01-contract.md`

**公开接口：**

```python
load_r2_config(path: Path) -> R2ProtocolConfig
verify_frozen_inputs(project_root: Path, external_sources: ExternalSourceRoots, config: R2ProtocolConfig) -> SourceLock
verify_genis_archive(path: Path, spec: GeNISArtifactSpec) -> GeNISArchiveInventory
resume_official_download(spec: GeNISArtifactSpec, destination: Path) -> DownloadReceipt
build_execution_code_lock(project_root: Path, required_paths: Sequence[str]) -> ExecutionCodeLock
verify_execution_code_lock(project_root: Path, lock: ExecutionCodeLock) -> None
write_source_lock(lock: SourceLock, output_root: Path) -> None
canonical_json_sha256(value: object) -> str
```

**最小行为：**

- 配置精确冻结版本、发布根、8 字段顺序、字段角色、枚举、Parquet 参数、源路径、已知哈希、GeNIS 官方元数据、矩阵数量、覆盖门槛和 A/B/C/D 预算。
- 拒绝绝对路径进入源锁；本机和服务器绝对源路径只能由命令参数解析，冻结锁写逻辑相对路径。
- 对本机正式预检所用 `2-flows.zip` 核对 380,755,720 字节、官方 MD5、固定归档 SHA-256、ZIP 完整性、四尺度各 11 个 CSV、无路径穿越/符号链接/重复成员，并计算 10 秒尺度每个 CSV 的大小与 SHA-256。
- 官方恢复接口只允许 `https` 和配置登记的 Zenodo URL。已有临时文件必须带同 URL、版本、大小和官方 MD5 的旁路锁才可发送 `Range`；服务器返回必须是匹配的 `206 Content-Range`，返回完整 `200` 时只截断该临时文件并从零重启。任何校验失败都不得发布。
- 对旧冻结制品和 TQH A/B/C 上游逐项核对哈希与行数；任何缺项或变化失败。
- A/C 历史提取器只允许按第 2.2 节写入明确阻塞证据；测试证明缺少旧快照不会被伪造为已核验，当前 B 快照也不能替代 A/C。
- 代码锁必须拒绝未跟踪生产文件、脏工作树、非 40 位提交、配置或 `uv.lock` 漂移、生产文件哈希漂移以及 Python/PyArrow 版本不一致；源锁必须绑定代码锁 SHA-256。
- 源锁按逻辑路径排序且重复构建逐字节一致。
- 测试使用本地临时 HTTP 服务覆盖断点续传、错误 `Content-Range`、大小错误、MD5 错误、ZIP 路径穿越、重复成员、损坏中央目录、已存在目标拒绝覆盖和成功原子发布；测试不得访问公网。

**实现后本机与服务器验收：**

```bash
uv run --no-sync python -B -c 'import flow_probe.r2_protocol_contract'
uv run --no-sync pyright src/flow_probe/r2_protocol_contract.py
uv run --no-sync pytest -q tests/test_r2_protocol_contract.py
```

#### 任务 01R：源锁与 ns-3 共享父目录冲突修复

**依赖：** 任务 01 已绑定提交 `527531f2f188de21489311259dbb5fcf4f1731ee`；任务 04 已在 `runs/data-freeze-configs/r2-protocol-v1/` 发布 `ns3-config-manifest.jsonl` 与 `ns3-config-manifest.sha256`。

**根因：** 任务 01 把 `source_lock_root` 直接设为任务 04 已使用的共享父目录，并要求该目录事前不存在后整体原子改名，因此两项各自正确的并行制品无法共存。

**最小修复：**

- 将源锁专属根精确改为 `runs/data-freeze-configs/r2-protocol-v1/source-locks-v1`，其阶段根为同级 `source-locks-v1.partial`；任务 04 的两个 ns-3 清单继续留在父目录且逐字节不变。
- 只修改 `src/flow_probe/r2_protocol_contract.py`、`configs/r2_protocol_data_v1.yaml`、`src/flow_probe/r2_protocol_tqhc2.py`、`runs/launchers/r2-protocol-data-rebuild-v0/local-producer/tqhc2-handoff-params.json`、直接绑定该常量的最小测试和 `reports/report-task-01-contract.md`。后两项仅把任务 03 的消费路径同步到 `source-locks-v1`，不得改变移交数据、标签或校验条件。不得修改、移动、复制或删除 ns-3 清单，不得放宽“源锁专属根已存在即失败”和原子发布门禁。
- 修复后必须形成新提交并重建执行代码锁；旧提交和旧代码锁保留为历史证据，不得伪装为新路径的代码锁。
- 不运行独立冒烟、重复 Pyright、格式化或全量测试。代码与真实配置随正式源预检一起执行；运行时必须先核对父目录恰好保留已登记的 ns-3 文件，源锁专属根事前不存在，失败时保留报告且不得覆盖已有制品。

### 任务 02：GeNIS 原始行回接与单位门禁

**依赖：** 任务 01。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_genis.py`
- 新建 `tests/test_r2_protocol_genis.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-02-genis.md`

**公开接口：**

```python
iter_genis_10s_rows(archive: Path, inventory: GeNISArchiveInventory) -> Iterator[GeNISRawRow]
reconnect_genis_candidate(candidate: Path, archive: Path, config: R2ProtocolConfig) -> GeNISMaterialization
validate_genis_units(evidence: GeNISUnitEvidence) -> UnitGateResult
```

**最小行为：**

- 按 ZIP 成员名和 CSV 一基行号重建旧 `sample_id`，再严格复用 `sha256("dataset-candidate-genis-v0\\0" + old_sample_id)` 生成候选标识；不得按标签、协议、时间近邻或特征向量连接。
- 每条冻结候选必须恰好命中一条官方原始行；重复、缺失、多对一或未消费的目标候选均失败。
- 逐行复算标签、来源、`group_id` 和 8 个共同字段，与冻结候选做规范值和缺失掩码比较。
- `source_row_map` 只保留新旧标识、归档和成员 SHA-256、不可逆行引用、连接状态和记录哈希；不保留文件名、地址、端口、`FlowID` 或可逆行号。
- `TotBytes` 必须由 HERA 官方实现或对冻结候选对应原始包的网络层长度逐包复算证明为网络层字节。对比必须记录证据制品 SHA-256、算法和逐行精确整数一致数；不能证明即失败。
- `TcpRtt`、`SrcWin`、`DstWin` 必须分别有一手单位、缩放和聚合语义。经验相关、字段名称、少量样本拟合或推测不构成证据；缺任一项即保持 `NO-GO`。
- `Loss`、`Retrans` 只接受非负包计数；`SrcWin`/`DstWin` 明确标为通告接收窗口而非 `cwnd`。

**实现后本机与服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_genis.py tests/test_r2_protocol_genis.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_genis.py tests/test_r2_protocol_genis.py
uv run --no-sync pytest -q tests/test_r2_protocol_genis.py
```

### 任务 02R：GeNIS `TotBytes` Rust 逐包复算与口径裁决

**依赖：** 任务 02 单位审计已确认 `TcpRtt`、`SrcWin`、`DstWin` 语义级 `GO`，且 `TotBytes` 是唯一剩余单位阻塞。需要完整 GeNIS 权威归档及其可连接的原始包证据；只有特征 CSV 而无原始包或一手实现时必须输出 `NO-GO`，不得推测。

**文件白名单：**

- 新建 `tools/r2_genis_totbytes_verifier/Cargo.toml`
- 新建 `tools/r2_genis_totbytes_verifier/Cargo.lock`
- 新建 `tools/r2_genis_totbytes_verifier/src/**`
- 新建 `tools/r2_genis_totbytes_verifier/README.md`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-02-genis-totbytes-rust-verifier.md`

**正式输出：**

- `runs/data-audit/r2-genis-totbytes-rust-v1/run_manifest.json`
- `runs/data-audit/r2-genis-totbytes-rust-v1/flow_byte_comparison.parquet`
- `runs/data-audit/r2-genis-totbytes-rust-v1/summary.json`
- `runs/data-audit/r2-genis-totbytes-rust-v1/artifact_manifest.json`

**冻结输入补充：**

- 成员配对清单固定写入 `runs/data-audit/r2-genis-totbytes-rust-v1-inputs/member-map.jsonl`，按两份官方归档中 11 个 PCAPNG 与 11 个 10 秒 CSV 的规范化同名规则确定性生成并先冻结 SHA-256。
- 正式输出目录 `runs/data-audit/r2-genis-totbytes-rust-v1/` 在运行前必须不存在；不得把成员清单预写入该目录，也不得为复用输入放宽原子发布和拒绝覆盖门禁。

**最小行为：**

- 使用 Rust 流式读取原始包及冻结连接清单，在有界内存中对每个流同时累计二层线上字节与三层网络字节；不得使用标签、场景名、地址、端口或采集单元作为匹配捷径。
- 对每个冻结样本输出 CSV `TotBytes`、二层线上字节、三层网络字节、匹配状态、整数差值与证据哈希；重复、多对一、丢失和未消费样本直接失败。
- 只有冻结候选全量样本在事前声明的口径下精确一致，才允许将 `TotBytes` 改为 `GO`；相关性、抽样一致或总量接近均不足以过门禁。
- 运行目录写入工具提交、Rust 工具链、输入大小与 SHA-256、处理包数、峰值内存、耗时、错误计数和所有输出 SHA-256。
- 实现使用 `rust-skills`，生产二进制由一次 `cargo build --release` 生成；不运行 `cargo fmt`，不以合成数据或少量样本声称语义通过。

**当前阶段：** 先完成可编译工具、输入合同与运行参数；服务器开机后把权威原件拉取至本机，再运行全量裁决。

#### 任务 02S：GeNIS 持续时间量化语义架构审查

**触发原因：** Rust 全量审计已完成 11 个 PCAPNG 和 3,973 条候选处理，但先后暴露整数秒起止时间、科学计数法持续时间和 `670 ns` 包级跨度差异。连续三次解析或语义修复后仍未通过，禁止继续第四次补丁式修改。

**目标：** 基于 GeNIS/HERA/Argus 一手实现、字段格式和全体候选的只读误差分布，裁决 `Dur` 是精确点值、四舍五入值、截断值还是只能表示一个量化区间；同时判断流匹配唯一性是否应与持续时间相容性分开验收。不得根据单个失败样本选择容差。

**允许工作：** 只读检查原始论文、官方源码/文档、CSV 原始字符串、PCAP 首末时间和既有三版失败代码锁；可以生成发布根外的诊断报告与误差分布，但不得修改 Rust/Python 生产代码、数据、候选、阈值、标签或源归档。

**裁决门槛：** 只有一手实现或全体格式证据能够证明确定的量化规则时，才提出区间删失模型及下一次独立实现计划；区间必须由字段表示精度推导，并保持包数、字节、五元组和候选唯一性门禁不变。证据不足则保持 `NO-GO`，改为关闭公开数据 `Dur` 强监督或重新调用官方流导出器，不能继续放宽误差。

**输出：** `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-02s-genis-duration-semantics.md`，明确一手证据、全体误差分布、可证伪架构选项和唯一推荐，不修改实验源码。

### 任务 03：TQH 包序列、QUIC 线图像与聚合重算

**依赖：** 无实现依赖；任务 07 集成前必须通过任务 01 的正式模式校验。

**实现语言裁决（2026-07-31）：** 本轮继续使用既有 Python 解析与物化链路。当前没有 `Cargo.toml` 或可复用 Rust 物化器，而且现有 39 列模式、哈希、源锁和 QUIC 解析合同已绑定 Python 参照实现。将它们迁移到 Rust 预计需要 `1—2` 天和逐字节等价验证，而 Python 两次独立派生事前估时为 `2—6` 小时，读取约 98 GiB 原始数据的磁盘带宽也是瓶颈。Rust 只保留为数据合同冻结后的独立加速实现，不作为当前物化或训练的前置条件。若后续启用，必须与 Python 参照物逐项比较行数、列顺序、数据类型、缺失值、`sample_id`、排序、语义载荷 Merkle 和文件 SHA-256。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_tqhc2.py`
- 新建 `tests/test_r2_protocol_tqhc2.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-03-tqhc2.md`

**公开接口：**

```python
parse_quic_wire_image(frame: PcapFrame, context: QuicConnectionContext) -> QuicObservation
materialize_tqhc2_sequences(bindings: TQHSourceBindings, selected_ids: AbstractSet[str], work_dir: Path) -> TQHMaterialization
aggregate_packet_sequence(rows: Sequence[PacketObservation]) -> TQHAggregates
compare_tqhc2_materializations(left: Path, right: Path) -> TQHDeterministicComparison
write_tqhc2_handoff(materialization: TQHMaterialization, comparison: TQHDeterministicComparison, locks: TQHHandoffLocks, output: Path) -> TQHHandoffManifest
verify_tqhc2_handoff(root: Path, manifest: TQHHandoffManifest, locks: TQHHandoffLocks) -> TQHHandoffReceipt
```

**最小行为：**

- 不修改旧 `tqh_c2.py` 和旧候选构建器；新模块只复用其稳定 PCAP 迭代和基础 IP 解析接口，QUIC 解析和跨行组重组独立实现。
- 在读取大包表前加载冻结样本 ID 集并进行列裁剪；按稳定哈希桶落盘，再按 `(sample_id, packet_index)` 排序合并，不能依赖行组连续性。
- 基础包字段逐条与上游一致，重算 12 个聚合比例、共同字段和基础序列哈希。
- QUIC 只实现第 3.4 节允许字段。长首部以首字节 `0x80` 位识别，读取四字节网络序版本、目的连接标识长度与源连接标识长度；v1 仅在两个长度均不超过 20 且载荷足够时按首字节 `0x30` 位解释 `INITIAL/0RTT/HANDSHAKE/RETRY`。版本 0 固定为版本协商，未知非零版本不解释 v1 类型。
- v1 短首部只在已绑定上下文中读取 `0x20` 旋转位；`0x40` 固定位可记录但不能作为拒绝条件。测试覆盖 v1 长首部、版本协商、未知版本、可信上下文短首部、无上下文短首部、固定位随机化、旋转位、截断、连接标识变化和禁止原始连接标识输出。
- `profile=B` 及其他 profile 不参与 QUIC 判定；没有受控配置或日志真值时 `protocol_target` 不得写 QUIC。
- 包序列主键、首包、单调时间、方向、网络层长度、TCP 标志适用性、截断掩码和旧/新序列哈希全部有失败测试。
- 正式本机物化必须从两个空目录独立执行；比较器逐文件核对四项载荷的字节、行数、列顺序、数据类型、模式哈希和语义载荷 Merkle，任何差异都不选边、不发布。
- 移交清单必须绑定第 2.5 节全部源锁、代码锁、配置和双派生比较对象；写出与服务器验收都拒绝额外文件、符号链接、绝对路径、敏感字段、源锁变化和代码锁变化。
- 服务器消费接口只读接收已核验规范根，不读取不存在的本机 PCAP 路径；测试证明同一移交根可供后续两个空目录构建独立读取，且任一载荷单字节变化、模式变化或清单重放均失败。

**实现后本机与服务器验收：**

```bash
uv run --no-sync python -B -c 'import flow_probe.r2_protocol_tqhc2'
uv run --no-sync pyright src/flow_probe/r2_protocol_tqhc2.py
uv run --no-sync pytest -q tests/test_r2_protocol_tqhc2.py
```

### 任务 04：ns-3 配对矩阵生成

**依赖：** 无实现依赖；任务 05 启动前必须通过任务 01 的正式模式校验。

**文件白名单：**

- 新建 `src/flow_probe/r2_ns3_protocol_matrix.py`
- 新建 `configs/r2_ns3_protocol_matrix_v1.yaml`
- 新建 `tests/test_r2_ns3_protocol_matrix.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-04-ns3-matrix.md`

**公开接口：**

```python
generate_base_configs(config: R2NS3MatrixConfig) -> Sequence[BaseProtocolConfig]
expand_protocol_pairs(base: Sequence[BaseProtocolConfig]) -> Sequence[ProtocolRunConfig]
write_frozen_manifest(configs: Sequence[ProtocolRunConfig], output_dir: Path) -> MatrixReceipt
```

**最小行为：**

- 精确生成第 5.1 节的 256 个基础配置和 512 条协议运行。
- 每个基础配置恰有一个 TCP 和一个普通 UDP，除协议外的规范配置 JSON 与种子完全相同。
- 每个划分的标签、到达过程、队列和负载覆盖符合固定因子设计；协议不能由标签、列表奇偶、配置标识或种子预测。
- 输出清单在相同配置下逐字节一致，已存在输出拒绝覆盖。
- 测试显式防止复现旧 `traffic_mode` 与 `transport` 共用奇偶索引的捷径。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_ns3_protocol_matrix.py tests/test_r2_ns3_protocol_matrix.py
uv run --no-sync ruff check src/flow_probe/r2_ns3_protocol_matrix.py tests/test_r2_ns3_protocol_matrix.py
uv run --no-sync pytest -q tests/test_r2_ns3_protocol_matrix.py
```

#### 任务 04R：拥塞控制身份合同修复

**根因：** 任务 04 配置与 512 条冻结清单错误声明 `ns3::TcpCubic`，而本计划、任务 05 C++ 场景及 Python 审计固定使用 `ns3::TcpNewReno`。第二次正式矩阵的首个 TCP/UDP 配对均因此在 `truth_tcp_congestion_control` 身份校验处安全失败；配对回执已证明该冲突，PPP 头修复本身不受影响。

**唯一裁决：** 保留章级计划既定的 `ns3::TcpNewReno`，不得临时把场景切换为 Cubic。只允许修正任务 04 配置、确定性重生成 256 个基础配置/512 条协议清单与摘要，并更新任务 05 运行器、受控参数、直接测试和任务 04/05 报告中的清单与配置哈希绑定。配置因子、种子、顺序、协议、标签、拓扑和输出字段必须逐项不变。

**失败证据与正式重启：** 第二次失败输出必须原子归档到独立的 `runs/ns3-data/r2-protocol-paired-v0.failed-attempt2-cubic-contract/`，不得删除、覆盖或混入新矩阵。修复后使用新的 `runs/launchers/r2-ns3-protocol-matrix-v0-attempt3/`，并从事前不存在的固定输出根重新执行。不得运行独立冒烟、格式化、Pyright 或全量测试；首个正式配对继续承担编译、身份、120 窗、双守恒和 TCP 状态断言。

### 任务 05：ns-3 场景、TCP trace 与可恢复运行器

**依赖：** 任务 04；服务器 ns-3.48 trace source 只读核验完成。

**文件白名单：**

- 新建 `ns3/r2_protocol_queue_scenario.cc`
- 新建 `src/flow_probe/r2_ns3_protocol_runner.py`
- 新建 `scripts/run_r2_ns3_protocol_matrix.sh`
- 新建 `tests/test_r2_ns3_protocol_runner.py`
- 新建 `tests/test_run_r2_ns3_protocol_matrix_wrapper.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-05-ns3-runner.md`

**公开接口：**

```python
audit_ns3_trace_contract(ns3_root: Path, scenario_source: Path) -> NS3TraceContract
run_protocol_matrix(ns3_root: Path, manifest: Path, output_dir: Path, resume: bool) -> MatrixRunSummary
validate_protocol_pair(pair_dir: Path, trace_contract: NS3TraceContract) -> PairValidation
```

**最小行为：**

- C++ 场景使用显式 TCP socket 或可验证配置路径取得 `CongestionWindow` trace，固定 `ns3::TcpNewReno`，写出 ns-3 版本、trace 名、聚合方式和适用掩码。
- 每窗直接写共同公开观测、共享队列精确计数、容量积分、已核验 TCP 状态或 UDP 应用状态；不得由公开统计反推训练期真值。
- 下游丢失和接收端计数必须与网络层字节口径一致，不能用应用载荷字节替代网络层字节守恒。
- 运行器逐配置写 `.partial` CSV 和状态回执，成功校验后原子发布单运行目录；重启只跳过配置哈希、源码哈希、CSV 哈希和验收状态均一致的已完成运行。
- 每条配置 JSON、TCP/UDP CSV 和成功或失败回执都记录逻辑相对路径、字节数与 SHA-256，并在总运行结束后并入 `source-lock.json`；失败配置不能从源清单消失。
- 一侧协议失败时配对组整体不进入序列，但两侧回执均保留。守恒残差非零、窗口不是 120、TCP 缺 `cwnd`、UDP 出现 TCP 状态、配置哈希不配对均失败。
- 包装器先 `source ~/.bashrc`，只使用 CPU，不初始化 SwanLab，接受一个受控参数 JSON，并由统一远程启动器持久化日志与状态。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_ns3_protocol_runner.py tests/test_r2_ns3_protocol_runner.py tests/test_run_r2_ns3_protocol_matrix_wrapper.py
uv run --no-sync ruff check src/flow_probe/r2_ns3_protocol_runner.py tests/test_r2_ns3_protocol_runner.py tests/test_run_r2_ns3_protocol_matrix_wrapper.py
bash -n scripts/run_r2_ns3_protocol_matrix.sh
uv run --no-sync pytest -q tests/test_r2_ns3_protocol_runner.py tests/test_run_r2_ns3_protocol_matrix_wrapper.py
```

最小服务器场景验收只运行一个基础配置的 TCP/UDP 配对，确认编译、120 窗、双守恒和 `cwnd` 后停止；不得把该冒烟结果混入正式矩阵。

#### 任务 05R：`PhyRxDrop` 网络层字节语义修复

**根因：** ns-3.48 的 `PointToPointNetDevice::Receive` 在错误分支先触发 `PhyRxDrop`，只有未丢包分支随后才调用 `ProcessHeader` 移除 PPP 头；当前场景在回调中直接累计 `packet->GetSize()`，因此把 2 字节 PPP 头错误计入网络层字节。Python 审计原先要求相反的生命周期顺序，正式入口据此安全失败，未产生矩阵数据。

**文件白名单：** `ns3/r2_protocol_queue_scenario.cc`、`src/flow_probe/r2_ns3_protocol_runner.py`、`configs/r2_ns3_protocol_matrix_runtime_v0.json`、直接绑定该语义的最小测试与 `reports/report-task-05-ns3-runner.md`。

**唯一允许的修复：** `OnDownstreamErrorLoss` 使用只读 `PeekHeader(PppHeader&)` 验证 PPP 头并扣除实际解析长度；包长不足、解析失败或头长不符合一手源码时立即失败。审计器改为同时证明 `PhyRxDrop` 前 PPP 头仍存在、`PppHeader` 的序列化长度以及场景显式解析扣除。禁止固定盲减、容差抵消、改字段定义或改 256 组/512 条冻结矩阵。

**正式重启：** 更新场景哈希及受控参数哈希后同步白名单文件，使用新的 `runs/launchers/r2-ns3-protocol-matrix-v0-attempt2/` 保存启动状态、能力清单和日志；不得覆盖第一次失败证据。输出根仍为事前不存在的 `runs/ns3-data/r2-protocol-paired-v0/`。不运行独立冒烟、格式化、Pyright 或全量测试，首个正式配对承担编译、120 窗、双守恒和 TCP 状态运行时断言；失败即停并保留证据。

### 任务 06：协议校准和未知回退

**依赖：** 任务 03。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_calibration.py`
- 新建 `tests/test_r2_protocol_calibration.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-06-calibration.md`

**公开接口：**

```python
fit_protocol_router(train_fit: ProtocolFrame, config: CalibrationConfig) -> FrozenProtocolRouter
fit_temperature(router: FrozenProtocolRouter, calibration: ProtocolFrame) -> TemperatureCalibration
apply_unknown_policy(predictions: ProtocolPredictions, config: CalibrationConfig) -> RoutedProtocols
```

**最小行为：**

- 训练输入只含允许的协议观测；二元攻击标签、来源名、profile、地址、端口和配置字段进入即失败。
- 温度只读取 calibration，测试和开放协议的读取由测试替身显式阻止。
- 置信低于 0.80、未知 QUIC 版本、`AMBIGUOUS` 或协议证据冲突全部进入 `UNKNOWN` 并关闭 TCP/UDP 专家。
- 相同训练、配置和库版本产生逐字节相同的参数与预测；报告指标不含样本敏感字段。
- 提供后续模型可调用的冻结数组接口，并测试攻击分类标签变化不改变路由结果。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_calibration.py tests/test_r2_protocol_calibration.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_calibration.py tests/test_r2_protocol_calibration.py
uv run --no-sync pytest -q tests/test_r2_protocol_calibration.py
```

### 任务 07：统一视图、划分和 A/B/C/D 绑定

**依赖：** 任务 02、03、05、06 的接口冻结。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_views.py`
- 新建 `tests/test_r2_protocol_views.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-07-views.md`

**公开接口：**

```python
materialize_common_view(inputs: R2SourceFrames, schema: R2Schema) -> Table
materialize_protocol_view(inputs: R2SourceFrames, routing: RoutedProtocols, schema: R2Schema) -> Table
materialize_physics_view(ns3: NS3ValidatedRuns, schema: R2Schema) -> Table
build_split_manifests(master: Table, config: SplitConfig) -> SplitManifests
bind_information_budget(dataset_root: Path, group: Literal["A", "B", "C", "D"]) -> BudgetBinding
```

**最小行为：**

- 10,000 条分类候选的 ID、来源配额、顺序、标签和共同字段与冻结输入绑定；新 ns-3 仅为 `physics_auxiliary`。
- 划分严格按第 4.1 节的组哈希算法，组不跨划分，现有验证/测试和开放集不回流训练。
- A/C 分类器只见 `x_common`，B/D 分类器见完全相同的 `x_common+x_proto`，C/D 物理路由完全相同，四组物理辅助真值集合完全相同。
- `packet_view_available` 和空序列分支对四组完全相同。
- 所有模型视图执行禁止字段扫描；`protocol_target` 和训练期物理真值不得被预算绑定为分类输入。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_views.py tests/test_r2_protocol_views.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_views.py tests/test_r2_protocol_views.py
uv run --no-sync pytest -q tests/test_r2_protocol_views.py
```

### 任务 08：连接、单位、泄漏、列联和重复审计

**依赖：** 任务 02、03、07。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_audits.py`
- 新建 `tests/test_r2_protocol_audits.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-08-audits.md`

**公开接口：**

```python
run_join_audit(materialization: R2Materialization) -> Mapping[str, object]
run_unit_audit(materialization: R2Materialization) -> Mapping[str, object]
run_leakage_audit(materialization: R2Materialization) -> Mapping[str, object]
build_protocol_label_contingency(materialization: R2Materialization) -> Mapping[str, object]
run_duplicate_screen(materialization: R2Materialization) -> Mapping[str, object]
build_tqh_control(control: TQHControl, materialization: R2Materialization) -> ControlBinding
```

**最小行为：**

- 五份构建期审计文件使用固定键顺序和状态枚举 `pass/fail/not_applicable`，不得因失败而省略证据。
- 生成第 4.3 节全部负对照绑定和非空检查；敏感地址/端口基线只接受隔离审计摘要。
- 重复检查覆盖包序列、共同特征、源记录和组哈希；跨划分标签冲突硬失败。
- 单位审计逐字段记录规范单位、来源单位、一手证据 SHA-256、换算公式和状态；不接受自由文本“看起来一致”。
- 审计输出只含计数、哈希和无敏感字段的分层标签。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_audits.py tests/test_r2_protocol_audits.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_audits.py tests/test_r2_protocol_audits.py
uv run --no-sync pytest -q tests/test_r2_protocol_audits.py
```

### 任务 09：R2 构建编排器

**依赖：** 任务 01 至 08。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_rebuild.py`
- 新建 `tests/test_r2_protocol_rebuild.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-09-rebuild.md`

**公开接口：**

```python
rebuild_r2_protocol_dataset(project_root: Path, config_path: Path, output: Path) -> BuildReceipt
main() -> None
```

**最小行为：**

- 固定入口只接受 `python -m flow_probe.r2_protocol_rebuild --config configs/r2_protocol_data_v1.yaml --output runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial` 或将 build-a 精确替换为 build-b 的第二条命令。
- 启动时核对发布根不存在、源锁、代码锁、TQH 移交清单、配置、库版本、可用磁盘和输出命名。
- 第一次启动要求输出不存在；只有目录含合法 `_INCOMPLETE.json` 且源锁、配置、代码和模式哈希完全相同时才允许阶段恢复。陌生目录或哈希变化立即失败。
- build-a 与 build-b 分别从空目录只读消费同一已验收 TQH 规范移交根，不重新访问本机原始路径，也不得复制移交根后绕过清单核验；两次构建都独立调用 `verify_tqhc2_handoff` 并把清单 SHA-256 写入构建回执和冻结清单。
- 按固定阶段写主记录、四视图、映射、五份构建期审计、字段角色、模式、源制品和不含自指文件的载荷摘要。
- Parquet 参数固定为 `version=2.6`、`compression=zstd`、`compression_level=9`、`use_dictionary=false`、`write_statistics=true`、`data_page_version=1.0`、`row_group_size=65536`；运行时 PyArrow 完整版本和 `uv.lock` SHA-256 写入冻结清单。
- 构建器不得写 `deterministic-build-comparison.json` 和最终 `artifact-checksums.json`，不得发布；这些由验证器完成。
- 失败保留 `_INCOMPLETE.json` 和阶段回执，禁止留下看似完整的最终树。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_rebuild.py tests/test_r2_protocol_rebuild.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_rebuild.py tests/test_r2_protocol_rebuild.py
uv run --no-sync pytest -q tests/test_r2_protocol_rebuild.py
```

### 任务 10：双构建验证与原子发布

**依赖：** 任务 09。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_validate.py`
- 新建 `tests/test_r2_protocol_validate.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-10-validate.md`

**公开接口：**

```python
compare_independent_builds(left: Path, right: Path) -> DeterministicComparison
finalize_and_publish(left: Path, right: Path, publication: Path) -> PublicationReceipt
main() -> None
```

**最小行为：**

- 固定入口为 `python -m flow_probe.r2_protocol_validate --left runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial --right runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial`。
- 验证两边源锁、配置、代码、模式、行数、列顺序、数据类型、主键、样本顺序、划分和每个语义载荷文件 SHA-256 一致。
- 先在内存生成一份规范比较对象，再原子写入两边相同的 `audits/deterministic-build-comparison.json`。
- 比较对象只使用逻辑名称 `build-a` 与 `build-b`，记录逐相对文件哈希、行数、模式和载荷 Merkle；不得写两边绝对路径、时间、主机名或进程信息。
- `freeze-manifest.json` 绑定源、配置、代码、模式、行数、A/B/C/D 预算哈希和语义载荷 Merkle 摘要。Merkle 固定排除 `freeze-manifest.json`、`artifact-checksums.json` 和确定性比较文件，避免自指。
- `artifact-checksums.json` 覆盖除自身外全部最终发布文件，包括冻结清单和确定性比较文件。
- 移除两边 `_INCOMPLETE.json` 和工作分片后再次逐文件比较；任何差异都不选边、不发布。
- 发布根不存在、build-a 与发布根同文件系统且所有 P0 通过时，才以 `os.replace(build-a, publication)` 原子发布。build-b 不删除。
- 测试覆盖字节差异、列顺序差异、自指排除、发布根已存在、跨文件系统、崩溃后重入和 build-b 保留。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_validate.py tests/test_r2_protocol_validate.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_validate.py tests/test_r2_protocol_validate.py
uv run --no-sync pytest -q tests/test_r2_protocol_validate.py
```

### 任务 11：混合主机预检、移交、双构建包装和重启恢复

**依赖：** 任务 01、03、09、10。

**文件白名单：**

- 新建 `scripts/run_r2_protocol_source_preflight.sh`
- 新建 `scripts/run_r2_protocol_tqhc2_handoff.sh`
- 新建 `scripts/run_r2_protocol_data_rebuild.sh`
- 新建 `tests/test_run_r2_protocol_source_preflight_wrapper.py`
- 新建 `tests/test_run_r2_protocol_tqhc2_handoff_wrapper.py`
- 新建 `tests/test_run_r2_protocol_data_rebuild_wrapper.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-11-remote.md`

**最小行为：**

- 三个包装器都先 `source ~/.bashrc`，接受单个参数 JSON，验证 `host_role=local_producer/server_consumer`、项目根、GeNIS/TQH/ns-3 外部源根、输入锁、输出白名单和固定命令，不内嵌临时代码。绝对外部源根只存在于发布根外的参数与运行回执，冻结源锁和移交清单仅写逻辑路径。
- 数据预检、构建和验证设置 `CUDA_VISIBLE_DEVICES` 为空，不调用 `nvidia-smi` 作为门禁，不导入或初始化 SwanLab。
- 原始 TQH 上传、镜像或把原始根列入同步清单必须在磁盘检查和网络连接前失败；任何参数都不得用“大文件传输”模式绕过该拒绝。
- 本机源预检和 TQH 双派生门槛为 `max(3221225472, 3 × expected_handoff_bytes + optional_genis_staging_bytes)`；首轮 `expected_handoff_bytes` 依据存储审计的 0.8 GiB 上界固定为向上取整的 `858993460`，复制完整 GeNIS 时 `optional_genis_staging_bytes=380755720`，只读挂载时为零。实物超过该上界即停止并更新发布根外 `local-producer/handoff-sizing-receipt.json` 与计划，不得在运行中放宽。
- 服务器接收门槛为 `2 × handoff_manifest.total_size_bytes + 1073741824`，只覆盖 `.incoming.partial`、原子发布后的规范根和 1 GiB 安全余量，不适用原始源容量。
- 服务器最终双构建门槛为 `max(3 × expected_publication_bytes, 2 × handoff_manifest.total_size_bytes) + 1073741824`；取消与实际制品规模无关的固定 20 GiB 下限。`expected_publication_bytes` 必须来自通过目标行为门禁的完整干跑或前置阶段清单，并固定写入发布根外 `server-consumer/publication-sizing-receipt.json`；收据缺失、代码锁不符或数值小于实际已写字节即失败。当前约 14.40 GiB 可用空间只有满足该公式时才允许继续，否则仍须释放空间或扩容，禁止手工跳过。
- 任一门槛不足都必须在创建 `.partial`、连接传输端或写源锁前失败，并记录所用字节数、公式输入和失败阶段到发布根外回执。
- 固定启动根为 `runs/launchers/r2-protocol-data-rebuild-v0/{local-producer,server-consumer}/`，至少写 `status.txt`、`launcher.log`、`params.json`、`capabilities.json`、`transfer-receipt.json` 和 `receipt.json`。这些运行回执不进入冻结数据。
- 本机包装器先验证干净代码锁和完整 GeNIS，再执行完整源预检及两个空目录的 TQH 派生；服务器包装器只接收移交清单枚举项，接收后重新计算全部哈希、模式、行数与 Merkle，并验证同一提交的代码锁，任何差异都不得进入数据重建。
- 状态为 `running` 且进程或 screen 仍存在时只读观察，禁止重复启动。状态为 `failed` 或进程消失时，先核验现有源锁和 `.partial` 的阶段状态，再从首个未完成阶段恢复。
- 状态为 `finished` 且发布根存在时只做 `artifact-checksums.json` 复核，不再次运行构建。发布根存在但状态不一致时停止人工审查。
- build-a 与 build-b 必须由两个独立 Python 进程从各自空目录开始；不得复制其中一份作为另一份。
- 测试覆盖原始根上传拒绝、未跟踪或脏代码拒绝、损坏 GeNIS 拒绝、A/C 阻塞证据保留、三类磁盘门槛边界、额外文件、符号链接、传输截断、单字节变化、模式变化、旧清单重放、接收原子性和重启恢复。静态与运行验收只使用真实导入、Pyright、目标测试和必要冒烟。

**实现后本机与服务器验收：**

```bash
uv run --no-sync python -B -c 'import flow_probe.r2_protocol_contract, flow_probe.r2_protocol_tqhc2, flow_probe.r2_protocol_rebuild'
uv run --no-sync pyright src/flow_probe/r2_protocol_contract.py src/flow_probe/r2_protocol_tqhc2.py src/flow_probe/r2_protocol_rebuild.py
bash -n scripts/run_r2_protocol_source_preflight.sh scripts/run_r2_protocol_tqhc2_handoff.sh scripts/run_r2_protocol_data_rebuild.sh
uv run --no-sync pytest -q tests/test_run_r2_protocol_source_preflight_wrapper.py tests/test_run_r2_protocol_tqhc2_handoff_wrapper.py tests/test_run_r2_protocol_data_rebuild_wrapper.py
```

### 任务 12：全链路审查与读取兼容门禁

**依赖：** 任务 01 至 11 全部实现且各自行为测试、哈希、必要冒烟和制品隔离通过；独立复审可以保持 `review_pending` 并行进行。

**文件白名单：**

- 新建 `src/flow_probe/r2_protocol_baseline_adapter.py`
- 新建 `tests/test_r2_protocol_end_to_end.py`
- 新建 `tests/test_r2_protocol_gradient_contract.py`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/report-task-12-end-to-end.md`
- 新建 `.Codex/docs/sdd/task-r2-data-rebuild/reports/review-task-12-final.md`

**公开接口：**

```python
load_qwen_records(dataset_root: Path, group: Literal["A", "B", "C", "D"], split: str) -> Iterator[dict[str, object]]
load_tabular_matrix(dataset_root: Path, group: Literal["A", "B", "C", "D"], split: str) -> TabularBatch
load_distilbert_records(dataset_root: Path, group: Literal["A", "B", "C", "D"], split: str) -> Iterator[dict[str, object]]
load_physics_batches(dataset_root: Path, group: Literal["A", "B", "C", "D"], split: str) -> Iterator[PhysicsBatch]
```

**最小行为：**

- 使用微型三源夹具运行两个独立构建和验证器，确认最终树、模式、哈希、A/B/C/D 绑定、失败保留和原子发布。
- 微型全链路必须使用彼此隔离的本机生产者根和服务器消费者根，证明只靠源锁、代码锁、移交清单和四项 TQH 派生载荷可完成消费；原始 TQH 路径出现在消费者参数、移交单字节变化或 A/C 状态被提升为已核验时必须失败。
- 读取兼容测试必须证明 Qwen、HGB、XGBoost、DistilBERT、状态仅基线和统一物理基线能通过统一预算接口读取相应视图；该测试只做解析和一个批次前向形状检查，不启动训练。
- 适配器只读取冻结视图和预算绑定，不复制数据；Qwen 与 DistilBERT 使用相同规范文本字段顺序，HGB 与 XGBoost 使用相同数值矩阵，状态仅与统一物理基线使用相同物理辅助运行哈希。
- 测试证明 A/C 不读取 `x_proto`，B/D 分类器读取完全相同 `x_proto`，C/D 物理路由相同，攻击标签变化不能改变冻结路由。
- 纯 CPU 梯度测试把冻结路由转换为不可训练张量，证明攻击分类损失对识别器代理参数和温度的梯度为 `None` 或精确零，同时独立协议损失仍能在协议识别训练阶段更新参数。
- 最终审查代理与 `review_pending` 运行并行逐项核对本计划、R2 合同和远程执行合同；不得因复审尚未结束阻塞启动。发现严重或重要问题时必须立即停止相关运行、作废受影响制品，再交由新的修复代理最小修复并重跑目标门禁。

**实现后服务器验收：**

```bash
uv run --no-sync black src/flow_probe/r2_protocol_baseline_adapter.py tests/test_r2_protocol_end_to_end.py tests/test_r2_protocol_gradient_contract.py
uv run --no-sync ruff check src/flow_probe/r2_protocol_baseline_adapter.py tests/test_r2_protocol_end_to_end.py tests/test_r2_protocol_gradient_contract.py
uv run --no-sync pytest -q tests/test_r2_protocol_end_to_end.py tests/test_r2_protocol_gradient_contract.py
```

---

## 7. 并行执行波次

### 第一波：立即可并行的实现任务

1. **任务 01：合同常量、模式、源预检和代码锁修订。** 冻结所有下游共享接口；目标行为门禁通过并完成正式提交绑定后即可进入 `review_pending`，复审并行。
2. **任务 03：TQH 包序列、QUIC 与移交合同修订。** 仅使用合同中已经明确的包模式和独立新文件，不等待 GeNIS 单位证据；正式实物运行等待任务 01 代码锁通过。
3. **任务 04：ns-3 配对矩阵。** 只生成配置，不访问服务器或运行模拟。

第一波三个任务文件完全不重叠，且各自夹具行为测试不要求另一任务先落地。任务 03 和 04 的最终审查必须额外验证其固定枚举、字段顺序、移交绑定和矩阵合同与任务 01 的正式配置一致；正式源预检与 TQH 派生不得在代码锁前运行。

### 第二波：源与真值并行

1. **任务 02：GeNIS 回接与单位门禁。** 依赖任务 01；本机源预检使用第 2.3 节已核验完整 ZIP，服务器下游只读消费其成员锁和后续规范派生。
2. **任务 05：ns-3 场景与运行器。** 依赖任务 04，并在服务器恢复后先做 trace 只读核验。
3. **任务 06：协议校准。** 依赖任务 03。

### 第三波：统一物化

1. 任务 07 完成视图、划分和预算。
2. 任务 08 在任务 07 接口冻结后并行实现审计；同一物化夹具由任务 07 提供，只读复用。

### 第四波：构建、验证和远程包装

1. 任务 09 构建编排器。
2. 任务 10 双构建验证器。
3. 任务 11 混合主机包装、移交和恢复。
4. 任务 12 全链路审查。

不得跨波次提前运行正式源物化或 ns-3 矩阵。并行仅指代码实现和只读输入审计并行，不允许在代码锁、GeNIS 完整性或移交门禁前启动正式源预检。

---

## 8. 正式混合主机执行顺序

主代理必须先按恢复协议核对现有子代理、最新日志、进程、screen 和两端磁盘，再严格执行以下顺序。任何跨主机步骤都以逻辑路径和内容哈希识别制品，不以本机或服务器绝对路径作为身份。

1. 在本机和服务器核对同一 40 位 Git 提交、干净工作树、`uv.lock`、配置及生产代码逐文件 SHA-256；生成并双端验证 `execution-code-lock.json`。任务 01/03 任一生产文件未跟踪或工作树脏即停止。
2. 从已核验服务器权威原件取得完整 GeNIS ZIP 到第 2.3 节新暂存路径或只读挂载；取得动作必须有发布根外回执。本机重新核对 `380755720` 字节、MD5、固定 SHA-256、CRC、路径安全和 11 个物化成员。禁止读取损坏旧副本。
3. 在本机运行任务 01 完整源预检，读取本机只读 TQH 原始源、旧冻结制品和完整 GeNIS，生成四份源/代码锁。A/C 提取器必须保持 `blocked`；216 个非提取器源文件任一大小或 SHA-256 变化即停止。

```bash
bash scripts/run_r2_protocol_source_preflight.sh \
  runs/launchers/r2-protocol-data-rebuild-v0/local-producer/source-preflight-params.json
```

4. 在本机从两个空目录独立运行任务 03，逐文件一致后原子发布规范 TQH 移交根并生成 `tqhc2-handoff-manifest.json`；任何差异都不选边、不传输。

```bash
bash scripts/run_r2_protocol_tqhc2_handoff.sh \
  runs/launchers/r2-protocol-data-rebuild-v0/local-producer/tqhc2-handoff-params.json
```

5. 本机移交包装器只同步清单、四份锁和四项 TQH 载荷到服务器 `.incoming.partial`。服务器使用消费者参数再次运行同一包装器，复核文件集合、大小、SHA-256、行数、模式、Merkle、代码锁和源锁后原子接收；同步参数出现 TQH 原始根、PCAP 或标签目录即停止。

```bash
bash scripts/run_r2_protocol_tqhc2_handoff.sh \
  runs/launchers/r2-protocol-data-rebuild-v0/server-consumer/tqhc2-handoff-params.json
```

6. 在服务器核验 HERA 或原始包证据，闭合 `TotBytes`、`TcpRtt`、`SrcWin`、`DstWin`。任一未闭合则记录 `unit-audit` 失败并停止，不启动最终双构建。
7. 在服务器只读核验 ns-3.48 trace source，生成 `ns3-trace-contract.json`；缺 `CongestionWindow` 即停止。随后冻结并哈希 256 个基础配对配置，以可恢复 CPU 运行器生成 512 条运行；不使用 SwanLab。
8. 完成全部实现、真实导入、Pyright、目标 pytest、必要 C++ 配对冒烟、哈希与制品隔离后立即以 `review_pending` 继续；独立复审并行且不得阻塞启动。本次计划修订不执行格式化。
9. 服务器消费者包装器先按任务 11 的实际制品公式核对磁盘，再从空目录分别执行 build-a 和 build-b；两个构建独立复核并只读消费同一 TQH 规范移交根。正式入口为：

```bash
bash scripts/run_r2_protocol_data_rebuild.sh \
  runs/launchers/r2-protocol-data-rebuild-v0/server-consumer/data-rebuild-params.json
```

包装器内部只允许以下两条固定构建命令：

```bash
python -m flow_probe.r2_protocol_rebuild \
  --config configs/r2_protocol_data_v1.yaml \
  --output runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial

python -m flow_probe.r2_protocol_rebuild \
  --config configs/r2_protocol_data_v1.yaml \
  --output runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial
```

10. 执行验证和原子发布：

```bash
python -m flow_probe.r2_protocol_validate \
  --left runs/data-frozen/dataset-candidate-r2-protocol-v0.build-a.partial \
  --right runs/data-frozen/dataset-candidate-r2-protocol-v0.build-b.partial
```

11. 发布后只读复核全部制品哈希、10,000 条候选身份、源配额、六个划分、A/B/C/D 绑定、TQH 移交清单绑定和本机/服务器两份 build-b 留存。
12. P1 负对照、协议校准、覆盖和六类基线读取门禁全部通过后，才允许另立正式实验计划。SwanLab 仅在该后续正式实验中启用。

混合主机专项验收命令固定为：

```bash
uv run --no-sync python -B -c 'import flow_probe.r2_protocol_contract, flow_probe.r2_protocol_tqhc2, flow_probe.r2_protocol_rebuild, flow_probe.r2_protocol_validate'
uv run --no-sync pyright src/flow_probe/r2_protocol_contract.py src/flow_probe/r2_protocol_tqhc2.py src/flow_probe/r2_protocol_rebuild.py src/flow_probe/r2_protocol_validate.py
bash -n scripts/run_r2_protocol_source_preflight.sh scripts/run_r2_protocol_tqhc2_handoff.sh scripts/run_r2_protocol_data_rebuild.sh
uv run --no-sync pytest -q tests/test_r2_protocol_contract.py tests/test_r2_protocol_tqhc2.py tests/test_run_r2_protocol_source_preflight_wrapper.py tests/test_run_r2_protocol_tqhc2_handoff_wrapper.py tests/test_run_r2_protocol_data_rebuild_wrapper.py tests/test_r2_protocol_rebuild.py tests/test_r2_protocol_validate.py
```

---

## 9. P0 发布门禁

- [ ] 全部源逻辑路径、大小、SHA-256、配置哈希和代码锁完整，旧冻结制品哈希未变；本机与服务器提交、`uv.lock`、生产代码哈希和 PyArrow 版本一致，工作树干净。
- [ ] GeNIS 正式 ZIP 大小、官方 MD5 和固定归档 SHA-256 匹配，10 秒尺度 11 个 CSV 的 SHA-256 和清单已冻结；本机损坏副本未被读取。
- [ ] A/C 历史提取器严格保留 `approved_manifest_only_blocked` / `blocked`，未生成、复制或伪造旧快照，报告未宣称其已实物核验。
- [ ] 本机两次独立 TQH 派生逐文件一致；服务器接收文件集合、大小、SHA-256、行数、模式、Merkle、源锁和代码锁与移交清单完全一致，未上传 TQH 原始根。
- [ ] 10,000 条共同候选、来源数量和两份验证清单与冻结身份完全一致。
- [ ] 所有表主键唯一，连接一对一，标签和分组不变，包索引连续。
- [ ] 8 个共同字段名称、顺序、单位、空值和换算通过；`TotBytes`、`TcpRtt`、`SrcWin`、`DstWin` 无猜测或未决语义。
- [ ] TQH 包聚合、旧基础序列哈希、新 QUIC 序列哈希、传输比例和截断掩码一致。
- [ ] TQH QUIC 识别不使用 profile、地址、端口或攻击标签，未知版本和低置信均回退共享专家。
- [ ] 新 ns-3 具有 TCP/普通 UDP 配对、至少 95% 规定覆盖、逐窗包与网络层字节零残差，以及直接 trace 的 `cwnd`。
- [ ] UDP 未携带伪 TCP 状态，TCP/UDP 的公开字段和物理真值口径一致。
- [ ] 所有禁止字段均不在模型视图、冻结临时分片或日志摘要中。
- [ ] 协议校准集独立，开放协议拒识存在，攻击分类标签不能改变路由，后续分类梯度合同已由接口测试锁定。
- [ ] A/B/C/D 候选、顺序、标签、划分、共同输入和物理辅助真值哈希一致；B/D 与 C/D 的 `x_proto` 完全相同。
- [ ] 五份构建期审计均通过，协议标签列联表明确标出可支持和不可支持的论断单元。
- [ ] build-a 与 build-b 所有最终文件逐字节一致，发布根原先不存在，发布使用同文件系统原子重命名，build-b 未删除。
- [ ] 三类磁盘门槛均使用任务 11 的实际制品公式并写入回执；没有使用固定 20 GiB、人工估算缺失值或手工跳过门禁。

## 10. P1 实验启动门禁

- [ ] 协议字段置换、全掩码、去握手、留一 profile、协议标签匹配子集和隔离地址/端口审计均可生成且非空。
- [ ] ns-3 配对完成率、每因子单元、每协议标签划分的序列数和 TCP `cwnd` 覆盖达到第 5.2 节预注册门槛。
- [ ] 协议校准、开放集、状态误差和检测指标的阈值、随机种子、置信区间及非劣界另行预注册且未查看测试结果。
- [ ] Qwen、HGB、XGBoost、DistilBERT、状态仅基线和统一物理基线均通过新冻结视图的一批次读取检查。
- [ ] A/C 基线复用的五类哈希已逐项判定；需要重跑的基线已形成独立正式实验清单。

---

## 11. 明确阻塞与禁止猜测

当前可解除项：

- 服务器 GeNIS ZIP 已通过大小、MD5、SHA-256、中央目录和成员核验；按第 2.3 节把该原件只读提供给本机并重验后即可闭合本机完整预检输入。
- 本机 TQH 合同引用的 216 个非提取器源文件已通过存在性和字节数核验；正式预检仍须逐项重算 SHA-256。
- 约 98 GiB TQH 原始目录不需要上传服务器；任务 03 本机双派生已通过，待第 2.5 节移交验收闭合后，服务器只读消费规范派生根。
- ns-3 配对矩阵、场景和运行器可在代码实现后用 CPU 生成。

永久证据限制：

- A/C 的 46,140 字节历史提取器快照当前不可从本机或 Git 历史恢复，只能保持 `approved_manifest_only_blocked` / `blocked`。该限制不得通过伪造快照解除，也不得误写成 TQH PCAP、标签或上游制品缺失。

当前硬阻塞项：

- 任务 01/03 生产文件、配置和测试当前尚未全部进入同一正式 Git 提交；生成源锁前必须通过目标行为门禁、完成提交、双端干净工作树与代码锁验收，独立复审随后并行且不阻塞启动。
- 本机尚未取得或只读挂载完整的 `380755720` 字节 GeNIS 正式归档，现有损坏副本禁止使用。
- 本机 TQH 双派生已完成并通过逐字节、模式、行数和 Arrow 语义比较；任务01源锁、执行代码锁、移交清单和服务器消费者包装仍未完成实物验收，因此两份构建保留 `.partial`，不得发布为规范根。
- `TotBytes` 尚未由 HERA 一手实现或逐包网络层复算证明与共同字段语义相同。
- `TcpRtt` 的单位与聚合语义尚未闭合。
- `SrcWin`、`DstWin` 的单位、缩放和聚合语义尚未闭合。
- TQH QUIC 训练真值必须来自受控配置或可信日志；若只能用 profile 推断，QUIC 训练和主收益结论停止。
- ns-3.48 的 `CongestionWindow` 及其他候选 trace 尚未在正式服务器源码和最小运行中核验。

这些硬阻塞不得用相关性、字段名称、经验常识、零填充、单位猜测、标签拟合或人工修表解除。证据不足时唯一允许的结果是写明失败并保持 `NO-GO`。

---

## 12. 计划状态

- [x] 完整读取根目录、论文、实验、脚本、原始材料、输出和过程文档规则。
- [x] 完整读取两份恢复文档、R2 数据合同、最终研究裁决和远程执行合同。
- [x] 只读审计现有 GeNIS、TQH、共享 B0、统一预算、ns-3 和远程启动接口。
- [x] 冻结源边界、字段与单位、三源物化、A/B/C/D、双构建、服务器恢复和基线重跑边界。
- [x] 冻结每个实现任务的文件白名单、公开接口、最小行为测试、服务器验收和制品路径。
- [x] 完成 R2 存储解阻只读审计，并把本机生产、跨主机移交、GeNIS 取得、代码锁和分阶段磁盘门槛修订进本计划。
- [x] 完成任务 03 的本机 TQH 双派生：两次独立构建均含 `35,235` 个样本和 `2,475,729` 个包，四项载荷逐字节与语义一致，比较回执状态为 `pass`。
- [ ] 完成任务 01/03 修订实现、目标行为门禁并绑定同一干净 Git 提交；门禁通过后以 `review_pending` 启动本机阶段并并行复审，不得以当前未跟踪工作树生成正式源锁。
- [ ] 取得本机可读完整 GeNIS，执行本机源预检并完成 TQH 派生的源锁、移交清单和服务器消费者验收。
- [ ] 按修订后的第一波继续任务 04 及其余未完成实现。
- [ ] 完成各任务实现、目标行为门禁、服务器测试和最终双构建；独立复审保持并行，严重或重要发现触发停止与制品作废。
- [ ] 全部 P0/P1 通过后更新两份恢复文档并重新裁决 R2 主实验。
